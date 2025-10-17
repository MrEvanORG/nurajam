from django import forms
from django.core.exceptions import ValidationError
from .models import ServiceRequests , ActiveLocations , ActiveModems , ActivePlans

def fix_numbers(value):
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic  = "٠١٢٣٤٥٦٧٨٩"
    for i in range(10):
        value = value.replace(persian[i], str(i)).replace(arabic[i], str(i))
    return value

class SmsForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'cols': 80}),
        label='متن پیامک',
        help_text='می‌توانید از متغیرهایی مانند {user.first_name}, {user.last_name}, {user.username} در متن پیام استفاده کنید.'
    )
class RegiterphonePostForm(forms.Form):
    mobile = forms.CharField(max_length=11, label='شماره تلفن همراه', required=True)
    post_code = forms.CharField(max_length=10, label='کد پستی', required=True)

    def clean_mobile(self):
        mobile = fix_numbers(str(self.cleaned_data['mobile']))
        if not mobile.isdigit():
            raise ValidationError('شماره تلفن باید فقط شامل اعداد باشد')
        if len(mobile) != 11:
            raise ValidationError('شماره تلفن باید ۱۱ رقم باشد')
        return mobile

    def clean_post_code(self):
        code = fix_numbers(str(self.cleaned_data['post_code']))
        if not code.isdigit():
            raise ValidationError('کد پستی باید فقط شامل اعداد باشد')
        if len(code) != 10:
            raise ValidationError('کد پستی باید 10 رقم باشد')
        return code

    def clean(self):
        cleaned_data = super().clean()
        mobile = cleaned_data.get('mobile')
        code = cleaned_data.get('post_code')

        if not mobile or not code:
            return cleaned_data

        srv = ServiceRequests.objects.filter(post_code=code.strip())
        if srv.exists():
            req = ServiceRequests.objects.get(post_code=code.strip())
            if req.mobile_number != mobile:
                self.add_error('post_code', 'امکان تغییر این سرویس با این شماره تلفن وجود ندارد')
            elif req.marketer_status == 'accepted':
                self.add_error('post_code', 'سرویس این کد پستی در حال انجام است امکان تغییر اطلاعات وجود ندارد')

        return cleaned_data
    
class OtpVerifyForm(forms.Form):
    otp_code = forms.CharField(max_length=6,label='کد ارسالی',required=True)

    def clean_otp(self):
        otp_code = fix_numbers(str(self.cleaned_data['otp_code']))
        if not otp_code.isdigit():
            raise ValidationError('کد وارد شده باید فقط شامل اعداد باشد')
        if len(otp_code) != 6 :
            raise ValidationError('کد ارسالی باید 6 رقمی باشد')
        
        return otp_code
    
