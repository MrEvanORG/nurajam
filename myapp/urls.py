from django.urls import path 
from . import views
from . import addons

urlpatterns = [
    path('',views.index,name='index'),
    
    #register 
    path('register/index',views.register_index,name='register-index'),
    path('register/get_phonenumber', views.register_getnumber, name='register-getnumber'),
    path('register/send_otp',addons.register_sendotp,name="send-otp"),
    path('register/verify_phonenumber', views.register_verifyphonenumber, name='register-verifynumber'),
    path('register/personal_information', views.register_personal, name='register-personal'),
    path('register/select_service', views.register_selectservice, name='register-service'),
    path('register/contract_drafted', views.register_contractdrafted, name='register-contract'),

    path('send-sms-to-admins/', views.send_sms_page_view, name='send_sms_page'),

    path('send-sms-to-user', views.send_sms_page_view_user, name='send_user_message'),
    path('create_form/<str:kind>/<int:pk>/', addons.create_form, name='create-form'),
]
