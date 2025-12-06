document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("contactForm");

    form.addEventListener("submit", function (e) {
        let isValid = true;

        const name = form.querySelector("[name='name']");
        const email = form.querySelector("[name='email']");
        const message = form.querySelector("[name='message']");
        const captcha = form.querySelector("[name='captcha']");

        if (name.value.trim().length < 2) {
            alert("نام معتبر نیست.");
            isValid = false;
        }
        if (!email.value.includes("@")) {
            alert("ایمیل نامعتبر است.");
            isValid = false;
        }
        if (message.value.trim().length < 5) {
            alert("پیام خیلی کوتاه است.");
            isValid = false;
        }
        if (captcha.value.trim() === "") {
            alert("کد امنیتی را وارد کنید."); 
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
            document.getElementById("contact-section").scrollIntoView({ behavior: "smooth" });
        }
    });
});