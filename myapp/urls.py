from django.urls import path 
from . import views

urlpatterns = [
    path('',views.index),
    path('send-sms-to-admins/', views.send_sms_page_view, name='send_sms_page'),
]
