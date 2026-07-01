const API_URL = window.location.origin.includes('localhost:3000') ? '/api' : 'http://localhost:3000/api';

// --- Page Navigation & UI Elements ---
const mainContent = document.getElementById('main-content');
const authContent = document.getElementById('auth-content');
const loginPage = document.getElementById('login-page');
const registerPage = document.getElementById('register-page');
const footer = document.getElementById('footer');
const allPageSections = document.querySelectorAll('.page-section');
const mainMenuContainer = document.getElementById('main-menu-container');
const profileMenuContainer = document.getElementById('profile-menu-container');

const termsModal = document.getElementById('terms-modal');
const closeTermsModal = document.getElementById('close-terms-modal');
const openTermsFromMenu = document.getElementById('open-terms-from-menu');
const openTermsButtons = document.querySelectorAll('.open-terms-button');

const mainMenuButton = document.getElementById('main-menu-button');
const mainMenu = document.getElementById('main-menu');
const profileMenuButton = document.getElementById('profile-menu-button');
const profileMenu = document.getElementById('profile-menu');
const trafficMapToggle = document.getElementById('traffic-map-toggle');
const trafficMapSubmenu = document.getElementById('traffic-map-submenu');
const trafficArrow = document.getElementById('traffic-arrow');
const loggedOutView = document.getElementById('logged-out-view');
const loggedInView = document.getElementById('logged-in-view');
const userEmailDisplay = document.getElementById('user-email-display');
const trafficMapDivider = document.getElementById('traffic-map-divider');
const dashboardNavLink = document.getElementById('dashboard-nav-link');

const profileLoginButton = document.getElementById('profile-login-button');
const profileRegisterButton = document.getElementById('profile-register-button');
const profileLogoutButton = document.getElementById('profile-logout-button');
const navLinks = document.querySelectorAll('.nav-link');
const homeLinks = document.querySelectorAll('.home-link');
const switchToRegister = document.getElementById('switch-to-register');
const switchToLogin = document.getElementById('switch-to-login');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const loginEmailInput = document.getElementById('login-email');
const registerEmailInput = document.getElementById('register-email');
const googleSignInButton = document.getElementById('google-signin-button');

const loginSubmitButton = document.getElementById('login-submit-button');
const registerSubmitButton = document.getElementById('register-submit-button');
const loginTermsAgree = document.getElementById('login-terms-agree');
const registerTermsAgree = document.getElementById('register-terms-agree');

let isLoggedIn = false;
let postLoginRedirect = null;

// --- Page visibility functions ---
function showMainContent(pageId) {
    authContent.classList.add('hidden');
    mainContent.classList.remove('hidden');
    footer.classList.remove('hidden');
    mainMenuContainer.classList.remove('hidden');
    profileMenuContainer.classList.remove('hidden');

    allPageSections.forEach(section => {
        let isHomePageSection = section.id.startsWith('home-');
        if (pageId === 'home') {
            section.classList.toggle('hidden', !isHomePageSection);
        } else {
            section.classList.toggle('hidden', section.id !== pageId);
        }
    });
    window.scrollTo(0, 0);
}

function showAuthPage(pageId) {
    mainContent.classList.add('hidden');
    footer.classList.add('hidden');
    authContent.classList.remove('hidden');
    mainMenuContainer.classList.add('hidden');
    profileMenuContainer.classList.add('hidden');

    if (pageId === 'login') {
        loginPage.classList.remove('hidden');
        registerPage.classList.add('hidden');
    } else {
        loginPage.classList.add('hidden');
        registerPage.classList.remove('hidden');
    }
     window.scrollTo(0, 0);
}

function updateUIForLoginState(email = 'user@example.com') {
    if (isLoggedIn) {
        loggedOutView.classList.add('hidden');
        loggedInView.classList.remove('hidden');
        userEmailDisplay.textContent = email;
    } else {
        loggedOutView.classList.remove('hidden');
        loggedInView.classList.add('hidden');
    }
}

// --- Event Listeners ---
const openTerms = () => termsModal.classList.remove('hidden');
openTermsFromMenu.addEventListener('click', (e) => {
    e.preventDefault();
    openTerms();
    mainMenu.classList.add('hidden');
});
openTermsButtons.forEach(btn => btn.addEventListener('click', openTerms));
closeTermsModal.addEventListener('click', () => termsModal.classList.add('hidden'));

mainMenuButton.addEventListener('click', (e) => { 
    e.stopPropagation(); 
    mainMenu.classList.toggle('hidden');
    profileMenu.classList.add('hidden');
});

profileMenuButton.addEventListener('click', (e) => {
    e.stopPropagation();
    profileMenu.classList.toggle('hidden');
    mainMenu.classList.add('hidden');
});

trafficMapToggle.addEventListener('click', () => {
    if (isLoggedIn) {
         if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    trafficMapSubmenu.classList.toggle('hidden');
                    trafficArrow.classList.toggle('rotate-180');
                },
                (error) => {
                    alert("Location access denied. Please enable it in your browser settings.");
                    mainMenu.classList.add('hidden');
                }
            );
        } else {
            alert("Geolocation is not supported by your browser.");
        }
    } else {
        postLoginRedirect = 'home';
        alert('Please log in to view traffic maps.');
        showAuthPage('login');
        mainMenu.classList.add('hidden');
    }
});

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        const targetId = link.getAttribute('href').substring(1);
         if (targetId === 'dashboard' && !isLoggedIn) {
            e.preventDefault();
            postLoginRedirect = 'dashboard';
            alert('Please log in to view the dashboard.');
            showAuthPage('login');
            mainMenu.classList.add('hidden');
            return;
        }
        if (targetId === 'dashboard' && isLoggedIn) {
            e.preventDefault();
            // Redirect to traffic management dashboard
            window.location.href = 'index.html';
            return;
        }
        e.preventDefault();
        showMainContent(targetId);
        mainMenu.classList.add('hidden');
    });
});

homeLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        showMainContent('home');
    });
});

profileLoginButton.addEventListener('click', () => {
    showAuthPage('login');
    profileMenu.classList.add('hidden');
});

profileRegisterButton.addEventListener('click', () => {
    showAuthPage('register');
    profileMenu.classList.add('hidden');
});

switchToLogin.addEventListener('click', () => showAuthPage('login'));
switchToRegister.addEventListener('click', () => showAuthPage('register'));

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (loginForm.checkValidity()) {
        const email = loginEmailInput.value;
        const password = document.getElementById('login-password').value;
        
        loginSubmitButton.disabled = true;
        const originalText = loginSubmitButton.textContent;
        loginSubmitButton.textContent = 'Logging in...';
        
        try {
            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }
            
            isLoggedIn = true;
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            updateUIForLoginState(email);
            showMainContent(postLoginRedirect || 'home');
            postLoginRedirect = null;
        } catch (err) {
            console.error('Login error:', err);
            alert(err.message || 'Failed to login. Please try again.');
        } finally {
            loginSubmitButton.disabled = false;
            loginSubmitButton.textContent = originalText;
        }
    }
});

googleSignInButton.addEventListener('click', () => {
    // Keep standard mock for google sign in
    isLoggedIn = true;
    updateUIForLoginState('google.user@example.com');
    showMainContent(postLoginRedirect || 'home');
    postLoginRedirect = null;
});

profileLogoutButton.addEventListener('click', () => {
    isLoggedIn = false;
    postLoginRedirect = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    updateUIForLoginState();
    profileMenu.classList.add('hidden');
    showMainContent('home');
});

// --- Form Validation ---
const passwordInput = document.getElementById('register-password');
const confirmPasswordInput = document.getElementById('register-confirm-password');
const passwordLengthError = document.getElementById('password-length-error');
const passwordSpecialCharError = document.getElementById('password-special-char-error');
const passwordMatchError = document.getElementById('password-match-error');

function validatePasswords() {
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    const specialCharRegex = /[!@#$%^&*(),.?":{}|<>]/;
    let isValid = true;
    if (password.length > 0 && password.length < 8) { passwordLengthError.classList.remove('hidden'); isValid = false; } else { passwordLengthError.classList.add('hidden'); }
    if (password.length > 0 && !specialCharRegex.test(password)) { passwordSpecialCharError.classList.remove('hidden'); isValid = false; } else { passwordSpecialCharError.classList.add('hidden'); }
    if (confirmPassword.length > 0 && password !== confirmPassword) { passwordMatchError.classList.remove('hidden'); isValid = false; } else { passwordMatchError.classList.add('hidden'); }
    return isValid;
}

passwordInput.addEventListener('keyup', validatePasswords);
confirmPasswordInput.addEventListener('keyup', validatePasswords);
registerForm.addEventListener('submit', async (e) => { 
    e.preventDefault();
    if (registerForm.checkValidity() && validatePasswords()) {
        const name = document.getElementById('register-name').value;
        const email = registerEmailInput.value;
        const password = passwordInput.value;
        
        registerSubmitButton.disabled = true;
        const originalText = registerSubmitButton.textContent;
        registerSubmitButton.textContent = 'Creating Account...';
        
        try {
            const response = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Registration failed');
            }
            
            alert('Registration successful! Please log in.');
            showAuthPage('login');
        } catch (err) {
            console.error('Registration error:', err);
            alert(err.message || 'Failed to register. Please try again.');
        } finally {
            registerSubmitButton.disabled = false;
            registerSubmitButton.textContent = originalText;
        }
    }
});

// --- Terms and Conditions Checkbox Logic ---
loginTermsAgree.addEventListener('input', () => {
    loginSubmitButton.disabled = !loginTermsAgree.checked;
});

registerTermsAgree.addEventListener('input', () => {
    registerSubmitButton.disabled = !registerTermsAgree.checked;
});

window.addEventListener('click', (event) => {
    if (mainMenu && !mainMenu.classList.contains('hidden') && !mainMenu.contains(event.target) && !mainMenuButton.contains(event.target)) {
        mainMenu.classList.add('hidden');
    }
    if (profileMenu && !profileMenu.classList.contains('hidden') && !profileMenu.contains(event.target) && !profileMenuButton.contains(event.target)) {
        profileMenu.classList.add('hidden');
    }
    if (event.target === termsModal) {
        termsModal.classList.add('hidden');
    }
});

window.addEventListener('scroll', () => {
    const header = document.getElementById('header');
    header.classList.toggle('py-2', window.scrollY > 50);
    header.classList.toggle('py-4', window.scrollY <= 50);
});

// --- Dashboard Access Button ---
const accessDashboardBtn = document.getElementById('access-dashboard-btn');
if (accessDashboardBtn) {
    accessDashboardBtn.addEventListener('click', () => {
        if (isLoggedIn) {
            window.location.href = 'index.html';
        } else {
            postLoginRedirect = 'dashboard';
            alert('Please log in to access the dashboard.');
            showAuthPage('login');
        }
    });
}

// --- Initial Page Load ---
showMainContent('home');

const savedToken = localStorage.getItem('token');
const savedUser = localStorage.getItem('user');
if (savedToken && savedUser) {
    try {
        const user = JSON.parse(savedUser);
        isLoggedIn = true;
        updateUIForLoginState(user.email);
    } catch (e) {
        console.error('Error restoring session:', e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        updateUIForLoginState();
    }
} else {
    updateUIForLoginState();
}
