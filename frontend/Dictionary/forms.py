from django import forms
from .models import Dictionary

class DictionaryForm(forms.ModelForm):
    class Meta:
        model = Dictionary
        # fields = '__all__'

        fields = ['name', 'code', 'description', 'start_date', 'finish_date','name_eng','description_eng','name_bel','description_bel',
                  'gko','classifier', 'id_status','id_type', 'organization']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'description_eng': forms.Textarea(attrs={'rows': 3}),
            'description_bel': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'finish_date': forms.DateInput(attrs={'type': 'date'}),

        }

        help_texts = {
            'code': 'Прям Уникальный код справочника',
        }