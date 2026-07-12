// Synthwave Photo Gallery JavaScript

// Photo detail: click-to-navigate and swipe support
document.addEventListener("DOMContentLoaded", () => {
  const wrapper = document.querySelector(".photo-detail-clickable");
  if (!wrapper) return;

  const prevUrl = wrapper.dataset.prevUrl || "";
  const nextUrl = wrapper.dataset.nextUrl || "";
  const THRESHOLD = 80;
  const RESISTANCE = 0.3;

  // Click: left 25% = prev, right 25% = next
  wrapper.addEventListener("click", (e) => {
    if (wrapper._swiped) {
      wrapper._swiped = false;
      return;
    }
    const rect = wrapper.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const pct = x / rect.width;

    if (pct < 0.25 && prevUrl) {
      window.location.href = prevUrl;
    } else if (pct > 0.75 && nextUrl) {
      window.location.href = nextUrl;
    }
  });

  // Swipe with animated card movement
  let startX = 0;
  let startY = 0;
  let swiping = false;
  let decided = false;
  let isHorizontal = false;

  wrapper.addEventListener("touchstart", (e) => {
    if (wrapper._animating) return;
    startX = e.changedTouches[0].clientX;
    startY = e.changedTouches[0].clientY;
    swiping = true;
    decided = false;
    isHorizontal = false;
    wrapper.style.transition = "none";
  }, { passive: true });

  wrapper.addEventListener("touchmove", (e) => {
    if (!swiping || wrapper._animating) return;

    const dx = e.changedTouches[0].clientX - startX;
    const dy = e.changedTouches[0].clientY - startY;

    // Decide direction on first significant move
    if (!decided && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
      decided = true;
      isHorizontal = Math.abs(dx) > Math.abs(dy);
    }

    if (!isHorizontal) {
      // Vertical: cancel swipe, let scroll happen
      if (decided) swiping = false;
      return;
    }

    e.preventDefault();

    // Determine if this direction is allowed
    const movingLeft = dx < 0;
    const movingRight = dx > 0;
    const hasTarget = (movingLeft && nextUrl) || (movingRight && prevUrl);

    // Apply resistance when swiping toward a dead end
    const effectiveDx = hasTarget ? dx : dx * RESISTANCE;

    const progress = Math.min(Math.abs(effectiveDx) / wrapper.offsetWidth, 1);
    const scale = 1 - progress * 0.05;
    const opacity = 1 - progress * 0.3;

    wrapper.style.transform = `translateX(${effectiveDx}px) scale(${scale})`;
    wrapper.style.opacity = opacity;
  }, { passive: false });

  wrapper.addEventListener("touchend", (e) => {
    if (!swiping || wrapper._animating) return;
    swiping = false;

    const dx = e.changedTouches[0].clientX - startX;
    const movingLeft = dx < 0;
    const movingRight = dx > 0;
    const hasTarget = (movingLeft && nextUrl) || (movingRight && prevUrl);
    const effectiveDx = hasTarget ? dx : dx * RESISTANCE;

    wrapper.style.transition = "transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), opacity 0.3s ease";

    if (Math.abs(effectiveDx) >= THRESHOLD) {
      if (hasTarget) {
        // Swipe off-screen then navigate
        wrapper._animating = true;
        wrapper._swiped = true;
        const offscreen = movingLeft ? "-110%" : "110%";
        const targetUrl = movingLeft ? nextUrl : prevUrl;
        wrapper.style.transform = `translateX(${offscreen}) scale(0.9)`;
        wrapper.style.opacity = "0";
        setTimeout(() => { window.location.href = targetUrl; }, 300);
      } else {
        // Dead end: snap back then shake
        wrapper.style.transform = "translateX(0) scale(1)";
        wrapper.style.opacity = "1";
        wrapper.addEventListener("transitionend", function onSnap() {
          wrapper.removeEventListener("transitionend", onSnap);
          wrapper.classList.add("photo-detail-shake");
          wrapper.addEventListener("animationend", function onShake() {
            wrapper.removeEventListener("animationend", onShake);
            wrapper.classList.remove("photo-detail-shake");
          });
        });
      }
    } else {
      // Not enough: snap back to center
      wrapper.style.transform = "translateX(0) scale(1)";
      wrapper.style.opacity = "1";
    }
  }, { passive: true });
});

// Show bottom nav bar on scroll
document.addEventListener("DOMContentLoaded", () => {
  const bottomNav = document.querySelector(".bottom-nav");
  if (!bottomNav) return;

  let ticking = false;
  window.addEventListener("scroll", () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        bottomNav.classList.toggle("is-visible", window.scrollY > 60);
        ticking = false;
      });
      ticking = true;
    }
  });
});

// Confirm upload finishes and return to the gallery
window.confirmUploads = function () {
  const albumSelect = document.getElementById("album-select");
  const albumId = albumSelect ? albumSelect.value : "";
  if (albumId) {
    window.location.href = "/albums/" + albumId + "/";
  } else {
    window.location.href = "/albums/";
  }
};

// Set up Drag & Drop for uploads
document.addEventListener("DOMContentLoaded", () => {
  initDragAndDrop();
});

