document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("filterForm");
  const activeFilters = document.getElementById("activeFilters");

  const hiddenTrangThai = document.getElementById("hiddenTrangThai");
  const searchKeyword = document.getElementById("searchKeyword");
  const filterDonVi = document.getElementById("filterDonVi");
  const filterLoaiVB = document.getElementById("filterLoaiVB");
  const filterHinhThuc = document.getElementById("filterHinhThuc");
  const filterDoKhan = document.getElementById("filterDoKhan");

  window.setTrangThaiAndSubmit = function (value) {
    hiddenTrangThai.value = value;
    form.submit();
  };

  function createChip(label, value, onRemove) {
    const chip = document.createElement("div");
    chip.className = "filter-chip";

    const text = document.createElement("span");
    text.textContent = `${label}: ${value}`;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "×";
    btn.addEventListener("click", onRemove);

    chip.appendChild(text);
    chip.appendChild(btn);
    return chip;
  }

  function renderActiveFilters() {
    activeFilters.innerHTML = "";
    const chips = [];


    if (filterDonVi && filterDonVi.value) {
      chips.push(createChip("Đơn vị", filterDonVi.options[filterDonVi.selectedIndex].text, function () {
        filterDonVi.value = "";
        form.submit();
      }));
    }

    if (filterLoaiVB && filterLoaiVB.value) {
      chips.push(createChip("Loại văn bản", filterLoaiVB.options[filterLoaiVB.selectedIndex].text, function () {
        filterLoaiVB.value = "";
        form.submit();
      }));
    }

    if (filterHinhThuc && filterHinhThuc.value) {
      chips.push(createChip("Hình thức", filterHinhThuc.options[filterHinhThuc.selectedIndex].text, function () {
        filterHinhThuc.value = "";
        form.submit();
      }));
    }

    if (filterDoKhan && filterDoKhan.value) {
      chips.push(createChip("Độ khẩn", filterDoKhan.options[filterDoKhan.selectedIndex].text, function () {
        filterDoKhan.value = "";
        form.submit();
      }));
    }

    if (chips.length > 0) {
      const label = document.createElement("span");
      label.className = "active-filters-label";
      label.textContent = "Đang lọc:";
      activeFilters.appendChild(label);

      chips.forEach(chip => activeFilters.appendChild(chip));
      activeFilters.style.display = "flex";
    } else {
      activeFilters.style.display = "none";
    }
  }

  renderActiveFilters();

  [searchKeyword, filterDonVi, filterLoaiVB, filterHinhThuc, filterDoKhan].forEach(function (el) {
    if (el) {
      el.addEventListener("change", function () {
        form.submit();
      });
    }
  });

  if (searchKeyword) {
    // Submit khi nhấn Enter
    searchKeyword.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        form.submit();
      }
    });

    // Debounce: tự động tìm kiếm sau 400ms khi ngừng gõ
    let debounceTimer = null;
    searchKeyword.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        form.submit();
      }, 400);
    });
  }
});