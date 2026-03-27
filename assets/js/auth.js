/**
 * auth.js - Authentication Module
 * Hệ Thống Quản Lý Văn Bản và Điều Hành
 */

// Demo user accounts
const DEMO_USERS = [
  {
    username: 'lanhdao',
    password: '123456',
    name: 'Nguyễn Văn Lãnh Đạo',
    role: 'lanhdao',
    roleLabel: 'Lãnh đạo',
    avatar: 'LĐ',
    email: 'lanhdao@donvi.vn',
    phone: '0901 234 567',
    unit: 'Ban Giám đốc'
  },
  {
    username: 'vanthu',
    password: '123456',
    name: 'Trần Thị Văn Thư',
    role: 'vanthu',
    roleLabel: 'Văn thư',
    avatar: 'VT',
    email: 'vanthu@donvi.vn',
    phone: '0902 345 678',
    unit: 'Phòng Hành chính'
  },
  {
    username: 'chuyenvien',
    password: '123456',
    name: 'Lê Văn Chuyên Viên',
    role: 'chuyenvien',
    roleLabel: 'Chuyên viên',
    avatar: 'CV',
    email: 'chuyenvien@donvi.vn',
    phone: '0903 456 789',
    unit: 'Phòng Nghiệp vụ'
  }
];

const OTP_DEMO = '123456';
const OTP_TIMEOUT = 30; // seconds

/**
 * Attempt login - validate credentials and store temp session
 * @param {string} username
 * @param {string} password
 * @returns {{ success: boolean, error?: string }}
 */
function attemptLogin(username, password) {
  if (!username || !password) {
    return { success: false, error: 'Vui lòng nhập tên đăng nhập và mật khẩu.' };
  }

  const user = DEMO_USERS.find(
    u => u.username === username.trim() && u.password === password
  );

  if (!user) {
    return { success: false, error: 'Tên đăng nhập hoặc mật khẩu không đúng.' };
  }

  // Store pending auth (not yet OTP verified)
  sessionStorage.setItem('pendingUser', JSON.stringify(user));
  sessionStorage.removeItem('authenticated');

  return { success: true, user };
}

/**
 * Verify the OTP code
 * @param {string} otpCode - The 6-digit OTP entered
 * @returns {{ success: boolean, error?: string }}
 */
function verifyOTP(otpCode) {
  const pendingUser = getPendingUser();
  if (!pendingUser) {
    return { success: false, error: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.' };
  }

  if (otpCode !== OTP_DEMO) {
    return { success: false, error: 'Mã OTP không đúng. Vui lòng thử lại.' };
  }

  // Promote to authenticated
  localStorage.setItem('currentUser', JSON.stringify(pendingUser));
  sessionStorage.setItem('authenticated', 'true');
  sessionStorage.removeItem('pendingUser');

  return { success: true, user: pendingUser };
}

/**
 * Get the pending (pre-OTP) user from session
 */
function getPendingUser() {
  const data = sessionStorage.getItem('pendingUser');
  return data ? JSON.parse(data) : null;
}

/**
 * Get the authenticated user
 */
function getCurrentUser() {
  const data = localStorage.getItem('currentUser');
  return data ? JSON.parse(data) : null;
}

/**
 * Check if user is fully authenticated (login + OTP)
 */
function isAuthenticated() {
  return sessionStorage.getItem('authenticated') === 'true' && getCurrentUser() !== null;
}

/**
 * Logout - clear all auth data
 */
function logout() {
  localStorage.removeItem('currentUser');
  sessionStorage.removeItem('authenticated');
  sessionStorage.removeItem('pendingUser');
  window.location.href = 'index.html';
}

/**
 * Guard: redirect to login if not authenticated
 * Call this at top of each protected page.
 */
function requireAuth() {
  if (!isAuthenticated()) {
    window.location.href = 'index.html';
    return null;
  }
  return getCurrentUser();
}

/**
 * Check if current user has permission
 * @param {string[]} roles - Allowed roles
 */
function hasRole(...roles) {
  const user = getCurrentUser();
  if (!user) return false;
  return roles.includes(user.role);
}
