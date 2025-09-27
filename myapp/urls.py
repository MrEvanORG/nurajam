from django.urls import path 
from . import views
from . import addons

urlpatterns = [
    path('',views.index,name='index'),
    path('send-sms-to-admins/', views.send_sms_page_view, name='send_sms_page'),
    path('create_form/<str:kind>/<int:pk>/', addons.create_form, name='create-form'),
]
