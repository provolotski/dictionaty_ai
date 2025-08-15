import requests
from django.conf import settings
from requests.exceptions import RequestException
from .models import Dictionary
from accounts.utils import api_get, api_post

class DictionaryAPIClient:

    @classmethod
    def get_dictionaries(cls):
        """Получение списка справочников"""
        try:
            response = api_get(requests,'/models/list',service='dict')
            dictionaries = response.json()if response.status_code == 200 else []
            return dictionaries
        except RequestException as e:
            print(f"API Error: {str(e)}")
            return None

    @classmethod
    def sync_dictionaries(cls):
        """Синхронизация справочников с API"""
        data = cls.get_dictionaries()
        if not data:
            return False

        for item in data:
            Dictionary.objects.update_or_create(
                external_id=item['id'],
                defaults={
                    'name': item['name'],
                    'code': item['code'],
                    'description': item.get('description', ''),
                    'parent_id': item.get('parent_id')
                }
            )
        return True