function initDragAndDrop() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const progressContainer = document.getElementById("progress-container");
  const progressItems = document.getElementById("progress-items");

  if (!dropzone || !fileInput) return;

  let dragActive = false;

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(
      eventName,
      (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragActive = true;
        dropzone.classList.add("dragover");
      },
      false,
    );
  });

  ["dragleave"].forEach((eventName) => {
    dropzone.addEventListener(
      eventName,
      (e) => {
        e.preventDefault();
        e.stopPropagation();
        dragActive = false;
        dropzone.classList.remove("dragover");
      },
      false,
    );
  });

  dropzone.addEventListener(
    "drop",
    async (e) => {
      e.preventDefault();
      e.stopPropagation();
      dragActive = false;
      dropzone.classList.remove("dragover");
      handleFiles(e.dataTransfer.files);
    },
    false,
  );

  dropzone.addEventListener("click", () => {
    if (dragActive) return;
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    handleFiles(fileInput.files);
  });

  function handleFiles(files) {
    if (files.length === 0) return;

    dropzone.style.display = "none";
    progressContainer.style.display = "block";

    const progressTitle = document.getElementById("progress-status-title");
    if (progressTitle) {
      progressTitle.textContent = `Uploading ${files.length} photo(s)...`;
    }

    const filesArray = Array.from(files);
    const MAX_CONCURRENT = 4;
    let successCount = 0;
    let lastErrorText = "";

    const itemElements = filesArray.map((file, index) => {
      const itemId = `upload-item-${Date.now()}-${index}`;
      const itemHtml = `
                <div class="upload-progress-item" id="${itemId}">
                    <div style="flex-grow: 1; margin-right: 1rem;">
                        <div class="flex-container space-between" style="font-weight: bold;">
                            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 250px;">${file.name}</span>
                            <span class="progress-pct" style="color: var(--neon-cyan);">0%</span>
                        </div>
                        <div class="progress-bar-wrapper">
                            <div class="progress-bar" style="width: 0%;"></div>
                        </div>
                    </div>
                </div>
            `;
      progressItems.insertAdjacentHTML("beforeend", itemHtml);
      return progressItems.lastElementChild;
    });

    function uploadOne(index) {
      return new Promise((resolve) => {
        uploadFile(filesArray[index], itemElements[index], (success, errorText) => {
          if (success) successCount++;
          if (errorText && !lastErrorText) lastErrorText = errorText;
          resolve();
        });
      });
    }

    async function uploadAll() {
      let next = 0;

      function startNext() {
        if (next >= filesArray.length) return Promise.resolve();
        const index = next++;
        return uploadOne(index).then(startNext);
      }

      const workers = Array.from({ length: Math.min(MAX_CONCURRENT, filesArray.length) }, () => startNext());
      await Promise.all(workers);

      setTimeout(() => {
        progressContainer.style.display = "none";

        if (successCount === filesArray.length) {
          window.confirmUploads();
        } else {
          const completeMessage = document.getElementById(
            "upload-complete-message",
          );
          const completeText = document.getElementById(
            "upload-complete-text",
          );
          const completeError = document.getElementById(
            "upload-complete-error",
          );

          if (completeError && lastErrorText) {
            completeError.textContent = "Server response: " + lastErrorText;
            completeError.style.display = "block";
          }
          if (completeText) {
            if (successCount === 0) {
              completeText.textContent = `Upload failed for all ${filesArray.length} photo(s).`;
            } else {
              completeText.textContent = `Successfully processed and added ${successCount} of ${filesArray.length} photo(s) to the event library.`;
            }
          }
          if (completeMessage) {
            completeMessage.style.display = "block";
          }
        }
      }, 500);
    }

    uploadAll();
  }

  function getCsrfToken() {
    const headersAttr = document
      .querySelector("body")
      .getAttribute("hx-headers");
    if (headersAttr) {
      try {
        return JSON.parse(headersAttr)["X-CSRFToken"];
      } catch (e) {
        console.error("Error parsing CSRF token from hx-headers:", e);
      }
    }
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function uploadFile(file, itemElement, onComplete) {
    if (!itemElement) {
      onComplete(false, "");
      return;
    }

    const progressBar = itemElement.querySelector(".progress-bar");
    const progressPct = itemElement.querySelector(".progress-pct");

    function doUpload(fileToUpload) {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append("photos", fileToUpload);
      const albumSelect = document.getElementById("album-select");
      if (albumSelect && albumSelect.value) {
        formData.append("album", albumSelect.value);
      }

      xhr.open("POST", "/photos/upload/", true);
      xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable && e.total > 0) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          progressBar.style.width = percentComplete + "%";
          progressPct.textContent = percentComplete + "%";
        }
      });

      xhr.addEventListener("readystatechange", () => {
        if (xhr.readyState === XMLHttpRequest.DONE) {
          let success = false;
          if (xhr.status >= 200 && xhr.status < 300) {
            progressBar.style.width = "100%";
            progressBar.style.backgroundColor = "var(--neon-cyan)";
            progressBar.style.boxShadow = "0 0 8px var(--neon-cyan)";
            progressPct.textContent = "Done";
            progressPct.style.color = "var(--neon-cyan)";
            success = true;
          } else {
            progressBar.style.backgroundColor = "var(--neon-pink)";
            progressPct.textContent = "Error";
            progressPct.style.color = "var(--neon-pink)";
          }
          onComplete(success, xhr.status >= 400 ? xhr.responseText : "");
        }
      });

      xhr.send(formData);
    }

    if (file.size === 0) {
      const reader = new FileReader();
      reader.onload = () => {
        const blob = new Blob([reader.result], {
          type: file.type || "application/octet-stream",
        });
        const resolved = new File([blob], file.name, {
          type: file.type || "application/octet-stream",
        });
        doUpload(resolved);
      };
      reader.onerror = () => {
        console.error(
          "FileReader could not read",
          file.name,
          "- falling back to original",
        );
        doUpload(file);
      };
      reader.readAsArrayBuffer(file);
    } else {
      doUpload(file);
    }
  }
}
