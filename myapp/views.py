from .addons import *
from .forms import SmsForm 
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from .models import User , OtherInfo
from django.http import HttpResponseRedirect 
from django.contrib.admin.views.decorators import staff_member_required

def index(request):
    return render(request,'index.html')

def register_personal(request):
    days = range(1, 32)
    months = [
        "فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
        "مهر","آبان","آذر","دی","بهمن","اسفند"
    ]
    years = range(1315, 1387)

    return render(request, 'register_personal.html', {
        'days': days,
        'months': months,
        'years': years
    })

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