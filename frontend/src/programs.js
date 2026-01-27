import "./styles.css";
import flatpickr from "flatpickr";
import "flatpickr/dist/flatpickr.min.css";
import Alpine from 'alpinejs'

window.Alpine = Alpine

const buildPickerOptions = (input) => ({
  enableTime: true,
  dateFormat: "Y-m-d H:i",
  time_24hr: false,
  altInput: true,
  altFormat: "M j, Y h:i K",
  onChange: (_selectedDates, dateStr) => {
    // Ensure the original input (submitted to Django) is updated.
    input.value = dateStr;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  },
});

window.performanceDates = function performanceDates() {
  return {
    init() {
      // init flatpickr on any existing inputs Django rendered
      this.initPickers(document);
    },
    add() {
      const totalInput = document.querySelector('input[name="perf-TOTAL_FORMS"]');
      const index = parseInt(totalInput.value, 10);

      // Clone template HTML and replace __prefix__ with the next index
      const html = this.$refs.emptyRow.innerHTML.replaceAll("__prefix__", index);

      // Insert into DOM
      const container = document.getElementById("performance-rows");
      container.insertAdjacentHTML("beforeend", html);

      // Increment TOTAL_FORMS
      totalInput.value = index + 1;

      // Initialize flatpickr only on the newly-added row
      const newRow = container.lastElementChild;
      this.initPickers(newRow, true);
    },
    remove(event) {
      const row = event.target.closest(".perf-row");
      if (!row) return;

      const deleteInput = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (deleteInput) {
        deleteInput.checked = true;
        return;
      }

      row.remove();
    },
    initPickers(element, openOnInit = false) {
      const inputs = element.matches?.(".date-picker")
        ? [element]
        : Array.from(element.querySelectorAll?.(".date-picker") || []);

      inputs.forEach((input) => {
        if (input._flatpickr) return;
        const instance = flatpickr(input, buildPickerOptions(input));
        if (instance.altInput && input.placeholder) {
          instance.altInput.placeholder = input.placeholder;
          // Keep styling similar without re-triggering the picker.
          instance.altInput.className = input.className.replace("date-picker", "").trim();
        }
        if (openOnInit) {
          instance.open();
        }
      });
    },
  }
}

Alpine.start()
