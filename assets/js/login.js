/**
 * login.js - Login page logic
 */
document.addEventListener('DOMContentLoaded', function () {

  // Toggle password visibility
  const togglePwd = document.getElementById('togglePassword');
  const pwdInput = document.getElementById('password');
  const eyeIcon = document.getElementById('eyeIcon');

  if (togglePwd) {
    togglePwd.addEventListener('click', function () {
      const isHidden = pwdInput.type === 'password';
      pwdInput.type = isHidden ? 'text' : 'password';
      eyeIcon.style.fill = isHidden ? '#0076A2' : '#9ca3af';
    });
  }

  // Clear errors on input
  ['username', 'password'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', function () {
        this.classList.remove('error');
        const err = document.getElementById(id + 'Error');
        if (err) err.classList.remove('show');
        document.getElementById('loginError').classList.remove('show');
      });
    }
  });

  // Handle form submit
  const form = document.getElementById('loginForm');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginError = document.getElementById('loginError');
    const loginBtn = document.getElementById('loginBtn');

    // Client-side empty validation
    let valid = true;
    if (!username.trim()) {
      document.getElementById('username').classList.add('error');
      document.getElementById('usernameError').classList.add('show');
      valid = false;
    }
    if (!password) {
      document.getElementById('password').classList.add('error');
      document.getElementById('passwordError').classList.add('show');
      valid = false;
    }
    if (!valid) return;

    // Disable button during "processing"
    loginBtn.disabled = true;
    loginBtn.textContent = 'Đang xử lý...';

    // Simulate async call
    setTimeout(function () {
      const result = attemptLogin(username, password);
      if (result.success) {
        window.location.href = 'otp.html';
      } else {
        loginError.textContent = result.error;
        loginError.classList.add('show');
        loginBtn.disabled = false;
        loginBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M11 7L9.6 8.4l2.6 2.6H2v2h10.2l-2.6 2.6L11 17l5-5-5-5zm9 12h-8v2h8c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-8v2h8v14z"/></svg> Đăng nhập`;
      }
    }, 600);
  });

  // If already authenticated, redirect to dashboard
  if (isAuthenticated()) {
    window.location.href = 'dashboard.html';
  }
});
