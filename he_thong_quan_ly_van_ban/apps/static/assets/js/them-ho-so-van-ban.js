document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("hoSoForm");
    if (!form) return;

    const btnLuu = document.getElementById("btnLuu");
    const tieuDe = document.getElementById("tieu_de_ho_so");
    const kyHieu = document.getElementById("ky_hieu_ho_so");
    const ngayTao = document.getElementById("ngay_tao_ho_so");
    const thoiGianBaoQuan = document.getElementById("thoi_gian_bao_quan");
    const soNamLuuTru = document.getElementById("so_nam_luu_tru");
    const duKienText = document.getElementById("duKienLuuTruText");

    const nguoiXuLyPlaceholder = document.getElementById("nguoi_xu_ly_placeholder");
    const nguoiXuLyHiddenContainer = document.getElementById("nguoi_xu_ly_hidden_container");
    const selectedNguoiXuLyChips = document.getElementById("selectedNguoiXuLyChips");

    const openNguoiXuLyPopup = document.getElementById("openNguoiXuLyPopup");
    const closeNguoiXuLyPopup = document.getElementById("closeNguoiXuLyPopup");
    const cancelNguoiXuLyPopup = document.getElementById("cancelNguoiXuLyPopup");
    const saveNguoiXuLyPopup = document.getElementById("saveNguoiXuLyPopup");
    const nguoiXuLyPopup = document.getElementById("nguoiXuLyPopup");
    const searchNguoiXuLy = document.getElementById("searchNguoiXuLy");
    const nguoiXuLyRows = document.querySelectorAll(".popup-user-row");
    const selectedNguoiXuLyCount = document.getElementById("selectedNguoiXuLyCount");

    const phongBanDropdown = document.getElementById("phongBanDropdown");
    const phongBanDisplay = document.getElementById("phongBanDisplay");
    const checkAllPhongBan = document.getElementById("checkAllPhongBan");
    const pbCheckboxes = document.querySelectorAll(".pb-checkbox");

    const currentYear = new Date().getFullYear();

    function setSaveButtonState(isValid) {
        btnLuu.disabled = !isValid;
        btnLuu.classList.toggle("enabled", isValid);
    }

    function getCheckedPhongBan() {
        return document.querySelectorAll('.pb-checkbox:checked');
    }

    function getSelectedNguoiXuLyIds() {
        return nguoiXuLyHiddenContainer.querySelectorAll('input[name="nguoi_xu_ly"]');
    }

    function updateSoNamLuuTru() {
        const value = thoiGianBaoQuan.value;

        if (value === "Theo quy định - 2 năm") {
            soNamLuuTru.disabled = false;
            soNamLuuTru.readOnly = true;
            soNamLuuTru.value = 2;
        } else if (value === "Theo quy định - 5 năm") {
            soNamLuuTru.disabled = false;
            soNamLuuTru.readOnly = true;
            soNamLuuTru.value = 5;
        } else if (value === "Theo quy định - 10 năm") {
            soNamLuuTru.disabled = false;
            soNamLuuTru.readOnly = true;
            soNamLuuTru.value = 10;
        } else if (value === "Vĩnh viễn") {
            soNamLuuTru.disabled = true;
            soNamLuuTru.readOnly = true;
            soNamLuuTru.value = "";
        } else {
            soNamLuuTru.disabled = false;
            soNamLuuTru.readOnly = false;
            if (["2", "5", "10"].includes(soNamLuuTru.value)) {
                soNamLuuTru.value = "";
            }
        }

        updateDuKien();
        validateForm();
    }

    function updateDuKien() {
        if (thoiGianBaoQuan.value === "Vĩnh viễn") {
            duKienText.textContent = "Hồ sơ được lưu trữ vĩnh viễn.";
            return;
        }

        if (soNamLuuTru.disabled || !soNamLuuTru.value) {
            duKienText.textContent = "Hệ thống tự động tính dựa trên năm hiện tại";
            return;
        }

        const years = parseInt(soNamLuuTru.value, 10);
        if (!years || years <= 0) {
            duKienText.textContent = "Hệ thống tự động tính dựa trên năm hiện tại";
            return;
        }

        duKienText.textContent = "Dự kiến lưu trữ đến năm " + (currentYear + years) + ".";
    }

    function renderSelectedNguoiXuLy(selectedUsers) {
        nguoiXuLyHiddenContainer.innerHTML = "";
        selectedNguoiXuLyChips.innerHTML = "";

        selectedUsers.forEach(function (user) {
            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = "nguoi_xu_ly";
            hidden.value = user.id;
            nguoiXuLyHiddenContainer.appendChild(hidden);

            const chip = document.createElement("span");
            chip.className = "selected-user-chip";
            chip.style.cssText = "background: #e5e7eb; color: #374151; font-size: 13px; padding: 4px 10px; border-radius: 16px; display: inline-flex; align-items: center; z-index: 10;";
            chip.innerHTML = `${user.name} <span class="chip-delete" style="cursor:pointer; margin-left: 6px; font-weight: bold; font-size: 11px;">X</span>`;
            
            const deleteBtn = chip.querySelector('.chip-delete');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const row = document.querySelector(`.popup-user-row[data-user-id="${user.id}"]`);
                    if (row) {
                        const cb = row.querySelector('.popup-user-checkbox');
                        if (cb) {
                            cb.checked = false;
                            cb.dispatchEvent(new Event('change'));
                        }
                    }
                    const updatedUsers = selectedUsers.filter(u => u.id !== user.id);
                    renderSelectedNguoiXuLy(updatedUsers);
                });
            }
            
            selectedNguoiXuLyChips.appendChild(chip);
        });

        if (nguoiXuLyPlaceholder) {
            if (selectedUsers.length === 0) {
                nguoiXuLyPlaceholder.style.display = "block";
            } else {
                nguoiXuLyPlaceholder.style.display = "none";
            }
        }

        validateForm();
    }

    function validateForm() {
        const tieuDeOk = tieuDe.value.trim() !== "";
        const kyHieuOk = kyHieu.value.trim() !== "";
        const ngayTaoOk = ngayTao ? ngayTao.value.trim() !== "" : true;
        const thoiGianOk = thoiGianBaoQuan.value.trim() !== "";
        const phongBanOk = getCheckedPhongBan().length > 0;
        const nguoiXuLyOk = getSelectedNguoiXuLyIds().length > 0;

        let soNamOk = true;
        if (!soNamLuuTru.disabled) {
            soNamOk = soNamLuuTru.value.trim() !== "" && parseInt(soNamLuuTru.value, 10) > 0;
        }

        setSaveButtonState(
            tieuDeOk && kyHieuOk && ngayTaoOk && thoiGianOk && phongBanOk && nguoiXuLyOk && soNamOk
        );
    }

    function filterNguoiXuLyRows() {
        const keyword = (searchNguoiXuLy.value || "").toLowerCase().trim();

        nguoiXuLyRows.forEach(function (row) {
            const textSearch = [
                row.dataset.userName || "",
                row.dataset.chucVu || "",
                row.dataset.sdt || "",
                row.dataset.email || "",
                row.dataset.phongBanName || ""
            ].join(" ").toLowerCase();

            const show = keyword === "" || textSearch.includes(keyword);
            row.classList.toggle("hidden", !show);
        });
    }

    function openPopup() {
        searchNguoiXuLy.value = "";
        filterNguoiXuLyRows();
        nguoiXuLyPopup.classList.add("show");
    }

    function closePopup() {
        nguoiXuLyPopup.classList.remove("show");
    }

    function updateSelectedCount() {
        const checked = document.querySelectorAll(".popup-user-checkbox:checked");
        selectedNguoiXuLyCount.textContent = `${checked.length} người`;
    }

    if (openNguoiXuLyPopup) openNguoiXuLyPopup.addEventListener("click", openPopup);
    if (closeNguoiXuLyPopup) closeNguoiXuLyPopup.addEventListener("click", closePopup);
    if (cancelNguoiXuLyPopup) cancelNguoiXuLyPopup.addEventListener("click", closePopup);

    if (nguoiXuLyPopup) {
        nguoiXuLyPopup.addEventListener("click", function (event) {
            if (event.target === nguoiXuLyPopup) closePopup();
        });
    }

    if (searchNguoiXuLy) {
        searchNguoiXuLy.addEventListener("input", filterNguoiXuLyRows);
    }

    document.querySelectorAll(".popup-user-checkbox").forEach(function (checkbox) {
        checkbox.addEventListener("change", updateSelectedCount);
    });

    document.querySelectorAll(".department-group-row").forEach(function (row) {
        row.addEventListener("click", function (e) {
            if (e.target.type === "checkbox") return;
            const targetClass = row.querySelector(".popup-dept-checkbox").dataset.target;
            const users = document.querySelectorAll("." + targetClass);
            const icon = row.querySelector(".toggle-icon");
            let isHidden = false;
            users.forEach(function (userRow) {
                if (userRow.style.display === "none") {
                    userRow.style.display = "table-row";
                    isHidden = false;
                } else {
                    userRow.style.display = "none";
                    isHidden = true;
                }
            });
            if (icon) icon.textContent = isHidden ? "+" : "-";
        });
    });

    document.querySelectorAll(".popup-dept-checkbox").forEach(function (deptCb) {
        deptCb.addEventListener("change", function () {
            const targetClass = this.dataset.target;
            const userCheckboxes = document.querySelectorAll(".user-of-" + targetClass);
            userCheckboxes.forEach(function (cb) {
                // Only act on visible ones if there was a search, but let's just check all inside the group
                const row = cb.closest(".popup-user-row");
                if (!row.classList.contains("hidden")) {
                    cb.checked = deptCb.checked;
                }
            });
            updateSelectedCount();
        });
    });

    if (saveNguoiXuLyPopup) {
        saveNguoiXuLyPopup.addEventListener("click", function () {
            const checkedRows = document.querySelectorAll(".popup-user-checkbox:checked");
            if (checkedRows.length === 0) {
                alert("Vui lòng chọn ít nhất một người xử lý.");
                return;
            }

            const selectedUsers = [];
            checkedRows.forEach(function (checkbox) {
                const row = checkbox.closest(".popup-user-row");
                selectedUsers.push({
                    id: row.dataset.userId,
                    name: row.dataset.displayName
                });
            });

            renderSelectedNguoiXuLy(selectedUsers);
            closePopup();
        });
    }

    if (phongBanDropdown) {
        phongBanDropdown.querySelector(".dropdown-header").addEventListener("click", function () {
            phongBanDropdown.classList.toggle("open");
        });
        document.addEventListener("click", function (e) {
            if (!phongBanDropdown.contains(e.target)) {
                phongBanDropdown.classList.remove("open");
            }
        });

        if (checkAllPhongBan) {
            checkAllPhongBan.addEventListener("change", function () {
                pbCheckboxes.forEach(cb => cb.checked = this.checked);
                updatePhongBanDisplay();
                validateForm();
            });
        }

        pbCheckboxes.forEach(function (cb) {
            cb.addEventListener("change", function () {
                updatePhongBanDisplay();
                validateForm();
            });
        });

        function updatePhongBanDisplay() {
            const checkedBoxes = document.querySelectorAll(".pb-checkbox:checked");
            if (checkedBoxes.length === 0) {
                if (phongBanDisplay) {
                    phongBanDisplay.innerHTML = "-- Chọn phòng ban--";
                    phongBanDisplay.style.display = "block";
                    phongBanDisplay.style.flexWrap = "nowrap";
                    phongBanDisplay.style.gap = "0";
                    phongBanDisplay.style.color = "#6b7280";
                }
                if (checkAllPhongBan) checkAllPhongBan.checked = false;
            } else {
                if (phongBanDisplay) {
                    phongBanDisplay.innerHTML = "";
                    phongBanDisplay.style.display = "flex";
                    phongBanDisplay.style.flexWrap = "wrap";
                    phongBanDisplay.style.gap = "6px";
                    phongBanDisplay.style.color = "initial";
                    
                    checkedBoxes.forEach(function(cb) {
                         const chip = document.createElement("span");
                         chip.className = "selected-user-chip";
                         chip.style.cssText = "background: #e5e7eb; color: #374151; font-size: 13px; padding: 4px 10px; border-radius: 16px; display: inline-flex; align-items: center; z-index: 10;";
                         chip.innerHTML = `${cb.nextElementSibling.textContent.trim()} <span class="chip-delete" style="cursor:pointer; margin-left: 6px; font-weight: bold; font-size: 11px;">X</span>`;
                         
                         const deleteBtn = chip.querySelector('.chip-delete');
                         if (deleteBtn) {
                             deleteBtn.addEventListener('click', function(e) {
                                 e.stopPropagation();
                                 cb.checked = false;
                                 cb.dispatchEvent(new Event('change'));
                             });
                         }
                         
                         phongBanDisplay.appendChild(chip);
                    });
                }
                
                checkAllPhongBan.checked = (checkedBoxes.length === pbCheckboxes.length);
            }
        }
        updatePhongBanDisplay();
    }

    [tieuDe, kyHieu, ngayTao, thoiGianBaoQuan, soNamLuuTru].forEach(function (el) {
        if (!el) return;
        el.addEventListener("input", function () {
            updateDuKien();
            validateForm();
        });
        el.addEventListener("change", function () {
            updateDuKien();
            validateForm();
        });
    });

    thoiGianBaoQuan.addEventListener("change", updateSoNamLuuTru);

    function initSelectedNguoiXuLy() {
        const checkedRows = document.querySelectorAll(".popup-user-checkbox:checked");
        if (checkedRows.length > 0) {
            const selectedUsers = [];
            checkedRows.forEach(function (checkbox) {
                const row = checkbox.closest(".popup-user-row");
                selectedUsers.push({
                    id: row.dataset.userId,
                    name: row.dataset.displayName
                });
            });
            renderSelectedNguoiXuLy(selectedUsers);
        }
    }

    initSelectedNguoiXuLy();
    updateSoNamLuuTru();
    updateDuKien();
    validateForm();
    updateSelectedCount();
});