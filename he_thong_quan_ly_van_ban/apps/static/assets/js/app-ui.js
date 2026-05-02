/**
 * app-ui.js — Global UI interactions
 * Mobile sidebar drawer, keyboard handlers
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    /* ── Mobile Sidebar Drawer ── */
    var sidebar = document.querySelector(".app-sidebar");
    var overlay = document.getElementById("mobileOverlay");
    var openBtn = document.getElementById("mobileMenuBtn");
    var closeBtn = document.getElementById("mobileCloseBtn");

    function openMobileSidebar() {
      if (!sidebar || !overlay) return;
      sidebar.classList.add("mobile-open");
      overlay.classList.add("active");
      document.body.style.overflow = "hidden";
      if (closeBtn) closeBtn.focus();
    }

    function closeMobileSidebar() {
      if (!sidebar || !overlay) return;
      sidebar.classList.remove("mobile-open");
      overlay.classList.remove("active");
      document.body.style.overflow = "";
    }

    if (openBtn) {
      openBtn.addEventListener("click", openMobileSidebar);
    }

    if (closeBtn) {
      closeBtn.addEventListener("click", closeMobileSidebar);
    }

    if (overlay) {
      overlay.addEventListener("click", closeMobileSidebar);
    }

    /* Esc key closes sidebar */
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && sidebar && sidebar.classList.contains("mobile-open")) {
        closeMobileSidebar();
      }
    });

    /* Auto-close on resize above mobile breakpoint */
    var mql = window.matchMedia("(min-width: 769px)");
    function handleResize(e) {
      if (e.matches && sidebar && sidebar.classList.contains("mobile-open")) {
        closeMobileSidebar();
      }
    }
    if (mql.addEventListener) {
      mql.addEventListener("change", handleResize);
    } else if (mql.addListener) {
      mql.addListener(handleResize);
    }

    /* ── Clickable table rows: keyboard support ── */
    document.querySelectorAll("tr[onclick]").forEach(function (row) {
      if (!row.getAttribute("tabindex")) {
        row.setAttribute("tabindex", "0");
        row.setAttribute("role", "link");
      }
      row.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          row.click();
        }
      });
    });
  });
})();
