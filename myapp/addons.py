import os
import time
import random
import platform 
import threading
from .import views
import ghasedak_sms
from docxtpl import DocxTemplate
from .models import ServiceRequests
from django.http import JsonResponse
from django.http import HttpResponse , FileResponse , Http404
from myapp.templatetags.custom_filters import to_jalali
from django.shortcuts import get_object_or_404 , redirect , render
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

sms_api = ghasedak_sms.Ghasedak(api_key='e43935da3357ec792ac9bad1226b9ac6ae71ae59dbd6c0f3292dc1ddf909b94ayXcdVcWrLHmZmpfb')

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

def send_contact_email(request, data):
    from myapp.templatetags.custom_filters import to_jalali_persian
    from_email = data['email']
    ctg = data['category']
    if ctg.strip() == "همکاری":
        subject = f"درخواست همکاری از {data['name']}"
    elif ctg.strip() == "پشتیبانی":
        subject = f"درخواست پشتیبانی از {data['name']}"
    else:
        subject = f"انتقاد یا پیشنهاد از {data['name']}"
    to = ["info@nurajam.ir"] 

    context = {
        "subject":subject,
        "name": data.get("name", "-"),
        "company_name": data.get("company_name", "-"),
        "email": data.get("email", "-"),
        "category": data.get("category", "-"),
        "message": data.get("message", "-"),
        "ip": get_ip(request),
        "created_at": to_jalali_persian(timezone.now()),
    }
    html_content = render_to_string("emails/contact_template.html", context)
    plain_text = (
        f"نام: {context['name']}\n"
        f"شرکت: {context['company_name']}\n"
        f"ایمیل: {context['email']}\n"
        f"نوع درخواست: {context['category']}\n\n"
        f"پیام:\n{context['message']}\n\n"
        f"IP: {context['ip']}\n"
        f"زمان درخواست: {context['created_at']}\n"
    )

    msg = EmailMultiAlternatives(subject, plain_text, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def generate_captcha_text(length=5):
    return ''.join(random.choice(string.digits) for _ in range(length))

def captcha_image(request):
    captcha_text = generate_captcha_text()

    # ذخیره کپچا در سشن
    request.session['captcha_code'] = captcha_text

    img = Image.new('RGB', (150, 50), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # فونت ساده
    try:
        from django.conf import settings
        font_path = os.path.join(settings.BASE_DIR,"static/font/Shabnam.woff")
        font = ImageFont.truetype(font_path, 32)
    except:
        font = ImageFont.load_default()

    draw.text((15, 5), captcha_text, font=font, fill=(20, 20, 20))

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()

    return HttpResponse(img_bytes, content_type='image/png')

def notif_new_user(text):
    from .models import OtherInfo
    try:
        number = (OtherInfo.objects.get(id=1)).site_linenumber
    except:
        return False
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_users = User.objects.filter(register_messages=True)
    for admin in admin_users:
        response = sms_api.send_single_sms(
            ghasedak_sms.SendSingleSmsInput(
                message=text,
                receptor=str(admin.username).strip(),
                line_number=number,
                send_date='',
                client_reference_id=''
            )
        )

def send_tracking_code_to_user(phone,code):
    # 3000824492

    newotpcommand = ghasedak_sms.SendOtpInput(
        send_date=None,
        receptors=[
            ghasedak_sms.SendOtpReceptorDto(
                mobile=str(phone),
            )
        ],
        template_name='nuratracking',
        inputs=[
            ghasedak_sms.SendOtpInput.OtpInput(param='Code', value=str(code)),
        ],
        udh=False
    )
    response = sms_api.send_otp_sms(newotpcommand)
    return response['message'] # type: ignore

def generate_tracking_code():
    while True:
        code = random.randint(100000, 999999)
        if not ServiceRequests.objects.filter(tracking_code=code).exists():
            return code
        
PHONE_OTP_TIMESTAMPS = {}

otp_timestamps_lock = threading.Lock()

OTP_COOLDOWN_SECONDS = 60



def create_form(request, kind, pk):
    rq = request.session.get('secure_form_download')
    
    # بررسی امنیتی دانلود
    if not rq or not str(rq) == str(pk):
        return redirect('index') # نام ویو index باید صحیح باشد

    obj = get_object_or_404(ServiceRequests, pk=pk)
    system = platform.system()

    # تعریف سیمبل‌ها برای خوانایی بهتر و مدیریت راحت‌تر
    S_ON = '◼'  # Square Checked
    S_OFF = '◻' # Square Unchecked
    C_ON = '⬤'  # Circle Checked
    C_OFF = '◯' # Circle Unchecked

    # استخراج آبجکت‌های وابسته برای جلوگیری از کوئری تکراری و ارور NoneType
    plan = obj.plan
    modem = obj.modem
    marketer = obj.marketer_name

    supported_data = [20, 60, 120, 220]
    supported_months = ["mo3", "mo6", "mo12"]

    # منطق Custom Plan: اگر طرح هست ولی در لیست استاندارد نیست
    custom_plan_str = ''
    if plan and (plan.data not in supported_data):
        custom_plan_str = f'{C_ON} {plan.data}GB'
    
    # منطق Custom Time: اگر زمان طرح هست ولی در لیست استاندارد نیست
    custom_time_str = ''
    if plan and (plan.plan_time not in supported_months):
        custom_time_str = f"{C_ON} {obj.get_plan_time_display()}"


    context = {
        # --- اطلاعات شخصی ---
        "name": obj.get_full_name(),
        "fname": obj.father_name or "",
        "nc_code": obj.national_code or "",
        "bc_number": obj.bc_number or "",
        "birthday": obj.birthday or "",
        "lnumber": obj.landline_number or "",
        "mnumber": obj.mobile_number or "",
        "address": obj.address or "",
        "cpost": obj.post_code or "",
        
        # --- وضعیت مالکیت ---
        "owner": C_ON if obj.house_is_owner == 'owner' else C_OFF,
        "renter": C_ON if obj.house_is_owner == 'renter' else C_OFF,

        # --- مدت زمان طرح (با شرط وجود plan) ---
        "mo3": C_ON if (plan and plan.plan_time == "mo3") else C_OFF,
        "mo6": C_ON if (plan and plan.plan_time == "mo6") else C_OFF,
        "mo12": C_ON if (plan and plan.plan_time == "mo12") else C_OFF,
        "mo0": custom_time_str,

        # --- حجم طرح (با شرط وجود plan) ---
        "plan20": C_ON if (plan and plan.data == 20) else C_OFF,
        "plan60": C_ON if (plan and plan.data == 60) else C_OFF,
        "plan120": C_ON if (plan and plan.data == 120) else C_OFF,
        "plan220": C_ON if (plan and plan.data == 220) else C_OFF,
        "customp": custom_plan_str,

        # --- نوع پرداخت (با شرط وجود plan) ---
        "prep": C_ON if (plan and plan.plan_type == "prepayment") else C_OFF,
        "postp": C_ON if (plan and plan.plan_type == "postpayment") else C_OFF,

        # --- سایر سرویس‌ها ---
        "sip": S_ON if obj.sip_phone else S_OFF,
        
        # بررسی مودم: اگر مودم انتخاب نشده باشد (None) یا قیمت 0 باشد، تیک نمی‌خورد
        "reqmodem": S_ON if (modem and modem.price != 0) else S_OFF,

        # --- وضعیت فیوژن ---
        "ability": S_ON if (obj.fusion_status != "rejected") else S_OFF,
        "disability": S_ON if (obj.fusion_status == "rejected") else S_OFF,

        # --- اطلاعات فنی ---
        "fat": obj.fat_index or "",
        "zone": obj.odc_index or "",

        # --- بازاریاب ---
        "marketer": marketer.get_full_name() if marketer else "",
        
        # --- تاریخ ---
        "date": to_jalali(obj.request_time) if obj.request_time else "",
    }

    # مسیردهی فایل‌ها
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # توجه: مسیر dock-form باید در کنار فایل views.py یا در روت پروژه چک شود
    TEMPLATE_PATH = os.path.join(BASE_DIR, "dock-form", "template.docx")
    FTEMPLATE_PATH = os.path.join(BASE_DIR, "dock-form", "output.docx")
    FPDF_PATH = os.path.join(BASE_DIR, "dock-form", "output.pdf")

    try:
        doc = DocxTemplate(TEMPLATE_PATH)
        doc.render(context)
        doc.save(FTEMPLATE_PATH)
    except Exception as e:
        return HttpResponse(f"Error creating document: {e}")

    if kind == 'word':
        try:
            return FileResponse(open(FTEMPLATE_PATH, 'rb'), as_attachment=True, filename=f'{obj.get_full_name()}.docx')
        except FileNotFoundError:
            return HttpResponse("Error: Generated Word file not found.")
            
    else: # PDF Generation
        if system == "Windows":
            import pythoncom
            try:
                from docx2pdf import convert
                if os.path.isfile(FPDF_PATH):
                    os.remove(FPDF_PATH)
                
                # برای استفاده در محیط‌های Multi-thread مثل جنگو ضروری است
                pythoncom.CoInitialize() 
                convert(FTEMPLATE_PATH, FPDF_PATH)
                
                return FileResponse(open(FPDF_PATH, 'rb'), as_attachment=True, filename=f'{obj.get_full_name()}.pdf')

            except Exception as e:
                return HttpResponse(f"PDF Conversion Error: {e}")
        elif system == 'Linux':
            return HttpResponse("Unsupported in Linux platforms (LibreOffice needed for conversion).")
        else:
            return HttpResponse("Unsupported Operating System.")

def otp_generate():
    return str(random.randint(100000, 999999))

def send_otp(phone, code):
    newotpcommand = ghasedak_sms.SendOtpInput(
        send_date=None,
        receptors=[
            ghasedak_sms.SendOtpReceptorDto(
                mobile=str(phone),
            )
        ],
        template_name='nura',
        inputs=[
            ghasedak_sms.SendOtpInput.OtpInput(param='Code', value=str(code)),
        ],
        udh=False
    )
    print(f"--- MOCK SMS ---: Sending OTP code {code} to {phone}")
    response = sms_api.send_otp_sms(newotpcommand)
    return response

def cleanup_expired_otp_timestamps():
    with otp_timestamps_lock:
        now = time.time()
        expired_phones = [
            phone for phone, timestamp in PHONE_OTP_TIMESTAMPS.items()
            if now - timestamp > OTP_COOLDOWN_SECONDS
        ]
        
        for phone in expired_phones:
            del PHONE_OTP_TIMESTAMPS[phone]
        
        if expired_phones:
            print(f"--- OTP Cleanup: Removed {len(expired_phones)} expired entries from global cache.")

def periodic_cleanup_task():
    time.sleep(10)
    print("--- Starting periodic OTP cleanup task ---")
    while True:
        time.sleep(15 * 60)
        cleanup_expired_otp_timestamps()

@require_POST
def register_sendotp(request):
    session = request.session.get('register')
    
    if not session or not session.get('phone_number'):
        return JsonResponse({'success': False, 'message': 'سشن نامعتبر است'}, status=400)

    phone_number = session.get('phone_number')
    now = time.time()

    last_req_cookie_str = request.COOKIES.get('otp_cooldown_timestamp')
    wait_time_cookie = 0
    if last_req_cookie_str:
        time_since_last_req = now - float(last_req_cookie_str)
        if time_since_last_req < OTP_COOLDOWN_SECONDS:
            wait_time_cookie = OTP_COOLDOWN_SECONDS - time_since_last_req


    wait_time_server = 0
    with otp_timestamps_lock:
        last_req_server = PHONE_OTP_TIMESTAMPS.get(phone_number, 0)
    
    if last_req_server:
        time_since_last_req_server = now - last_req_server
        if time_since_last_req_server < OTP_COOLDOWN_SECONDS:
            wait_time_server = OTP_COOLDOWN_SECONDS - time_since_last_req_server
        else:
            with otp_timestamps_lock:
                if PHONE_OTP_TIMESTAMPS.get(phone_number) == last_req_server:
                    del PHONE_OTP_TIMESTAMPS[phone_number]

    remaining_wait_time = max(wait_time_cookie, wait_time_server)

    if remaining_wait_time > 0:
        return JsonResponse({
            'success': False,
            'message': f"برای تلاش مجدد لازم است {int(remaining_wait_time)} ثانیه صبر کنید",
            'remaining_seconds': int(remaining_wait_time)
        })


    otp_code = otp_generate()
    sendrs = send_otp(phone_number, otp_code)

    session['otp_code'] = otp_code
    request.session['register'] = session

    with otp_timestamps_lock:
        PHONE_OTP_TIMESTAMPS[phone_number] = now

    if sendrs['statusCode'] == 200: # type: ignore
        response = JsonResponse({'success':True, 'message': 'کد با موفقیت ارسال شد'})
    else:
        response = JsonResponse({'success':False, 'message': 'خطایی در ارسال کد پیش آمد ، مجدد تلاش کنید'})


    response.set_cookie('otp_cooldown_timestamp', str(now), max_age=OTP_COOLDOWN_SECONDS, httponly=True, samesite='Strict')
    
    return response

@staff_member_required # فقط ادمین‌ها دسترسی داشته باشند
def admin_contract_preview(request, request_id):
    service_request = get_object_or_404(ServiceRequests, id=request_id)
    
    # اگر اسنپ‌شات وجود نداشت (برای رکوردهای قدیمی)، هندل کنید
    if not service_request.contract_snapshot:
        return render(request, 'admin/contract_preview.html', {
            'error': 'برای این درخواست فاکتور ذخیره شده‌ای یافت نشد (رکورد قدیمی است).'
        })

    context = {
        'data': service_request.contract_snapshot,
        'tracking_code': service_request.tracking_code,
        'created_at': service_request.request_time,
        # اگر فیلتر خاصی نیاز دارید اینجا پاس دهید
    }
    return render(request, 'admin/contract_preview.html', context)

def get_ip(request):

    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        ip = forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@staff_member_required # بسیار مهم: این ویو را فقط برای ادمین/کارکنان محدود می‌کند
def download_document_view(request, pk):
    """
    این ویو یک فایل را برای دانلود بر اساس PK آبجکت ارائه می‌دهد.
    """
    # ۱. آبجکت را با اطمینان پیدا کن
    obj = get_object_or_404(ServiceRequests, pk=pk)
    
    # ۲. بررسی کن که آبجکت فایل دارد یا نه
    if not obj.documents:
        raise Http404("فایلی برای این آبجکت یافت نشد.")
        
    # ۳. نام فایل دانلودی را بساز
    # پسوند را از نام فایل ذخیره شده (که UUID است) بردار
    file_path_in_db = obj.documents.name
    filename, ext = os.path.splitext(file_path_in_db)
    
    # نام کامل کاربر را بگیر
    user_full_name = obj.get_full_name()
    download_name = f"{user_full_name.replace(' ', '_')}{ext}"

    # ۴. فایل را با استفاده از FileResponse برگردان
    # ما از .open() خود فیلد استفاده می‌کنیم تا با storage های مختلف (مثل S3) هم سازگار باشد
    try:
        response = FileResponse(
            obj.documents.open('rb'), 
            as_attachment=True, 
            filename=download_name
        )
        return response
    except FileNotFoundError:
        raise Http404("فایل در سرور یافت نشد.")