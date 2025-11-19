import os
import uuid
from PIL import Image
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(max_length=20, verbose_name='نام')
    last_name = models.CharField(max_length=20, verbose_name='نام خانوادگی')
    username = models.CharField(max_length=15, unique=True, verbose_name='نام کاربری (شماره تلفن)')

    register_messages = models.BooleanField(verbose_name='ارسال پیامک ثبت نام کاربر',default=False)

    role_supervisor = models.BooleanField(verbose_name='نقش (ناظر)',default=False)
    role_operator = models.BooleanField(verbose_name='نقش (اپراتور مخابرات)',default=False)
    role_marketer = models.BooleanField(verbose_name='نقش (بازاریاب)',default=False)
    role_dropagent = models.BooleanField(verbose_name='نقش (مسئول دراپ کشی)',default=False)
    role_fusionagent = models.BooleanField(verbose_name='نقش (مسئول فیوژن زنی)',default=False)


    def __str__(self):
        if self.is_superuser:return f"{self.first_name} {self.last_name} - ابرکاربر"
        role = ''
        if self.role_marketer :
            role += 'بازاریاب '
        if self.role_dropagent and role == '':
            role += 'دراپ کش '
        elif self.role_dropagent and not role == '':
            role += 'و دراپ کش '
        if self.role_fusionagent and role == '':
            role += 'فیوژن زن '
        elif self.role_fusionagent and not role == '':
            role += 'و فیوژن زن '
        if self.role_supervisor and role == '':
            role += 'ناظر '
        elif self.role_supervisor and not role == '':
            role += 'و ناظر ' 
        if self.role_operator and role == '':
            role += 'اپراتور'
        elif self.role_operator and not role == '':
            role += 'و اپراتور'
        
        
        return f"{self.first_name} {self.last_name} - {role}"

    def get_role(self):
        if self.is_superuser: return "ابرکاربر"
        role = ''
        if self.role_marketer :
            role += 'بازاریاب '
        if self.role_dropagent and role == '':
            role += 'دراپ کش '
        elif self.role_dropagent and not role == '':
            role += 'و دراپ کش '
        if self.role_fusionagent and role == '':
            role += 'فیوژن زن '
        elif self.role_fusionagent and not role == '':
            role += 'و فیوژن زن '
        if self.role_supervisor and role == '':
            role += 'ناظر '
        elif self.role_supervisor and not role == '':
            role += 'و ناظر ' 
        if self.role_operator and role == '':
            role += 'اپراتور'
        elif self.role_operator and not role == '':
            role += 'و اپراتور'       
        
        return f"{role}"  

    def get_full_name(self):
        return self.first_name+" "+self.last_name

class OtherInfo(models.Model):
    sip_phone_cost = models.BigIntegerField(verbose_name='هزینه سیپ فون (تومان)')
    drop_cost = models.BigIntegerField(verbose_name='هزینه دراپ کشی (تومان)')
    center_name = models.CharField(max_length=25,verbose_name='نام مرکز مخابرات')
    center_address = models.CharField(max_length=200,verbose_name='آدرس مرکز')
    contact_number = models.CharField(max_length=20,verbose_name='شماره تماس با ما (پشتیبانی)')
    site_linenumber = models.CharField(max_length=20,verbose_name='شماره ثابت سایت')

    link_phone = models.CharField(max_length=100,verbose_name='لینک تماس (فوتر)',null=True,blank=True)
    link_mail = models.CharField(max_length=100,verbose_name='لینک ایمیل (فوتر)',null=True,blank=True)
    link_instagram = models.CharField(max_length=100,verbose_name='لینک اینستاگرام (فوتر)',null=True,blank=True)
    link_whatsapp = models.CharField(max_length=100,verbose_name='لینک واتساپ (فوتر)',null=True,blank=True)


    def save(self,*args,**kwargs):
        self.pk = 1
        super().save(*args,**kwargs)

    @classmethod
    def get_instance(cls):
        obj , created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta :
        verbose_name = "سایراطلاعات"
        verbose_name_plural = "سایر اطلاعات"

    def __str__(self):
        return "سایر اطلاعات"
