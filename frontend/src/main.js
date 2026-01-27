import "./styles.css";
import "htmx.org"
import "@yaireo/tagify/dist/tagify.css";
import "filepond/dist/filepond.min.css";
import * as FilePond from "filepond";
import Tagify from "@yaireo/tagify";
import FilePondPluginFileValidateType from "filepond-plugin-file-validate-type";

FilePond.registerPlugin(FilePondPluginFileValidateType);

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

function updatePartAsset(pieceId, partAssetDto, newStatus) {
  if (!pieceId || !partAssetDto) return;
  const partIds = partAssetDto.parts.map(part => part.id);
  return fetch(`/api/piece/${pieceId}/asset/${partAssetDto.id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ status: newStatus, part_ids: partIds }),
  }).then(async (res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
      requestPartsRefresh({ immediate: false });
    return res;
  }).catch((err) => {
    console.error("Failed to update part asset status", err);
  });
}

let refreshTimer = null;
let scrollAnchorId = null;


function requestPartsRefresh({ anchorId = null, immediate = false } = {}) {
  const partsEl = document.getElementById("parts");
  if (!partsEl) return;
  if (anchorId) partsEl.dataset.scrollAnchor = anchorId;
  if (immediate) {
    document.body.dispatchEvent(new Event("refreshParts"));
    return;
  } 

  clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => {
      document.body.dispatchEvent(new Event("refreshParts"));
    }, 500);
}

document.body.addEventListener("htmx:afterRequest", (e) => {
  if (e.detail.successful && e.detail.requestConfig?.verb === "delete") {
    requestPartsRefresh({ immediate: true });
  }
});

document.body.addEventListener("click", (e) => {
  const a = e.target.closest("[data-scroll-anchor]");
  if (!a) return;

  // Store it on #parts so the next refresh can use it
  requestPartsRefresh({ anchorId: a.dataset.scrollAnchor });
});

document.addEventListener("htmx:afterSwap", (e) => {
  if (e.detail.target?.id !== "parts") return;

  const parts = e.detail.target;
  const anchorId = parts.dataset.scrollAnchor;

  const el = anchorId ? document.getElementById(anchorId) : null;
  (el || parts.querySelector(".part-asset-row:last-child"))
  ?.scrollIntoView({ block: el ? "center" : "end" });

  delete parts.dataset.scrollAnchor; // clear after using it

  // Automatically turn any <input class="instrument-sections"> into a Tagify instance
  document.querySelectorAll(".part-asset").forEach((instrumentElem) => {
    const whitelist = JSON.parse(instrumentElem.dataset.options || "[]");
    const initial = JSON.parse(instrumentElem.dataset.initial || "[]");
    const partId = instrumentElem.dataset.partId;
    const pieceId = instrumentElem.dataset.pieceId;
    const partAssetId = instrumentElem.dataset.partAssetId;

    const tagify = new Tagify(instrumentElem, {
      whitelist,
      enforceWhitelist: true,
      dropdown: { enabled: 0, closeOnSelect: false },
      originalInputValueFormat: (valuesArr) => valuesArr.map((tag) => tag.value).join(","),
    });

    tagify.loadOriginalValues(initial);

    // Perform PATCH updates
    let t = null;
    const save = () => {
      // For part instruments
      if (pieceId && partAssetId) {
        const partIds = tagify.value.map(tag => tag.id);
        fetch(`/api/piece/${pieceId}/asset/${partAssetId}`, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
          },
          body: JSON.stringify({ part_ids: partIds }),
        })
      }
    }

    tagify.on("change", (e) => {
      clearTimeout(t);
      t = setTimeout(save, 300);
    });
  });
})

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".instruments").forEach((instrumentElem) => {
    const initialScriptId = instrumentElem.dataset.initialId;
    const whitelistScriptId = instrumentElem.dataset.optionsId;
    const whitelist = JSON.parse(document.getElementById(whitelistScriptId).textContent);
    const initial = JSON.parse(document.getElementById(initialScriptId).textContent);
    // const whitelist = JSON.parse(instrumentElem.dataset.options || "[]");
    // const initial = JSON.parse(instrumentElem.dataset.initial || "[]");
    console.log(initial);

    const tagify = new Tagify(instrumentElem, {
      whitelist,
      enforceWhitelist: true,
      dropdown: { enabled: 0, closeOnSelect: false },
      originalInputValueFormat: (valuesArr) => valuesArr.map((t) => t.value).join(","),
    });

    tagify.loadOriginalValues(initial);
  });

  // FilePond - Automatically turn any <input type="file" class="filepond"> into a FilePond instance
  const inputs = document.querySelectorAll('input[type="file"].filepond');

  inputs.forEach((input) => {
    const pieceId = input.dataset.pieceId; // <input ... data-piece-id="{{ piece.id }}">
    console.log("HEllo", pieceId);

    FilePond.create(input, {
      allowMultiple: true,
      allowDrop: true,
      allowRemove: false,
      allowRevert: false,
      credits: null,
      maxFiles: null,
      dropOnPage: false,
      labelIdle: 'Drag & Drop Files to Upload Parts (or <span class="filepond--label-action"> Browse</span>)',
      acceptedFileTypes: ['application/pdf'],
      fileValidateTypeLabelExpectedTypes: "Only PDF files are allowed",
      server: {
        process: (fieldName, file, metadata, load, error, progress, abort) => {
          let partAssetDto = null;
          let xhr = null;


          // 1) Determine part for filename
          fetch(`/api/piece/${pieceId}/asset`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ filename: file.name }),
          })
            .then((res) => res.json())
            .then((data) => {
              partAssetDto = data;
              xhr = new XMLHttpRequest();
              xhr.open("PUT", data.upload_url, true);
              xhr.upload.onprogress = (e) => {
                if (e.lengthComputable)
                  progress(e.lengthComputable, e.loaded, e.total);
              };

              // 2) Update part status after upload
              xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                  updatePartAsset(pieceId, partAssetDto, "Uploaded");
                  load(partAssetDto.id);
                } else {
                  updatePartAsset(pieceId, partAssetDto, "Failed");
                  error("Upload failed");
                }
              };

              xhr.onerror = () => {
                updatePartAsset(pieceId, partAssetDto, "Aborted");
                error("Upload error");
              };

              xhr.send(file);
            })
            .catch(() => error("Could not create part"));

          return {
            abort: () => {
              // user cancelled
              abort();
            },
          };
        },
      },
    });
  });
});

export { FilePond };