from django import forms
from django.core.exceptions import ValidationError


class SmsForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'cols': 80}),
        label='متن پیامک',
        help_text='می‌توانید از متغیرهایی مانند {user.first_name}, {user.last_name}, {user.username} در متن پیام استفاده کنید.'
    )