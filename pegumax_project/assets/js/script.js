document.addEventListener('DOMContentLoaded', () => {
    // 1. Dynamic Slogan Typewriter Effect
    const slogans = [
        "Unlocking the Next Dimension of Reality.",
        "Crafting Tomorrow's Solutions, Today.",
        "Where Vision Meets Unrivaled Innovation.",
        "Redefining the Boundaries of Possibility."
    ];
    let sloganIndex = 0;
    let charIndex = 0;
    const animatedSloganElement = document.getElementById('animated-slogan');
    let typingSpeed = 70; // milliseconds per character - slightly faster for smoother feel
    let deletingSpeed = 35; // milliseconds per character - slightly faster
    let delayBetweenSlogans = 2000; // milliseconds - slightly shorter pause

    function typeSlogan() {
        if (charIndex < slogans[sloganIndex].length) {
            animatedSloganElement.textContent += slogans[sloganIndex].charAt(charIndex);
            charIndex++;
            setTimeout(typeSlogan, typingSpeed);
        } else {
            setTimeout(deleteSlogan, delayBetweenSlogans);
        }
    }

    function deleteSlogan() {
        if (charIndex > 0) {
            animatedSloganElement.textContent = slogans[sloganIndex].substring(0, charIndex - 1);
            charIndex--;
            setTimeout(deleteSlogan, deletingSpeed);
        } else {
            sloganIndex = (sloganIndex + 1) % slogans.length;
            setTimeout(typeSlogan, typingSpeed + 50); // Small delay before typing new slogan
        }
    }

    // Start the typewriter effect after the initial fade-in of other elements
    // Increased delay to allow hero section to fully load before slogan animation starts
    setTimeout(() => {
        typeSlogan();
    }, 2800); // Give the hero section a moment to load and fade in


    // 2. Scroll-Triggered Fade-In Effect for Sections
    // Explicitly add .js-scroll class to sections here to ensure they are targeted
    // Ensure these IDs exist or update them according to your HTML structure
    const sectionsToAnimate = ['#overview', '#mission', '#future', '#site-heroes', '#about-content', '#software-center-main', '#community-main', '#store-main']; // Added more page sections
    sectionsToAnimate.forEach(selector => {
        document.querySelector(selector)?.classList.add('js-scroll');
    });

    const scrollElements = document.querySelectorAll('.js-scroll');
    console.log("Scroll elements found for animation:", scrollElements.length); // Debugging line

    const elementInView = (el, dividend = 1) => {
        const elementTop = el.getBoundingClientRect().top;
        const elementHeight = el.getBoundingClientRect().height;
        const viewportHeight = (window.innerHeight || document.documentElement.clientHeight);

        // Element is considered in view if its top is above the bottom of the viewport
        // and its bottom is below the top of the viewport.
        // The dividend makes it appear earlier (e.g., when 1/2 of it is visible)
        return (elementTop <= viewportHeight - (elementHeight / dividend) && elementTop + elementHeight > 0);
    };

    const displayScrollElement = (element) => {
        element.classList.add('scrolled');
        if (element.id) {
            console.log("Element scrolled into view:", element.id); // Debugging line
        }    
    };

    const handleScrollAnimation = () => {
        updatedScrollElements.forEach((el) => { // Use updatedScrollElements
            if (elementInView(el, 1.5)) { // Adjusted dividend to 1.5 for slightly earlier trigger
                displayScrollElement(el);
            }
            // Optional: If you want elements to fade out when scrolled back up:
            // else if (el.classList.contains('scrolled')) {
            //     el.classList.remove('scrolled');
            // }
        });
    };

    // Re-select scrollElements after adding the classes to ensure they are included
    // This is important because querySelectorAll only grabs elements present at call time.
    const updatedScrollElements = document.querySelectorAll('.js-scroll');
    console.log("Updated scroll elements after class add:", updatedScrollElements.length);


    window.addEventListener('scroll', handleScrollAnimation);

    // Initial check in case elements are already in view on load (e.g., on larger screens)
    handleScrollAnimation();

    // 3. Update copyright year dynamically
    const currentYearElement = document.getElementById('current-year');
    if (currentYearElement) {
        currentYearElement.textContent = new Date().getFullYear();
    }

    // 4. Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                // Handle cases where href might be a full URL + hash
                const targetElement = document.querySelector(targetId.startsWith('#') ? targetId : '#' + targetId.split('#')[1]);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
    // Modal Control Functions
    // These need to be globally accessible if called by inline onclick attributes

    function openSubmitIdeaForm() {
        const modal = document.getElementById('submit-idea-popup');
        if (modal) {
            modal.style.display = 'flex'; // Use flex to enable centering
        } else {
            console.error('Submit Idea modal (submit-idea-popup) not found!');
        }
    }
    window.openSubmitIdeaForm = openSubmitIdeaForm; // Make globally accessible

    function closeSubmitIdeaForm() {
        const modal = document.getElementById('submit-idea-popup');
        if (modal) {
            modal.style.display = 'none';
        } else {
            console.error('Submit Idea modal (submit-idea-popup) not found!');
        }
    }
    window.closeSubmitIdeaForm = closeSubmitIdeaForm; // Make globally accessible

    // For the initial subscription popup ($100/month offer)
    // Note: The close button for this one in your HTML directly sets display to none.
    // The "Let Us Know!" button should open the *next* modal.

    function openSubscriptionInterestForm() {
        const initialPopup = document.getElementById('subscription-popup');
        const interestPopup = document.getElementById('subscription-interest-popup');

        if (initialPopup) {
            initialPopup.style.display = 'none'; // Hide the first popup
        }
        if (interestPopup) {
            interestPopup.style.display = 'flex'; // Show the interest form popup
        } else {
            console.error('Subscription Interest modal (subscription-interest-popup) not found!');
        }
    }
    window.openSubscriptionInterestForm = openSubscriptionInterestForm; // Make globally accessible

    function closeSubscriptionInterestForm() {
        const modal = document.getElementById('subscription-interest-popup');
        if (modal) {
            modal.style.display = 'none';
        } else {
            console.error('Subscription Interest modal (subscription-interest-popup) not found!');
        }
    }
    window.closeSubscriptionInterestForm = closeSubscriptionInterestForm; // Make globally accessible

    // 5. Software Center Poll (Basic visual selection)
    const pollOptions = document.querySelectorAll('.poll-option input[type="radio"]');
    const pollForm = document.getElementById('payment-poll-form');

    if (pollForm) {
        pollOptions.forEach(option => {
            option.addEventListener('change', () => {
                // You could add logic here to "submit" the poll,
                // for now, it just allows selection.
                console.log('Poll selection:', option.value);
                // Potentially show a thank you message
                const thankYouMessage = document.getElementById('poll-thank-you');
                if(thankYouMessage) thankYouMessage.style.display = 'block';
            });
        });
    }
     // 6. Software Center Tab and Popup Logic
    if (document.getElementById('software-center-main')) {
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
                tabcontent[i].classList.remove("active");
            }
            tablinks = document.getElementsByClassName("tab-link");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].classList.remove("active");
            }
            document.getElementById(tabName).style.display = "block";
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");

            if (tabName === 'all') {
                populateAllTab();
            }
        }

        function populateAllTab() {
            const allTabGrid = document.querySelector('#all .software-grid');
            allTabGrid.innerHTML = ''; // Clear previous items
            const items = document.querySelectorAll('.software-card[data-category]');
            items.forEach(item => {
                allTabGrid.appendChild(item.cloneNode(true));
            });
        }

        populateAllTab(); // Initialize the 'All' tab content on page load
        document.querySelector('.tab-link[onclick*="\'all\'"]')?.classList.add('active'); // Activate the first tab link

        // Popup logic
        const userName = "Valued User"; // Placeholder
        const popupUserNameElement = document.getElementById('popup-user-name');
        if (popupUserNameElement) {
            popupUserNameElement.textContent = userName;
        }

        setTimeout(() => {
            const popup = document.getElementById('subscription-popup');
            if (popup) {
                // For testing, you can clear this from browser dev tools (Application > Local Storage)
                // or temporarily comment out the check:
                // if (!localStorage.getItem('subscriptionPopupSeen')) {
                    popup.style.display = 'flex';
                //     localStorage.setItem('subscriptionPopupSeen', 'true');
                // }
            }
        }, 1500);

        // Make tab functions globally accessible if they are called via inline onclick
        window.openTab = openTab;
    }
});