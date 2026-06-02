export function initTheme() {
    const themeToggleFixed = document.getElementById('themeToggleFixed');
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') document.body.classList.add('dark');
    const updateThemeButton = () => {
        if (themeToggleFixed) themeToggleFixed.innerHTML = document.body.classList.contains('dark') ? '☀️' : '🌙';
    };
    updateThemeButton();
    if (themeToggleFixed) {
        themeToggleFixed.addEventListener('click', () => {
            document.body.classList.toggle('dark');
            localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
            updateThemeButton();
        });
    }
}