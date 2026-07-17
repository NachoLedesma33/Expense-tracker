(function() {
  const STORAGE_KEY = 'expense-tracker-theme';
  const HTML = document.documentElement;

  function getPreferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored || 'light';
  }

  function setTheme(theme) {
    HTML.classList.toggle('dark', theme === 'dark');
    localStorage.setItem(STORAGE_KEY, theme);
  }

  setTheme(getPreferredTheme());

  window.__toggleDarkMode = function() {
    const next = HTML.classList.contains('dark') ? 'light' : 'dark';
    setTheme(next);
  };
})();
