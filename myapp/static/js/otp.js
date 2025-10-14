document.addEventListener('DOMContentLoaded', () => {
    const resendBtn = document.getElementById('resend-btn');
    const resendText = document.getElementById('resend-text');
    const resendTimer = document.getElementById('resend-timer');
    const otpMessage = document.getElementById('otp-message');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    let countdownInterval;

    // تابع برای شروع شمارش معکوس
    const startCountdown = (duration) => {
        let timer = duration;
        
        // پاک کردن شمارنده قبلی اگر وجود داشته باشد
        clearInterval(countdownInterval);

        resendBtn.disabled = true;
        resendText.style.display = 'none';
        resendTimer.style.display = 'inline';

        countdownInterval = setInterval(() => {
            resendTimer.textContent = `ارسال مجدد تا ${timer} ثانیه دیگر`;
            timer--;

            if (timer < 0) {
                clearInterval(countdownInterval);
                resendBtn.disabled = false;
                resendText.style.display = 'inline';
                resendTimer.style.display = 'none';
                otpMessage.textContent = "";
            }
        }, 1000);
    };

    // تابع اصلی برای درخواست ارسال OTP
    const requestOtp = async () => {
        // قبل از ارسال، دکمه را غیرفعال می‌کنیم
        resendBtn.disabled = true;
        otpMessage.textContent = 'در حال ارسال کد...';

        try {
            const response = await fetch('/register/send_otp', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                otpMessage.textContent = 'کد با موفقیت ارسال شد.';
                startCountdown(60); // شروع شمارش معکوس ۶۰ ثانیه‌ای
            } else {
                // اگر سرور زمان انتظار باقیمانده را برگرداند
                if (data.remaining_seconds) {
                    otpMessage.textContent = data.message;
                    startCountdown(data.remaining_seconds);
                } else {
                    otpMessage.textContent = data.message || 'خطا در ارسال کد. لطفا دوباره تلاش کنید.';
                    resendBtn.disabled = false; // فعال کردن دکمه در صورت خطای کلی
                }
            }
        } catch (error) {
            console.error('Error requesting OTP:', error);
            otpMessage.textContent = 'خطای شبکه. لطفا اتصال خود را بررسی کنید.';
            resendBtn.disabled = false;
        }
    };

    resendBtn.addEventListener('click', requestOtp);

    // --- این بخش نهایی و اصلاح شده است ---
    // اگر این یک بارگذاری مجدد به خاطر خطای فرم نیست، کد را خودکار ارسال کن
    if (!isPostback) {
        requestOtp();
    } else {
        // در غیر این صورت، هیچ کد خودکاری ارسال نکن.
        // کاربر باید صراحتا روی دکمه "ارسال مجدد" کلیک کند.
        console.log("Postback detected. Automatic OTP request skipped.");
    }
});