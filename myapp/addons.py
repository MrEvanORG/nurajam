import os

import platform# import pypandoc
from .import views
import ghasedak_sms
from django.urls import reverse
from docxtpl import DocxTemplate
from .models import ServiceRequests
from django.http import HttpResponse , FileResponse
from myapp.templatetags.custom_filters import to_jalali
from django.shortcuts import render ,get_object_or_404 , redirect
sms_api = ghasedak_sms.Ghasedak(api_key='e43935da3357ec792ac9bad1226b9ac6ae71ae59dbd6c0f3292dc1ddf909b94ayXcdVcWrLHmZmpfb')

# sudo apt update
# sudo apt install pandoc
#sudo apt install texlive-xetex
#pandoc --version

def create_form(request,kind,pk):
    rq = request.session.get('secure_form_download')
    if not rq or not rq==pk :
        return redirect(views.index) 

    obj = get_object_or_404(ServiceRequests,pk=pk)
    system = platform.system()
    # ◻ : false
    # ◼ : true

    # ⬤ : true
    # ◯ : false
    supported_data = [20,60,120,220]
    context = {
        "name":obj.get_full_name(),
        "fname":obj.father_name,
        "nc_code":obj.national_code,
        "bc_number":obj.bc_number,
        "birthday":obj.birthday,
        "lnumber":obj.landline_number,
        "mnumber":obj.mobile_number,
        "address":obj.address,
        "cpost":obj.post_code,
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
        'ability':'◼' if not obj.request_status == "cantinstall" else '◻',
        'disability':'◼' if obj.request_status == "cantinstall"  else '◻',
        "fat":obj.fat_index,
        "marketer":'' if not obj.marketer else obj.marketer,
        "date":to_jalali(obj.request_time),
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
            try:
                import subprocess 
                if os.path.isfile(FPDF_PATH):
                    os.remove(FPDF_PATH)
                command = ["libreoffice","--headless","--convert-to","pdf",FTEMPLATE_PATH,"--outdir",FPDF_DIRECTORY]
                subprocess.run(command,check=True)
                return FileResponse(open(FPDF_PATH,'rb'),as_attachment=True,filename=f'{obj.get_full_name()}.pdf')
            except Exception as e:
                return HttpResponse(e)





