import "./styles.css";
import flatpickr from "flatpickr";
import "flatpickr/dist/flatpickr.min.css";

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".date-picker").forEach((datePickerElem) => {
    [...document.styleSheets].forEach((s, i) => {
        try {
        void s.cssRules;
        } catch (e) {
        console.warn("BLOCKED cssRules:", i, s.href || "[inline]", e.name);
        }
        });

    console.log("HI!");
    console.log(datePickerElem);
    flatpickr(datePickerElem);
  })
});
