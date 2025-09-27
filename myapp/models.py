from PIL import Image
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField(max_length=20, verbose_name='نام')
    last_name = models.CharField(max_length=20, verbose_name='نام خانوادگی')
    username = models.CharField(max_length=15, unique=True, verbose_name='نام کاربری (شماره تلفن)')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class OtherInfo(models.Model):
    sip_phone_cost = models.BigIntegerField(verbose_name='هزینه سیپ فون (تومان)')
    drop_cost = models.BigIntegerField(verbose_name='هزینه دراپ کشی (تومان)')
    center_name = models.CharField(max_length=25,verbose_name='نام مرکز مخابرات')
    center_address = models.CharField(max_length=200,verbose_name='آدرس مرکز')
    contact_number = models.CharField(max_length=12,verbose_name='شماره تماس با ما')
    site_linenumber = models.CharField(max_length=20,verbose_name='شماره ثابت سایت')

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
        mi3 = "mi3" , "اقساط 3 ماهه"
        mi6 = "mi6" , "اقساط 6 ماهه"
        mi12 = "mi12" , "اقساط 12 ماهه"
        nocash = "nocashneed","عدم نیاز به پرداخت وجه"
        cash  = "cash" , "پرداخت نقدی"

    name = models.CharField(max_length=200,verbose_name='نام مودم')
    price = models.BigIntegerField(verbose_name='قیمت مودم (تومان)')
    payment_method = models.CharField(choices=PaymentChoices,max_length=20,verbose_name='شیوه پرداخت')

    class Meta :
        verbose_name = "مودم"
        verbose_name_plural = "مودم ها"

    def __str__(self):
        return f"مودم {self.name} با {self.get_payment_method_display()}"

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

    class RequestStatus(models.TextChoices):
        pending_review = "pending review",'در انتظار بازبینی'
        queued = "queued" , "در صف نصب"
        done = "done","نصب انجام شده"
        rejected = "rejected" , "رد به علت ناقض بودن اطلاعات"
        cantinstall = "cantinstall","عدم امکان دائری"

    class ExecutionStatus(models.TextChoices):
        completed = "completed","انجام شده"
        pending = "pending","در انتظار اجرا"

    class SubmissionStatus(models.TextChoices):
        registered = "registered","ثبت شده"
        pending = "pending","در انتظار ثبت"
        rejected = "rejected","عدم امکان ثبت"

    class PayStatus(models.TextChoices):
        payed = "payed","پرداخت شده"
        pending = "pending","در انتظار پرداخت"


    #Personal information
    first_name = models.CharField(max_length=25,verbose_name='نام')
    last_name = models.CharField(max_length=50,verbose_name='نام خانوادگی')
    father_name = models.CharField(max_length=25,verbose_name='نام پدر')
    national_code = models.CharField(max_length=12,verbose_name='کد ملی')
    bc_number = models.CharField(max_length=12,verbose_name='شماره شناسنامه') 
    birthday = models.CharField(max_length=50,verbose_name='تاریخ تولد')
    documents = models.ImageField(upload_to='documents/',validators=[validate_dockphoto_size],verbose_name='مدارک بارگذاری شده')
    landline_number = models.CharField(max_length=12,verbose_name='تلفن منزل',null=True,blank=True) 
    mobile_number = models.CharField(max_length=12,verbose_name='تلفن همراه')
    location = models.ForeignKey(ActiveLocations,on_delete=models.PROTECT,verbose_name='واقع در')
    address = models.TextField(verbose_name='آدرس')
    house_is_owner = models.CharField(max_length=25,choices=HouseOwnerStatus,verbose_name='وضعیت مالکیت منزل')
    post_code = models.CharField(max_length=12,verbose_name='کد پستی',unique=True)

    #service information
    sip_phone = models.BooleanField(verbose_name='متقاضی سیپ فون روی فیبرنوری')
    modem = models.ForeignKey(ActiveModems,on_delete=models.PROTECT,verbose_name='مودم درخواستی')
    plan = models.ForeignKey(ActivePlans,on_delete=models.PROTECT,verbose_name='طرح درخواستی')

    #drop status
    fat_index = models.CharField(max_length=10,verbose_name='مشخصه FAT',null=True,blank=True)
    drop_status = models.CharField(max_length=30,choices=ExecutionStatus,default=ExecutionStatus.pending,verbose_name='وضعیت دراپ')
    outdoor_area = models.PositiveBigIntegerField(verbose_name='متراژ بیرونی (متر)')
    internal_area = models.PositiveBigIntegerField(verbose_name='متراژ داخلی (متر)') 
    fusion_status = models.CharField(max_length=30,choices=ExecutionStatus,default=ExecutionStatus.pending,verbose_name='وضعیت فیوژن')
    pay_status = models.CharField(max_length=30,choices=PayStatus,default=PayStatus.pending,verbose_name='وضعیت پرداخت')
    submission_status = models.CharField(max_length=30,choices=SubmissionStatus,default=SubmissionStatus.pending,verbose_name='وضعیت ثبت فرم')
    marketer = models.CharField(max_length=50,null=True,blank=True,verbose_name='نام بازاریاب')

    #Other information
    request_status = models.CharField(max_length=230,choices=RequestStatus,default=RequestStatus.pending_review,verbose_name='وضعیت درخواست')
    tracking_code = models.PositiveIntegerField(verbose_name='کد پیگیری',unique=True,null=True,blank=True)
    log_msg_status = models.TextField(verbose_name='لاگ ارسال پیامک',null=True,blank=True)

    #detail request
    request_time = models.DateTimeField(auto_now_add=True,null=True,blank=True,verbose_name='تاریخ درخواست')
    ip_address = models.GenericIPAddressField(null=True,blank=True,verbose_name='آیپی درخواست دهنده')

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


    def __str__(self):
        return f"{self.first_name} {self.last_name} واقع در {self.location.name}"


    class Meta :
        verbose_name = "درخواست سرویس"
        verbose_name_plural = "درخواست های سرویس"