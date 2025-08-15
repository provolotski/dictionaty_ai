from django import template

register = template.Library()

@register.filter
def get_range(value):
    """
    Фильтр для генерации диапазона чисел от 1 до value
    Используется для пагинации
    """
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return range(1)
