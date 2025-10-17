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
    const planCostCell = document.getElementById('plan-cost');
    const sipRow = document.getElementById('sip-phone-row');
    const sipCostCell = document.getElementById('sip-cost');
    // ردیف جدید مالیات در جدول خدمات
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
        const modemPaymentMethod = selectedModem.payment_method;

        // --- شروع محاسبات ---

        // 1. تعیین مدت قرارداد (N ماه)
        let N_MONTHS = 3; // پیش‌فرض
        if (modemPaymentMethod === 'mi6') N_MONTHS = 6;
        else if (modemPaymentMethod === 'mi12') N_MONTHS = 12;

        // 2. محاسبه مقادیر پایه
        let cashPayment = DROP_COST + (sipRequested ? SIP_COST : 0);
        
        let modemInstallment = 0;
        if (modemPaymentMethod.startsWith('mi')) {
            modemInstallment = modemPrice / N_MONTHS;
        }

        let firstPayment = planPrice + modemTax;
        if (modemPaymentMethod.startsWith('mi')) {
            firstPayment += modemInstallment;
        } else if (modemPaymentMethod === 'cash') {
            firstPayment += modemPrice;
        }

        let nextPayment = planPrice + modemInstallment;

        let totalContractPayment = DROP_COST + modemPrice + modemTax + (planPrice * N_MONTHS) + (sipRequested ? SIP_COST : 0);

        // --- بروزرسانی مقادیر در جدول‌ها ---

        // جدول اول: لیست خدمات
        modemNameCell.textContent = selectedModem.name;
        modemPaymentCell.textContent = selectedModem.payment_display+' (روی قبض)';
        modemCostCell.textContent = formatCurrency(modemPrice);
        planNameCell.textContent = selectedPlan.name;
        planCostCell.textContent = formatCurrency(planPrice);
        sipRow.style.display = sipRequested ? 'table-row' : 'none';
        sipCostCell.textContent = formatCurrency(SIP_COST);

        // جدول دوم: خلاصه پرداخت (منطق شرطی جدید)
        if (modemTax > 0) {
            // **حالت با مالیات**
            // نمایش مالیات در جدول خدمات
            modemTaxRow.style.display = 'table-row';
            modemTaxCostCell.textContent = formatCurrency(modemTax);
            
            // نمایش تمام ردیف‌های خلاصه پرداخت
            cashPaymentRow.style.display = 'table-row';
            firstPaymentRow.style.display = 'table-row';
            nextPaymentsRow.style.display = N_MONTHS > 1 ? 'table-row' : 'none';
            
            // تنظیم مقادیر و لیبل‌ها
            cashPaymentCostCell.textContent = formatCurrency(cashPayment);
            firstPaymentLabelCell.textContent = 'اولین پرداخت قبض (به همراه مالیات بر ارزش افزوده مودم)';
            firstPaymentCostCell.textContent = formatCurrency(firstPayment);
            if (N_MONTHS > 1) {
                nextPaymentsLabelCell.textContent = `${N_MONTHS - 1} پرداخت بعدی قبض`;
                nextPaymentsCostCell.textContent = formatCurrency(nextPayment);
            }
        } else {
            // **حالت بدون مالیات**
            // مخفی کردن ردیف مالیات در جدول خدمات
            modemTaxRow.style.display = 'none';

            // مخفی کردن ردیف "اولین پرداخت" و ادغام آن
            firstPaymentRow.style.display = 'none';
            cashPaymentRow.style.display = 'table-row';
            nextPaymentsRow.style.display = 'table-row';

            // تنظیم مقادیر و لیبل‌ها
            cashPaymentCostCell.textContent = formatCurrency(cashPayment);
            nextPaymentsLabelCell.textContent = `${N_MONTHS} پرداخت بعدی`;
            nextPaymentsCostCell.textContent = formatCurrency(nextPayment); // در این حالت firstPayment و nextPayment برابرند
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

    updateCosts();
});