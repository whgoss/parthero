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

window.programPieceSearch = function programPieceSearch(programId, initialPieces = []) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    title: "",
    composer: "",
    results: [],
    selectedPieces: initialPieces,
    loading: false,
    error: null,
    hasSearched: false,
    saving: false,
    saveError: null,
    async search() {
      this.loading = true;
      this.error = null;
      this.hasSearched = false;

      const params = new URLSearchParams();
      if (this.title.trim()) {
        params.append("title", this.title.trim());
      }
      if (this.composer.trim()) {
        params.append("composer", this.composer.trim());
      }

      if (!params.toString()) {
        this.results = [];
        this.loading = false;
        return;
      }

      const url = `/api/pieces/search?${params.toString()}`;
      try {
        const response = await fetch(url, {
          headers: { "Accept": "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to search pieces");
        }
        this.results = await response.json();
      } catch (error) {
        this.error = "Unable to fetch pieces right now.";
        this.results = [];
      } finally {
        this.loading = false;
        this.hasSearched = true;
      }
    },
    isSelected(piece) {
      return this.selectedPieces.some((selected) => selected.id === piece.id);
    },
    async addPiece(piece) {
      if (this.isSelected(piece)) {
        this.scrollToSelected();
        return;
      }
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/program/${this.programId}/pieces/${piece.id}`,
          {
            method: "PUT",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "X-CSRFToken": csrfToken(),
            },
          }
        );
        if (!response.ok) {
          throw new Error("Failed to add piece");
        }
        this.selectedPieces = await response.json();
        this.scrollToSelected();
      } catch (error) {
        this.saveError = "Unable to add piece right now.";
      } finally {
        this.saving = false;
      }
    },
    async removePiece(piece) {
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/program/${this.programId}/pieces/${piece.id}`,
          {
            method: "DELETE",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "X-CSRFToken": csrfToken(),
            },
          }
        );
        if (!response.ok) {
          throw new Error("Failed to remove piece");
        }
        this.selectedPieces = await response.json();
      } catch (error) {
        this.saveError = "Unable to remove piece right now.";
      } finally {
        this.saving = false;
      }
    },
    scrollToSelected() {
      this.$nextTick(() => {
        this.$refs.selectedPieces?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    },
  };
};

Alpine.start()
