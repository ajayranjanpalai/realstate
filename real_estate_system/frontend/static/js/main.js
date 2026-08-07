// API Base URL
const API_BASE = '/api';

// Utility Functions
class RealEstateApp {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
    }

    async checkAuth() {
        try {
            const response = await this.apiCall('/user');
            if (response.success && response.user) {
                this.currentUser = response.user;
                this.updateUIForAuth();
            } else {
                this.redirectToLogin();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.redirectToLogin();
        }
    }

    async apiCall(endpoint, options = {}) {
        const url = API_BASE + endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Navigation toggle for mobile
        const navToggle = document.getElementById('navToggle');
        if (navToggle) {
            navToggle.addEventListener('click', () => this.toggleMobileMenu());
        }
    }

    updateUIForAuth() {
        // Update user-specific UI elements
        const userElements = document.querySelectorAll('[data-user]');
        userElements.forEach(element => {
            const field = element.getAttribute('data-user');
            if (this.currentUser && this.currentUser[field]) {
                element.textContent = this.currentUser[field];
            }
        });
    }

    redirectToLogin() {
        if (!window.location.pathname.includes('login.html') && 
            !window.location.pathname.includes('register.html')) {
            window.location.href = '/templates/login.html';
        }
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.getElementById('message');
        if (messageDiv) {
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = message;
            messageDiv.style.display = 'block';

            // Auto-hide success messages
            if (type === 'success') {
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            }
        } else {
            alert(message);
        }
    }

    showLoading(button) {
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<div class="loading"></div> Loading...';
        button.setAttribute('data-original-text', originalText);
    }

    hideLoading(button) {
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        }
        button.disabled = false;
    }

    toggleMobileMenu() {
        const navMenu = document.getElementById('navMenu');
        if (navMenu) {
            navMenu.classList.toggle('active');
        }
    }

    // Property formatting utilities
    formatPrice(price) {
        return `₹${price} Crores`;
    }

    formatArea(area) {
        return area.toLocaleString('en-IN') + ' sqft';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

// Global functions
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        window.location.href = '/templates/login.html';
    } catch (error) {
        window.location.href = '/templates/login.html';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.realEstateApp = new RealEstateApp();
});