class AccountNumber(models.Model):
    Other_info = models.ForeignKey(OtherInfo, related_name='account_number', on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=20,verbose_name='نام بانک')
    account_number = models.CharField(max_length=15,verbose_name='شماره حساب')

    def clean(self):
        super().clean()
        if self.account_number:
            if not (self.account_number).isdigit():
                raise ValidationError('شماره حساب باید عددی باشد')

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

    class Meta:
        verbose_name = "شماره حساب"
        verbose_name_plural = "شناره های حساب"
        ordering = ['-id']

class ActiveLocations(models.Model):
    name = models.CharField(max_length=50,verbose_name='نام منطقه')
    area_limit = models.CharField(max_length=50,verbose_name='حدود منطقه')
    is_active = models.BooleanField(verbose_name='وضعیت فعال بودن',default=True)

    class Meta :
        verbose_name = "منطقه"
        verbose_name_plural = "منطقه های فعال"

    def __str__(self):
        return f"{self.name} - {self.area_limit}"
    
class ActiveModems(models.Model):
    class PaymentChoices(models.TextChoices):
        mi3 = "mi3" , "با اقساط 3 ماه"
        mi6 = "mi6" , "با اقساط 6 ماهه"
        mi9 = "mi9" , "با اقساط 9 ماهه"
        mi12 = "mi12" , "با اقساط 12 ماهه"
        nocash = "nocashneed","عدم نیاز به پرداخت وجه"
        cash  = "cash" , "با پرداخت نقدی"

    name = models.CharField(max_length=200,verbose_name='نام مودم')
    price = models.BigIntegerField(verbose_name='قیمت مودم (تومان)')
    added_tax = models.BigIntegerField(verbose_name='مالیات بر ارزش افزوده (تومان)',help_text='در صورت نبود مالیات عدد صفر را وارد کنید',default=0)
    payment_method = models.CharField(choices=PaymentChoices,max_length=20,verbose_name='شیوه پرداخت')
    is_active = models.BooleanField('وضعیت نمایش',default=True)


    class Meta :
        verbose_name = "مودم"
        verbose_name_plural = "مودم ها"

    def __str__(self):
        return f"{self.name} {self.get_payment_method_display()}" # type: ignore

class ActivePlans(models.Model):

    class PlanTypeChoices(models.TextChoices):
        prepayment = "prepayment","پیش پرداخت"
        postpayment = "postpayment","پس پرداخت"

    class PlanTimeChoices(models.TextChoices):
        mo3 = "mo3","3 ماهه"
        mo6 = "mo6","6 ماهه"
        mo9 = "mo9","9 ماهه"
        mo12 = "mo12","12 ماهه"


    data = models.IntegerField(verbose_name="حجم ماهانه (گیگابایت)")
    plan_type = models.CharField(choices=PlanTypeChoices,max_length=50,default=PlanTypeChoices.postpayment,verbose_name='نوع طرح')
    plan_time = models.CharField(max_length=20,choices=PlanTimeChoices,default=PlanTimeChoices.mo3,verbose_name='مدت طرح')
    price = models.BigIntegerField(verbose_name="قیمت (تومان)")
    is_active = models.BooleanField('وضعیت نمایش',default=True)

    class Meta :
        verbose_name = "طرح اینترنت"
        verbose_name_plural = "طرح های اینترنت"

    def __str__(self):
        return f"{self.data}G ماهانه ، {self.price} تومان ، {self.get_plan_type_display()} ، {self.get_plan_time_display()}" # type: ignore

def get_safe_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    
    unique_name = f"{uuid.uuid4()}.{ext}"
    
    return os.path.join('documents', unique_name)

def validate_dockphoto_size(image):
    max_size = 3000
    if image.size > max_size * 1024 :
        raise ValidationError("حجم عکس نباید بیشتر از 3000 کیلوبایت باشد")
    
