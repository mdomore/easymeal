// Translation system for EasyMeal
let currentLang = 'en';
let translations = {};

// Supported languages
const supportedLanguages = {
    'en': 'English',
    'fr': 'Français'
};

/**
 * Load translations for a given language
 */
async function loadTranslations(lang = 'en') {
    try {
        const response = await fetch(`/easymeal/static/i18n/${lang}.json`);
        if (!response.ok) {
            console.warn(`Translation file for ${lang} not found, falling back to English`);
            if (lang !== 'en') {
                return await loadTranslations('en');
            }
            return false;
        }
        translations = await response.json();
        currentLang = lang;
        
        // Save language preference
        localStorage.setItem('preferred-language', lang);
        
        // Update HTML lang attribute
        document.documentElement.lang = lang;
        
        return true;
    } catch (error) {
        console.error('Error loading translations:', error);
        if (lang !== 'en') {
            return await loadTranslations('en');
        }
        return false;
    }
}

/**
 * Get translation for a key (supports nested keys like "landing.signIn")
 */
function t(key, params = {}) {
    const keys = key.split('.');
    let value = translations;
    
    // Navigate through nested object
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            // Key not found, return the key as fallback
            console.warn(`Translation key not found: ${key}`);
            return key;
        }
    }
    
    // Handle string replacement with parameters
    if (typeof value === 'string') {
        Object.keys(params).forEach(paramKey => {
            value = value.replace(new RegExp(`{{${paramKey}}}`, 'g'), params[paramKey]);
        });
        
        // Handle newlines in strings
        value = value.replace(/\\n/g, '\n');
        
        return value;
    }
    
    return key;
}

/**
 * Initialize translations on page load
 */
async function initTranslations() {
    // Get preferred language from localStorage or browser
    const savedLang = localStorage.getItem('preferred-language');
    const browserLang = navigator.language.split('-')[0]; // Get language code (en, fr, etc.)
    
    // Determine which language to use
    let langToLoad = 'en'; // Default to English
    if (savedLang && supportedLanguages[savedLang]) {
        langToLoad = savedLang;
    } else if (browserLang && supportedLanguages[browserLang]) {
        langToLoad = browserLang;
    }
    
    // Load translations
    await loadTranslations(langToLoad);
    
    // Apply translations to elements with data-i18n attributes
    applyTranslations();
    
    // Update language toggle buttons (for mobile)
    if (window.updateLanguageButtonText) {
        window.updateLanguageButtonText();
    }
}

/**
 * Apply translations to all elements with data-i18n attributes
 */
function applyTranslations() {
    // Handle data-i18n-placeholder attributes
    const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
    placeholderElements.forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.placeholder = t(key);
    });
    
    // Handle data-i18n-title attributes
    const titleElements = document.querySelectorAll('[data-i18n-title]');
    titleElements.forEach(element => {
        const key = element.getAttribute('data-i18n-title');
        element.title = t(key);
    });
    
    // Find all elements with data-i18n attribute
    const elements = document.querySelectorAll('[data-i18n]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key);
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            // For input elements, set value or placeholder if not already handled
            if (!element.hasAttribute('data-i18n-placeholder')) {
                if (element.placeholder) {
                    element.placeholder = translation;
                } else {
                    element.value = translation;
                }
            }
        } else if (element.tagName === 'IMG') {
            // For images, set alt text
            element.alt = translation;
        } else if (element.tagName === 'LABEL') {
            // For labels, set text content
            element.textContent = translation;
        } else {
            // For other elements, set text content
            // Handle newlines if present
            if (translation.includes('\n')) {
                element.innerHTML = translation.split('\n').join('<br>');
            } else {
                element.textContent = translation;
            }
        }
    });
    
    // Update meta tags
    const titleMeta = document.querySelector('title');
    if (titleMeta) {
        titleMeta.textContent = t('meta.title');
    }
    
    const descMeta = document.querySelector('meta[name="description"]');
    if (descMeta) {
        descMeta.setAttribute('content', t('meta.description'));
    }
    
    // Update language switcher dropdowns
    const langSwitchers = document.querySelectorAll('#language-switcher, #language-switcher-landing');
    langSwitchers.forEach(switcher => {
        if (switcher) {
            switcher.value = currentLang;
        }
    });
}

/**
 * Change language and reload translations
 */
async function changeLanguage(lang) {
    if (!supportedLanguages[lang]) {
        console.warn(`Language ${lang} is not supported`);
        return false;
    }
    
    const success = await loadTranslations(lang);
    if (success) {
        applyTranslations();
        // Update language toggle buttons (for mobile)
        if (window.updateLanguageButtonText) {
            window.updateLanguageButtonText();
        }
        // Trigger custom event for JavaScript code that needs to update
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
        return true;
    }
    return false;
}

/**
 * Get current language
 */
function getCurrentLanguage() {
    return currentLang;
}

/**
 * Get supported languages
 */
function getSupportedLanguages() {
    return supportedLanguages;
}

// Expose functions globally for use in other scripts
window.t = t;
window.changeLanguage = changeLanguage;
window.getCurrentLanguage = getCurrentLanguage;
window.applyTranslations = applyTranslations;

// Auto-initialize when script loads (if DOM is ready)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTranslations);
} else {
    // DOM is already ready
    initTranslations();
}

