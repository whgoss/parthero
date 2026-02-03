import "./styles.css";
import "@yaireo/tagify/dist/tagify.css";
import flatpickr from "flatpickr";
import "flatpickr/dist/flatpickr.min.css";
import Tagify from "@yaireo/tagify";

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

window.programTabs = function programTabs() {
  return {
    activeTab: "pieces",
    init() {
      const saved = window.sessionStorage.getItem("program-active-tab");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          const isValidTab = parsed?.tab === "pieces" || parsed?.tab === "roster";
          const isFresh = parsed?.ts && Date.now() - parsed.ts < 10 * 60 * 1000;
          if (isValidTab && isFresh) {
            this.activeTab = parsed.tab;
          } else {
            window.sessionStorage.removeItem("program-active-tab");
          }
        } catch (error) {
          window.sessionStorage.removeItem("program-active-tab");
        }
      }
      if (this.activeTab === "roster") {
        setTimeout(() => {
          window.dispatchEvent(new Event("roster-tab:show"));
        }, 0);
      }
    },
    setTab(tab) {
      this.activeTab = tab;
      window.sessionStorage.setItem(
        "program-active-tab",
        JSON.stringify({ tab, ts: Date.now() })
      );
      if (tab === "roster") {
        setTimeout(() => {
          window.dispatchEvent(new Event("roster-tab:show"));
        }, 0);
      }
    },
  };
};

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

window.programRosterSearch = function programRosterSearch(programId) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    name: "",
    instrument: "",
    results: [],
    roster: [],
    rosterInstruments: {},
    tagifyInstances: new Map(),
    isActive: false,
    rootEl: null,
    loading: false,
    error: null,
    hasSearched: false,
    saving: false,
    saveError: null,
    init() {
      this.rootEl = this.$el;
      if (!this._rosterTabListener) {
        this._rosterTabListener = () => {
          this.isActive = true;
          this.resetRosterTagify();
        };
        window.addEventListener("roster-tab:show", this._rosterTabListener);
      }
      this.isActive = this.$el && this.$el.offsetParent !== null;
      this.fetchRoster();
    },
    async fetchRoster() {
      if (this.loading) {
        return;
      }

      try {
        const response = await fetch(`/api/programs/${this.programId}/musicians`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch program roster");
        }
        this.roster = await response.json();
      } catch (error) {
        this.error = "Unable to load program roster.";
      } finally {
        this.loading = false;
        if (this.isActive) {
          this.resetRosterTagify();
        }
      }
    },
    resetRosterTagify() {
      this.destroyTagify();
      this.$nextTick(() => this.initRosterTagify());
    },
    destroyTagify() {
      this.tagifyInstances.forEach((instance, input) => {
        instance.destroy();
        if (input?.dataset) {
          delete input.dataset.tagifyInitialized;
        }
      });
      this.tagifyInstances.clear();
    },
    initRosterTagify() {
      const scope = this.rootEl || this.$el || document;
      const inputs = scope.querySelectorAll?.(".roster-instruments") || [];
      const optionsEl = document.getElementById("instrument-options");
      const whitelist = optionsEl ? JSON.parse(optionsEl.textContent) : [];
      const normalizedWhitelist = whitelist.map((value) => ({ value }));

      inputs.forEach((input) => {
        if (input._tagify || input.dataset.tagifyInitialized === "true") return;
        const tagify = new Tagify(input, {
          whitelist: normalizedWhitelist,
          enforceWhitelist: true,
          dropdown: { enabled: 0, closeOnSelect: false },
          originalInputValueFormat: (valuesArr) =>
            valuesArr.map((tag) => tag.value).join(","),
        });

        const initial = (input.dataset.initial || "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean)
          .map((value) => ({ value }));
        if (initial.length) {
          tagify.addTags(initial, true, true);
        }

        input.dataset.tagifyInitialized = "true";
        this.tagifyInstances.set(input, tagify);

        const programMusicianId = input.dataset.programMusicianId;
        if (!programMusicianId) return;

        const onTagChange = (event, method) => {
          const instrument = event?.detail?.data?.value;
          if (instrument) {
            this.updateMusicianInstrument(programMusicianId, instrument, method);
          }
        };

        tagify.on("add", (event) => onTagChange(event, "PUT"));
        tagify.on("remove", (event) => onTagChange(event, "DELETE"));
      });
    },
    async updateMusicianInstrument(programMusicianId, instrument, method) {
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/musicians/${programMusicianId}/instruments`,
          {
            method,
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ instrument }),
          }
        );
        if (!response.ok) {
          throw new Error("Failed to update musician instrument");
        }
        this.roster = await response.json();
        this.resetRosterTagify();
      } catch (error) {
        this.saveError = "Unable to update musician instruments.";
      }
    },
    async search() {
      this.loading = true;
      this.error = null;
      this.hasSearched = false;

      const params = new URLSearchParams();
      if (this.name.trim()) {
        params.append("name", this.name.trim());
      }
      if (this.instrument.trim()) {
        params.append("instrument", this.instrument.trim());
      }

      if (!params.toString()) {
        this.results = [];
        this.loading = false;
        return;
      }

      const url = `/api/musicians/search?${params.toString()}`;
      try {
        const response = await fetch(url, {
          headers: { "Accept": "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to search musicians");
        }
        this.results = await response.json();
      } catch (error) {
        this.error = "Unable to fetch musicians right now.";
        this.results = [];
      } finally {
        this.loading = false;
        this.hasSearched = true;
      }
    },
    formatInstrumentList(musician) {
      if (!musician?.instruments?.length) {
        return "";
      }
      return musician.instruments
        .map((entry) => entry.instrument)
        .filter(Boolean)
        .join(", ");
    },
    isInRoster(musician) {
      return this.roster.some((member) => member.musician_id === musician.id);
    },
    async addMusician(musician) {
      if (this.isInRoster(musician)) {
        return;
      }
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(`/api/programs/${this.programId}/musicians`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify({ musician_id: musician.id }),
        });
        if (!response.ok) {
          throw new Error("Failed to add musician");
        }
        this.roster = await response.json();
        this.resetRosterTagify();
      } catch (error) {
        this.saveError = "Unable to add musician right now.";
      } finally {
        this.saving = false;
      }
    },
    async removeMusician(musician) {
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/musicians/${musician.id}`,
          {
            method: "DELETE",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
          }
        );
        if (!response.ok) {
          throw new Error("Failed to remove musician");
        }
        this.roster = await response.json();
        this.resetRosterTagify();
      } catch (error) {
        this.saveError = "Unable to remove musician right now.";
      } finally {
        this.saving = false;
      }
    },
  };
};
