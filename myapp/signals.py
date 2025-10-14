from django.db.models.signals import pre_save , post_delete
from django.dispatch import receiver
from .models import ServiceRequests

# این سیگنال برای حذف فایل در زمان حذف کامل رکورد است (کد خودتان)
@receiver(post_delete, sender=ServiceRequests)
def delete_associated_file_on_delete(sender, instance, **kwargs):
    if instance.documents:
        instance.documents.delete(save=False)

# راه‌حل جدید: این سیگنال برای حذف فایل قدیمی در زمان آپدیت است
@receiver(pre_save, sender=ServiceRequests)
def delete_old_file_on_update(sender, instance, **kwargs):
    """
    این تابع قبل از ذخیره شدن یک نمونه از مدل ServiceRequests اجرا می‌شود.
    فایل قدیمی را در صورتی که فایل جدیدی جایگزین آن شده باشد، حذف می‌کند.
    """
    # اگر نمونه جدید است و هنوز در دیتابیس ذخیره نشده، کاری انجام نده
    if not instance.pk:
        return

    try:
        # نمونه قدیمی را از دیتابیس بخوان
        old_instance = ServiceRequests.objects.get(pk=instance.pk)
    except ServiceRequests.DoesNotExist:
        # اگر به هر دلیلی نمونه قدیمی وجود نداشت، کاری انجام نده
        return

    # اگر فایل قدیمی وجود دارد و با فایل جدید متفاوت است
    if old_instance.documents and old_instance.documents != instance.documents:
        # فایل قدیمی را حذف کن
        old_instance.documents.delete(save=False)