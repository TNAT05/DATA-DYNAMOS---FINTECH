// SecurePay AI Voice Assistant
// Uses Web Speech API with no external dependencies

document.addEventListener('DOMContentLoaded', () => {
    const fab = document.getElementById('voice-assistant-btn');

    if (!('webkitSpeechRecognition' in window)) {
        console.warn('Web Speech API not supported in this browser.');
        fab.style.display = 'none';
        return;
    }

    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    let isListening = false;

    fab.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    recognition.onstart = () => {
        isListening = true;
        fab.classList.add('listening');
        speak("I'm listening...");
    };

    recognition.onend = () => {
        isListening = false;
        fab.classList.remove('listening');
    };

    function showToast(message) {
        // Remove existing toasts
        const existing = document.querySelectorAll('.voice-toast');
        existing.forEach(e => e.remove());

        // Create a temporary toast for feedback
        const toast = document.createElement('div');
        toast.className = 'voice-toast position-fixed bottom-0 start-50 translate-middle-x mb-5 p-3 rounded-pill text-white bg-dark bg-opacity-75 shadow-lg fade-in';
        toast.style.zIndex = '1050';
        toast.style.backdropFilter = 'blur(10px)';
        toast.innerHTML = `<i class="bi bi-mic-fill me-2"></i> ${message}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    recognition.onresult = (event) => {
        const originalTranscript = event.results[0][0].transcript;
        const lowerTranscript = originalTranscript.toLowerCase();
        console.log('Voice Command:', originalTranscript);
        showToast(`Heard: "${originalTranscript}"`);
        handleCommand(lowerTranscript, originalTranscript);
    };

    function speak(text) {
        // Cancel any current speech to avoid overlapping
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    }

    function handleCommand(lowerCommand, originalCommand) {
        const cleanCommand = lowerCommand.trim();

        // --- Navigation Commands ---
        if (cleanCommand.includes('dashboard') || cleanCommand.includes('home')) {
            speak("Navigating to dashboard.");
            window.location.href = '/';
        }
        else if (cleanCommand.includes('create') || cleanCommand.includes('new payment')) {
            speak("Opening payment creation form.");
            window.location.href = '/create/';
        }
        else if (cleanCommand.includes('history') || cleanCommand.includes('my payments')) {
            speak("Showing your payment history.");
            window.location.href = '/my-payments/';
        }
        else if (cleanCommand.includes('approval') || cleanCommand.includes('pending')) {
            speak("Checking pending approvals.");
            window.location.href = '/pending/';
        }
        else if (cleanCommand.includes('log out') || cleanCommand.includes('sign out')) {
            speak("Logging you out securely.");
            const logoutForms = document.querySelectorAll('form[action="/accounts/logout/"]');
            if (logoutForms.length > 0) logoutForms[0].submit();
        }

        // --- Interaction Commands ---
        else if (cleanCommand.includes('scroll down')) {
            window.scrollBy({ top: 500, behavior: 'smooth' });
        }
        else if (cleanCommand.includes('scroll up')) {
            window.scrollBy({ top: -500, behavior: 'smooth' });
        }

        // --- Smart Form Filling (Hyper Permissive Mode) ---
        else if (cleanCommand.includes('name') || cleanCommand.includes('user') || cleanCommand.includes('login as')) {
            // Aggressive extraction: take the last word if "is" exists, or just the word after "user"
            let username = "";
            const words = cleanCommand.split(' ');
            username = words[words.length - 1]; // Default to last word

            if (cleanCommand.includes('name is')) username = cleanCommand.split('name is')[1];
            else if (cleanCommand.includes('user is')) username = cleanCommand.split('user is')[1];

            username = username.trim().replace(/[.]/g, ''); // Remove trailing periods

            const input = document.querySelector('input[name="username"]');
            if (input) {
                input.value = username;
                speak(`Username set to ${username}`);
                input.focus();
            } else {
                speak("I can't find a username field.");
            }
        }
        else if (cleanCommand.includes('pass') || cleanCommand.includes('code') || cleanCommand.includes('word')) {
            let password = "";
            const words = cleanCommand.split(' ');
            password = words[words.length - 1]; // Default to last word

            if (cleanCommand.includes('password is')) password = cleanCommand.split('password is')[1];

            password = password.trim().replace(/\s/g, '').replace(/[.]/g, '');

            const input = document.querySelector('input[name="password"]');
            if (input) {
                input.value = password;
                speak("Password entered.");
            } else {
                speak("I can't find a password field.");
            }
        }
        else if (cleanCommand.includes('login') || cleanCommand.includes('sign in') || cleanCommand.includes('submit') || cleanCommand.includes('enter')) {
            const form = document.querySelector('form');
            if (form) {
                speak("Submitting now.");
                form.submit();
            }
        }
        // --- Payment Creation Form (Initiator) ---
        else if (cleanCommand.includes('beneficiary') || cleanCommand.includes('pay to')) {
            let name = "";
            if (cleanCommand.includes('beneficiary is')) name = cleanCommand.split('beneficiary is')[1];
            else if (cleanCommand.includes('pay to')) name = cleanCommand.split('pay to')[1];

            name = name.trim().replace(/[.]/g, '');

            const input = document.querySelector('input[name="beneficiary_name"]');
            if (input) {
                input.value = name;
                speak(`Beneficiary set to ${name}`);
            }
        }
        else if (cleanCommand.includes('amount') || cleanCommand.includes('value is')) {
            let amount = cleanCommand.replace(/[^0-9.]/g, ''); // Extract numbers

            const input = document.querySelector('input[name="amount"]');
            if (input) {
                input.value = amount;
                speak(`Amount set to ${amount}`);
            }
        }
        else if (cleanCommand.includes('description') || cleanCommand.includes('for')) {
            let desc = "";
            if (cleanCommand.includes('description is')) desc = cleanCommand.split('description is')[1];
            else if (cleanCommand.includes('for')) desc = cleanCommand.split('for')[1];

            desc = desc.trim().replace(/[.]/g, '');

            const input = document.querySelector('textarea[name="description"]');
            if (input) {
                input.value = desc;
                speak(`Description set to ${desc}`);
            }
        }

        // --- Registration Form Commands ---
        else if (cleanCommand.includes('email is') || cleanCommand.includes('mail is')) {
            const email = cleanCommand.split('is')[1].trim().replace(/\s/g, '').replace('at', '@').replace('dot', '.');
            const input = document.querySelector('input[name="email"]');
            if (input) {
                input.value = email;
                speak(`Email set to ${email}`);
            }
        }
        else if (cleanCommand.includes('role is') || cleanCommand.includes('select role')) {
            const roleSelect = document.querySelector('select[name="role"]');
            if (roleSelect) {
                if (cleanCommand.includes('initiator')) {
                    roleSelect.value = 'INITIATOR';
                    speak("Selected Initiator role.");
                } else if (cleanCommand.includes('approver')) {
                    roleSelect.value = 'APPROVER';
                    speak("Selected Approver role.");
                } else if (cleanCommand.includes('admin')) {
                    roleSelect.value = 'ADMIN';
                    speak("Selected Admin role.");
                }
            } else {
                speak("I can't find a role selection here.");
            }
        }

        // --- Action Commands (Approve/Reject/Execute) ---
        else if (cleanCommand.includes('approve') || cleanCommand.includes('accept')) {
            const btn = document.querySelector('a[href*="/approve/"]');
            if (btn) {
                speak("Approving payment.");
                btn.click();
            } else {
                speak("I don't see an approve button here.");
            }
        }
        else if (cleanCommand.includes('reject') || cleanCommand.includes('decline')) {
            const btn = document.querySelector('a[href*="/reject/"]');
            if (btn) {
                speak("Rejecting payment.");
                btn.click();
            } else {
                speak("I don't see a reject button here.");
            }
        }
        else if (cleanCommand.includes('execute') || cleanCommand.includes('transfer')) {
            const btn = document.querySelector('a[href*="/execute/"]');
            if (btn) {
                speak("Executing payment transfer.");
                btn.click();
            } else {
                speak("I cannot execute this payment right now.");
            }
        }

        // --- Help Command ---
        else if (cleanCommand.includes('help') || cleanCommand.includes('what can i do')) {
            speak("You can say things like: Go to Dashboard, Create Payment, Approve this, or My name is Sandeep.");
            showToast("Try: 'Go Home', 'Approve', 'My user is...'");
        }

        else {
            speak("I heard " + cleanCommand + ". Say 'Help' for commands.");
        }
    }
});
