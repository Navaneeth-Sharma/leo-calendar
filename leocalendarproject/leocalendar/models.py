from django.db import models
from schedule.models.events import Event
import tagulous.models


class LeoEvent(Event):

    emails = tagulous.models.TagField(
        blank=True,
        null=True,
        force_lowercase=True,
        max_count=5,
    )
