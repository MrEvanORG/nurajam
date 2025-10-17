import json
from .forms import SmsForm , RegiterphonePostForm , OtpVerifyForm , PersonalInfoForm , ServiceInfoForm
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from .models import User , OtherInfo
from django.http import HttpResponseRedirect 
from .models import ActiveModems , ActivePlans, ActiveLocations , OtherInfo , ServiceRequests
from django.contrib.admin.views.decorators import staff_member_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect
from .addons import *
import datetime
from django.http import HttpResponse
from myapp.templatetags.custom_filters import to_jalali_persian


def generate_tracking_code():
    while True:
        code = random.randint(100000, 999999)
        if not ServiceRequests.objects.filter(tracking_code=code).exists():
            return code
     
def index(request):
    return render(request,'index.html')

def register_index(request):
    request.session['register'] = {
        "is_indexed":True,
    }
    return render(request,'register_index.html')

def register_getnumber(request):
    session = request.session.get('register',None)
    if (not session) or (not session.get('is_indexed')) :
        return redirect(register_index)
    
    if request.method == "GET":
        return render(request,'register_getnumber.html')
    
    if request.method == "POST":
        form = RegiterphonePostForm(request.POST)
        if form.is_valid():

            session.update({
                "phone_number":form.cleaned_data['mobile'],
                "post_code":form.cleaned_data['post_code'],
            })
            request.session['register'] = session
            return redirect(register_verifyphonenumber)
        else:
            return render(request,'register_getnumber.html',{'form':form})
        
def register_verifyphonenumber(request):
    session = request.session.get('register', None)
    if (not session) or (not session.get('is_indexed')) :
        return redirect(register_index)
    
    elif (not session.get('phone_number')) or ( not session.get('post_code')):
        return redirect(register_getnumber)
    
    if request.method == "GET" :
        context = {
            "phone_number": session.get('phone_number'),
            "is_postback": False  
        }
        return render(request, 'register_verifyphonenumber.html', context)
    

    if request.method == "POST" :
        form = OtpVerifyForm(request.POST)
        
   
        if form.is_valid():
            if form.cleaned_data['otp_code'].strip() == session.get('otp_code'):
                session.update({"postcode_verified":True})
                request.session['register'] = session
                return redirect('register-personal')
            else:
                context = {
                    "code_invalid": True,
                    "phone_number": session.get('phone_number'),
                    "is_postback": True 
                }
                return render(request, 'register_verifyphonenumber.html', context)
        
        else:
            context = {
                "form": form,
                "phone_number": session.get('phone_number'),
                "is_postback": True 
            }
            return render(request,'register_verifyphonenumber.html', context)
    
