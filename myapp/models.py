from PIL import Image
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(max_length=20, verbose_name='نام')
    last_name = models.CharField(max_length=20, verbose_name='نام خانوادگی')
    username = models.CharField(max_length=15, unique=True, verbose_name='نام کاربری (شماره تلفن)')

    role_supervisor = models.BooleanField(verbose_name='نقش (ناظر)',default=False)
    role_marketer = models.BooleanField(verbose_name='نقش (بازاریاب)',default=False)
    role_dropagent = models.BooleanField(verbose_name='نقش (مسئول دراپ کشی)',default=False)
    role_fusionagent = models.BooleanField(verbose_name='نقش (مسئول فیوژن زنی)',default=False)


    def __str__(self):
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
        
        
        return f"{self.first_name} {self.last_name} - {role}"

class OtherInfo(models.Model):
    sip_phone_cost = models.BigIntegerField(verbose_name='هزینه سیپ فون (تومان)')
    drop_cost = models.BigIntegerField(verbose_name='هزینه دراپ کشی (تومان)')
    center_name = models.CharField(max_length=25,verbose_name='نام مرکز مخابرات')
    center_address = models.CharField(max_length=200,verbose_name='آدرس مرکز')
    contact_number = models.CharField(max_length=12,verbose_name='شماره تماس با ما')
    site_linenumber = models.CharField(max_length=20,verbose_name='شماره ثابت سایت')

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

class ActiveLocations(models.Model):
    name = models.CharField(max_length=50,verbose_name='نام منطقه')
    area_limit = models.CharField(max_length=50,verbose_name='حدود منطقه')

    class Meta :
        verbose_name = "منطقه"
        verbose_name_plural = "منطقه های فعال"

    def __str__(self):
        return f"{self.name} - {self.area_limit}"
    
class ActiveModems(models.Model):
    class PaymentChoices(models.TextChoices):
        mi3 = "mi3" , "با اقساط 3 ماه"
        mi6 = "mi6" , "با اقساط 6 ماهه"
        mi12 = "mi12" , "با اقساط 12 ماهه"
        nocash = "nocashneed","عدم نیاز به پرداخت وجه"
        cash  = "cash" , "با پرداخت نقدی"

    name = models.CharField(max_length=200,verbose_name='نام مودم')
    price = models.BigIntegerField(verbose_name='قیمت مودم (تومان)')
    payment_method = models.CharField(choices=PaymentChoices,max_length=20,verbose_name='شیوه پرداخت')

    class Meta :
        verbose_name = "مودم"
        verbose_name_plural = "مودم ها"

    def __str__(self):
        return f"{self.name} {self.get_payment_method_display()}"

class ActivePlans(models.Model):
    data = models.IntegerField(verbose_name="حجم ماهانه (گیگابایت)")
    price = models.BigIntegerField(verbose_name="قیمت (تومان)")

    class Meta :
        verbose_name = "طرح اینترنت"
        verbose_name_plural = "طرح های اینترنت"

    def __str__(self):
        return f"{self.data}G ماهانه - {self.price} تومان"

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
        rejected = "rejected","عدم امکان ثبت"

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
        repending = "repending","دراپ تایید نشد ، در انتظار دراپ کشی مجدد" #hidden

    class SuperVisorStatus(models.TextChoices):
        pending = "pending","در انتظار بررسی ناظر"
        # repending = "repending","در انتظار بازبینی مجدد ناظر"
        accepted = "accepted","دراپ کشی تایید شد"
        rejected = "rejected","رد و بازبینی دراپ"

    class FusionStatus(models.TextChoices):
        pending = "pending","در انتظار بررسی فیوژن زنی"
        queued = "queued","در صف فیوژن زنی"
        accepted = "accepted","فیوژن زنی انجام شد"

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
    documents = models.ImageField(upload_to='documents/',validators=[validate_dockphoto_size],verbose_name='بارگذاری / تغییر مدارک')
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
    #proc status
    marketer_status = models.CharField(max_length=100,choices=MarketerFormStatus,default=MarketerFormStatus.pending,verbose_name='وضعیت تایید بازاریاب')
    drop_status = models.CharField(max_length=100,choices=DropStatus,default=DropStatus.pending,verbose_name='وضعیت دراپ')
    supervisor_status = models.CharField(max_length=100,choices=SuperVisorStatus,default=SuperVisorStatus.pending,verbose_name='وضعیت تایید ناظر')
    fusion_status = models.CharField(max_length=100,choices=FusionStatus,default=FusionStatus.pending,verbose_name='وضعیت فیوژن')
    submission_status = models.CharField(max_length=30,choices=SubmissionStatus,default=SubmissionStatus.pending,verbose_name='وضعیت ثبت فرم')
    finalization_status = models.CharField(max_length=100,choices=FinalizationStatus,default=FinalizationStatus.pending,verbose_name='وضعیت اتمام نصب')

    pay_status = models.CharField(max_length=30,choices=PayStatus,default=PayStatus.pending,verbose_name='وضعیت پرداخت')

    marketer = models.CharField(max_length=50,null=True,blank=True,verbose_name='نام بازاریاب')
    #-----------------------------------------------------
    #Other information
    finished_request = models.BooleanField(default=False,verbose_name='وضعیت اتمام ثبت نام سیستم')
    tracking_code = models.PositiveIntegerField(verbose_name='کد پیگیری',unique=True,null=True,blank=True)
    log_msg_status = models.TextField(verbose_name='لاگ ارسال پیامک',null=True,blank=True)
    request_time = models.DateTimeField(auto_now_add=True,null=True,blank=True,verbose_name='تاریخ درخواست')
    ip_address = models.GenericIPAddressField(null=True,blank=True,verbose_name='آیپی درخواست دهنده')


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