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
sms_api = ghasedak_sms.Ghasedak(api_key='e43935da3357ec792ac9bad1226b9ac6ae71ae59dbd6c0f3292dc1ddf909b94ayXcdVcWrLHmZmpfb')


def send_system_to_user_message(phone,message):
    # 3000824492
    try:
        from .models import OtherInfo
        config = OtherInfo.get_instance()
        number = config.site_linenumber
    except Exception as e:
        return f"ارور : لاین نامبر سایت تعریف نشده است + {e}"

    response = sms_api.send_single_sms(
        ghasedak_sms.SendSingleSmsInput(
            message=message,
            receptor=str(phone),
            line_number=str(number),
            send_date='',
            client_reference_id='',
        )
    )
    return response['message'] # type: ignore

def generate_tracking_code():
    while True:
        code = random.randint(100000, 999999)
        if not ServiceRequests.objects.filter(tracking_code=code).exists():
            return code
        
PHONE_OTP_TIMESTAMPS = {}

otp_timestamps_lock = threading.Lock()

OTP_COOLDOWN_SECONDS = 60

def create_form(request,kind,pk):
    rq = request.session.get('secure_form_download')
    if not rq or not rq==pk :
        return redirect(views.index) 

    obj = get_object_or_404(ServiceRequests,pk=pk)
    system = platform.system()
    # '◻' : false
    # '◼' : true

    # '⬤' : true
    # '◯' : false
    supported_data = [20,60,120,220]
    context = {
        "name":obj.get_full_name(),
        "fname":obj.father_name or "",
        "nc_code":obj.national_code or "",
        "bc_number":obj.bc_number or "",
        "birthday":obj.birthday or "",
        "lnumber":obj.landline_number or "",
        "mnumber":obj.mobile_number or "",
        "address":obj.address or "",
        "cpost":obj.post_code or "",
        "owner":'⬤'if obj.house_is_owner == 'owner' else '◯',
        "renter":'⬤'if obj.house_is_owner == 'renter' else  '◯',
        "mo3":'⬤' if obj.modem.payment_method == "mi3" else '◯',
        "mo6":'⬤' if obj.modem.payment_method == "mi6" else '◯',
        "mo12":'⬤' if obj.modem.payment_method == "mi12" else '◯',
        "plan20":'⬤' if obj.plan.data == 20 else '◯',
        "plan60":'⬤' if obj.plan.data == 60 else '◯',
        "plan120":'⬤' if obj.plan.data == 120 else '◯',
        "plan220":'⬤' if obj.plan.data == 220 else '◯',
        "customp":f'⬤ {obj.plan.data}GB' if not obj.plan.data in supported_data else '',
        "sip": '◼' if obj.sip_phone else '◻',
        "reqmodem": '◼' if not obj.modem.price == 0 else '◻',
        'ability':'◼' if not obj.fusion_status == "rejected" else '◻',
        'disability':'◼' if obj.fusion_status == "rejected"  else '◻',
        "fat":obj.fat_index or "",
        "zone":obj.odc_index or "",
        "marketer":'' if not obj.marketer_name else obj.marketer_name.get_full_name(),
        "date":to_jalali(obj.request_time),
        "prep":'⬤' if obj.plan.plan_type == "prepayment" else '◯',
        "postp":'⬤' if obj.plan.plan_type == "postpayment" else '◯',
    }
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_PATH = os.path.join(BASE_DIR,"dock-form","template.docx")
    FTEMPLATE_PATH = os.path.join(BASE_DIR,"dock-form","output.docx")
    FPDF_PATH = os.path.join(BASE_DIR,"dock-form","output.pdf")
    FPDF_DIRECTORY = os.path.dirname(FPDF_PATH)
    try:
        doc = DocxTemplate(TEMPLATE_PATH)
    except Exception as e:
        return HttpResponse(e)
    doc.render(context)
    doc.save(FTEMPLATE_PATH)
    if kind == 'word':
        return FileResponse(open(FTEMPLATE_PATH,'rb'),as_attachment=True,filename=f'{obj.get_full_name()}.docx')
    else:
        if system == "Windows":
            import pythoncom
            try:
                from docx2pdf import convert
                if os.path.isfile(FPDF_PATH):
                    os.remove(FPDF_PATH)
                pythoncom.CoInitialize()
                convert(FTEMPLATE_PATH,FPDF_PATH)
                return FileResponse(open(FPDF_PATH,'rb'),as_attachment=True,filename=f'{obj.get_full_name()}.pdf')

            except Exception as e:
                return HttpResponse(e)
        elif system == 'Linux':
            return HttpResponse("Unsopported in Linux platforms .... ")

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