import re
class PersonalInfoForm(forms.Form):
    first_name = forms.CharField(max_length=24, required=True)
    last_name = forms.CharField(max_length=49, required=True)
    father_name = forms.CharField(max_length=24, required=True)
    originated_from = forms.CharField(max_length=49,required=True)
    national_code = forms.CharField(max_length=10, required=True)
    bc_number = forms.CharField(max_length=10, required=True)
    
    YEAR_CHOICES = [(str(y), str(y)) for y in range(1386, 1314, -1)]
    MONTH_CHOICES = [
        ('01', 'فروردین'),
        ('02', 'اردیبهشت'),
        ('03', 'خرداد'),
        ('04', 'تیر'),
        ('05', 'مرداد'),
        ('06', 'شهریور'),
        ('07', 'مهر'),
        ('08', 'آبان'),
        ('09', 'آذر'),
        ('10', 'دی'),
        ('11', 'بهمن'),
        ('12', 'اسفند'),
    ]
    DAY_CHOICES = [(f"{d:02}", f"{d:02}") for d in range(1, 32)]
    LOCATION_CHOICES = [ (lc.pk,lc.__str__()) for lc in ActiveLocations.objects.all() ]

    year = forms.ChoiceField(choices=YEAR_CHOICES, required=True)
    month = forms.ChoiceField(choices=MONTH_CHOICES, required=True)
    day = forms.ChoiceField(choices=DAY_CHOICES, required=True)

    location = forms.ChoiceField(choices=LOCATION_CHOICES,required=True)

    id_image = forms.FileField(required=True)
    
    OWNER_STATUS_CHOICES = [('owner', 'مالک'), ('renter', 'مستاجر')]
    ownerstatus = forms.ChoiceField(choices=OWNER_STATUS_CHOICES, widget=forms.RadioSelect,initial='owner', required=True)
    
    mobile = forms.CharField(max_length=11, required=True)
    post_code = forms.CharField(max_length=10, required=True)
    
    home_phone = forms.CharField(max_length=8, required=False)
    address = forms.CharField(max_length=300, widget=forms.Textarea, required=True)

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if not re.match(r'^[\u0600-\u06FF\s]+$', first_name):
            raise ValidationError('نام باید فقط شامل حروف فارسی باشد.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if not re.match(r'^[\u0600-\u06FF\s]+$', last_name):
            raise ValidationError('نام خانوادگی باید فقط شامل حروف فارسی باشد.')
        return last_name

    def clean_father_name(self):
        father_name = self.cleaned_data['father_name']
        if not re.match(r'^[\u0600-\u06FF\s]+$', father_name):
            raise ValidationError('نام پدر باید فقط شامل حروف فارسی باشد.')
        return father_name

    def clean_national_code(self):
        national_code = self.cleaned_data['national_code']
        fixed_code = fix_numbers(national_code)
        if not fixed_code.isdigit() or len(fixed_code) != 10:
            raise ValidationError('کد ملی باید ۱۰ رقم و فقط شامل اعداد باشد.')
        return fixed_code

    def clean_bc_number(self):
        bc_number = self.cleaned_data['bc_number']
        fixed_number = fix_numbers(bc_number)
        if not fixed_number.isdigit():
            raise ValidationError('شماره شناسنامه باید فقط شامل اعداد باشد.')
        if len(fixed_number) > 10:
             raise ValidationError('شماره شناسنامه نمی‌تواند بیشتر از ۱۰ رقم باشد.')
        return fixed_number

    def clean_originated_from(self):
        fromc = self.cleaned_data['originated_from']
        if not re.match(r'^[\u0600-\u06FF\s]+$', fromc):
            raise ValidationError('محل صدور باید فقط شامل حروف فارسی باشد')
        return fromc

    def clean_id_image(self):
        image = self.cleaned_data.get('id_image')
        if not image:
            raise ValidationError('ارسال عکس الزامی است.')
        if image.size > 3 * 1024 * 1024:
            raise ValidationError('حجم فایل نباید بیشتر از ۳ مگابایت باشد.')
        allowed_extensions = ['jpg', 'jpeg', 'png']
        extension = image.name.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise ValidationError(f'فرمت فایل معتبر نیست. فقط {", ".join(allowed_extensions)} مجاز است.')
        return image

    def clean_home_phone(self):
        home_phone = self.cleaned_data.get('home_phone')
        if not home_phone:
            return home_phone
        fixed_phone = fix_numbers(home_phone)
        if not fixed_phone.isdigit() or len(fixed_phone) != 8:
            raise ValidationError('شماره تلفن منزل در صورت ورود، باید ۸ رقمی باشد.')
        return fixed_phone
        
    def clean_post_code(self):
        post_code = self.cleaned_data['post_code']
        fixed_code = fix_numbers(post_code)
        if not fixed_code.isdigit() or len(fixed_code) != 10:
            raise ValidationError('کد پستی باید ۱۰ رقمی باشد.')
        return fixed_code

    def clean_home_phone(self):
        home_phone = self.cleaned_data.get('home_phone')

        if not home_phone:
            return None

        home_phone = str(home_phone).strip()
        home_phone = fix_numbers(home_phone)

        if not home_phone.isdigit():
            raise ValidationError("تلفن منزل باید فقط شامل عدد باشد.")

        if len(home_phone) != 8:
            raise ValidationError("تلفن منزل باید دقیقا ۸ رقم باشد.")

        return home_phone
    
class ServiceInfoForm(forms.Form):

    payment_priority = {"mi12": 4,"mi6": 3,"mi3": 2,"nocashneed": 1,"cash": 0,}

    modems_qs = ActiveModems.objects.all()
    MODEMS_SORTED = sorted(modems_qs,key=lambda m: (m.price, {"mi12": 4,"mi6": 3,"mi3": 2,"nocashneed": 1,"cash": 0,}.get(m.payment_method, -1)),reverse=True)
    PLAN_SORTED = ActivePlans.objects.all().order_by('-data')

    SIP_STATUS_CHOICES = [('true', 'بله'), ('false', 'خیر')]
    PLAN_CHOICES = [ (pl.pk,pl.__str__()) for pl in PLAN_SORTED ]
    MODEM_CHOICES = [ (mo.pk,mo.__str__()) for mo in MODEMS_SORTED ]

    sipstatus = forms.ChoiceField(choices=SIP_STATUS_CHOICES,widget=forms.RadioSelect,initial='no',required=True)
    plan = forms.ChoiceField(choices=PLAN_CHOICES,required=True)
    modem = forms.ChoiceField(choices=MODEM_CHOICES,required=True)