class ServiceRequests(models.Model):

    class HouseOwnerStatus(models.TextChoices):
        owner = "owner","مالک"
        renter = "renter","مستاجر"

    class SubmissionStatus(models.TextChoices):
        registered = "registered","ثبت شده"
        pending = "pending","در انتظار ثبت"

    class PayStatus(models.TextChoices):
        payed = "payed","پرداخت شده"
        pending = "pending","در انتظار پرداخت"

    #---------------------------------------------

    class MarketerFormStatus(models.TextChoices):
        pending = "pending","در انتظار بررسی مدارک"
        accepted = "accepted","تایید اطلاعات و مدارک"
        rejected = "rejected","رد اطلاعات و مدارک"

    class DropStatus(models.TextChoices):
        pending = "pending","در انتظار بررسی دراپ کشی"
        queued = "queued","در صف دراپ کشی "
        accepted = "accepted","دراپ کشی انجام شد"
        rejected = "rejected","عدم امکان دائری فنی"
        # repending = "repending","دراپ تایید نشد ، در انتظار دراپ کشی مجدد" #hidden

    class SuperVisorStatus(models.TextChoices):
        pending = "pending","در انتظار بررسی ناظر"
        # repending = "repending","در انتظار بازبینی مجدد ناظر"
        accepted = "accepted","تایید دراپ و فیوژن"
        rejected = "rejected","رد دراپ و فیوژن"

    class FusionStatus(models.TextChoices):
        pending = "pending","در انتظار بررسی فیوژن زنی"
        queued = "queued","در صف فیوژن زنی"
        accepted = "accepted","فیوژن زنی انجام شد"
        repending = "repending","دراپ و فیوژن تایید نشد ، در انتظار بازبینی مجدد شما" #hidden

    class FinalizationStatus(models.TextChoices):
        pending = "pending","در انتظار اتمام کار"
        ended = "ended","تحویل سرویس و اتمام کار"

    #-----------------------------------------------------
    #Personal information
    first_name = models.CharField(max_length=25,verbose_name='نام')
    last_name = models.CharField(max_length=50,verbose_name='نام خانوادگی')
    father_name = models.CharField(max_length=25,verbose_name='نام پدر')
    national_code = models.CharField(max_length=12,verbose_name='کد ملی')
    bc_number = models.CharField(max_length=12,verbose_name='شماره شناسنامه') 
    birthday = models.CharField(max_length=50,verbose_name='تاریخ تولد')
    originated_from = models.CharField(max_length=50,verbose_name='صادره از')
    documents = models.ImageField(upload_to=get_safe_upload_path,validators=[validate_dockphoto_size],verbose_name='بارگذاری / تغییر مدارک')
    landline_number = models.CharField(max_length=12,verbose_name='تلفن منزل',null=True,blank=True) 
    mobile_number = models.CharField(max_length=12,verbose_name='تلفن همراه')
    location = models.ForeignKey(ActiveLocations,on_delete=models.PROTECT,verbose_name='واقع در')
    address = models.TextField(verbose_name='آدرس')
    house_is_owner = models.CharField(max_length=25,choices=HouseOwnerStatus,verbose_name='وضعیت مالکیت منزل')
    post_code = models.CharField(max_length=12,verbose_name='کد پستی',unique=True)
    #-----------------------------------------------------
    #service information
    sip_phone = models.BooleanField(verbose_name='متقاضی سیپ فون روی فیبرنوری',null=True)
    modem = models.ForeignKey(ActiveModems,on_delete=models.PROTECT,verbose_name='مودم درخواستی',null=True)
    plan = models.ForeignKey(ActivePlans,on_delete=models.PROTECT,verbose_name='طرح درخواستی',null=True)
    #-----------------------------------------------------
    #drop status
    outdoor_area = models.PositiveIntegerField(verbose_name='متراژ بیرونی (متر)',null=True,blank=True)
    internal_area = models.PositiveIntegerField(verbose_name='متراژ داخلی (متر)',null=True,blank=True)
    fat_index = models.CharField(max_length=10,verbose_name='مشخصه FAT',null=True,blank=True)
    odc_index = models.CharField(max_length=10,verbose_name='مشخصه ODC',null=True,blank=True)
    pole_count = models.PositiveIntegerField(verbose_name='تعداد تیر',null=True,blank=True)
    headpole_count = models.PositiveIntegerField(verbose_name='تعداد سر تیر',null=True,blank=True)
    hook_count = models.PositiveIntegerField(verbose_name='تعداد قلاب',null=True,blank=True)
    #-----------------------------------------------------

    #tci service status
    #-----------------------------------------------------
    virtual_number = models.CharField(max_length=10,verbose_name='شماره مجازی',null=True,blank=True)
    port_number = models.PositiveIntegerField(verbose_name='شماره پورت',null=True,blank=True)
    #-----------------------------------------------------
    #proc status
    #-----------------------------------------------------
    marketer_status = models.CharField(max_length=100,choices=MarketerFormStatus,default=MarketerFormStatus.pending,verbose_name='وضعیت تایید بازاریاب')
    drop_status = models.CharField(max_length=100,choices=DropStatus,default=DropStatus.pending,verbose_name='وضعیت دراپ')
    supervisor_status = models.CharField(max_length=100,choices=SuperVisorStatus,default=SuperVisorStatus.pending,verbose_name='وضعیت تایید ناظر')
    fusion_status = models.CharField(max_length=100,choices=FusionStatus,default=FusionStatus.pending,verbose_name='وضعیت فیوژن')
    submission_status = models.CharField(max_length=30,choices=SubmissionStatus,default=SubmissionStatus.pending,verbose_name='وضعیت ثبت فرم')
    finalization_status = models.CharField(max_length=100,choices=FinalizationStatus,default=FinalizationStatus.pending,verbose_name='وضعیت اتمام نصب')

    pay_status = models.CharField(max_length=30,choices=PayStatus,default=PayStatus.pending,verbose_name='وضعیت پرداخت')
    account_number = models.ForeignKey(AccountNumber,null=True,blank=True,on_delete=models.SET_NULL,verbose_name='شماره حساب')
    tracking_payment = models.CharField(max_length=20,verbose_name='کد پیگیری پرداخت',null=True,blank=True)
    payment_date = models.DateField(verbose_name='تاریخ پرداخت',null=True,blank=True)
    payment_time = models.TimeField(verbose_name='زمان پرداخت',null=True,blank=True)

    marketer_name = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,verbose_name='نام بازاریاب')
    #-----------------------------------------------------
    #Other information
    finished_request = models.BooleanField(default=False,verbose_name='وضعیت اتمام ثبت نام سیستم')
    tracking_code = models.PositiveIntegerField(verbose_name='کد پیگیری',unique=True,null=True,blank=True)
    log_msg_status = models.TextField(verbose_name='لاگ ارسال پیامک',null=True,blank=True)
    request_time = models.DateTimeField(auto_now_add=True,null=True,blank=True,verbose_name='تاریخ درخواست')
    ip_address = models.GenericIPAddressField(null=True,blank=True,verbose_name='آیپی درخواست دهنده')

    def clean(self):
        super().clean()
        if self.tracking_code:
            if not len(str(self.tracking_code)) == 6:
                raise ValidationError('کد پیگیری حتما باید 6 رقمی باشد .')
            
        if self.virtual_number:
            if not (self.virtual_number).isdigit():
                raise ValidationError('شماره مجازی حتما باید عددی باشد')
            
        if self.tracking_payment:
            if not (self.tracking_payment).isdigit():
                raise ValidationError("کد پیگیری پرداخت باید عددی باشد")
    
        if self.drop_status == "accepted":
            fields = [
                self.outdoor_area,
                self.internal_area,
                self.fat_index,
                self.odc_index,
                self.pole_count,
                self.headpole_count,
                self.hook_count,
            ]

            if any(field is None or field == "" for field in fields):
                raise ValidationError("برای اتمام کار دراپ وارد کردن جزییات دراپ الزامی است، در صورت نبود مقدار صفر را وارد کنید.")
            
        if self.submission_status == "registered":
            if not self.virtual_number or not self.port_number :
                raise ValidationError("لطفا شماره مجازی و شماره پورت را وارد نمایید")

        if self.pay_status == "payed":
            if not self.tracking_payment or not self.payment_date or not self.payment_time or not self.account_number :
                raise ValidationError("وارد کردن جزییات پرداخت الزامی است : شماره حساب - شماره پیگیری - تاریخ - زمان")
            
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def add_sms_log(self,message):
        old  = self.log_msg_status 
        if str(old) == 'None':
            new = message
        else:
            new = str(old)+"\n"+message
        self.log_msg_status = new
        self.save(update_fields=["log_msg_status"])

    def __str__(self):
        return f"{self.first_name} {self.last_name} واقع در {self.location.name}"

    class Meta :
        verbose_name = "درخواست سرویس"
        verbose_name_plural = "درخواست های سرویس"








