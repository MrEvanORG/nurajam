from typing import Any
from django import forms
from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpRequest, HttpResponseRedirect , HttpResponse
from django.contrib.auth import get_user_model 
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User ,ServiceRequests , ActiveLocations , ActiveModems , ActivePlans , OtherInfo
from myapp.templatetags.custom_filters import to_jalali_persian

class NoorajamAdminSite(admin.AdminSite):
    site_header = 'پنل ادمین سایت نوراجم'
    site_title = 'پنل مدیریت'
    index_title = 'به پنل مدیریت شرکت توسعه و زیرساخت نوراجم خوش آمدید'

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        for app in app_list:
            if app['app_label'] == 'myapp':
                custom_order = [
                    'User',
                    'ServiceRequests',
                    'ActiveModems',
                    'ActivePlans',
                    'ActiveLocations',
                    'OtherInfo',
                ]
                app['models'].sort(
                    key=lambda x: custom_order.index(x['object_name'])
                    if x['object_name'] in custom_order else len(custom_order)
                )
        return app_list

super_admin_site = NoorajamAdminSite(name='noorajam_admin')

@admin.register(ServiceRequests , site=super_admin_site)
class ServiceRequestsAdmin(admin.ModelAdmin):
    list_display = ('first_name','last_name','location','mobile_number')
    list_display_links = ("first_name","last_name")

    readonly_fields = ("ip_address","request_time","send_message","view_document","download_document","download_form","log_msg_status","jalali_request_time")

    fieldsets = (
        ('باکس دانلود',{'fields':('view_document','download_document','download_form','documents')}),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'father_name', 'national_code', 'bc_number', 'birthday','landline_number','mobile_number','address','location','post_code','house_is_owner',), 'classes': ('collapse',)
        }),
        ('اطلاعات سرویس', { 
            'fields': ('sip_phone', 'modem','plan'), 'classes': ('collapse',)
        }),
        ('اطلاعات دراپ',{'fields':('fat_index','drop_status','outdoor_area','internal_area','fusion_status','pay_status','submission_status'), 'classes': ('collapse',)}),
        ("سایر اطلاعات",{'fields':('request_status','send_message','tracking_code','log_msg_status','jalali_request_time','ip_address'), 'classes': ('collapse',)}),
    )
    list_filter = ("location","request_status","drop_status","fusion_status","pay_status","submission_status")
    search_fields = ("mobile_number","national_code","post_code")
    ordering = ("-request_time",)

    def jalali_request_time(self, obj):
        return to_jalali_persian(obj.request_time)
    jalali_request_time.short_description = "زمان درخواست"

    def send_message(self,obj):
        return format_html(f"""<a class="button" href="#">ارسال پیامک</a>""")
    send_message.short_description = "ارسال پیامک"       

    def download_form(self,obj):
        return format_html(f"""<a class="button" href="#">دانلود</a>""")
    download_form.short_description = "دانلود فرم ثبت نام"

    def download_document(self,obj):
        url = obj.documents.url
        return format_html(f"""<a class="button" href="{url}" target=_blank download>دانلود</a>""")
    download_document.short_description = "دانلود مدارک"

    def view_document(self,obj):
        url = obj.documents.url
        return format_html(f"""<a class="button" href="{url}">مشاهده</a>""")
    view_document.short_description = "مشاهده مدارک"

    actions = ['export_excel_information']

    @admin.action(description='خروجی اکسل برای کاربران انتخاب شده')
    def export_excel_information(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "شما دسترسی لازم برای انجام این کار را ندارید.", level='error')
            return
        
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['selected_user_ids_for_excel'] = selected_ids

        # return HttpResponseRedirect(reverse('get_excel_export'))
        return HttpResponse("به زودی ...")

@admin.register(ActiveLocations,site=super_admin_site)
class ActiveLocationsAdmin(admin.ModelAdmin):
    list_display = ("name","area_limit")

@admin.register(ActiveModems,site=super_admin_site)
class ActiveModemsAdmin(admin.ModelAdmin):
    list_display = ("name","price","payment_method")

@admin.register(ActivePlans,site=super_admin_site)
class ActivePlansAdmin(admin.ModelAdmin):
    list_display = ("data","price")

@admin.register(OtherInfo,site=super_admin_site)
class OtherInfoAdmin(admin.ModelAdmin):
    list_display = ("sip_phone_cost","drop_cost","center_name","center_address")


User = get_user_model()

class UserAdminForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = User

@admin.register(User,site=super_admin_site)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm

    list_display = ("first_name", "last_name", "username", "email", "is_staff", "is_superuser")

    ordering = ("-date_joined",)

    readonly_fields = ("jalali_last_login", "jalali_date_joined")

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
        ('دسترسی ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ های مهم', {'fields': ('jalali_last_login', 'jalali_date_joined')}),
    )

    def has_add_permission(self, request): return request.user.is_superuser

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        if not request.user.is_superuser:
    
            new_fieldsets = list(fieldsets)

            for fieldset_name, fieldset_options in new_fieldsets:
                if 'is_superuser' in fieldset_options.get('fields', ()):
      
                    fields = list(fieldset_options['fields'])
                    fields.remove('is_superuser')
                    fieldset_options['fields'] = tuple(fields)
                    break 
            return new_fieldsets
        
        return fieldsets

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(pk=request.user.pk)
        return queryset

    def jalali_last_login(self, obj):
        return to_jalali_persian(obj.last_login)
    jalali_last_login.short_description = "آخرین ورود"
    jalali_last_login.admin_order_field = 'last_login'

    def jalali_date_joined(self, obj):
        return to_jalali_persian(obj.date_joined)
    jalali_date_joined.short_description = "تاریخ عضویت"
    jalali_date_joined.admin_order_field = 'date_joined'


    actions = ['send_custom_sms']

    @admin.action(description='ارسال پیامک به کاربران انتخاب شده')
    def send_custom_sms(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "شما دسترسی لازم برای انجام این کار را ندارید.", level='error')
            return
        
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['selected_user_ids_for_sms'] = selected_ids

        return HttpResponseRedirect(reverse('send_sms_page'))