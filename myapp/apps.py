from django.apps import AppConfig
import threading
import sys

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = 'برنامه ثبت سرویس'

    def ready(self):
        import myapp.signals
        is_runserver = any(arg in ['runserver', 'gunicorn', 'uwsgi'] for arg in sys.argv)
        
        if is_runserver:
            from . import addons 
            cleanup_thread = threading.Thread(
                target=addons.periodic_cleanup_task,
                daemon=True
            )
            cleanup_thread.start()