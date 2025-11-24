from .models import OtherInfo
def link_processor(request):
    try:
        config = OtherInfo.get_instance()
        return {
                "link_phone":config.link_phone,
                "link_prphone":config.link_prphone,
                "link_mail":config.link_mail,
                "link_instagram":config.link_instagram,
                "link_whatsapp":config.link_whatsapp,
                "link_twitter":config.link_twitter,
                "link_telegram":config.link_telegram,
                "link_address":config.link_address,
                "address_text":config.address_text,
            }
    except:
        return {}