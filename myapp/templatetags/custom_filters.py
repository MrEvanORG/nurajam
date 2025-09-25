from django import template
from django.utils import timezone
import jdatetime

register = template.Library()

@register.filter
def format_toman(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        return "۰ تومان"

    million = value // 1_000_000
    thousand = (value % 1_000_000) // 1_000

    if million and thousand:
        return f"{million} میلیون و {thousand} هزار تومان"
    elif million:
        return f"{million} میلیون تومان"
    elif thousand:
        return f"{thousand} هزار تومان"
    else:
        return f"{value:,} تومان"

@register.filter
def format_cost_number(value):
    try:
        value = int(value)
        return f"{value:,}"
    except:
        return value

@register.filter
def get_image(post,name):
    return getattr(post,name,None)

@register.filter
def to_jalali(value):
    """تبدیل datetime میلادی به تاریخ و زمان شمسی با درنظر گرفتن تایم‌زون ایران"""
    if not value:
        return ""
    try:
        value = timezone.localtime(value)
        jalali_datetime = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_datetime.strftime('%Y/%m/%d - %H:%M')
    except Exception:
        return str(value)
    
@register.filter
def to_jalali_persian(value):
    """تبدیل datetime میلادی به تاریخ و زمان شمسی با درنظر گرفتن تایم‌زون ایران"""
    if not value:
        return ""
    try:
        value = timezone.localtime(value)
        jalali_datetime = jdatetime.datetime.fromgregorian(datetime=value,locale=jdatetime.FA_LOCALE)
        return jalali_datetime.strftime('%A %d %B %Y - %H:%M')
    except Exception:
        return str(value)
    
@register.filter
def time_ago(value):
    if not value:
        return ""
    try:
        now = timezone.now()
        diff = now - value

        seconds = diff.total_seconds()
        minutes = int(seconds // 60)
        hours = int(seconds // 3600)
        days = diff.days
        months = days // 30
        years = days // 365

        if seconds < 60:
            return "چند لحظه پیش"
        elif minutes < 60:
            return f"{minutes} دقیقه پیش"
        elif hours < 24:
            return f"{hours} ساعت پیش"
        elif days < 30:
            return f"{days} روز پیش"
        elif days < 365:
            return f"{months} ماه پیش"
        else:
            return f"{years} سال پیش"
    except Exception:
        return ""
    
