import * as FilePond from "filepond";
import "filepond/dist/filepond.min.css";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

// Automatically turn any <input type="file" class="filepond"> into a FilePond instance
document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll('input[type="file"].filepond');

  inputs.forEach((input) => {
    const pieceId = input.dataset.pieceId; // <input ... data-piece-id="{{ piece.id }}">

    FilePond.create(input, {
      server: {
        process: (fieldName, file, metadata, load, error, progress, abort) => {
          // 1) Create part, get presigned URL
          fetch(`/api/piece/${pieceId}/part`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ filename: file.name }),
          })
            .then((res) => res.json())
            .then((data) => {
              const xhr = new XMLHttpRequest();
              xhr.open("PUT", data.upload_url, true);
              xhr.upload.onprogress = (e) => {
                if (e.lengthComputable)
                  progress(e.lengthComputable, e.loaded, e.total);
              };
              xhr.onload = () => (xhr.status >= 200 && xhr.status < 300)
                ? load(data.id)
                : error("Upload failed");
              xhr.onerror = () => error("Upload error");
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

// Automatically turn any <input type="file" class="filepond"> into a FilePond instance
// document.addEventListener("DOMContentLoaded", () => {
//   const inputs = document.querySelectorAll('input[type="file"].filepond');

//   inputs.forEach((input) => {
//     FilePond.create(input, {
//       allowMultiple: true,
//     });
//   });
// });

export { FilePond };
