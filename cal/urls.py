#encoding: utf-8


from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('ajax_demo', views.ajax_demo),
    path('calendar/<user_id>', views.calendar)
]

