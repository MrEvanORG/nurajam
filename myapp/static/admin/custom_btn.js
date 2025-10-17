document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById("fileInput");
    const fileBtn = document.querySelector(".file-btn");
    const fileStatus = document.getElementById("fileStatus");
    
    // متغیری برای نگهداری وضعیت اعتبار فایل
    let isFileValid = false;
    fileInput.addEventListener("change", function () {
        const file = this.files[0];
        const errorSpan = fileStatus.parentElement.nextElementSibling;
        
        // ریست وضعیت
        fileBtn.classList.remove("success", "error");
        fileStatus.classList.remove("success", "error", "normal");
        errorSpan.textContent = "";
        fieldsValidity.file = false;

        if (!file) {
            fileStatus.textContent = "فایلی بارگذاری نشده";
            fileStatus.classList.add("normal");
            fileBtn.textContent = "انتخاب فایل";
            checkFormValidity();
            return;
        }

        const maxSize = 3 * 1024 * 1024; // 3MB
        if (file.size > maxSize) {
            errorSpan.textContent = "حجم فایل بیش از ۳ مگابایت است.";
            fileStatus.textContent = "خطا در بارگذاری";
            fileStatus.classList.add("error");
            fileBtn.classList.add("error");
            fileBtn.textContent = "انتخاب دوباره";
            this.value = "";
            checkFormValidity();
            return;
        }

        const allowedTypes = ["image/png", "image/jpeg"];
        if (!allowedTypes.includes(file.type)) {
            errorSpan.textContent = "فرمت فایل نامعتبر است (فقط png, jpg).";
            fileStatus.textContent = "خطا در بارگذاری";
            fileStatus.classList.add("error");
            fileBtn.classList.add("error");
            fileBtn.textContent = "انتخاب دوباره";
            this.value = "";
            checkFormValidity();
            return;
        }

        // اگر همه چیز معتبر بود
        fileStatus.textContent = "فایل معتبر بارگذاری شد";
        fileStatus.classList.add("success");
        fileBtn.classList.add("success");
        fileBtn.textContent = "تغییر فایل";
        fieldsValidity.file = true; // وضعیت فایل را معتبر کن
        checkFormValidity(); // وضعیت کل فرم را بررسی کن
    });
}