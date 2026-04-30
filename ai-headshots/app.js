(function () {
  "use strict";

  const TAB_ORDER = ["upload", "style", "review", "generate"];

  /** @type {HTMLElement | null} */
  const wizard = document.querySelector("[data-wizard]");
  if (!wizard) return;

  const tabs = Array.from(wizard.querySelectorAll(".tabs__tab"));
  const panels = Array.from(wizard.querySelectorAll("[data-panel]"));
  const dropzone = wizard.querySelector("[data-dropzone]");
  const fileInput = dropzone && dropzone.querySelector('input[type="file"]');
  const preview = wizard.querySelector("[data-preview]");
  const reviewPhoto = wizard.querySelector("[data-review-photo]");
  const reviewStyle = wizard.querySelector("[data-review-style]");
  const progressBar = wizard.querySelector("[data-progressbar]");
  const progressText = wizard.querySelector("[data-progress-text]");
  const progressBlock = wizard.querySelector("[data-progress-block]");
  const simulateBtn = wizard.querySelector("[data-simulate]");
  const gallery = wizard.querySelector("[data-gallery]");
  const galleryEmpty = wizard.querySelector("[data-gallery-empty]");

  let objectUrl = null;
  let lastFileName = "—";

  function getPanelId(name) {
    return "panel-" + name;
  }

  function setActiveTab(name) {
    tabs.forEach((tab) => {
      const id = tab.getAttribute("data-tab");
      const selected = id === name;
      tab.setAttribute("aria-selected", selected ? "true" : "false");
      tab.tabIndex = selected ? 0 : -1;
    });
    panels.forEach((panel) => {
      const id = panel.getAttribute("data-panel");
      const active = id === name;
      panel.classList.toggle("panel--active", active);
      panel.hidden = !active;
    });
  }

  function activateTabByName(name) {
    if (!TAB_ORDER.includes(name)) return;
    setActiveTab(name);
    const tabEl = tabs.find((t) => t.getAttribute("data-tab") === name);
    tabEl && tabEl.focus();
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const name = tab.getAttribute("data-tab");
      if (name) activateTabByName(name);
    });
    tab.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      const idx = tabs.indexOf(tab);
      const next =
        e.key === "ArrowRight"
          ? Math.min(idx + 1, tabs.length - 1)
          : Math.max(idx - 1, 0);
      const name = tabs[next].getAttribute("data-tab");
      if (name) activateTabByName(name);
    });
  });

  wizard.querySelectorAll("[data-next]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.getAttribute("data-next");
      if (next) activateTabByName(next);
    });
  });

  wizard.querySelectorAll("[data-prev]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const prev = btn.getAttribute("data-prev");
      if (prev) activateTabByName(prev);
    });
  });

  function updateReviewStyle() {
    const checked = wizard.querySelector('input[name="style"]:checked');
    if (reviewStyle && checked) {
      const label = checked.closest(".style-card");
      const text = label && label.querySelector(".style-card__label");
      reviewStyle.textContent = text ? text.textContent.trim() : checked.value;
    }
  }

  wizard.querySelectorAll('input[name="style"]').forEach((input) => {
    input.addEventListener("change", updateReviewStyle);
  });

  function setPreviewFromFile(file) {
    if (!preview || !dropzone) return;
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    if (file) {
      objectUrl = URL.createObjectURL(file);
      preview.src = objectUrl;
      preview.removeAttribute("hidden");
      dropzone.classList.add("has-file");
      lastFileName = file.name;
    } else {
      preview.removeAttribute("src");
      preview.setAttribute("hidden", "");
      dropzone.classList.remove("has-file");
      lastFileName = "—";
    }
    if (reviewPhoto) reviewPhoto.textContent = lastFileName;
  }

  if (fileInput && dropzone) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      setPreviewFromFile(file || null);
    });

    ["dragenter", "dragover"].forEach((ev) => {
      dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.style.borderColor = "rgba(124, 92, 255, 0.6)";
      });
    });
    ["dragleave", "drop"].forEach((ev) => {
      dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.style.borderColor = "";
      });
    });
    dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      const file = dt && dt.files && dt.files[0];
      if (file && file.type.startsWith("image/")) {
        try {
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          fileInput.files = dataTransfer.files;
        } catch {
          setPreviewFromFile(file);
          return;
        }
        setPreviewFromFile(file);
      }
    });
  }

  function setProgress(value, text) {
    if (progressBar) {
      progressBar.setAttribute("aria-valuenow", String(value));
      wizard.style.setProperty("--progress-pct", value + "%");
    }
    if (progressText) progressText.textContent = text;
  }

  function clearGalleryPlaceholders() {
    if (!gallery) return;
    gallery.querySelectorAll(".gallery__thumb").forEach((n) => n.remove());
    if (galleryEmpty) galleryEmpty.hidden = false;
  }

  function addPlaceholderThumbs(count) {
    if (!gallery || !galleryEmpty) return;
    galleryEmpty.hidden = true;
    const labels = ["Formal", "Casual", "Exec.", "Criativo"];
    for (let i = 0; i < count; i++) {
      const div = document.createElement("div");
      div.className = "gallery__thumb";
      div.setAttribute("role", "img");
      div.setAttribute(
        "aria-label",
        "Placeholder de retrato " + (i + 1) + " de " + count
      );
      div.textContent = labels[i % labels.length];
      gallery.appendChild(div);
    }
  }

  if (simulateBtn) {
    simulateBtn.addEventListener("click", () => {
      if (progressBlock) progressBlock.setAttribute("aria-busy", "true");
      simulateBtn.disabled = true;
      clearGalleryPlaceholders();
      setProgress(0, "A preparar modelo…");

      const steps = [
        { pct: 25, msg: "A analisar rosto e iluminação…" },
        { pct: 55, msg: "A gerar variações de estilo…" },
        { pct: 85, msg: "A refinar detalhes…" },
        { pct: 100, msg: "Concluído (demo). Galeria placeholder." },
      ];
      let i = 0;
      const tick = window.setInterval(() => {
        if (i >= steps.length) {
          window.clearInterval(tick);
          addPlaceholderThumbs(4);
          if (progressBlock) progressBlock.setAttribute("aria-busy", "false");
          simulateBtn.disabled = false;
          return;
        }
        setProgress(steps[i].pct, steps[i].msg);
        i++;
      }, 650);
    });
  }

  updateReviewStyle();
  setProgress(0, "Pronto para simular.");
})();
