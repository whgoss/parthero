import "./styles.css";
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

function updatePart(editionId, dto, newStatus) {
  if (!dto) return;

  const updatedDto = { ...dto, status: newStatus };

  return fetch(`/api/edition/${editionId}/part/${dto.id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(updatedDto),
  }).catch((err) => {
    console.error("Failed to update part status", err);
  });
}

// Automatically turn any <input type="file" class="filepond"> into a FilePond instance
document.addEventListener("DOMContentLoaded", () => {
  // Tagify
  const instrumentElem = document.querySelector("#instrument-sections");
  if (instrumentElem) {
    const whitelist = JSON.parse(instrumentElem.dataset.options || "[]");
    const initial = JSON.parse(instrumentElem.dataset.initial || "[]");

    const tagify = new Tagify(instrumentElem, {
      whitelist: whitelist,
      enforceWhitelist: true,
      dropdown: {
        enabled: 0,
        closeOnSelect: false,
      },
      originalInputValueFormat: (valuesArr) =>
        valuesArr.map((t) => t.value).join(","),
    });

    // Just in case there's any leftover value from the DOM, clear it
    tagify.removeAllTags();

    if (initial.length) {
      tagify.addTags(initial);
    }
  }

  // FilePond
  const inputs = document.querySelectorAll('input[type="file"].filepond');

  inputs.forEach((input) => {
    const editionId = input.dataset.editionId; // <input ... data-edition-id="{{ edition.id }}">

    FilePond.create(input, {
      allowMultiple: true,
      allowDrop: true,
      allowRemove: false,
      allowRevert: false,
      credits: null,
      maxFiles: null,
      dropOnPage: false,
      labelIdle: 'Drag & Drop to Upload Parts (or <span class="filepond--label-action"> Browse</span>)',
      acceptedFileTypes: ['application/pdf'],
      fileValidateTypeLabelExpectedTypes: "Only PDF files are allowed",
      server: {
        process: (fieldName, file, metadata, load, error, progress, abort) => {
          let partDto = null;
          let xhr = null;

          // 1) Create part, get presigned URL
          fetch(`/api/edition/${editionId}/part`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ filename: file.name }),
          })
            .then((res) => res.json())
            .then((data) => {
              partDto = data;
              xhr = new XMLHttpRequest();
              xhr.open("PUT", data.upload_url, true);
              xhr.upload.onprogress = (e) => {
                if (e.lengthComputable)
                  progress(e.lengthComputable, e.loaded, e.total);
              };

              // 2) Update part status after upload
              xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                  updatePart(editionId, partDto, "Uploaded");
                  load(partDto.id);
                } else {
                  updatePart(editionId, partDto, "Failed");
                  error("Upload failed");
                }
              };

              xhr.onerror = () => {
                updatePart(editionId, partDto, "Aborted");
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