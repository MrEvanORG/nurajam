function openContractModal(url) {
    // 1. ساخت ساختار مودال در لحظه
    const modalHtml = `
        <div class="modal-overlay" id="contractModal" onclick="closeContractModal(event)">
            <div class="modal-content">
                <button class="modal-close" onclick="forceCloseModal()">×</button>
                <div id="modal-body-content" style="min-height:200px; display:flex; justify-content:center; align-items:center;">
                    <span style="font-size:20px; color:#666;">⏳ در حال بارگذاری...</span>
                </div>
            </div>
        </div>
    `;
    
    // اضافه کردن به انتهای بادی
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 2. فچ کردن محتوا از جنگو ویو
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const contentDiv = document.getElementById('modal-body-content');
            contentDiv.style.display = 'block'; // بازگشت به حالت عادی
            contentDiv.innerHTML = html;
        })
        .catch(err => {
            document.getElementById('modal-body-content').innerHTML = 
                '<p style="color:red; text-align:center; padding:20px;">خطا در دریافت اطلاعات قرارداد</p>';
        });
}

function closeContractModal(event) {
    // بستن مودال اگر روی قسمت تیره کلیک شد
    if (event.target.id === 'contractModal') {
        forceCloseModal();
    }
}

function forceCloseModal() {
    const modal = document.getElementById('contractModal');
    if (modal) modal.remove();
}