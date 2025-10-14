document.addEventListener('DOMContentLoaded', function () {
    // 1. گرفتن المان‌های لازم
    const modemSelect = document.getElementById('modem-select');
    const planSelect = document.getElementById('plan-select');
    const sipRadios = document.querySelectorAll('input[name="sipstatus"]');
    const costDetailsDiv = document.getElementById('cost-details');
    const rulesSection = document.getElementById('rules-section');
    const rulesCheckbox = document.getElementById('rules');
    const submitButton = document.getElementById('submit-button');

    // داده‌ها
    const costDataDiv = document.getElementById('cost-data');
    const DROP_COST = parseFloat(costDataDiv.dataset.dropCost);
    const SIP_COST = parseFloat(costDataDiv.dataset.sipCost);
    const modemsData = JSON.parse(document.getElementById('modems-data').textContent);
    const plansData = JSON.parse(document.getElementById('plans-data').textContent);

    // سلول‌های جدول
    const modemNameCell = document.getElementById('modem-name');
    const modemPaymentCell = document.getElementById('modem-payment-type');
    const modemCostCell = document.getElementById('modem-cost');
    const planNameCell = document.getElementById('plan-name');
    const planCostCell = document.getElementById('plan-cost');
    const sipRow = document.getElementById('sip-phone-row');
    const sipCostCell = document.getElementById('sip-cost');
    const cashSummaryCell = document.getElementById('cash-summary-cost');
    const installmentSummaryCell = document.getElementById('installment-summary-cost');
    const installmentLabelCell = document.getElementById('installment-label');

    // سلول مجموع قرارداد
    const totalContractLabelCell = document.getElementById('total-contract-label');
    const totalContractCostCell = document.getElementById('total-contract-cost');

    // فرمت پولی (انگلیسی با جداکننده 3 رقمی)
    const formatCurrency = (num) => {
        return new Intl.NumberFormat('en-US').format(Math.round(num)) + ' تومان';
    };

    // بروزرسانی هزینه‌ها
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

        // نمایش جدول و قوانین
        costDetailsDiv.style.display = 'block';
        rulesSection.style.display = 'block';

        const selectedModem = modemsData[selectedModemId];
        const selectedPlan = plansData[selectedPlanId];

        let cashPayment = DROP_COST;
        let modemInstallment = 0;
        let N_MONTHS = 0;
        let installmentLabelText = '';

        // سیپ فون
        if (sipRequested) {
            cashPayment += SIP_COST;
            sipRow.style.display = 'table-row';
        } else {
            sipRow.style.display = 'none';
        }

        // مودم
        const modemPrice = parseFloat(selectedModem.price);
        const modemPaymentMethod = selectedModem.payment_method;

        switch (modemPaymentMethod) {
            case 'mi3':
                N_MONTHS = 3;
                modemInstallment = modemPrice / N_MONTHS;
                installmentLabelText = 'پرداخت اقساط (3 ماهه)';
                break;
            case 'mi6':
                N_MONTHS = 6;
                modemInstallment = modemPrice / N_MONTHS;
                installmentLabelText = 'پرداخت اقساط (6 ماهه)';
                break;
            case 'mi12':
                N_MONTHS = 12;
                modemInstallment = modemPrice / N_MONTHS;
                installmentLabelText = 'پرداخت اقساط (12 ماهه)';
                break;
            case 'cash':
                cashPayment += modemPrice;
                modemInstallment = 0;
                installmentLabelText = 'پرداخت ماهانه (بدون قسط مودم)';
                N_MONTHS = 3;
                break;
            case 'nocashneed':
            default:
                modemInstallment = 0;
                installmentLabelText = 'پرداخت ماهانه (بدون هزینه مودم)';
                N_MONTHS = 3;
                break;
        }

        // اینترنت
        const planPrice = parseFloat(selectedPlan.price);
        const monthlyPayment = planPrice + modemInstallment;

        // مجموع قرارداد: نقدی + ماهانه*n
        const totalContractPayment = cashPayment + (planPrice * N_MONTHS + modemPrice);

        // --- آپدیت جدول‌ها ---
        modemNameCell.textContent = selectedModem.name;
        modemPaymentCell.textContent = selectedModem.payment_display;
        modemCostCell.textContent = formatCurrency(modemPrice);

        planNameCell.textContent = selectedPlan.name;
        planCostCell.textContent = formatCurrency(planPrice);
        sipCostCell.textContent = formatCurrency(SIP_COST);

        cashSummaryCell.textContent = formatCurrency(cashPayment);
        installmentLabelCell.textContent = installmentLabelText;
        installmentSummaryCell.textContent = formatCurrency(monthlyPayment);

        totalContractLabelCell.textContent = `مجموع پرداخت تا ${N_MONTHS} ماه`;
        totalContractCostCell.textContent = formatCurrency(totalContractPayment);

        // وضعیت دکمه ثبت‌نام (به چک‌باکس وابسته است)
        submitButton.disabled = !rulesCheckbox.checked;
    }

    // تغییر وضعیت چک‌باکس قوانین
    rulesCheckbox.addEventListener('change', function () {
        submitButton.disabled = !this.checked;
    });

    // لیسنر انتخاب‌ها
    modemSelect.addEventListener('change', updateCosts);
    planSelect.addEventListener('change', updateCosts);
    sipRadios.forEach(radio => radio.addEventListener('change', updateCosts));

    // اجرای اولیه
    updateCosts();
});
