import logging
from django.db import models
from datetime import date
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)

class Dictionary(models.Model):
    STATUS_CHOICES = [
        (0, 'Не действующий'),
        (1, 'Действующий'),
    ]

    DICTIONARY_TYPE = [
        (0, 'На основе классификатора'),
        (1, 'Локальный справочник'),
    ]

    name = models.CharField('Название', max_length=120)
    code = models.CharField('Код', max_length=20)
    description = models.TextField('Описание', blank=True)
    start_date = models.DateField('Дата введения в действие', default=date.today)
    finish_date = models.DateField('дата окончания действия', default='9999-12-31')
    name_eng = models.CharField('Название на английском языке', max_length=255, blank=True)
    description_eng = models.TextField('Описание на английском языке', blank=True)
    name_bel = models.CharField('Название на белорусском языке', max_length=255, blank=True)
    description_bel = models.TextField('Описание на белорусском языке', blank=True)
    gko = models.CharField('ГКО', max_length=255, blank=True)
    classifier = models.CharField('классификатор', max_length=255, blank=True)
    id_status = models.IntegerField('Статус', choices=STATUS_CHOICES, default=1)
    id_type = models.IntegerField('Тип справочника', choices=DICTIONARY_TYPE, default=0)
    organization = models.CharField('Ответственная организация', max_length=255, blank=True)
    id = models.AutoField('ID справочника', primary_key=True)  # Изменено на AutoField

    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'
        ordering = ['name']

    def __str__(self):
        return f"({self.code}) {self.name}"

    def save(self, *args, **kwargs):
        logger.info('save')
        super().save(*args, **kwargs)
        # Убрана асинхронная задача для упрощения


class DictionaryIn(BaseModel):
    """Базовая модель описания справочника"""

    name: str = Field(..., description="Наименование на русском языке")
    code: str = Field(..., description="Уникальный код справочника")
    description: str = Field(default="", description="Описание справочника")
    start_date: str = Field(..., description="Дата начала действия")
    finish_date: str = Field(default="9999-12-31", description="Дата окончания действия")
    name_eng: Optional[str] = Field(default="", description="Наименование на английском языке")
    name_bel: Optional[str] = Field(default="", description="Наименование на белорусском языке")
    description_eng: Optional[str] = Field(default="", description="Описание на английском языке")
    description_bel: Optional[str] = Field(default="", description="Описание на белорусском языке")
    gko: str = Field(default="", description="ГКО")
    organization: str = Field(default="", description="Организация")
    classifier: Optional[str] = Field(default="", description="Классификатор")
    id_status: int = Field(default=1, description="Статус справочника")
    id_type: int = Field(default=0, description="Тип справочника")