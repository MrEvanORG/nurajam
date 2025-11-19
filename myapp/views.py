import json
import datetime
from threading import Thread
from .addons import *
from django.urls import reverse
from django.contrib import messages
from .models import User , OtherInfo
from django.http import HttpResponse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect 
from django.shortcuts import render , get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from myapp.templatetags.custom_filters import to_jalali_persian
from django.contrib.admin.views.decorators import staff_member_required
from .models import ActiveModems , ActivePlans, ActiveLocations , OtherInfo , ServiceRequests
from .forms import SmsForm , RegiterphonePostForm , OtpVerifyForm , PersonalInfoForm , ServiceInfoForm ,TrackingCodeForm , SmsUserForm
#-------------------------------------------#

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

    from .addons import get_ip , generate_tracking_code 

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

    dbj = ServiceInfoForm()

    plans_data_for_js = {
            p.pk: {
                'name': p.__str__(),
                'price': p.price,
                'plan_type': p.plan_type,
                'plan_time': p.plan_time,  # این فیلد حیاتی است (mo3, mo6, ...)
                'plan_time_display': p.get_plan_time_display() # برای نمایش متن
            }
            for p in dbj.PLAN_SORTED
        }

    modems_data_for_js = {
            m.pk: {
                'name': m.name,
                'price': m.price,
                'payment_method': m.payment_method,
                'payment_display': m.get_payment_method_display(),
                'tax': m.added_tax,
            }
            for m in dbj.MODEMS_SORTED
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
            from .addons import send_tracking_code_to_user
            sms_result = send_tracking_code_to_user(phone=initial_data.get('mobile'),code=rq.tracking_code)
            from django.utils import timezone
            sms_log = f'پیامک کد پیگیری | { to_jalali_persian(timezone.now())} | {sms_result} | توسط سیستم'
            rq.add_sms_log(sms_log)
            rq.save()
            from .addons import notif_new_user
            Thread(target=notif_new_user,args=(f"اطلاع رسانی : ثبت نام کاربر جدید روی سایت نوراجم  ، {rq.__str__()}\nلغو11",)).start()

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

def tracking_text_generator(service):
    number = service.mobile_number
    postcode = service.post_code
    text = "مشترک گرامی "
    if service.marketer_status == "accepted":
        if service.drop_status == "accepted":
            if service.fusion_status == "accepted":
                if service.supervisor_status == "accepted":
                    if service.submission_status == "registered":
                        text += "نصب و راه اندازی سرویس شما به اتمام رسیده است ، احتمالا در حال استفاده از سرویس خود هستید در صورت هرگونه مشکل با مخابرات منطقه تماس حاصل فرمایید ."
                    elif service.submission_status == "pending":
                        text += "نصب و تایید سرویس شما انجام شده است ، پس از ثبت سرویس در مخابرات منطقه قادر به استفاده از اینترنت پر سرعت مخابرات ایران هستید ."
                else:
                    text += "نصب سرویس شما انجام شده است ، پس از تایید نصب شما توسط کارشناسان و ثبت سرویس در مخابرات منطقه قادر به استفاده از اینترنت پر سرعت شرکت مخابرات ایران خواهید بود ."
            else:
                text += "سرویس شما در مرحله نصب است ، پس از اتمام نصب سرویس و راه اندازی سرویس شما در مخابرات منطقه قادر به استفاده از اینترنت پرسرعت شرکت مخابرات ایران خواهید بود ."
        elif service.drop_status == "rejected":
            text += "متاسفانه امکان نصب و راه اندازی سرویس برای شما وجود ندارد ، جهت اطلاعات بیشتر با پشتیبانی تماس حاصل فرمایید ."
        else:
            text += "سرویس شما در مرحله نصب است ، پس از اتمام نصب سرویس و راه اندازی سرویس شما در مخابرات منطقه قادر به استفاده از اینترنت پرسرعت شرکت مخابرات ایران خواهید بود ."
    elif service.marketer_status == "rejected":
        text += f"اطلاعات شخصی یا سرویس انتخاب شده شما توسط کارشناسان رد شده است لطفا با شماره {number} و کدپستی {postcode} اقدام به ثبت نام سرویس کنید و اطلاعات خود را در مرحله ثبت نام ویرایش کنید\n، جهت اطلاعات بیشتر درباره علت رد شدن سرویس خود میتوانید با پشتیبانی تماس حاصل فرمایید ."
    else:
        text += " ثبت نام سرویس شما با موفقیت انجام شد پس از تایید اطلاعات شما توسط کارشناسان فرایند نصب سرویس شما آغاز میشود ."

    if service.pay_status == "pending":
        text += '<br><br>ضمنا هزینه نصب و راه اندازی سرویس توسط شما پرداخت نشده است لطفا با پشتیبانی تماس حاصل کرده و نسبت به پرداخت مبلغ قرار داد شده اقدام نمایید .'

    return text


def tracking_entercode(request):

    form = TrackingCodeForm()
    
    if request.method == "POST":
        form = TrackingCodeForm(request.POST)
        if form.is_valid() :
            request.session['trackingcode'] = form.cleaned_data['tracking_code']
            return redirect(tracking_result)
    
    return render(request,'tracking_entercode.html',{"form":form})


def tracking_result(request):
    session = request.session.get('trackingcode',None)
    if not session :
        return redirect(tracking_entercode)
    
    tracking_code = int(session)
    service = get_object_or_404(ServiceRequests,tracking_code=tracking_code)
    text = tracking_text_generator(service)

    config = OtherInfo.get_instance()

    context = {
        "text":text,
        "post_code":service.post_code,
        "tracking_code":service.tracking_code,
        "support_phone":config.contact_number,
    }

    del request.session['trackingcode']
    return render(request,'tracking_result.html',context=context)

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

@staff_member_required
def send_sms_user(request,pk):
    if getattr(request.user, "role_marketer", False) == False and not request.user.is_superuser :
        print(getattr(request.user, "role_marketer", False))
        print(request.user.is_superuser)
        messages.error(request,"شما دسترسی برای ارسال پیامک ندارید")
        return redirect(reverse("admin:index"))
    
    service = get_object_or_404(ServiceRequests,pk=pk)
    context = {"service":service}
    return render(request, 'admin/sms_formats.html', context)

@staff_member_required
def send_sms_user_type(request,pk,type):
    if getattr(request.user, "role_marketer", False) == False and not request.user.is_superuser :
        messages.error(request,"شما دسترسی برای ارسال پیامک ندارید")
        return redirect(reverse("admin:index"))
    print(type)
    if not type in ["cash","tracking","custom","endservice"]:
        messages.error(request,"نوع وارد شده نامعتبر است")
        return redirect(send_sms_user,pk=pk)
    
    converted_type = ""
    if type == "cash":
        converted_type = "واریز وجه"
    
    elif type == "tracking":
        converted_type = "کد پیگیری"
    

    elif type == "custom":
        converted_type = "سفارشی"

    form = SmsUserForm(data=request.POST,extra_value=type)
    if request.method == "POST":
        if form.is_valid():
            request.session["message_info"] = {
                "pk":pk,
                "type":type,
                "card_number":form.cleaned_data.get("card_number",None),
                "cost":form.cleaned_data.get("cost",None),
                "text":form.cleaned_data.get("message",None),
            }
            return redirect(send_sms_user_sending)
        

    service = get_object_or_404(ServiceRequests,pk=pk)
    context = {"service":service,"type":converted_type,"form":form,"title":f"ارسال پیامک {converted_type}"}
    return render(request, 'admin/sms_readyforsend.html', context)

@staff_member_required
def send_sms_user_sending(request):
    session = request.session.get('message_info',None)
    if not session :
        return redirect(reverse("admin:myapp_servicerequests"))
    import ghasedak_sms
    sms_api = ghasedak_sms.Ghasedak(api_key='e43935da3357ec792ac9bad1226b9ac6ae71ae59dbd6c0f3292dc1ddf909b94ayXcdVcWrLHmZmpfb')
    
    service = get_object_or_404(ServiceRequests,pk=session.get("pk"))

    type = session.get("type")
    converted_type = ""
    if type == "cash":
        converted_type = "واریز وجه"
    
    elif type == "tracking":
        converted_type = "کد پیگیری"
    

    elif type == "custom":
        converted_type = "سفارشی"

    if type == "cash":
        newotpcommand = ghasedak_sms.SendOtpInput(
            send_date=None,
            receptors=[
                ghasedak_sms.SendOtpReceptorDto(
                    mobile=str(service.mobile_number),
                )
            ],
            template_name='nuracash',
            inputs=[
                ghasedak_sms.SendOtpInput.OtpInput(param='Cost', value=str(session.get("cost"))),
                ghasedak_sms.SendOtpInput.OtpInput(param='Number', value=str(session.get("card_number"))),
            ],
            udh=False
        )
        response = sms_api.send_otp_sms(newotpcommand)
    elif type == "tracking":
        if not service.tracking_code :
            messages.error(request,f"کد پیگیری برای سرویس {service} وجود ندارد")
            return redirect(reverse("admin:myapp_servicerequests"))
        newotpcommand = ghasedak_sms.SendOtpInput(
            send_date=None,
            receptors=[
                ghasedak_sms.SendOtpReceptorDto(
                    mobile=str(service.mobile_number),
                )
            ],
            template_name='nuratracking',
            inputs=[
                ghasedak_sms.SendOtpInput.OtpInput(param='Code', value=str(service.tracking_code)),
            ],
            udh=False
        )
        response = sms_api.send_otp_sms(newotpcommand)
    elif type == "custom":
        try:
            number = (OtherInfo.objects.get(id=1)).site_linenumber
        except:
            messages.error(request,'لاین نامبر سایت در سایر اطلاعات وارد نشده است')
            return HttpResponseRedirect(reverse('admin:myapp_servicerequests'))

        response = sms_api.send_single_sms(
            ghasedak_sms.SendSingleSmsInput(
                message=session.get("text"),
                receptor=str(service.mobile_number),
                line_number=number,
            )
        )
    else:
        return HttpResponse("invalid type")
    print(response)
    result = {
        "status" : "موفق" if response.get('isSuccess') else "ناموفق", # type: ignore
        "reason" :  response.get('message', 'خطای نامشخص'), # type: ignore
        "sms_type" : f"پیامک {converted_type}", # type: ignore
    }

    context = {
        "service":service,
        "name":service.get_full_name(),
        "result":result,
        "title":f"گزارش ارسال پیامک {converted_type}"
    }
    from django.utils import timezone
    sms_log = f'پیامک {converted_type} | { to_jalali_persian(timezone.now())} | {result["reason"]} | توسط {request.user.get_full_name()}'
    service.add_sms_log(sms_log)
    service.save()
    return render(request,"admin/user_sms_results.html",context=context)
    


    


