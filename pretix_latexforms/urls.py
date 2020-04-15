from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/latex/$',
        views.TemplateList.as_view(),
        name='index'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/latex/create$',
        views.TemplateCreate.as_view(),
        name='create'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/latex/(?P<template>\d+)/$',
        views.TemplateUpdate.as_view(),
        name='edit'),
    url(r'^control/event/(?P<organizer>[^/]+)/(?P<event>[^/]+)/latex/(?P<template>\d+)/delete$',
        views.TemplateDelete.as_view(),
        name='delete'),
    url(r'^(?P<organizer>[^/]+)/(?P<event>[^/]+)/order/(?P<order>[^/]+)/(?P<secret>[A-Za-z0-9]+)/download_form/(?P<template>\d+)/$', views.form_download,
        name='download'),
]
