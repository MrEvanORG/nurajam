document.addEventListener('DOMContentLoaded', function () {
    // 1. گرفتن المان‌های لازم
    const modemSelect = document.getElementById('modem-select');
    const planSelect = document.getElementById('plan-select');
    const sipRadios = document.querySelectorAll('input[name="sipstatus"]');
    const costDetailsDiv = document.getElementById('cost-details');
    const rulesSection = document.getElementById('rules-section');
    const rulesCheckbox = document.getElementById('rules');
    const submitButton = document.getElementById('submit-button');

    // المان‌های جدید نمایشی
    const contractDurationRow = document.getElementById('contract-duration-row');
    const contractDurationText = document.getElementById('contract-duration-text');

    // 2. داده‌های اولیه
    const costDataDiv = document.getElementById('cost-data');
    const DROP_COST = parseFloat(costDataDiv.dataset.dropCost);
    const SIP_COST = parseFloat(costDataDiv.dataset.sipCost);
    const modemsData = JSON.parse(document.getElementById('modems-data').textContent);
    const plansData = JSON.parse(document.getElementById('plans-data').textContent);

    // 3. و 4. گرفتن سلول‌های جدول (مشابه قبل)
    const modemNameCell = document.getElementById('modem-name');
    const modemPaymentCell = document.getElementById('modem-payment-type');
    const modemCostCell = document.getElementById('modem-cost');
    const planNameCell = document.getElementById('plan-name');
    const planPaymentTypeCell = document.querySelector('#plan-name + td');
    const planCostCell = document.getElementById('plan-cost');
    const sipRow = document.getElementById('sip-phone-row');
    const sipCostCell = document.getElementById('sip-cost');
    const modemTaxRow = document.getElementById('modem-tax-row');
    const modemTaxCostCell = document.getElementById('modem-tax-cost');

    const cashPaymentRow = document.getElementById('cash-payment-row');
    const cashPaymentCostCell = document.getElementById('cash-payment-cost');
    const firstPaymentRow = document.getElementById('first-payment-row');
    const firstPaymentLabelCell = document.getElementById('first-payment-label');
    const firstPaymentCostCell = document.getElementById('first-payment-cost');
    const nextPaymentsRow = document.getElementById('next-payments-row');
    const nextPaymentsLabelCell = document.getElementById('next-payments-label');
    const nextPaymentsCostCell = document.getElementById('next-payments-cost');
    const totalContractLabelCell = document.getElementById('total-contract-label');
    const totalContractCostCell = document.getElementById('total-contract-cost');

    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-US').format(Math.round(num)) + ' تومان';
    };

    // مپ کردن کد زمان طرح به عدد ماه
    const planTimeMapping = {
        'mo3': 3,
        'mo6': 6,
        'mo9': 9,
        'mo12': 12
    };

    // --- تابع جدید: فیلتر کردن طرح‌ها بر اساس مودم ---
    function filterPlansByModem() {
        const selectedModemId = modemSelect.value;
        if (!selectedModemId) return;

        const selectedModem = modemsData[selectedModemId];
        const paymentMethod = selectedModem.payment_method;

        // تعیین پسوند مجاز (مثلا mi6 باید mo6 را نشان دهد)
        let allowedSuffix = null; // null یعنی همه طرح‌ها مجاز است

        if (paymentMethod === 'mi3') allowedSuffix = 'mo3';
        else if (paymentMethod === 'mi6') allowedSuffix = 'mo6';
        else if (paymentMethod === 'mi9') allowedSuffix = 'mo9';
        else if (paymentMethod === 'mi12') allowedSuffix = 'mo12';
        // برای cash و nocashneed مقدار allowedSuffix همان null می ماند

        const options = planSelect.options;
        let currentPlanValid = false;

        for (let i = 0; i < options.length; i++) {
            const opt = options[i];
            const planId = opt.value;

            // گزینه "انتخاب کنید" را رد میکنیم
            if (!planId) continue; 

            const plan = plansData[planId];
            
            // منطق فیلتر
            if (allowedSuffix && plan.plan_time !== allowedSuffix) {
                // اگر محدودیت داریم و این طرح نمیخورد -> مخفی کن
                opt.hidden = true;
                opt.disabled = true; // برای اطمینان بیشتر در برخی مرورگرها
                opt.style.display = 'none';
            } else {
                // نمایش بده
                opt.hidden = false;
                opt.disabled = false;
                opt.style.display = 'block';
            }

            // بررسی اینکه آیا طرحی که الان انتخاب شده هنوز معتبر است؟
            if (planSelect.value === planId && !opt.disabled) {
                currentPlanValid = true;
            }
        }

        // اگر طرح انتخاب شده فعلی با مودم جدید سازگار نیست، انتخاب را ریست کن
        if (planSelect.value && !currentPlanValid) {
            planSelect.value = "";
            // چون طرح ریست شد، محاسبات را مخفی کن تا کاربر دوباره طرح بزند
            costDetailsDiv.style.display = 'none';
            rulesSection.style.display = 'none';
            submitButton.disabled = true;
        }
    }

    // --- تابع اصلی محاسبه هزینه ---
    function updateCosts() {
        const selectedModemId = modemSelect.value;
        const selectedPlanId = planSelect.value;
        const sipRequested = document.querySelector('input[name="sipstatus"]:checked').value === 'true';

        if (!selectedModemId || !selectedPlanId) {
            costDetailsDiv.style.display = 'none';
            rulesSection.style.display = 'none';
            submitButton.disabled = true;
            return;
        }

        // نمایش بخش ها
        costDetailsDiv.style.display = 'block';
        rulesSection.style.display = 'block';

        const selectedModem = modemsData[selectedModemId];
        const selectedPlan = plansData[selectedPlanId];
        
        const modemPrice = parseFloat(selectedModem.price);
        const modemTax = parseFloat(selectedModem.tax) || 0;
        const modemPaymentMethod = selectedModem.payment_method;
        
        const planPrice = parseFloat(selectedPlan.price);
        const planType = selectedPlan.plan_type; 
        // **تغییر مهم**: گرفتن مدت قرارداد از روی طرح، نه مودم
        const planTimeCode = selectedPlan.plan_time; // مثلا mo6
        const N_MONTHS = planTimeMapping[planTimeCode] || 3; // پیش فرض 3

        // نمایش مدت قرارداد در جدول
        contractDurationRow.style.display = 'table-row';
        contractDurationText.innerHTML = `${selectedPlan.plan_time_display} <span style="font-size:0.85em; font-weight:normal; display:block; margin-top:5px; color:#666;">(پس از پایان این مدت، نیاز به تمدید سرویس اینترنت می‌باشد)</span>`;

        // --- محاسبات مالی ---

        // 1. محاسبه پرداختی نقدی (Upfront)
        let cashPayment = DROP_COST + (sipRequested ? SIP_COST : 0);

        // اگر مودم نقدی است
        if (modemPaymentMethod === 'cash') {
            cashPayment += modemPrice;
        }

        // 2. محاسبه اقساط مودم
        let modemInstallment = 0;
        if (modemPaymentMethod.startsWith('mi')) {
            // نکته: اینجا چون فیلتر کردیم، N_MONTHS برابر مدت قسط مودم هم هست
            // اما برای اطمینان ریاضی از تقسیم قیمت بر مدت قرارداد استفاده میکنیم
            modemInstallment = modemPrice / N_MONTHS;
        }

        // 3. هزینه طرح
        let planPaymentInFirstBill = 0;
        let planPaymentInNextBills = 0;

        if (planType === 'prepayment') {
            // پیش پرداخت: کل پول n ماه در قبض اول
            planPaymentInFirstBill = planPrice * N_MONTHS; // قیمت طرح در دیتابیس ماهانه است یا کلی؟ 
            // فرضیه کد قبلی شما: price * N_MONTHS بود. یعنی price قیمت ماهیانه است.
            // اگر price در مدل ActivePlans قیمت کل پکیج است، ضرب در N_MONTHS را بردارید.
            // طبق عرف ISP ها معمولا قیمت کل طرح را میزنند. اما من طبق کد قبلی شما (price * N) رفتم.
            planPaymentInNextBills = 0;
        } else { 
            // پس پرداخت: ماه به ماه
            planPaymentInFirstBill = planPrice;
            planPaymentInNextBills = planPrice;
        }

        // 4. اولین قبض
        let firstPayment = planPaymentInFirstBill + modemTax;
        if (modemPaymentMethod.startsWith('mi')) {
            firstPayment += modemInstallment;
        }

        // 5. قبض های بعدی
        let nextPayment = planPaymentInNextBills + modemInstallment;

        // 6. مجموع کل
        let totalContractPayment = DROP_COST + modemPrice + modemTax + (planPrice * N_MONTHS) + (sipRequested ? SIP_COST : 0);

        // --- بروزرسانی جدول ---
        modemNameCell.textContent = selectedModem.name;
        
        if (modemPaymentMethod === 'cash') {
            modemPaymentCell.textContent = selectedModem.payment_display;
        } else {
            modemPaymentCell.textContent = selectedModem.payment_display + ' (روی قبض)';
        }
        
        modemCostCell.textContent = formatCurrency(modemPrice);
        planNameCell.textContent = selectedPlan.name;

        if (planType === 'prepayment') {
            planPaymentTypeCell.textContent = 'پرداخت با اولین قبض';
            planCostCell.textContent = formatCurrency(planPrice * N_MONTHS);
        } else { 
            planPaymentTypeCell.textContent = 'پرداخت قبض ماهانه';
            planCostCell.textContent = formatCurrency(planPrice);
        }

        sipRow.style.display = sipRequested ? 'table-row' : 'none';
        sipCostCell.textContent = formatCurrency(SIP_COST);

        // جدول دوم: خلاصه
        if (modemTax > 0) {
            modemTaxRow.style.display = 'table-row';
            modemTaxCostCell.textContent = formatCurrency(modemTax);
            
            cashPaymentRow.style.display = 'table-row';
            firstPaymentRow.style.display = 'table-row';
            
            nextPaymentsRow.style.display = N_MONTHS > 1 ? 'table-row' : 'none';
            
            cashPaymentCostCell.textContent = formatCurrency(cashPayment);
            firstPaymentLabelCell.textContent = 'اولین پرداخت قبض (به همراه مالیات مودم)';
            firstPaymentCostCell.textContent = formatCurrency(firstPayment);
            
            if (N_MONTHS > 1) {
                nextPaymentsLabelCell.textContent = `${N_MONTHS - 1} پرداخت بعدی قبض`;
                nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
            }

        } else {
            // حالت بدون مالیات
            modemTaxRow.style.display = 'none';
            cashPaymentRow.style.display = 'table-row';
            cashPaymentCostCell.textContent = formatCurrency(cashPayment);

            const roundedFirst = Math.round(firstPayment);
            const roundedNext = Math.round(nextPayment);

            if (roundedFirst === roundedNext) {
                firstPaymentRow.style.display = 'none';
                nextPaymentsRow.style.display = 'table-row';
                nextPaymentsLabelCell.textContent = `${N_MONTHS} پرداخت قبض`;
                nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
            } else {
                firstPaymentRow.style.display = 'table-row';
                firstPaymentLabelCell.textContent = 'اولین پرداخت قبض';
                firstPaymentCostCell.textContent = formatCurrency(firstPayment);

                if (N_MONTHS > 1 && nextPayment > 0) {
                    nextPaymentsRow.style.display = 'table-row';
                    nextPaymentsLabelCell.textContent = `${N_MONTHS - 1} پرداخت بعدی قبض`;
                    nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
                } else {
                    nextPaymentsRow.style.display = 'none';
                }
            }
        }

        totalContractLabelCell.textContent = `مجموع هزینه ها تا ${N_MONTHS} ماه`;
        totalContractCostCell.textContent = formatCurrency(totalContractPayment);

        submitButton.disabled = !rulesCheckbox.checked;
    }

    rulesCheckbox.addEventListener('change', function () {
        if (modemSelect.value && planSelect.value) {
            submitButton.disabled = !this.checked;
        }
    });

    // ایونت لیسنر برای مودم: هم فیلتر کن هم محاسبه
    modemSelect.addEventListener('change', function() {
        filterPlansByModem();
        updateCosts(); // اگر طرح انتخاب شده پریده باشد، این تابع مخفی میکند
    });

    planSelect.addEventListener('change', updateCosts);
    sipRadios.forEach(radio => radio.addEventListener('change', updateCosts));

    // اجرا هنگام لود (اگر مقادیر قبلی در فرم مانده باشد)
    filterPlansByModem();
    updateCosts();
});