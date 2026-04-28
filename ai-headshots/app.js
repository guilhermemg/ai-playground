(function () {
  "use strict";

  const STYLE_LABELS = {
    formal: "Executivo",
    casual: "Smart casual",
    criativo: "Criativo",
    tecnico: "Tech / inovação",
  };

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const previewRow = document.getElementById("preview-row");
  const previewImg = document.getElementById("preview-img");
  const fileNameEl = document.getElementById("file-name");
  const fileSizeEl = document.getElementById("file-size");
  const btnClearFile = document.getElementById("btn-clear-file");
  const btnNext1 = document.getElementById("btn-next-1");
  const btnNext2 = document.getElementById("btn-next-2");
  const btnBack2 = document.getElementById("btn-back-2");
  const btnBack3 = document.getElementById("btn-back-3");
  const btnGenerate = document.getElementById("btn-generate");
  const btnRestart = document.getElementById("btn-restart");
  const reviewFile = document.getElementById("rev-file");
  const reviewStyle = document.getElementById("rev-style");
  const statusView = document.getElementById("status-view");
  const resultView = document.getElementById("result-view");
  const resultActions = document.getElementById("result-actions");
  const ringFg = document.getElementById("ring-fg");
  const gallery = document.getElementById("gallery");

  const tabs = Array.from(document.querySelectorAll(".step-tab"));
  const sections = Array.from(document.querySelectorAll(".step-section"));

  let currentStep = 1;
  let objectUrl = null;
  let selectedFile = null;

  const circumference = 2 * Math.PI * 45;

  function setRingProgress(pct) {
    const offset = circumference * (1 - pct / 100);
    ringFg.style.strokeDasharray = String(circumference);
    ringFg.style.strokeDashoffset = String(offset);
  }

  setRingProgress(0);

  function getSelectedStyle() {
    const checked = document.querySelector('input[name="style"]:checked');
    return checked ? checked.value : "formal";
  }

  function updateTabs() {
    tabs.forEach((tab, i) => {
      const step = i + 1;
      const selected = step === currentStep;
      tab.setAttribute("aria-selected", selected ? "true" : "false");
      tab.setAttribute("aria-disabled", step > currentStep ? "true" : "false");
    });
  }

  function showStep(n) {
    currentStep = n;
    sections.forEach((sec) => {
      const step = parseInt(sec.dataset.step, 10);
      const active = step === n;
      sec.classList.toggle("is-active", active);
      sec.toggleAttribute("hidden", !active);
    });
    updateTabs();
  }

  function clearFile() {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    selectedFile = null;
    fileInput.value = "";
    previewRow.hidden = true;
    btnNext1.disabled = true;
  }

  function onFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    clearFile();
    selectedFile = file;
    objectUrl = URL.createObjectURL(file);
    previewImg.src = objectUrl;
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatSize(file.size);
    previewRow.hidden = false;
    btnNext1.disabled = false;
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  }

  fileInput.addEventListener("change", function () {
    const f = fileInput.files && fileInput.files[0];
    if (f) onFile(f);
  });

  btnClearFile.addEventListener("click", function () {
    clearFile();
  });

  ["dragenter", "dragover"].forEach((ev) => {
    dropzone.addEventListener(ev, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("is-drag");
    });
  });

  ["dragleave", "drop"].forEach((ev) => {
    dropzone.addEventListener(ev, function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("is-drag");
    });
  });

  dropzone.addEventListener("drop", function (e) {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) onFile(f);
  });

  btnNext1.addEventListener("click", function () {
    showStep(2);
  });

  btnBack2.addEventListener("click", function () {
    showStep(1);
  });

  btnNext2.addEventListener("click", function () {
    const style = getSelectedStyle();
    reviewFile.textContent = selectedFile ? selectedFile.name : "—";
    reviewStyle.textContent = STYLE_LABELS[style] || style;
    showStep(3);
  });

  btnBack3.addEventListener("click", function () {
    showStep(2);
  });

  function runFakeProgress(done) {
    let t = 0;
    const id = setInterval(function () {
      t += 4;
      if (t > 100) {
        t = 100;
        clearInterval(id);
        setRingProgress(100);
        if (typeof done === "function") done();
        return;
      }
      setRingProgress(t);
    }, 90);
  }

  function buildGallery(styleKey) {
    gallery.innerHTML = "";
    const styleName = STYLE_LABELS[styleKey] || styleKey;
    const items = [
      { label: "Retrato 1 — " + styleName },
      { label: "Retrato 2 — variação" },
      { label: "Retrato 3 — recorte" },
      { label: "Retrato 4 — expressão" },
    ];
    items.forEach(function (item) {
      const fig = document.createElement("figure");
      fig.setAttribute("role", "listitem");
      const ph = document.createElement("div");
      ph.className = "img-placeholder";
      ph.setAttribute("aria-label", "Placeholder para imagem gerada");
      ph.textContent = "Imagem após a API de inferência";
      const cap = document.createElement("figcaption");
      cap.textContent = item.label;
      fig.appendChild(ph);
      fig.appendChild(cap);
      gallery.appendChild(fig);
    });
  }

  btnGenerate.addEventListener("click", function () {
    const style = getSelectedStyle();
    showStep(4);
    statusView.hidden = false;
    resultView.hidden = true;
    resultActions.hidden = true;
    setRingProgress(0);
    runFakeProgress(function () {
      statusView.hidden = true;
      resultView.hidden = false;
      resultActions.hidden = false;
      buildGallery(style);
    });
  });

  btnRestart.addEventListener("click", function () {
    showStep(1);
  });
})();
