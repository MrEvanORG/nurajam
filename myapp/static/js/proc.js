document.addEventListener('DOMContentLoaded', function() {
    const steps = document.querySelectorAll('.step');
    const progressBarFill = document.getElementById('progress-bar-fill');
    
    // Find the target step using the 'pactive' class
    const targetStepElement = document.querySelector('.step.pactive');
    
    // If no target step is defined, do nothing
    if (!targetStepElement) return;

    // Find the index of the target step (e.g., 0, 1, 2, ...)
    const targetStepIndex = Array.from(steps).indexOf(targetStepElement);
    
    // Calculate the required width for the progress bar fill
    const totalSteps = steps.length;
    const progressWidth = (targetStepIndex / (totalSteps - 1)) * 85 ;
    
    // A small delay to ensure the page is fully rendered before starting the animation
    setTimeout(() => {
        // Animate the progress bar fill
        progressBarFill.style.width = progressWidth + '%';

        // Sequentially add the 'active' class to steps up to the target one
        let currentStep = 0;
        const intervalTime = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--step-interval'));

        const stepActivationInterval = setInterval(() => {
            if (currentStep <= targetStepIndex) {
                // Activate the current step
                steps[currentStep].classList.add('active');

                // If this is the target step, also remove 'pactive'
                if (currentStep === targetStepIndex) {
                    steps[currentStep].classList.remove('pactive');
                }
                
                currentStep++;
            } else {
                // Stop the interval once all necessary steps are activated
                clearInterval(stepActivationInterval);
            }
        }, intervalTime);

    }, 500); // Initial delay before the entire animation starts
});