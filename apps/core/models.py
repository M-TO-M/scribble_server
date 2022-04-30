from dataclasses import dataclass

from django.db import models


@dataclass
class Default:
    user: int
    book_object: int
    note: int
    page: int
    page_comment: int


class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
