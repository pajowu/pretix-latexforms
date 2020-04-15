from django.dispatch import receiver
from django.template.loader import get_template
from django.urls import resolve, reverse
from django.utils.translation import ugettext_lazy as _, get_language
from pretix.base.signals import logentry_display, event_copy_data
from pretix.control.signals import nav_event
from pretix.multidomain.urlreverse import eventreverse
from pretix.presale.signals import (
    checkout_confirm_messages, order_info
)

from .models import LatexTemplate
from django.forms import formset_factory
from django.forms import BaseFormSet
from django.forms import formset_factory
from django.shortcuts import render
from django.template import loader
from pretix.base.models import Order

@receiver(nav_event, dispatch_uid="latexforms_nav")
def control_nav_templates(sender, request=None, **kwargs):
    if not request.user.has_event_permission(request.organizer, request.event, 'can_change_event_settings',
                                             request=request):
        return []
    url = resolve(request.path_info)
    return [
        {
            'label': _('Latex Templates'),
            'url': reverse('plugins:pretix_latexforms:index', kwargs={
                'event': request.event.slug,
                'organizer': request.event.organizer.slug,
            }),
            'active': (url.namespace == 'plugins:pretix_latexforms'),
            'icon': 'file-text',
        }
    ]


@receiver(signal=event_copy_data, dispatch_uid="latexforms_copy_data")
def event_copy_data_receiver(sender, other, **kwargs):
    for p in LatexTemplate.objects.filter(event=other):
        p.pk = None
        p.event = sender
        p.save()


@receiver(signal=logentry_display, dispatch_uid="latexforms_logentry_display")
def pretixcontrol_logentry_display(sender, logentry, **kwargs):
    event_type = logentry.action_type
    plains = {
        'pretix_latexforms.template.added': _('The template has been created.'),
        'pretix_latexforms.template.changed': _('The template has been modified.'),
        'pretix_latexforms.template.deleted': _('The template has been deleted.'),
    }

    if event_type in plains:
        return plains[event_type]

@receiver(order_info, dispatch_uid="latexforms_order_info")
def order_info(sender, order, request, **kwargs):
    if order.status == Order.STATUS_PAID:
        template = get_template('pretix_latexforms/order_info.html')
        documents = LatexTemplate.objects.filter(event=sender).filter(limit_products__in=order.positions.values_list('item__pk', flat=True))
        ctx = {
            'order': order,
            'documents': documents,
            'event': sender
        }
        t = loader.get_template('pretix_latexforms/order_info.html')
        return t.render(ctx, request)
