from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from i18nfield.fields import I18nCharField, I18nTextField
from pretix.base.models import LoggedModel
from django_scopes import ScopedManager

class LatexTemplate(LoggedModel):
    event = models.ForeignKey('pretixbase.Event', on_delete=models.CASCADE)
    position = models.IntegerField(default=0)
    title = I18nCharField(verbose_name=_('Template name'))
    text = I18nTextField(verbose_name=_('Template code'))
    all_products = models.BooleanField(blank=True)
    limit_products = models.ManyToManyField('pretixbase.Item', verbose_name=_("Limit to products"), blank=True)

    objects = ScopedManager(organizer='event__organizer')

    class Meta:
        ordering = ['position', 'title']
