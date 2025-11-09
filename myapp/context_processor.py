from .models import OtherInfo
def link_processor(request):
    try:
        config = OtherInfo.get_instance()
        return {
                "link_phone":config.link_phone,
                "link_mail":config.link_mail,
                "link_instagram":config.link_instagram,
                "link_whatsapp":config.link_whatsapp,
            }
    except:
        return {}