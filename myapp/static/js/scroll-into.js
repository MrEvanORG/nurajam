
document.addEventListener("DOMContentLoaded", function() {
let userInteracted = false;

// تابعی برای لغو اسکرول خودکار در صورت تعامل کاربر
const cancelAutoScroll = () => {
    userInteracted = true;
    clearTimeout(timeoutId); // لغو تایمر
};

// شنود تعاملات کاربر
window.addEventListener('scroll', cancelAutoScroll, { once: true });
window.addEventListener('touchstart', cancelAutoScroll, { once: true });
window.addEventListener('wheel', cancelAutoScroll, { once: true });

// تعیین تاخیر قبل از اجرای اسکرول (۲ ثانیه)
const timeoutId = setTimeout(function() {
    if (userInteracted) return; // اگر کاربر قبل از این تاچ کرد، انجام نده

    const target = document.getElementById("form-section");
    if (target) {
    const bottomPosition = target.offsetTop - 57;
    window.scrollTo({
        top: bottomPosition,
        behavior: "smooth" // حرکت نرم و زیبا
    });
    }
}, 2000); // تأخیر ۲ ثانیه
});