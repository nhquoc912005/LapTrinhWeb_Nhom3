document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const passwordInput = document.getElementById("password");
    const toggleButton = document.getElementById("togglePassword");

    if (!passwordInput || !toggleButton || !loginForm) {
        return;
    }

    if (toggleButton && passwordInput) {
        toggleButton.addEventListener("click", function () {
            const isPassword = passwordInput.getAttribute("type") === "password";
            passwordInput.setAttribute("type", isPassword ? "text" : "password");
            toggleButton.setAttribute("aria-pressed", String(isPassword));
        });
    }

    loginForm.addEventListener("submit", function () {
        const csrfInput = loginForm.querySelector('input[name="csrfmiddlewaretoken"]');
        const csrfCookie = getCookie("qlvb_csrftoken") || getCookie("csrftoken");

        if (csrfInput && csrfCookie) {
            csrfInput.value = csrfCookie;
        }
    });
});

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        window.location.reload();
    }
});

function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (const cookie of cookies) {
        const trimmedCookie = cookie.trim();
        const prefix = `${name}=`;

        if (trimmedCookie.startsWith(prefix)) {
            return decodeURIComponent(trimmedCookie.slice(prefix.length));
        }
    }

    return "";
}
