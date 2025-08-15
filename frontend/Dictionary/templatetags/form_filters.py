# templatetags/form_filters.py
from django import template
from django.forms import widgets

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Добавляет CSS класс к полю формы"""
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        widget = field.field.widget
        if hasattr(widget, 'attrs'):
            widget.attrs['class'] = widget.attrs.get('class', '') + ' ' + css_class
        else:
            widget.attrs = {'class': css_class}
    return field

@register.filter
def widget_type(field):
    """Возвращает тип виджета поля"""
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        return field.field.widget.__class__.__name__
    return ''

@register.filter
def input_type(field):
    """Возвращает тип input для поля"""
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        widget = field.field.widget
        if hasattr(widget, 'input_type'):
            return widget.input_type
        elif isinstance(widget, widgets.Textarea):
            return 'textarea'
        elif isinstance(widget, widgets.Select):
            return 'select'
        elif isinstance(widget, widgets.DateInput):
            return 'date'
        elif isinstance(widget, widgets.CheckboxInput):
            return 'checkbox'
    return 'text'

@register.filter
def field_errors(field):
    """Возвращает ошибки поля в виде списка"""
    if hasattr(field, 'errors'):
        return field.errors
    return []

@register.inclusion_tag('dictionaries/form_field.html')
def render_field(field, label_class='', field_class='', help_class='form-text'):
    """Рендерит поле формы с Bootstrap классами"""
    return {
        'field': field,
        'label_class': label_class,
        'field_class': field_class,
        'help_class': help_class,
    }