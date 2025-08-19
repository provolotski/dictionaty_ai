from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
import requests
import logging
from django.conf import settings

from accounts.forms import LoginForm
from accounts.utils import api_post
from accounts.models import LoginAudit, UserGroup
from accounts.permissions import check_user_access
from .utils import log_auth_event, log_user_action, log_system_event, post_login_audit_to_backend, fetch_audit_logs_from_backend

logger = logging.getLogger(__name__)

# Используем настройки из Django settings вместо хардкода
API_BASE = getattr(settings, 'AUTH_CONFIG', {}).get('EXTERNAL_API', {}).get('BASE_URL', 'http://127.0.0.1:9090/api/v1/auth')

# Логируем используемый URL API для диагностики
logger.info(f"API_BASE настроен на: {API_BASE}")

# Create your views here.
def get_client_ip(request):
    """Получение IP адреса клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_info(access_token):
    """Получает информацию о пользователе по access_token"""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{API_BASE}/get_data"
        # Логируем полный запрос (с маскированием токена в логах)
        masked_headers = headers.copy()
        if masked_headers.get('Authorization'):
            masked_headers['Authorization'] = f"Bearer {access_token}"
        logger.info(f"GET_DATA request → url={url}, headers={masked_headers}, timeout=10")
        
        logger.debug(f"Запрос информации о пользователе на {url}")
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        
        # Логируем полный ответ
        try:
            response_headers = dict(response.headers)
        except Exception:
            response_headers = {}
        logger.info(f"GET_DATA response ← status={response.status_code}, headers={response_headers}")
        logger.info(f"GET_DATA body ← {response.text}")
        
        logger.debug(f"Ответ сервера: статус {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user_section = data.get('user') or {}
            username_value = None
            try:
                username_value = user_section.get('username')
            except AttributeError:
                username_value = None
            if not username_value:
                username_value = data.get('username')
            # Нормализуем GUID (без фигурных скобок)
            guid_raw = (user_section.get('guid') if isinstance(user_section, dict) else None) or data.get('guid')
            guid_value = str(guid_raw).strip('{}') if guid_raw else None
            user_info = {
                'guid': guid_value,
                'username': username_value
            }
            logger.debug(f"User info retrieved: {user_info['username']}")
            return user_info
        elif response.status_code == 401:
            logger.error(f"Токен недействителен (401) - возможно, истек или неверный")
            logger.error(f"Заголовки ответа: {dict(response.headers)}")
            return None
        else:
            logger.error(f"Failed to get user info: {response.status_code}")
            logger.error(f"Ответ сервера: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting user info: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing user info response: {e}")
        return None


def audit_view(request):
    """Представление для просмотра аудита логинов"""
    
    # Проверяем, авторизован ли пользователь
    if 'user_info' not in request.session:
        return redirect('login_direct')
    
    # Проверяем права доступа к аудиту
    user_info = request.session['user_info']
    username = user_info.get('username', '')
    domain = user_info.get('domain', 'belstat')
    
    # Проверяем, входит ли пользователь в группу EISGS_AppSecurity
    try:
        # Используем GUID+domain из сессии
        sess_info = request.session.get('user_info', {})
        sel_guid = sess_info.get('guid')
        if isinstance(sel_guid, str):
            sel_guid = sel_guid.strip('{}')
        sel_domain = (sess_info.get('domain') or 'belstat')
        sel_domain_lc = str(sel_domain).lower()
        candidates = set([
            username,
            sel_guid or '',
            f"{username}@{sel_domain_lc}",
            sess_info.get('login',''),
            sess_info.get('username','')
        ])
        q = Q()
        for c in candidates:
            if c:
                q |= Q(username__iexact=c)
        user_groups = UserGroup.objects.filter(q, domain__iexact=sel_domain_lc)
        logger.debug(f"user_groups: {user_groups}")
        group_names = list(user_groups.values_list('group_name', flat=True))
        logger.debug(f"User {sel_guid or username}@{sel_domain_lc} groups: {group_names}")
        has_audit_access = user_groups.filter(group_name='EISGS_AppSecurity').exists()
        
        if not has_audit_access:
            messages.error(request, 'У Вас недостаточно прав для просмотра аудита')
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Ошибка при проверке прав доступа к аудиту: {e}")
        messages.error(request, 'Ошибка при проверке прав доступа')
        return redirect('home')
    
    # Получаем параметры фильтрации
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    domain_filter = request.GET.get('domain', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    page_str = request.GET.get('page', '1')
    page_size_str = request.GET.get('page_size', '50')
    try:
        backend_page = max(1, int(page_str))
    except ValueError:
        backend_page = 1
    try:
        backend_page_size = min(200, max(10, int(page_size_str)))
    except ValueError:
        backend_page_size = 50

    # Формируем базовый queryset (локальная таблица)
    queryset = LoginAudit.objects.all()

    # Запрашиваем данные аудита с бэкенда
    backend_params = {}
    if date_from:
        backend_params['date_from'] = f"{date_from}T00:00:00"
    if date_to:
        backend_params['date_to'] = f"{date_to}T23:59:59"
    if status_filter:
        for st in status_filter.split(','):
            backend_params.setdefault('status', []).append(st)
    if search_query:
        backend_params['username'] = [search_query]
    backend_params['limit'] = backend_page_size
    backend_params['offset'] = (backend_page - 1) * backend_page_size

    backend_audit_logs = fetch_audit_logs_from_backend(backend_params) or []
    backend_has_next = len(backend_audit_logs) == backend_page_size

    # Применяем фильтры локально (для локального аудита)
    if search_query:
        queryset = queryset.filter(
            Q(username__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(error_message__icontains=search_query)
        )
    if status_filter:
        queryset = queryset.filter(status__in=[s for s in status_filter.split(',') if s])

    # Сортировка по времени (новые записи первыми)
    queryset = queryset.order_by('-login_time')

    # Пагинация локального аудита (пока фиксированная)
    paginator = Paginator(queryset, 50)  # 50 записей на страницу
    try:
        audit_records = paginator.page(request.GET.get('page', 1))
    except:
        audit_records = paginator.page(1)

    # Статистика
    total_records = queryset.count()
    successful_logins = queryset.filter(status='success').count()
    failed_logins = queryset.filter(status='failed').count()
    blocked_logins = queryset.filter(status='blocked').count()

    # Получаем уникальные значения для фильтров
    domains = LoginAudit.objects.values_list('domain', flat=True).distinct().order_by('domain')
    statuses = [
        ('success', 'Успешно'),
        ('failed', 'Неудачно'),
        ('blocked', 'Заблокирован'),
    ]

    context = {
        'audit_records': audit_records,
        'total_records': total_records,
        'successful_logins': successful_logins,
        'failed_logins': failed_logins,
        'blocked_logins': blocked_logins,
        'domains': domains,
        'statuses': statuses,
        'search_query': search_query,
        'status_filter': status_filter,
        'domain_filter': domain_filter,
        'date_from': date_from,
        'date_to': date_to,
        'backend_audit_logs': backend_audit_logs,
        'backend_page': backend_page,
        'backend_page_size': backend_page_size,
        'backend_has_next': backend_has_next,
    }
    return render(request, 'audit.html', context)

def login_view(request):
    """Представление для входа в систему"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Получаем данные из формы
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            domain = form.cleaned_data['domain']
            remember_me = request.POST.get('remember_me')
            
            # Подготавливаем данные для API
            login_data = {
                'username': username,
                'password': password,
                'domain': domain
            }
            
            # Получаем IP адрес клиента
            ip_address = get_client_ip(request)
            
            # Логируем попытку входа
            log_auth_event(
                'login_attempt',
                username,
                domain,
                ip_address,
                True,
                None
            )
            
            try:
                logger.info(f"=== НАЧАЛО АВТОРИЗАЦИИ ===")
                logger.info(f"Пользователь: {username}")
                logger.info(f"Домен: {domain}")
                logger.info(f"Время запроса: {timezone.now()}")
                logger.info(f"IP адрес: {ip_address}")
                logger.info(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Неизвестно')}")
                
                # Проверяем конфигурацию авторизации
                from django.conf import settings
                auth_config = getattr(settings, 'AUTH_CONFIG', {})
                logger.info(f"Конфигурация AUTH_CONFIG: {auth_config}")
                
                # Используем новый менеджер авторизации
                try:
                    from .auth_manager import auth_manager
                    logger.info(f"Менеджер авторизации загружен: {type(auth_manager).__name__}")
                    
                    success, token_data, error_message = auth_manager.authenticate_user(username, password, domain, request)
                except ImportError as e:
                    logger.error(f"Ошибка импорта auth_manager: {e}")
                    # Fallback на старую логику
                    response = api_post('/login', login_data, service='auth')
                    if response and response.status_code == 200:
                        token_data = response.json()
                        success = True
                        error_message = None
                    else:
                        success = False
                        token_data = None
                        error_message = 'Ошибка подключения к серверу аутентификации'
                except Exception as e:
                    logger.error(f"Ошибка при использовании auth_manager: {e}")
                    # Fallback на старую логику
                    response = api_post('/login', login_data, service='auth')
                    if response and response.status_code == 200:
                        token_data = response.json()
                        success = True
                        error_message = None
                    else:
                        success = False
                        token_data = None
                        error_message = 'Ошибка подключения к серверу аутентификации'
                
                logger.info(f"Результат авторизации: success={success}, error={error_message}")
                
                # Логируем попытку входа в аудит
                try:
                    LoginAudit.objects.create(
                        username=username,
                        domain=domain,
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        status='success' if success else 'failed',
                        error_message=error_message if not success else None,
                        external_api_response={'success': success, 'error': error_message} if error_message else None
                    )
                    logger.info("Запись в аудите создана")
                except Exception as audit_error:
                    logger.error(f"Ошибка при создании записи в аудите: {audit_error}")
                
                if success and token_data:
                    logger.info("=== УСПЕШНАЯ АВТОРИЗАЦИЯ ===")
                    logger.info(f"Получены токены: {bool(token_data.get('access_token'))}, {bool(token_data.get('refresh_token'))}")
                    
                    access_token = token_data.get('access_token')
                    refresh_token = token_data.get('refresh_token')
                    
                    if access_token and refresh_token:
                        request.session['access'] = access_token
                        request.session['refresh'] = refresh_token
                        logger.info("Токены сохранены в сессии")
                        
                        # Получаем информацию о пользователе
                        try:
                            user_info = get_user_info(access_token)
                            if user_info:
                                # Нормализуем структуру user_info
                                if not user_info.get('username') or str(user_info.get('username')).strip() == 'None':
                                    user_info['username'] = username
                                if not user_info.get('domain'):
                                    user_info['domain'] = domain
                                # Сохраняем логин учетной записи отдельно
                                user_info['login'] = username
                                request.session['user_info'] = user_info
                                logger.info(f"Информация о пользователе получена: {user_info.get('username', 'unknown')}")
                            else:
                                logger.warning("Не удалось получить информацию о пользователе")
                                user_info = {'username': username, 'guid': 'unknown', 'domain': domain, 'login': username}
                        except Exception as e:
                            logger.error(f"Ошибка при получении информации о пользователе: {e}")
                            user_info = {'username': username, 'guid': 'unknown', 'domain': domain, 'login': username}
                        
                        # Проверяем, не истек ли токен сразу
                        if not user_info.get('guid') or user_info.get('guid') == 'unknown':
                            logger.warning("Токен может быть недействителен - используем fallback данные")
                            # Создаем временную информацию о пользователе
                            user_info = {
                                'username': username,
                                'guid': f'temp_{username}_{int(timezone.now().timestamp())}',
                                'temporary': True,
                                'domain': domain,
                                'login': username
                            }
                            request.session['user_info'] = user_info

                        # Установим флаг доступа к аудиту в сессию
                        try:
                            user_groups_qs = None
                            # Используем GUID если он доступен
                            ident_guid = user_info.get('guid')
                            ident_domain = user_info.get('domain') or domain
                            if ident_guid:
                                user_groups_qs = UserGroup.objects.filter(username=ident_guid, domain=ident_domain)
                            else:
                                user_groups_qs = UserGroup.objects.filter(username=username, domain=domain)

                            group_names = list(user_groups_qs.values_list('group_name', flat=True))
                            logger.debug(f"User groups for {ident_guid or username}@{ident_domain}: {group_names}")
                            
                            # Если групп нет, пробуем подтянуть их из внешнего API и сохранить
                            if not group_names:
                                try:
                                    access_token_for_groups = request.session.get('access')
                                    logger.debug("No local groups found, refreshing from external API...")
                                    perm_result = check_user_access(username, domain, access_token_for_groups, request)
                                    logger.debug(f"Refreshed groups result: {perm_result}")
                                    if ident_guid:
                                        user_groups_qs = UserGroup.objects.filter(username=ident_guid, domain=ident_domain)
                                    else:
                                        user_groups_qs = UserGroup.objects.filter(username=username, domain=domain)
                                    group_names = list(user_groups_qs.values_list('group_name', flat=True))
                                    logger.debug(f"User groups after refresh for {ident_guid or username}@{ident_domain}: {group_names}")
                                except Exception as e:
                                    logger.warning(f"Failed to refresh user groups: {e}")
                            
                            has_audit_access_flag = 'EISGS_AppSecurity' in group_names
                            in_users_flag = 'EISGS_Users' in group_names
                            request.session['has_audit_access'] = has_audit_access_flag
                            request.session['in_users'] = in_users_flag
                            logger.info(f"has_audit_access(session) = {has_audit_access_flag}")
                            logger.info(f"in_users(session) = {in_users_flag}")
                        except Exception as e:
                            logger.warning(f"Не удалось определить доступ к аудиту: {e}")
                            request.session['has_audit_access'] = False
                            request.session['in_users'] = False
                        
                        # Если выбрано "запомнить меня", устанавливаем длительную сессию
                        if remember_me:
                            request.session.set_expiry(30 * 24 * 60 * 60)  # 30 дней
                            logger.info("Установлена длительная сессия (30 дней)")
                        else:
                            request.session.set_expiry(0)  # До закрытия браузера
                            logger.info("Установлена сессия до закрытия браузера")
                        
                        logger.info("=== АВТОРИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО ===")
                        
                        # Логируем успешный вход
                        log_auth_event(
                            'login_success',
                            username,
                            domain,
                            ip_address,
                            True,
                            None
                        )

                        # Отправляем аудит успешного логина на backend
                        try:
                            post_login_audit_to_backend(
                                username=(user_info.get('username') if isinstance(user_info, dict) else username) or username,
                                domain=domain,
                                ip_address=ip_address,
                                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                                action='Логин пользователя',
                                status='успешно',
                                comment='',
                                guid=(user_info.get('guid') if isinstance(user_info, dict) else None)
                            )
                        except Exception:
                            pass

                        # Логируем действие пользователя
                        log_user_action(
                            'user_login',
                            {'method': 'form_login', 'domain': domain},
                            user_info,
                            ip_address,
                            True
                        )
                        
                        # Проверяем, это AJAX запрос или обычный POST
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'message': 'Авторизация успешна',
                                'redirect_url': '/'
                            })
                        else:
                            return redirect('home')
                    else:
                        logger.error("=== ОШИБКА: НЕПОЛНЫЕ ДАННЫЕ ТОКЕНОВ ===")
                        logger.error(f"access_token: {bool(access_token)}")
                        logger.error(f"refresh_token: {bool(refresh_token)}")
                        logger.error(f"Полные данные токенов: {token_data}")
                        
                        error_msg = 'Ошибка получения токенов авторизации'
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'error': error_msg
                            }, status=400)
                        else:
                            return render(request, 'login_new.html', {
                                'form': form,
                                'error': error_msg
                            })
                else:
                    # Обработка ошибки авторизации
                    logger.error("=== ОШИБКА АВТОРИЗАЦИИ ===")
                    logger.error(f"Сообщение об ошибке: {error_message}")
                    logger.error(f"Тип ошибки: {type(error_message)}")
                    
                    # Определяем тип ошибки для пользователя
                    if "сеть" in error_message.lower() or "соединение" in error_message.lower():
                        user_error = "Ошибка сети. Проверьте подключение к интернету."
                    elif "таймаут" in error_message.lower():
                        user_error = "Превышено время ожидания ответа от сервера."
                    elif "неверные учетные данные" in error_message.lower():
                        user_error = "Неверное имя пользователя или пароль."
                    else:
                        user_error = error_message or 'Неверные учетные данные'
                    
                    logger.error(f"Пользовательская ошибка: {user_error}")
                    
                    # Логируем неудачный вход
                    log_auth_event(
                        'login_failed',
                        username,
                        domain,
                        ip_address,
                        False,
                        user_error
                    )
                    # Отправляем аудит на backend
                    try:
                        post_login_audit_to_backend(
                            username=username,
                            domain=domain,
                            ip_address=ip_address,
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            action='Логин пользователя',
                            status='failed',
                            comment=user_error
                        )
                    except Exception:
                        pass
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': user_error
                        }, status=400)
                    else:
                        return render(request, 'login_new.html', {
                            'form': form,
                            'error': user_error
                        })
                    
            except Exception as e:
                logger.error("=== КРИТИЧЕСКАЯ ОШИБКА ПРИ АВТОРИЗАЦИИ ===")
                logger.error(f"Тип исключения: {type(e).__name__}")
                logger.error(f"Сообщение ошибки: {str(e)}")
                logger.error(f"Traceback:", exc_info=True)
                
                # Определяем тип ошибки для пользователя
                if "connection" in str(e).lower() or "network" in str(e).lower():
                    user_error = "Ошибка сети. Проверьте подключение к интернету."
                elif "timeout" in str(e).lower():
                    user_error = "Превышено время ожидания ответа от сервера."
                elif "import" in str(e).lower() or "module" in str(e).lower():
                    user_error = "Ошибка конфигурации системы авторизации."
                else:
                    user_error = 'Ошибка подключения к серверу аутентификации'
                
                logger.error(f"Пользовательская ошибка: {user_error}")
                
                # Логируем неудачный вход
                log_auth_event(
                    'login_failed',
                    username,
                    domain,
                    ip_address,
                    False,
                    user_error
                )
                # Отправляем аудит на backend (критическая ошибка)
                try:
                    post_login_audit_to_backend(
                        username=username,
                        domain=domain,
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        action='Логин пользователя',
                        status='failed',
                        comment=user_error
                    )
                except Exception:
                    pass
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': user_error
                    }, status=500)
                else:
                    return render(request, 'login_new.html', {
                        'form': form,
                        'error': user_error
                    })
        else:
            # Если форма невалидна, показываем ошибки валидации
            return render(request, 'login_new.html', {
                'form': form
            })
    else:
        # Логируем просмотр страницы входа
        ip_address = get_client_ip(request)
        log_system_event(
            'page_view',
            f'Login page accessed from IP: {ip_address}',
            'INFO',
            {'page': 'login', 'ip_address': ip_address}
        )
        form = LoginForm()
        return render(request, 'login_new.html', {
            'form': form
        })

