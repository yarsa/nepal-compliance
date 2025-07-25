const THEMES = {
    DARK: 'dark',
    LIGHT: 'light'
};

function applyCalendarTheme(theme) {
    if (!theme || typeof theme !== 'string') {
        theme = THEMES.LIGHT;
const THEMES = {
    DARK: 'dark',
    LIGHT: 'light'
};

function applyCalendarTheme(theme) {
    if (!theme || typeof theme !== 'string') {
        theme = THEMES.LIGHT;
    }

    const root = document.documentElement;
    const set = (key, value) => root.style.setProperty(key, value);

    if (theme === THEMES.DARK) {
        set('--calendar-bg', '#1e1e2f');
        set('--calendar-text', '#ffffff');
        set('--calendar-border', '#444');
        set('--calendar-header-bg', '#2a2a3a');
        set('--calendar-header-text', '#ffffff');
        set('--calendar-nav-bg', '#444');
        set('--calendar-nav-text', '#ffffff');
        set('--calendar-nav-hover', '#555');
        set('--calendar-day-text', '#ffffff');
        set('--calendar-selected-bg', '#ffffff');
        set('--calendar-selected-text', '#000000');
        set('--calendar-current-bg', '#424242');
        set('--calendar-current-text', '#ffffff');
        set('--calendar-hover-bg', '#333333');
    } else {
        set('--calendar-bg', '#ffffff');
        set('--calendar-text', '#000000');
        set('--calendar-border', '#ddd');
        set('--calendar-header-bg', '#f8f8f8');
        set('--calendar-header-text', '#000000');
        set('--calendar-nav-bg', '#171717');
        set('--calendar-nav-text', '#ffffff');
        set('--calendar-nav-hover', '#2b2b3a');
        set('--calendar-day-text', '#000000');
        set('--calendar-selected-bg', '#171717');
        set('--calendar-selected-text', '#ffffff');
        set('--calendar-current-bg', '#f5f5f5');
        set('--calendar-current-text', '#000000');
        set('--calendar-hover-bg', '#e0e0e0');
    }
}
        set('--calendar-day-text', '#000000');
        set('--calendar-selected-bg', '#171717');
        set('--calendar-selected-text', '#ffffff');
        set('--calendar-current-bg', '#f5f5f5');
        set('--calendar-current-text', '#000000');
        set('--calendar-hover-bg', '#e0e0e0');
    }
}

frappe.after_ajax(() => {
    const theme = frappe.boot?.user?.theme?.toLowerCase() || "light";
    applyCalendarTheme(theme);
});

frappe.router.on('change', () => {
    const theme = frappe.boot?.user?.theme?.toLowerCase() || "light";
    applyCalendarTheme(getCurrentTheme() || theme);
});
