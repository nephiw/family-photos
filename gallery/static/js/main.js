// Synthwave Photo Gallery JavaScript

// Hide brand title on scroll
document.addEventListener("DOMContentLoaded", () => {
  const header = document.querySelector(".header-container");
  if (!header) return;

  let ticking = false;
  window.addEventListener("scroll", () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        header.classList.toggle("header-scrolled", window.scrollY > 60);
        ticking = false;
      });
      ticking = true;
    }
  });
});

// Confirm upload finishes and return to the gallery
window.confirmUploads = function () {
  window.location.href = "/photos/";
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
    const CONCURRENCY = 4;
    const timestamp = Date.now();
    let currentIndex = 0;
    let completedCount = 0;
    let successCount = 0;

    filesArray.forEach((file, index) => {
      const itemId = `upload-item-${timestamp}-${index}`;
      const itemHtml = `
                <div class="upload-progress-item" id="${itemId}">
                    <div style="flex-grow: 1; margin-right: 1rem;">
                        <div style="display: flex; justify-content: space-between; font-weight: bold;">
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
    });

    function uploadNext() {
      if (currentIndex >= filesArray.length) return;

      const index = currentIndex++;
      const file = filesArray[index];
      const itemElement = document.getElementById(
        `upload-item-${timestamp}-${index}`,
      );
      if (!itemElement) return;

      uploadFile(file, itemElement, (success) => {
        completedCount++;
        if (success) successCount++;

        if (completedCount === filesArray.length) {
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

              if (completeText) {
                completeText.textContent = `Successfully processed and added ${successCount} of ${filesArray.length} photo(s) to the event library.`;
              }
              if (completeMessage) {
                completeMessage.style.display = "block";
              }
            }
          }, 500);
        } else {
          uploadNext();
        }
      });
    }

    for (let i = 0; i < Math.min(CONCURRENCY, filesArray.length); i++) {
      uploadNext();
    }
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
      onComplete(false);
      return;
    }

    const progressBar = itemElement.querySelector(".progress-bar");
    const progressPct = itemElement.querySelector(".progress-pct");

    function doUpload(fileToUpload) {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append("photos", fileToUpload);

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
            console.error(
              `Upload error status ${xhr.status}: ${xhr.responseText}`,
            );
          }
          onComplete(success);
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
