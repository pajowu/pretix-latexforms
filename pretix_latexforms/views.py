import bleach
from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)
from pretix.base.forms import I18nModelForm
from pretix.control.permissions import (
    EventPermissionRequiredMixin,
    event_permission_required,
)
from pretix.presale.utils import event_view

from .models import LatexTemplate
from django_scopes.forms import (
    SafeModelChoiceField,
    SafeModelMultipleChoiceField,
)
from django_scopes import scope

from django.shortcuts import get_object_or_404
from pretix.base.models import Event, Order
from django.http import HttpResponse
from .tex import render_tex, latex_jinja_env


class TemplateList(EventPermissionRequiredMixin, ListView):
    model = LatexTemplate
    context_object_name = "templates"
    paginate_by = 20
    template_name = "pretix_latexforms/index.html"
    permission = "can_change_event_settings"

    def get_queryset(self):
        return LatexTemplate.objects.filter(event=self.request.event)


class TemplateForm(I18nModelForm):
    def __init__(self, *args, **kwargs):
        self.event = kwargs.get("event")
        super().__init__(*args, **kwargs)
        self.fields["limit_products"].queryset = self.event.items.all()

    class Meta:
        model = LatexTemplate
        fields = ("title", "text", "all_products", "limit_products")
        widgets = {
            "limit_products": forms.CheckboxSelectMultiple(
                attrs={"class": "scrolling-multiple-choice"}
            ),
        }
        field_classes = {
            "limit_products": SafeModelMultipleChoiceField,
        }


class TemplateEditForm(TemplateForm):
    pass


class TemplateDetailMixin:
    def get_object(self, queryset=None) -> LatexTemplate:
        try:
            return LatexTemplate.objects.get(
                event=self.request.event, id=self.kwargs["template"]
            )
        except LatexTemplate.DoesNotExist:
            raise Http404(_("The requested template does not exist."))

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_latexforms:index",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )


class TemplateDelete(EventPermissionRequiredMixin, TemplateDetailMixin, DeleteView):
    model = LatexTemplate
    form_class = TemplateForm
    template_name = "pretix_latexforms/delete.html"
    context_object_name = "template"
    permission = "can_change_event_settings"

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.log_action(
            "pretix_latexforms.template.deleted", user=self.request.user
        )
        self.object.delete()
        messages.success(request, _("The selected template has been deleted."))
        self.request.event.cache.clear()
        return HttpResponseRedirect(self.get_success_url())


class TemplateEditorMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.request.event
        return kwargs

    def form_invalid(self, form):
        messages.error(
            self.request, _("We could not save your changes. See below for details.")
        )
        return super().form_invalid(form)

class TemplateUpdate(
    EventPermissionRequiredMixin, TemplateDetailMixin, TemplateEditorMixin, UpdateView
):
    model = LatexTemplate
    form_class = TemplateEditForm
    template_name = "pretix_latexforms/form.html"
    context_object_name = "template"
    permission = "can_change_event_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_latexforms:edit",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
                "template": self.object.pk,
            },
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx["locales"] = []
        for lng in self.request.event.settings.locales:
            dataline = (
                self.object.text.data[lng]
                if self.object.text is not None
                and (isinstance(self.object.text.data, dict))
                and lng in self.object.text.data
                else ""
            )
            ctx["locales"].append((lng, dataline))
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        messages.success(self.request, _("Your changes have been saved."))
        if form.has_changed():
            self.object.log_action(
                "pretix_latexforms.template.changed",
                user=self.request.user,
                data={k: form.cleaned_data.get(k) for k in form.changed_data},
            )
        self.request.event.cache.clear()
        return super().form_valid(form)


class TemplateCreate(EventPermissionRequiredMixin, TemplateEditorMixin, CreateView):
    model = LatexTemplate
    form_class = TemplateForm
    template_name = "pretix_latexforms/form.html"
    permission = "can_change_event_settings"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx["locales"] = [(l, "") for l in self.request.event.settings.locales]
        return ctx

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_latexforms:index",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    @transaction.atomic
    def form_valid(self, form):
        form.instance.event = self.request.event
        form.instance.position = (
            self.request.event.latextemplate_set.aggregate(p=Max("position"))["p"] or 0
        ) + 1
        messages.success(self.request, _("The new template has been created."))
        ret = super().form_valid(form)
        form.instance.log_action(
            "pretix_latexforms.template.added",
            data=dict(form.cleaned_data),
            user=self.request.user,
        )
        self.request.event.cache.clear()
        return ret

@scope(organizer=None)
def form_download(request, organizer, event, order, secret, template):
    event = get_object_or_404(
        Event.objects.select_related("organizer"),
        slug__iexact=event,
        organizer__slug__iexact=organizer,
    )
    order = get_object_or_404(Order, event=event, code=order, secret=secret)
    template = get_object_or_404(
        LatexTemplate.objects.filter(event=event).filter(
            limit_products__in=order.positions.values_list("item__pk", flat=True)
        ),
        pk=template,
    )
    jinja_template = latex_jinja_env.from_string(str(template.text))
    form_source = jinja_template.render(order=order)
    filename = "{order} - {title}.pdf".format(order=order.code, title=template.title)
    response = HttpResponse(render_tex(form_source), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="{filename}"'.format(
        filename=filename
    )
    return response