def register_personal(request):
    session = request.session.get('register',None)
    if not session:
        return redirect(register_verifyphonenumber)

    is_verified = session.get('postcode_verified')
    if (not session) or (not is_verified) or (not is_verified == True):
        return redirect(register_verifyphonenumber)

    from .addons import get_ip , generate_tracking_code , send_system_to_user_message

    initial_data = {
        'mobile': session.get('phone_number', '09123456789'),
        'post_code': session.get('post_code',None), 
    }
    instance = ServiceRequests.objects.filter(post_code= str(initial_data.get('post_code')).strip() ).first()
    # print(instance)

    if instance:
        print("runed")
        if instance.birthday:
            try:
                year, month, day = instance.birthday.split('/')
                initial_data.update({
                    'first_name': instance.first_name,
                    'last_name': instance.last_name,
                    'father_name': instance.father_name,
                    'national_code': instance.national_code,
                    'bc_number': instance.bc_number,
                    'originated_from':instance.originated_from,
                    'year': year,
                    'month': month,
                    'day': day,
                    'address': instance.address,
                    'home_phone': instance.landline_number,
                    'ownerstatus': instance.house_is_owner,
                    'location': str(instance.location.id) if instance.location else None, # type: ignore
                    'id_image': instance.documents,
                })
            except ValueError as e:
                pass

    if request.method == 'POST':
        form = PersonalInfoForm(request.POST, request.FILES)
        if form.is_valid():
            location_id = form.cleaned_data['location']
            location = ActiveLocations.objects.get(pk=location_id)
            birth = f"{form.cleaned_data['year']}/{form.cleaned_data['month']}/{form.cleaned_data['day']}"
            rq , created = ServiceRequests.objects.update_or_create(
                post_code = initial_data.get('post_code'),
                defaults = {
                "first_name" : form.cleaned_data['first_name'],
                "last_name" : form.cleaned_data['last_name'],
                "father_name" : form.cleaned_data['father_name'],
                "national_code" : form.cleaned_data['national_code'],
                "bc_number" : form.cleaned_data['bc_number'],
                "originated_from":form.cleaned_data['originated_from'],
                "birthday" : birth,
                "documents" : form.cleaned_data['id_image'],
                "mobile_number" : initial_data.get('mobile'),
                "location" : location,
                "address" : form.cleaned_data['address'],
                "house_is_owner" : form.cleaned_data['ownerstatus'],
                "landline_number" : form.cleaned_data['home_phone'],
                "finished_request" : False,
                "marketer" : 'ثبت نام شده توسط سیستم',
                "ip_address" : get_ip(request),
                })
            if created:
                tracking_code = generate_tracking_code()
                rq.tracking_code = tracking_code
                # sms_result = send_system_to_user_message(phone=initial_data.get('mobile'),message='کاربر گرامی مشخصات شما در کارتابل سایت بارگذاری شد جهت تکمیل ثبت نام سرویس مورد نظر خود را در منوی پیش رو انتخاب کنید \nلغو 11')
            else:
                pass
                # sms_result = send_system_to_user_message(phone=initial_data.get('mobile'),message='کاربر گرامی مشخصات جدید شما در کارتابل سایت بارگذاری شد پس از انتخاب سرویس در منوی پیش رو ثبت نام شما پایان میپذیرد .\nلغو11')

            # from django.utils import timezone
            # sms_log = f'ارسال پیامک وضعیت | { to_jalali_persian(timezone.now())} | {sms_result}'
            # rq.add_sms_log(sms_log)
            rq.save()
            session.update({'personal_registered':True})
            request.session['register'] = session
            return redirect(register_selectservice)
    else:
        form = PersonalInfoForm(initial=initial_data)

    
    return render(request, 'register_personal.html', {'form': form})

def register_selectservice(request):
    session = request.session.get('register',None)
    if (not session):
        return redirect(register_personal)

    personal_registered = session.get('personal_registered')
    if (not personal_registered) or (not personal_registered == True):
        return redirect(register_personal)


    plans_data_for_js = {
        p.pk: {'name': p.__str__(), 'price': p.price}
        for p in ServiceInfoForm.PLAN_SORTED
    }

    
    modems_data_for_js = {
        m.pk: {
            'name': m.name,
            'price': m.price,
            'payment_method': m.payment_method,
            'payment_display': m.get_payment_method_display(),
            'tax':m.added_tax,
        }
        for m in ServiceInfoForm.MODEMS_SORTED
    }

    try:
        from .models import OtherInfo
        config = OtherInfo.get_instance()
    except Exception as e:
        return HttpResponse(f"{e}")

    #this -------------------------------------------

    initial_data = {
        'mobile': session.get('phone_number',None),
        'post_code': session.get('post_code',None), 
    }
    instance = ServiceRequests.objects.filter(post_code= str(initial_data.get('post_code')).strip() ).first()
    if instance:
        try:
            initial_data.update({
                "plan":str(instance.plan.pk),
                "modem":str(instance.modem.pk),
                "sipstatus":"false" if not instance.sip_phone else "true",
            })
        except:
            pass

    if request.method == "POST":
        form = ServiceInfoForm(request.POST)
        if form.is_valid() :
            from django.shortcuts import get_object_or_404
            rq = get_object_or_404(ServiceRequests,post_code=initial_data.get('post_code'))

            modem = get_object_or_404(ActiveModems,id=int(form.cleaned_data['modem']))
            plan = get_object_or_404(ActivePlans,id=int(form.cleaned_data['plan']))

            rq.sip_phone = True if form.cleaned_data['sipstatus'] == 'true' else False
            rq.plan = plan
            rq.modem = modem
            rq.finished_request = True

            rq.save(update_fields=['sip_phone','modem','plan','finished_request'])
            from .addons import send_system_to_user_message
            sms_result = send_system_to_user_message(phone=initial_data.get('mobile'),message=f'کاربر گرامی ثبت نام سرویس شما با موفقیت انجام شد\nکد پیگیری سرویس شما : {rq.tracking_code}\nلغو11')
            from django.utils import timezone
            sms_log = f'ارسال پیامک وضعیت | { to_jalali_persian(timezone.now())} | {sms_result}'
            rq.add_sms_log(sms_log)
            rq.save()
            session.update({
                "service_registered":True,
                "tracking_code":rq.tracking_code,
            })
            print('session updated')
            request.session['register'] = session
            return redirect(register_contractdrafted)
        else:
            pass
            
    
    elif request.method == "GET":
        form = ServiceInfoForm(initial=initial_data)

    context = {
        "drop_cost": config.drop_cost, 
        "sip_cost": config.sip_phone_cost,
        
        "plans_data_json": json.dumps(plans_data_for_js),
        "modems_data_json": json.dumps(modems_data_for_js, cls=DjangoJSONEncoder),
        "form":form,
    }
    return render(request, 'register_selectservice.html', context)
    
