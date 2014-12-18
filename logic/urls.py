from django.conf.urls import patterns, include, url
from django.contrib import admin
import logic.views

urlpatterns = patterns(
    '',
    url(r'^$', logic.views.home, name='home'),
)
