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
    path('admin/contract-preview/<int:request_id>/', addons.admin_contract_preview, name='admin_contract_preview'),

    #tracking
    path('tracking/enter_code', views.tracking_entercode, name='tracking-entercode'),
    path('tracking/result', views.tracking_result, name='tracking-result'),


    path('send-sms-to-admins/', views.send_sms_page_view, name='send_sms_page'),

    path('send-sms-user/<int:pk>', views.send_sms_user, name='send_user_message'),
    path('send-sms-user/<int:pk>/type=<str:type>/', views.send_sms_user_type, name='send_user_message_type'),
    path('send-sms-user/sending/', views.send_sms_user_sending, name='send_user_message_type'),

    path('create_form/<str:kind>/<int:pk>/', addons.create_form, name='create-form'),
    path('download-document/<int:pk>/',addons.download_document_view,name='download-document'),
]


