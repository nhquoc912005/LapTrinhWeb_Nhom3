document.addEventListener("DOMContentLoaded", function () {

  // ===== HÀM DÙNG CHUNG CHO MODAL =====
  function setupModal(openBtnId, modalId, closeBtnId) {
    const openBtn = document.getElementById(openBtnId);
    const modal = document.getElementById(modalId);
    const closeBtn = document.getElementById(closeBtnId);

    if (!modal) return;

    // mở modal
    if (openBtn) {
      openBtn.addEventListener("click", function (e) {
        e.preventDefault();
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
      });
    }

    // đóng modal bằng nút
    if (closeBtn) {
      closeBtn.addEventListener("click", function (e) {
        e.preventDefault();
        modal.style.display = "none";
        document.body.style.overflow = "";
      });
    }

    // click ra ngoài để đóng
    modal.addEventListener("click", function (e) {
      if (e.target === modal) {
        modal.style.display = "none";
        document.body.style.overflow = "";
      }
    });
  }

  // ===== ÁP DỤNG CHO CÁC POPUP =====
  setupModal("openApprovalModal", "approvalModal", "closeApprovalModal");
  setupModal("openReturnModal", "returnModal", "closeReturnModal");

});