def register_contractdrafted(request):
    session = request.session.get('register',None)
    if (not session):
        return redirect(register_selectservice)

    service_registered = session.get('service_registered',None)
    tracking_code = session.get('tracking_code',None)
    if (service_registered == None) or (tracking_code == None):
        print("not sessiom")
        return redirect(register_selectservice)
    
    initial_data = {
        'mobile': session.get('phone_number',None),
        'post_code': session.get('post_code',None), 
        'tracking_code':tracking_code,
    }
    del request.session['register']

    return render(request,'register_contractdrafted.html',initial_data)

@staff_member_required
def send_sms_page_view(request):
    user_ids = request.session.get('selected_user_ids_for_sms')
    
    if not user_ids:
        messages.error(request, 'کاربری انتخاب نشده یا نشست شما منقضی شده است.')
        return HttpResponseRedirect(reverse('admin:myapp_user_changelist'))
    try:
        number = (OtherInfo.objects.get(id=1)).site_linenumber
    except:
        messages.error(request,'لاین نامبر سایت در سایر اطلاعات وارد نشده است')
        return HttpResponseRedirect(reverse('admin:myapp_user_changelist'))

    users = User.objects.filter(id__in=user_ids)
    
    if request.method == 'POST':
        form = SmsForm(request.POST)
        if form.is_valid():
            message_template = form.cleaned_data['message']
            results = []
            success_count = 0
            fail_count = 0

            for user in users:
                final_message = message_template.format(user=user)
                
                try:
                    response = sms_api.send_single_sms(
                        ghasedak_sms.SendSingleSmsInput(
                            message=final_message,
                            receptor=(user.username).strip(),
                            line_number=number,
                        )
                    )

                    if response.get('isSuccess'):
                        success_count += 1
                        status = 'موفق'
                    else:
                        fail_count += 1
                        status = 'ناموفق'

                    results.append({
                        'user_id': user.id,
                        'full_name': user.get_full_name() or (user.first_name+' '+user.last_name),
                        'phone_number': user.username,
                        'sms_text' : final_message , 
                        'status': status,
                        'reason': response.get('message', 'خطای نامشخص')
                    })

                except Exception as e:
                    fail_count += 1
                    results.append({
                        'user_id': user.id,
                        'full_name': user.get_full_name() or (user.first_name+' '+user.last_name),
                        'phone_number': user.username,
                        'status': 'ناموفق',
                        'reason': f'خطای سیستمی: {str(e)}'
                    })

            del request.session['selected_user_ids_for_sms']
            
            context = {
                'title': 'گزارش نهایی ارسال پیامک',
                'results': results,
                'success_count': success_count,
                'fail_count': fail_count,
                'total_count': len(users)
            }
            return render(request, 'admin/sms_results.html', context)
    else:
        form = SmsForm()

    context = {
        'title': f'ارسال پیامک به {len(users)} کاربر',
        'users': users,
        'form': form,
    }
    return render(request, 'admin/send_sms_form.html', context)