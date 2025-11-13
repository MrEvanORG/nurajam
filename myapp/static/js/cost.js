document.addEventListener('DOMContentLoaded', function () {
    // 1. گرفتن المان‌های لازم از صفحه
    const modemSelect = document.getElementById('modem-select');
    const planSelect = document.getElementById('plan-select');
    const sipRadios = document.querySelectorAll('input[name="sipstatus"]');
    const costDetailsDiv = document.getElementById('cost-details');
    const rulesSection = document.getElementById('rules-section');
    const rulesCheckbox = document.getElementById('rules');
    const submitButton = document.getElementById('submit-button');

    // 2. خواندن داده‌های اولیه از تمپلیت
    const costDataDiv = document.getElementById('cost-data');
    const DROP_COST = parseFloat(costDataDiv.dataset.dropCost);
    const SIP_COST = parseFloat(costDataDiv.dataset.sipCost);
    const modemsData = JSON.parse(document.getElementById('modems-data').textContent);
    const plansData = JSON.parse(document.getElementById('plans-data').textContent);

    // 3. گرفتن سلول‌های جدول خدمات
    const modemNameCell = document.getElementById('modem-name');
    const modemPaymentCell = document.getElementById('modem-payment-type');
    const modemCostCell = document.getElementById('modem-cost');
    const planNameCell = document.getElementById('plan-name');
    const planPaymentTypeCell = document.querySelector('#plan-name + td'); // سلول نوع پرداخت طرح
    const planCostCell = document.getElementById('plan-cost');
    const sipRow = document.getElementById('sip-phone-row');
    const sipCostCell = document.getElementById('sip-cost');
    const modemTaxRow = document.getElementById('modem-tax-row');
    const modemTaxCostCell = document.getElementById('modem-tax-cost');

    // 4. گرفتن ردیف‌ها و سلول‌های جدول خلاصه پرداخت
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

    // تابع برای فرمت کردن اعداد
    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-US').format(Math.round(num)) + ' تومان';
    };

    // تابع اصلی برای محاسبه و بروزرسانی هزینه‌ها
// تابع اصلی برای محاسبه و بروزرسانی هزینه‌ها
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

        costDetailsDiv.style.display = 'block';
        rulesSection.style.display = 'block';

        const selectedModem = modemsData[selectedModemId];
        const selectedPlan = plansData[selectedPlanId];
        const modemPrice = parseFloat(selectedModem.price);
        const modemTax = parseFloat(selectedModem.tax) || 0;
        const planPrice = parseFloat(selectedPlan.price);
        const planType = selectedPlan.plan_type; 
        const modemPaymentMethod = selectedModem.payment_method;

        // --- شروع محاسبات ---

        // 1. تعیین مدت قرارداد (N ماه)
        let N_MONTHS = 3; // پیش‌فرض
        if (modemPaymentMethod === 'mi6') N_MONTHS = 6;
        else if (modemPaymentMethod === 'mi12') N_MONTHS = 12;

        // 2. محاسبه پرداختی نقدی (Upfront)
        // شروع با هزینه دراپ و سیپ‌فون
        let cashPayment = DROP_COST + (sipRequested ? SIP_COST : 0);

        // *** تغییر جدید: اگر مودم نقدی است، به پرداخت نقدی اضافه شود ***
        if (modemPaymentMethod === 'cash') {
            cashPayment += modemPrice;
        }

        // 3. محاسبه اقساط مودم
        let modemInstallment = 0;
        if (modemPaymentMethod.startsWith('mi')) {
            modemInstallment = modemPrice / N_MONTHS;
        }

        // 4. محاسبه هزینه طرح (پیش‌پرداخت یا پس‌پرداخت)
        let planPaymentInFirstBill = 0;
        let planPaymentInNextBills = 0;

        if (planType === 'prepayment') {
            planPaymentInFirstBill = planPrice * N_MONTHS;
            planPaymentInNextBills = 0;
        } else { // postpayment
            planPaymentInFirstBill = planPrice;
            planPaymentInNextBills = planPrice;
        }

        // 5. محاسبه اولین قبض
        // شامل: هزینه طرح + مالیات مودم (اگر باشد) + قسط مودم (اگر قسطی باشد)
        let firstPayment = planPaymentInFirstBill + modemTax;
        
        if (modemPaymentMethod.startsWith('mi')) {
            firstPayment += modemInstallment;
        }
        // نکته: دیگر شرطی برای اضافه کردن modemPrice در حالت cash اینجا نداریم (چون رفت در cashPayment)

        // 6. محاسبه قبض‌های بعدی
        let nextPayment = planPaymentInNextBills + modemInstallment;

        // 7. مجموع کل قرارداد
        let totalContractPayment = DROP_COST + modemPrice + modemTax + (planPrice * N_MONTHS) + (sipRequested ? SIP_COST : 0);


        // --- بروزرسانی مقادیر در جدول‌ها ---

        // جدول اول: لیست خدمات
        modemNameCell.textContent = selectedModem.name;
        
        // تغییر متن نوع پرداخت مودم در جدول
        if (modemPaymentMethod === 'cash') {
            modemPaymentCell.textContent = selectedModem.payment_display; // مثلا "نقدی"
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


        // جدول دوم: خلاصه پرداخت
        if (modemTax > 0) {
            // **حالت با مالیات**
            modemTaxRow.style.display = 'table-row';
            modemTaxCostCell.textContent = formatCurrency(modemTax);
            
            cashPaymentRow.style.display = 'table-row';
            firstPaymentRow.style.display = 'table-row';
            // اگر فقط 1 ماه باشد، پرداخت بعدی نداریم
            nextPaymentsRow.style.display = N_MONTHS > 1 ? 'table-row' : 'none';
            
            cashPaymentCostCell.textContent = formatCurrency(cashPayment);
            firstPaymentLabelCell.textContent = 'اولین پرداخت قبض (به همراه مالیات بر ارزش افزوده مودم)';
            firstPaymentCostCell.textContent = formatCurrency(firstPayment);
            
            if (N_MONTHS > 1) {
                nextPaymentsLabelCell.textContent = `${N_MONTHS - 1} پرداخت بعدی قبض`;
                nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
            }

        } else {
            // **حالت بدون مالیات**
            modemTaxRow.style.display = 'none';
            cashPaymentRow.style.display = 'table-row';
            cashPaymentCostCell.textContent = formatCurrency(cashPayment);

            // بررسی تفاوت اولین قبض و قبض‌های بعدی
            // (مثلاً در حالت طرح پیش‌پرداخت، اولین قبض خیلی بیشتر از بعدی‌هاست)
            const roundedFirst = Math.round(firstPayment);
            const roundedNext = Math.round(nextPayment);

            if (roundedFirst === roundedNext) {
                // هزینه‌ها یکسان است (طرح پس‌پرداخت + مودم قسطی یا بدون مودم)
                firstPaymentRow.style.display = 'none';
                nextPaymentsRow.style.display = 'table-row';
                nextPaymentsLabelCell.textContent = `${N_MONTHS} پرداخت قبض`;
                nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
            } else {
                // هزینه‌ها متفاوت است (طرح پیش‌پرداخت)
                firstPaymentRow.style.display = 'table-row';
                firstPaymentLabelCell.textContent = 'اولین پرداخت قبض';
                firstPaymentCostCell.textContent = formatCurrency(firstPayment);

                if (N_MONTHS > 1) {
                    // فقط اگر هزینه‌ای برای ماه‌های بعد باقی مانده باشد نشان بده
                    // در حالت "مودم نقدی" + "طرح پیش‌پرداخت"، nextPayment صفر می‌شود.
                    if (nextPayment > 0) {
                        nextPaymentsRow.style.display = 'table-row';
                        nextPaymentsLabelCell.textContent = `${N_MONTHS - 1} پرداخت بعدی قبض`;
                        nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
                    } else {
                        // اگر هزینه بعدی 0 است (مثلا پیش‌پرداخت کامل و مودم نقدی) مخفی کن
                        nextPaymentsRow.style.display = 'none';
                    }
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

    modemSelect.addEventListener('change', updateCosts);
    planSelect.addEventListener('change', updateCosts);
    sipRadios.forEach(radio => radio.addEventListener('change', updateCosts));

    // اجرای تابع در اولین بارگذاری صفحه (برای زمانی که مقادیر اولیه از سشن آمده‌اند)
    updateCosts();
});