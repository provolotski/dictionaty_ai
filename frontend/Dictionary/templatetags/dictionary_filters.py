from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Получает значение из словаря по ключу
    Использование: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
