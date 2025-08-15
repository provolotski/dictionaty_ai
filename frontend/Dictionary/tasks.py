import requests
from celery import shared_task
import logging
from .models import Dictionary


logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def sync_with_api(self, dictonary_id):
    instance = Dictionary.objects.get(id=dictonary_id)
    logger.info(instance)

