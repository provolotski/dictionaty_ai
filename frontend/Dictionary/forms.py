from django import forms
from .models import Dictionary

class DictionaryForm(forms.ModelForm):
    class Meta:
        model = Dictionary
        # fields = '__all__'

        fields = ['name', 'code', 'description', 'start_date', 'finish_date','name_eng','description_eng','name_bel','description_bel',
                  'gko','classifier', 'id_status','id_type', 'organization']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название справочника на русском языке...',
                'style': 'font-size: 1rem;'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите уникальный код справочника...',
                'style': 'font-size: 1rem; font-family: monospace;'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Введите описание справочника на русском языке...',
                'style': 'resize: vertical; min-height: 100px;'
            }),
            'description_eng': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Enter dictionary description in English...',
                'style': 'resize: vertical; min-height: 100px;'
            }),
            'description_bel': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Увядзіце апісанне даведніка на беларускай мове...',
                'style': 'resize: vertical; min-height: 100px;'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'style': 'font-size: 1rem;'
            }),
            'finish_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'style': 'font-size: 1rem;'
            }),
            'name_eng': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter dictionary name in English...',
                'style': 'font-size: 1rem;'
            }),
            'name_bel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Увядзіце назву даведніка на беларускай мове...',
                'style': 'font-size: 1rem;'
            }),
            'gko': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите код ГКО...',
                'style': 'font-size: 1rem;'
            }),
            'classifier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название классификатора...',
                'style': 'font-size: 1rem;'
            }),
            'id_status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'font-size: 1rem;'
            }),
            'id_type': forms.Select(attrs={
                'class': 'form-control',
                'style': 'font-size: 1rem;'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название ответственной организации...',
                'style': 'font-size: 1rem;'
            }),
        }
        
        labels = {
            'name': 'Название справочника',
            'code': 'Код справочника',
            'description': 'Описание (русский)',
            'start_date': 'Дата введения в действие',
            'finish_date': 'Дата окончания действия',
            'name_eng': 'Название на английском языке',
            'description_eng': 'Описание на английском языке',
            'name_bel': 'Название на белорусском языке',
            'description_bel': 'Описание на белорусском языке',
            'gko': 'Код ГКО',
            'classifier': 'Классификатор',
            'id_status': 'Статус справочника',
            'id_type': 'Тип справочника',
            'organization': 'Ответственная организация',
        }

        help_texts = {
            'code': 'Уникальный код справочника в системе (например: ORG001, CLASS001)',
            'name': 'Основное название справочника на русском языке',
            'description': 'Подробное описание назначения и содержания справочника',
            'start_date': 'Дата, с которой справочник вводится в действие',
            'finish_date': 'Дата окончания действия справочника (по умолчанию: 31.12.9999)',
            'name_eng': 'Название справочника на английском языке (опционально)',
            'description_eng': 'Описание справочника на английском языке (опционально)',
            'name_bel': 'Название справочника на белорусском языке (опционально)',
            'description_bel': 'Описание справочника на белорусском языке (опционально)',
            'gko': 'Код государственного классификатора (опционально)',
            'classifier': 'Название базового классификатора (опционально)',
            'id_status': 'Статус справочника: действующий или не действующий',
            'id_type': 'Тип справочника: на основе классификатора или локальный',
            'organization': 'Название организации, ответственной за справочник',
        }

class DictionaryDescriptionForm(forms.ModelForm):
    """Форма для редактирования описания справочника"""
    
    class Meta:
        model = Dictionary
        fields = ['description', 'description_eng', 'description_bel']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Введите описание справочника на русском языке...',
                'style': 'resize: vertical; min-height: 100px;'
            }),
            'description_eng': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Enter dictionary description in English...',
                'style': 'resize: vertical; min-height: 100px;'
            }),
            'description_bel': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Увядзіце апісанне даведніка на беларускай мове...',
                'style': 'resize: vertical; min-height: 100px;'
            }),
        }
        labels = {
            'description': 'Описание (русский)',
            'description_eng': 'Описание (английский)',
            'description_bel': 'Описание (белорусский)',
        }
        help_texts = {
            'description': 'Подробное описание назначения и содержания справочника',
            'description_eng': 'Detailed description of the dictionary purpose and content in English',
            'description_bel': 'Падрабязнае апісанне прызначэння і зместу даведніка на беларускай мове',
        }

    def clean(self):
        cleaned_data = super().clean()
        description = cleaned_data.get('description')
        description_eng = cleaned_data.get('description_eng')
        description_bel = cleaned_data.get('description_bel')
        
        # Проверяем, что хотя бы одно описание заполнено
        if not any([description, description_eng, description_bel]):
            raise forms.ValidationError(
                'Необходимо заполнить хотя бы одно описание (на любом языке)'
            )
        
        return cleaned_data