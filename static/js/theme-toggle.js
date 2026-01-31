/**
 * AIMS EXAM - Theme Toggle
 * Handles Light/Dark mode switching with localStorage persistence
 */

(function() {
    'use strict';

    const THEME_KEY = 'aims-theme';
    const DARK_THEME = 'dark';
    const LIGHT_THEME = 'light';

    // Get saved theme or default to light
    function getSavedTheme() {
        return localStorage.getItem(THEME_KEY) || LIGHT_THEME;
    }

    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
        
        // Update toggle button state
        const toggleBtn = document.querySelector('.theme-toggle');
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-pressed', theme === DARK_THEME);
            toggleBtn.setAttribute('title', theme === DARK_THEME ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        }
    }

    // Toggle between themes
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || LIGHT_THEME;
        const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
        applyTheme(newTheme);
    }

    // Initialize theme on page load
    function initTheme() {
        const savedTheme = getSavedTheme();
        applyTheme(savedTheme);

        // Attach event listeners to all theme toggles
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.addEventListener('click', toggleTheme);
        });
    }

    // Check for system preference if no saved theme
    function checkSystemPreference() {
        if (!localStorage.getItem(THEME_KEY)) {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            return prefersDark ? DARK_THEME : LIGHT_THEME;
        }
        return getSavedTheme();
    }

    // Apply theme immediately to prevent flash
    (function() {
        const theme = checkSystemPreference();
        document.documentElement.setAttribute('data-theme', theme);
    })();

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }

    // Expose toggle function globally
    window.toggleTheme = toggleTheme;
})();
