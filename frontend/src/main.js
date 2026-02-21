import "./styles.css";
import "./littlebigtable";
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
  const partIds = (partAssetDto.parts || []).map((part) => part.id);
  return fetch(`/api/pieces/${pieceId}/asset/${partAssetDto.id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ status: newStatus, part_ids: partIds }),
  }).then(async (res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    window.dispatchEvent(new Event("part-assets:refresh"));
    return res;
  }).catch((err) => {
    console.error("Failed to update part asset status", err);
  });
}

function initializeFilePonds(scope = document) {
  const inputs = scope.querySelectorAll?.('input[type="file"].filepond') || [];

  inputs.forEach((input) => {
    if (input.dataset.filepondInitialized === "true") {
      return;
    }

    const pieceId = input.dataset.pieceId;
    const assetType = input.dataset.assetType || "Clean";
    const labelIdle =
      input.dataset.filepondLabel ||
      'Drag & Drop Files to Upload Parts (or <span class="filepond--label-action"> Browse</span>)';

    FilePond.create(input, {
      allowMultiple: true,
      allowDrop: true,
      allowRemove: false,
      allowRevert: false,
      credits: null,
      maxFiles: null,
      dropOnPage: false,
      labelIdle,
      acceptedFileTypes: ["application/pdf"],
      fileValidateTypeLabelExpectedTypes: "Only PDF files are allowed",
      server: {
        process: (fieldName, file, metadata, load, error, progress, abort) => {
          let partAssetDto = null;
          let xhr = null;

          fetch(`/api/pieces/${pieceId}/asset`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ filename: file.name, asset_type: assetType }),
          })
            .then((res) => res.json())
            .then((data) => {
              partAssetDto = data;
              xhr = new XMLHttpRequest();
              xhr.open("PUT", data.upload_url, true);
              xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                  progress(e.lengthComputable, e.loaded, e.total);
                }
              };

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
              abort();
            },
          };
        },
      },
      onprocessfile: (err, file) => {
        if (err || !file) return;
        setTimeout(() => {
          const pond = FilePond.find(input);
          pond?.removeFile(file.id);
        }, 2000);
      },
    });

    input.dataset.filepondInitialized = "true";
  });
}

window.initializeFilePonds = initializeFilePonds;

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".instrument").forEach((instrumentElem) => {
    const initialScriptId = instrumentElem.dataset.initialId;
    const whitelistScriptId = instrumentElem.dataset.optionsId;
    const whitelist = JSON.parse(document.getElementById(whitelistScriptId).textContent);
    const initial = JSON.parse(document.getElementById(initialScriptId).textContent);

    const tagify = new Tagify(instrumentElem, {
      whitelist,
      enforceWhitelist: true,
      maxTags: 1,
      dropdown: { enabled: 0, closeOnSelect: true },
      originalInputValueFormat: (valuesArr) => valuesArr.map((t) => t.value).join(","),
    });

    tagify.loadOriginalValues(initial);
  });

  document.querySelectorAll(".instruments").forEach((instrumentElem) => {
    const initialScriptId = instrumentElem.dataset.initialId;
    const whitelistScriptId = instrumentElem.dataset.optionsId;
    const whitelist = JSON.parse(document.getElementById(whitelistScriptId).textContent);
    const initial = JSON.parse(document.getElementById(initialScriptId).textContent);

    const tagify = new Tagify(instrumentElem, {
      whitelist,
      enforceWhitelist: true,
      dropdown: { enabled: 0, closeOnSelect: false },
      originalInputValueFormat: (valuesArr) => valuesArr.map((t) => t.value).join(","),
    });

    tagify.loadOriginalValues(initial);
  });

  initializeFilePonds(document);
});