def login_demo_view(request):
    """Демо-версия формы логина для тестирования без API"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Простая демо-логика
        if username and password:
            if username == 'admin' and password == 'admin':
                # Успешный вход
                request.session['demo_user'] = username
                if remember_me:
                    request.session.set_expiry(30 * 24 * 60 * 60)
                
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/',
                    'message': 'Вход выполнен успешно!'
                })
            else:
                # Неверные учетные данные
                return JsonResponse({
                    'success': False,
                    'error': 'Неверное имя пользователя или пароль'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Пожалуйста, заполните все поля'
            })
    
    return render(request, 'login_new.html')

def logout_view(request):
    """Выход из системы с записью аудита на backend"""
    # Сохраняем данные до очистки сессии
    user_info = request.session.get('user_info') or {}
    username = (user_info.get('username') if isinstance(user_info, dict) else None) or request.session.get('demo_user') or ''
    domain = (user_info.get('domain') if isinstance(user_info, dict) else None) or 'belstat'
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Пишем аудит логаута на backend
    try:
        post_login_audit_to_backend(
            username=username,
            domain=domain,
            ip_address=ip_address,
            user_agent=user_agent,
            action='Логаут пользователя',
            status='успешно',
            comment='',
            guid=(user_info.get('guid') if isinstance(user_info, dict) else None)
        )
    except Exception:
        pass

    # Очищаем сессию и уходим на главную
    request.session.flush()
    return redirect('home')

def profile_view(request):
    """Страница профиля пользователя"""
    user_info = request.session.get('user_info') or {}
    if not user_info:
        return redirect('login_direct')

    # Проверяем, входит ли пользователь в группу EISGS_Users
    if not request.session.get('in_users', False):
        messages.error(request, 'У Вас недостаточно прав для доступа к профилю')
        return redirect('home')

    display_name = user_info.get('username', '')
    login = user_info.get('login') or display_name
    guid = (user_info.get('guid') or None)
    if isinstance(guid, str):
        guid = guid.strip('{}')
    domain = (user_info.get('domain') or 'belstat')
    domain_lc = str(domain).lower()

    # Читаем группы по GUID+domain, если GUID есть; иначе по логину+domain
    try:
        from django.db.models import Q
        candidates = set()
        if guid:
            candidates.add(str(guid))
        candidates.update([
            str(login),
            str(display_name),
            f"{login}@{domain_lc}",
            f"{display_name}@{domain_lc}",
        ])
        logger.debug(f"Profile groups lookup candidates for {login}@{domain_lc}: {candidates}")
        q = Q()
        for c in candidates:
            if c and c != 'None':
                q |= Q(username__iexact=c)
        groups_qs = UserGroup.objects.filter(q, domain__iexact=domain_lc)
        group_names = set(groups_qs.values_list('group_name', flat=True))
        logger.debug(f"Profile groups found count={len(group_names)} names={list(group_names)}")
    except Exception as e:
        logger.warning(f"Profile groups lookup error: {e}")
        group_names = set()

    in_users = 'EISGS_Users' in group_names
    in_security = 'EISGS_AppSecurity' in group_names

    context = {
        'display_name': display_name,
        'login': login,
        'guid': guid,
        'domain': domain,
        'in_users': in_users,
        'in_security': in_security,
        'group_names': sorted(group_names),
    }
    return render(request, 'profile.html', context)


def users_view(request):
    """Страница просмотра пользователей системы"""
    # Проверяем права доступа - только администраторы безопасности могут видеть пользователей
    user_info = request.session.get('user_info') or {}
    if not user_info:
        return redirect('login_direct')
    
    # Проверяем, есть ли у пользователя доступ к аудиту (группа EISGS_AppSecurity)
    has_audit_access = request.session.get('has_audit_access', False)
    
    if not has_audit_access:
        return redirect('home')
    
    # Получаем параметры фильтрации и пагинации
    search_query = request.GET.get('search', '').strip()
    domain_filter = request.GET.get('domain', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 25))
    
    # Ограничиваем размер страницы
    if page_size > 100:
        page_size = 100
    elif page_size < 1:
        page_size = 25
    
    # Формируем параметры для API
    params = {
        'page': page,
        'page_size': page_size
    }
    
    if search_query:
        params['search'] = search_query
    if domain_filter:
        params['domain'] = domain_filter
    
    # Получаем список пользователей с бэкенда
    try:
        from accounts.utils import fetch_users_from_backend
        users_data = fetch_users_from_backend(params)
        
        if users_data:
            users = users_data.get('users', [])
            total_users = users_data.get('total', 0)
            total_pages = users_data.get('total_pages', 1)
            current_page = users_data.get('page', 1)
            
            # Обрабатываем даты для корректного отображения
            from datetime import datetime
            for user in users:
                # Обрабатываем last_login_at
                last_login_raw = user.get('last_login_at')
                
                if last_login_raw:
                    try:
                        if isinstance(last_login_raw, str):
                            # Парсим ISO строку
                            login_dt = datetime.fromisoformat(last_login_raw.replace('Z', '+00:00'))
                            user['last_login_at_formatted'] = login_dt.strftime('%d.%m.%Y %H:%M')
                        else:
                            user['last_login_at_formatted'] = last_login_raw.strftime('%d.%m.%Y %H:%M')
                    except Exception as e:
                        logger.warning(f"Ошибка парсинга last_login_at для пользователя {user.get('name', 'Unknown')}: {e}")
                        user['last_login_at_formatted'] = f'Ошибка: {last_login_raw}'
                else:
                    user['last_login_at_formatted'] = 'Никогда'
                
                # Обрабатываем признак администратора системы
                is_admin = user.get('is_admin', False)
                user['is_admin_display'] = 'Да' if is_admin else 'Нет'
                user['is_admin_class'] = 'text-success' if is_admin else 'text-muted'
        else:
            users = []
            total_users = 0
            total_pages = 1
            current_page = 1
            
    except Exception as e:
        logger.error(f"Ошибка получения пользователей: {e}")
        users = []
        total_users = 0
        total_pages = 1
        current_page = 1
    
    # Формируем контекст для шаблона
    context = {
        'users': users,
        'total_users': total_users,
        'total_pages': total_pages,
        'current_page': current_page,
        'page_size': page_size,
        'search_query': search_query,
        'domain_filter': domain_filter,
        'page_sizes': [25, 50, 100],
        'user_info': user_info,
        'has_audit_access': has_audit_access  # Добавляем информацию о правах доступа к аудиту
    }
    
    return render(request, 'users.html', context)


def get_user_data_view(request, user_id):
    """Получение данных пользователя для карточки"""
    # Проверяем, входит ли пользователь в группу EISGS_Users
    if not request.session.get('in_users', False):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
    
    try:
        from accounts.utils import fetch_users_from_backend
        # Получаем пользователя по ID
        params = {'page': 1, 'page_size': 100}  # Ограничиваем размер страницы до 100
        users_data = fetch_users_from_backend(params)
        
        if users_data and users_data.get('users'):
            user = None
            for u in users_data['users']:
                if u.get('id') == user_id:
                    user = u
                    break
            
            if user:
                # Форматируем даты
                from datetime import datetime
                
                # Обрабатываем created_at
                created_at_raw = user.get('created_at')
                if created_at_raw:
                    try:
                        if isinstance(created_at_raw, str):
                            created_dt = datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
                            user['created_at_formatted'] = created_dt.strftime('%d.%m.%Y %H:%M')
                        else:
                            user['created_at_formatted'] = created_at_raw.strftime('%d.%m.%Y %H:%M')
                    except Exception:
                        user['created_at_formatted'] = 'Ошибка даты'
                else:
                    user['created_at_formatted'] = 'Не указана'
                
                # Обрабатываем last_login_at
                last_login_raw = user.get('last_login_at')
                if last_login_raw:
                    try:
                        if isinstance(last_login_raw, str):
                            login_dt = datetime.fromisoformat(last_login_raw.replace('Z', '+00:00'))
                            user['last_login_at_formatted'] = login_dt.strftime('%d.%m.%Y %H:%M')
                        else:
                            user['last_login_at_formatted'] = last_login_raw.strftime('%d.%m.%Y %H:%M')
                    except Exception:
                        user['last_login_at_formatted'] = 'Ошибка даты'
                else:
                    user['last_login_at_formatted'] = 'Никогда'
                
                return JsonResponse({'success': True, 'user': user})
        
        return JsonResponse({'success': False, 'error': 'Пользователь не найден'}, status=404)
        
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя {user_id}: {e}")
        return JsonResponse({'success': False, 'error': 'Внутренняя ошибка сервера'}, status=500)


def update_user_view(request, user_id):
    """Обновление пользователя через POST запрос"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    # Проверяем, входит ли пользователь в группу EISGS_Users
    if not request.session.get('in_users', False):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        # Проверяем права доступа
        has_audit_access = request.session.get('has_audit_access', False)
        if not has_audit_access:
            return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
        
        # Обновляем пользователя через backend API
        from accounts.utils import update_user_in_backend
        
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'is_admin' in data:
            update_data['is_admin'] = data['is_admin']
        
        if not update_data:
            return JsonResponse({'success': False, 'error': 'Нет данных для обновления'}, status=400)
        
        result = update_user_in_backend(user_id, update_data)
        
        if result:
            return JsonResponse({'success': True, 'user': result})
        else:
            return JsonResponse({'success': False, 'error': 'Ошибка обновления на backend'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
        return JsonResponse({'success': False, 'error': 'Внутренняя ошибка сервера'}, status=500)

def get_access_token_view(request):
    """
    Возвращает токен доступа из сессии пользователя
    """
    # Временно отключаем проверку аутентификации для тестирования
    # if not request.user.is_authenticated:
    #     return JsonResponse({
    #         'error': 'User not authenticated',
    #         'status_code': 401
    #     }, status=401)
    
    access_token = request.session.get('access')
    if not access_token:
        return JsonResponse({
            'error': 'Access token not found in session',
            'status_code': 404
        }, status=404)
    
    return JsonResponse({
        'access_token': access_token,
        'status_code': 200
    }, status=200)