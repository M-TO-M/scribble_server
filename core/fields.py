import re

from django.db.models import CharField
from django.utils.translation import gettext_lazy as _
from django.core.validators import EMPTY_VALUES

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.validators import ISBNValidator


class ChoiceTypeField(serializers.ChoiceField):
    def __init__(self, valid_choice=None, **kwargs):
        super().__init__(**kwargs)
        self.valid_choice = valid_choice

    def fail(self, key, **kwargs):
        msg = self.error_messages.get(key, None)
        message_string = msg.format(**kwargs)
        detail = {"detail": message_string}
        detail.update(self.valid_choice)
        raise ValidationError(detail, code=key)

    default_error_messages = {
        'invalid_choice': "invalid_choice_{input}",
    }


class ISBNField(CharField):

    description = _("ISBN-10 or ISBN-13")

    def __init__(self, normalize_isbn=True, *args, **kwargs):
        self.normalize_isbn = normalize_isbn
        kwargs["max_length"] = kwargs["max_length"] if "max_length" in kwargs else 28
        kwargs["validators"] = [ISBNValidator]
        super(ISBNField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            "min_length": 10,
            "verbose_name": u"ISBN"
        }
        defaults.update(kwargs)
        return super(ISBNField, self).formfield(**defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(ISBNField, self).deconstruct()
        if not self.normalize_isbn:
            kwargs["normalize_isbn"] = self.normalize_isbn
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if self.normalize_isbn and value not in EMPTY_VALUES:
            normalized = re.sub(" |-", "", value).upper()
            setattr(model_instance, self.attname, normalized)
        return super(ISBNField, self).pre_save(model_instance, add)
