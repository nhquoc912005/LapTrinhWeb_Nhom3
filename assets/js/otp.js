/**
 * otp.js - OTP Verification page logic
 */
document.addEventListener('DOMContentLoaded', function () {
  // Check pending user
  const pending = getPendingUser();
  if (!pending) {
    window.location.href = 'index.html';
    return;
  }

  const inputs = Array.from({ length: 6 }, (_, i) => document.getElementById('otp' + i));
  const verifyBtn = document.getElementById('verifyBtn');
  const errorEl = document.getElementById('otpError');
  const successEl = document.getElementById('otpSuccess');
  const timerEl = document.getElementById('otpTimer');
  const timerWrap = document.getElementById('otpTimerWrap');
  const resendBtn = document.getElementById('resendBtn');
  let countdown = OTP_TIMEOUT;
  let timerInterval = null;

  // --- OTP input behavior ---
  inputs.forEach((input, idx) => {
    input.addEventListener('input', function () {
      // Only allow digits
      this.value = this.value.replace(/[^0-9]/g, '').slice(0, 1);
      if (this.value) {
        this.classList.add('filled');
        this.classList.remove('error');
        if (idx < 5) inputs[idx + 1].focus();
      } else {
        this.classList.remove('filled');
      }
      clearErrors();
      autoVerifyIfComplete();
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace') {
        if (!this.value && idx > 0) {
          inputs[idx - 1].value = '';
          inputs[idx - 1].classList.remove('filled');
          inputs[idx - 1].focus();
        }
      }
      // Handle paste
      if (e.key === 'v' && (e.ctrlKey || e.metaKey)) {
        // handled below
      }
    });

    input.addEventListener('paste', function (e) {
      e.preventDefault();
      const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/[^0-9]/g, '');
      pasted.split('').slice(0, 6).forEach((char, i) => {
        if (inputs[i]) {
          inputs[i].value = char;
          inputs[i].classList.add('filled');
        }
      });
      const nextEmpty = inputs.findIndex(inp => !inp.value);
      if (nextEmpty !== -1) inputs[nextEmpty].focus();
      else inputs[5].focus();
      clearErrors();
      autoVerifyIfComplete();
    });
  });

  function getOTPCode() {
    return inputs.map(i => i.value).join('');
  }

  function clearErrors() {
    errorEl.textContent = '';
    errorEl.classList.remove('show');
    inputs.forEach(i => i.classList.remove('error'));
  }

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add('show');
    inputs.forEach(i => i.classList.add('error'));
    // Shake animation
    const wrap = document.getElementById('otpInputs');
    wrap.style.animation = 'none';
    setTimeout(() => {
      wrap.style.animation = '';
    }, 10);
  }

  function autoVerifyIfComplete() {
    if (getOTPCode().length === 6) {
      verifyBtn.click();
    }
  }

  // --- Timer ---
  function startTimer() {
    countdown = OTP_TIMEOUT;
    timerEl.textContent = countdown;
    timerWrap.classList.remove('expired');
    resendBtn.classList.remove('show');
    verifyBtn.disabled = false;
    inputs.forEach(i => { i.disabled = false; i.value = ''; i.classList.remove('filled', 'error'); });
    inputs[0].focus();
    clearErrors();

    clearInterval(timerInterval);
    timerInterval = setInterval(function () {
      countdown--;
      timerEl.textContent = countdown;
      if (countdown <= 0) {
        clearInterval(timerInterval);
        timerEl.textContent = '00';
        timerWrap.classList.add('expired');
        timerWrap.innerHTML = '<span style="color:#EF4444;">Mã OTP đã hết hạn</span>';
        resendBtn.classList.add('show');
        verifyBtn.disabled = true;
        inputs.forEach(i => i.disabled = true);
      }
    }, 1000);
  }

  startTimer();

  // --- Resend OTP ---
  resendBtn.addEventListener('click', function () {
    successEl.style.display = 'none';
    startTimer();
    showToast && showToast('Mã OTP mới đã được gửi (demo: 123456)', 'info');
  });

  // --- Verify Button ---
  verifyBtn.addEventListener('click', function () {
    const code = getOTPCode();
    if (code.length < 6) {
      showError('Vui lòng nhập đủ 6 chữ số OTP.');
      return;
    }

    verifyBtn.disabled = true;
    verifyBtn.textContent = 'Đang xác thực...';

    setTimeout(function () {
      const result = verifyOTP(code);
      if (result.success) {
        clearErrors();
        successEl.style.display = 'block';
        clearInterval(timerInterval);
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 1200);
      } else {
        showError(result.error || 'Mã OTP không đúng.');
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg> Xác thực`;
      }
    }, 500);
  });

  // Focus first input
  inputs[0].focus();

  // Stub for toast (if not available on this page)
  if (typeof showToast === 'undefined') {
    window.showToast = function () {};
  }
});
