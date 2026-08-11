(function () {
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const saved = localStorage.getItem("rainblog-theme");

    function preferredTheme() {
        return media.matches ? "dark" : "light";
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;
        const button = document.querySelector("[data-theme-toggle]");
        if (button) {
            const dark = theme === "dark";
            button.textContent = dark ? "☀" : "☾";
            button.setAttribute("aria-label", dark ? "切换到浅色模式" : "切换到深色模式");
            button.title = dark ? "切换到浅色模式" : "切换到深色模式";
        }
    }

    applyTheme(saved === "light" || saved === "dark" ? saved : preferredTheme());

    document.addEventListener("DOMContentLoaded", function () {
        applyTheme(root.dataset.theme);
        const button = document.querySelector("[data-theme-toggle]");
        if (!button) return;

        button.addEventListener("click", function () {
            const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
            localStorage.setItem("rainblog-theme", nextTheme);
            applyTheme(nextTheme);
        });
    });

    media.addEventListener("change", function () {
        if (!localStorage.getItem("rainblog-theme")) applyTheme(preferredTheme());
    });
})();
