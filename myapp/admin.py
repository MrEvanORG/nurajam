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
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe



class DisplayOnlyWidget(forms.Widget):
    def __init__(self, text, color="black", *args, **kwargs):
        self.text = text
        self.color = color
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        html = f"<div style='padding:5px; color:{self.color}; font-weight:normal;'>{self.text}</div>"
        return mark_safe(html)

class NoorajamAdminSite(admin.AdminSite):
    site_header = 'پنل ادمین سایت نوراجم'
    site_title = 'پنل مدیریت'
    index_title = 'به پنل مدیریت شرکت توسعه و زیرساخت نوراجم خوش آمدید'

    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        for app in app_list:
            if app['app_label'] == 'myapp':
                custom_order = [
                    'ServiceRequests',
                    'ActiveLocations',
                    'ActivePlans',
                    'ActiveModems',
                    'OtherInfo',
                    'User',
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

    readonly_fields = ["ip_address","request_time","send_message","view_document","download_document","download_form","log_msg_status","jalali_request_time"]

    fieldsets = (
        ('اطلاعات نصب و دراپ', {
            'fields': ('fat_index','outdoor_area','internal_area','pay_status','marketer'),
            # 'classes': ('collapse','open')
        }),
        ('باکس دانلود', {
            'fields': ('view_document','download_document','download_form','documents'),
            'classes': ('collapse',)
        }),
        ('اطلاعات شخصی', {
            'fields': (
                'first_name', 'last_name', 'father_name', 'national_code',
                'bc_number', 'birthday','landline_number','mobile_number',
                'address','location','post_code','house_is_owner',
            ),
            'classes': ('collapse',)
        }),
        ('اطلاعات سرویس', {
            'fields': ('sip_phone', 'modem','plan'),
            'classes': ('collapse',)
        }),
        ("سایر اطلاعات", {
            'fields': (
                'request_status','send_message','tracking_code','log_msg_status',
                'jalali_request_time','ip_address'
            ),
            'classes': ('collapse',)
        }),
    )
    list_filter = ("location","finalization_status","marketer_status","drop_status","fusion_status","pay_status","submission_status")
    search_fields = ("mobile_number","national_code","post_code")
    ordering = ("-request_time",)

    def jalali_request_time(self, obj):
        return to_jalali_persian(obj.request_time)
    jalali_request_time.short_description = "زمان درخواست" # type: ignore

    def send_message(self,obj):
        return format_html(f"""<a class="button" href="#">ارسال پیامک</a>""")
    send_message.short_description = "ارسال پیامک"        # type: ignore

    def download_form(self,obj):
        try:
            word_url = reverse('create-form',args=['word',obj.pk])
            pdf_url = reverse('create-form',args=['pdf',obj.pk])
        except:
            word_url = '#'
            pdf_url = '#'
        return format_html(f"""<a class="button" href="{word_url}">Word دانلود</a>&nbsp; - 
                           <a class="button" href="{pdf_url}">Pdf دانلود</a>""")
    download_form.short_description = "دانلود فرم ثبت نام"

    def download_document(self,obj):
        url = obj.documents.url
        return format_html(f"""<a class="button" href="{url}" target=_blank download>دانلود</a>""")
    download_document.short_description = "دانلود مدارک"

    def view_document(self,obj):
        url = obj.documents.url
        return format_html(f"""<a class="button" href="{url}">مشاهده</a>""")
    view_document.short_description = "مشاهده مدارک"

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        formfield = super().formfield_for_choice_field(db_field, request, **kwargs)

        if db_field.name == "drop_status":
            all_choices = list(formfield.choices)

            # hidden choice
            hidden_value = "repending"

            # مقدار فعلی آبجکت رو پیدا کن
            obj_id = request.resolver_match.kwargs.get("object_id")
            current_value = None
            if obj_id:
                obj = ServiceRequests.objects.filter(pk=obj_id).first()
                if obj:
                    current_value = obj.drop_status

            # اگر مقدار فعلی repending نیست → حذفش کن
            if current_value != hidden_value:
                formfield.choices = [c for c in all_choices if c[0] != hidden_value]

        return formfield

    def save_model(self, request, obj, form, change):
        if not change:
            try:
                obj.marketer = request.user.get_full_name()  # type: ignore
            except:
                pass
            obj.save()

        elif change:
            old_obj = self.model.objects.get(pk=obj.pk)

            # اگر از pending به accepted رفت
            if old_obj.drop_status in ['pending','repending'] and form.cleaned_data['drop_status'] == "accepted":
                obj.supervisor_status = 'pending'

            # اگر ناظر رد کرد → وضعیت repending
            if old_obj.supervisor_status != 'rejected' and form.cleaned_data['supervisor_status'] == 'rejected':
                obj.drop_status = 'repending'

            obj.save()
        super().save_model(request, obj, form, change)

    def get_fieldsets(self, request, obj=None):
        # deleted fields : 'marketer_status' , 'drop_status' , 'supervisor_status' ,
        #                  'fusion_status' , 'submission_status', 'finalization_status'
        fieldsets = list(super().get_fieldsets(request, obj))

        for i, fs in enumerate(fieldsets):
            if fs[0] != 'اطلاعات نصب و دراپ':
                continue

            base_fields = list(fs[1].get('fields', ()))
            extra = []

            if request.user.is_superuser:
                extra = [
                    'marketer_status', 'drop_status', 'supervisor_status',
                    'fusion_status', 'submission_status','finalization_status'
                ]
                extra = [f for f in extra if f not in base_fields]
                new_fields = tuple(extra + base_fields)
                fs1 = fs[1].copy()
                fs1['fields'] = new_fields
                fieldsets[i] = (fs[0], fs1)
                return fieldsets

            if getattr(request.user, "role_marketer", False):
                extra += ['submission_status','marketer_status','finalization_status']
            if getattr(request.user, "role_dropagent", False):
                extra += ['drop_status','finalization_status']
            if getattr(request.user, "role_supervisor", False):
                extra += ['supervisor_status']
            if getattr(request.user, "role_fusionagent", False):
                extra += ['fusion_status']

            extra = list(dict.fromkeys(extra))   
            extra = [f for f in extra if f not in base_fields]

            if extra:
                new_fields = tuple(extra + base_fields)
                fs1 = fs[1].copy()
                fs1['fields'] = new_fields
                fieldsets[i] = (fs[0], fs1)

            return fieldsets

        return fieldsets

    def get_readonly_fields(self, request, obj=None) :
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            request.session['secure_form_download'] = obj.pk
        if not request.user.is_superuser:
            secure_fields = ['marketer','tracking_code','ip_address']
            for i in secure_fields:
                readonly_fields.append(i)
        return readonly_fields
              
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            obj.refresh_from_db()

            #رد انلی شدن تایید مدارک
            if request.user.role_marketer or request.user.is_superuser:
                if obj.drop_status == "accepted":

                    form.base_fields['marketer_status'].disabled = True
                    form.base_fields['marketer_status'].widget = DisplayOnlyWidget(
                    "امکان تغییر این بخش وجود ندارد ، مدارک تایید و دراپ کشی انجام شده است", color="yellow")
             
                if obj.drop_status == "queued" :
        
                    form.base_fields['marketer_status'].disabled = True
                    form.base_fields['marketer_status'].widget = DisplayOnlyWidget(
                    "امکان تغییر این بخش وجود ندارد ، سرویس در صف دراپ کشی قرار گرفته است", color="yellow")
    
            #رد انلی شدن دراپ 
            if request.user.role_dropagent or request.user.is_superuser:
                if obj.marketer_status != "accepted":
                    form.base_fields['drop_status'].disabled = True
                    form.base_fields['drop_status'].widget = DisplayOnlyWidget(
                    "در انتظار تایید مدارک و اطلاعات توسط بازاریاب", color="aqua"
                        )
                if obj.supervisor_status == "accepted":
                    form.base_fields['drop_status'].disabled = True
                    form.base_fields['drop_status'].widget = DisplayOnlyWidget(
                    "دراپ توسط ناظر تایید شده امکان تغییر وضعیت وجود ندارد", color="yellow"
                        )
            #رد انلی شدن ناظر
            if request.user.role_supervisor or request.user.is_superuser:
                if obj.drop_status != "accepted" :
                    form.base_fields['supervisor_status'].disabled = True
                    form.base_fields['supervisor_status'].widget = DisplayOnlyWidget(
                    "امکان بازبینی وجود ندارد ، دراپ کشی هنوز انجام نشده است", color="aqua")                     
                if obj.fusion_status == "queued" :
                    form.base_fields['supervisor_status'].disabled = True
                    form.base_fields['supervisor_status'].widget = DisplayOnlyWidget(
                    "امکان تغییر وجود ندارد ، سرویس در صف فیوژن زنی قرار گرفته است", color="yellow")
                                      
                elif obj.fusion_status == "accepted":
                    form.base_fields['supervisor_status'].disabled = True
                    form.base_fields['supervisor_status'].widget = DisplayOnlyWidget(
                    "امکان تغییر وجود ندارد ، فیوژن زنی سرویس انجام شده است", color="yellow")      
                    
            #رد انلی شدن فیوژن
            if request.user.role_fusionagent or request.user.is_superuser:
                if obj.supervisor_status != "accepted":
                    form.base_fields['fusion_status'].disabled = True
                    form.base_fields['fusion_status'].widget = DisplayOnlyWidget(
                    "امکان فیوژن زنی وجود ندارد دراپ هنوز توسط ناظر تایید نشده است", color="aqua")
                if obj.finalization_status == "ended":
                    form.base_fields['fusion_status'].disabled = True
                    form.base_fields['fusion_status'].widget = DisplayOnlyWidget(
                    "امکان تغییر وجود ندارد ، سرویس ثبت نهایی شده است", color="yellow")

            # رد انلی شدن فانالیزیشن
            if request.user.role_marketer or request.user.role_fusionagent or request.user.is_superuser :
                if obj.fusion_status != "accepted" and  obj.submission_status != "registered":
                    form.base_fields['finalization_status'].disabled = True
                    form.base_fields['finalization_status'].widget = DisplayOnlyWidget(
                    "امکان ثبت نهایی وجود ندارد وضعیت فیوژن و ثبت فرم ناتمام است", color="aqua")
                elif obj.fusion_status != "accepted" and obj.submission_status == "registered":
                    form.base_fields['finalization_status'].disabled = True
                    form.base_fields['finalization_status'].widget = DisplayOnlyWidget(
                    "امکان ثبت نهایی وجود ندارد وضعیت فیوژن ناتمام است", color="aqua")
                elif obj.fusion_status == "accepted" and obj.submission_status != "registered":
                    form.base_fields['finalization_status'].disabled = True
                    form.base_fields['finalization_status'].widget = DisplayOnlyWidget(
                    "امکان ثبت نهایی وجود ندارد فرم ثبت نام هنوز ثبت نشده است", color="aqua")

            #رد انلی شدن ثبت فرم
            if request.user.role_marketer or request.user.role_fusionagent or request.user.is_superuser :
                if obj.finalization_status == "ended":
                    form.base_fields['submission_status'].disabled = True
                    form.base_fields['submission_status'].widget = DisplayOnlyWidget(
                    "امکان تغییر ثبت وجود ندارد ، سرویس ثبت نهایی شده است", color="yellow")


                
            
        return form
    
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
        ('نقش ها',{'fields':('role_supervisor','role_marketer','role_dropagent','role_fusionagent')}),
        # ('دسترسی ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('دسترسی ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}), # گروه ها حذف شد 
        ('تاریخ های مهم', {'fields': ('jalali_last_login', 'jalali_date_joined')}),
    )

    def has_add_permission(self, request): return request.user.is_superuser


    def get_fieldsets(self, request, obj=None): # type: ignore
        if not request.user.is_superuser:
            return (
        (None, {'fields': ('username', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'email')}),
        # ('نقش ها',{'fields':('role_supervisor','role_marketer','role_dropagent','role_fusionagent')}),
        # ('دسترسی ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        # ('تاریخ های مهم', {'fields': ('jalali_last_login', 'jalali_date_joined')}),
    )
        return super().get_fieldsets(request, obj)

    def get_queryset(self, request): # فقط خودش رو مشاهده کنه 
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(pk=request.user.pk)
        return queryset



    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and not obj.is_superuser:
            # همه دسترسی‌ها رو بده به کاربر
            obj.user_permissions.set(Permission.objects.all())
            obj.is_staff = True
            obj.save()

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
    
