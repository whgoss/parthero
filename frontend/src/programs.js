import "./styles.css";
import "@yaireo/tagify/dist/tagify.css";
import flatpickr from "flatpickr";
import "flatpickr/dist/flatpickr.min.css";
import Tagify from "@yaireo/tagify";
import { programBowings } from "./bowings";
import { programOverrides } from "./overrides";
import {
  programAssignments,
  magicDelivery,
  magicAssignments,
} from "./assignments";

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

window.programTabs = function programTabs(programId, initialChecklist = null) {
  return {
    programId,
    checklist: initialChecklist || {},
    activeTab: "pieces",
    isStepComplete(completedOnField) {
      return Boolean(this.checklist?.[completedOnField]);
    },
    isTabEnabled(tab) {
      if (tab === "pieces" || tab === "roster") {
        return true;
      }
      if (tab === "bowings") {
        return this.isStepComplete("pieces_completed_on");
      }
      if (tab === "overrides") {
        return this.isStepComplete("pieces_completed_on");
      }
      if (tab === "assignments") {
        const piecesComplete = this.isStepComplete("pieces_completed_on");
        const rosterComplete = this.isStepComplete("roster_completed_on");
        const bowingsComplete = this.isStepComplete("bowings_completed_on");
        const overridesComplete = this.isStepComplete("overrides_completed_on");
        return piecesComplete && rosterComplete && bowingsComplete && overridesComplete;
      }
      return false;
    },
    tabButtonClass(tab) {
      if (!this.isTabEnabled(tab)) {
        return "border-transparent bg-slate-100 text-slate-400 cursor-not-allowed";
      }
      if (this.activeTab === tab) {
        return "-mb-px border-slate-200 bg-white text-slate-900";
      }
      return "border-transparent bg-slate-100 text-slate-600 hover:bg-slate-200/70 hover:text-slate-800 cursor-pointer";
    },
    async refreshChecklist() {
      try {
        const response = await fetch(`/api/programs/${this.programId}/checklist`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          return;
        }
        this.checklist = await response.json();
      } catch (error) {
        return;
      }
      if (!this.isTabEnabled(this.activeTab)) {
        this.setTab("pieces");
      }
    },
    init() {
      if (!this._checklistRefreshListener) {
        this._checklistRefreshListener = () => {
          this.refreshChecklist();
        };
        window.addEventListener(
          "program-checklist:refresh",
          this._checklistRefreshListener
        );
      }

      const saved = window.sessionStorage.getItem("program-active-tab");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          const isSameProgram = parsed?.program_id === this.programId;
          const isValidTab =
            parsed?.tab === "pieces" ||
            parsed?.tab === "bowings" ||
            parsed?.tab === "roster" ||
            parsed?.tab === "overrides" ||
            parsed?.tab === "assignments";
          const isFresh = parsed?.ts && Date.now() - parsed.ts < 10 * 60 * 1000;
          if (isSameProgram && isValidTab && isFresh && this.isTabEnabled(parsed.tab)) {
            this.activeTab = parsed.tab;
          } else {
            window.sessionStorage.removeItem("program-active-tab");
          }
        } catch (error) {
          window.sessionStorage.removeItem("program-active-tab");
        }
      }
      if (this.activeTab === "bowings") {
        setTimeout(() => {
          window.dispatchEvent(new Event("bowings-tab:show"));
        }, 0);
      }
      if (this.activeTab === "roster") {
        setTimeout(() => {
          window.dispatchEvent(new Event("roster-tab:show"));
        }, 0);
      }
      if (this.activeTab === "assignments") {
        setTimeout(() => {
          window.dispatchEvent(new Event("assignments-tab:show"));
        }, 0);
      }
    },
    setTab(tab) {
      if (!this.isTabEnabled(tab)) {
        return;
      }
      this.activeTab = tab;
      window.sessionStorage.setItem(
        "program-active-tab",
        JSON.stringify({ program_id: this.programId, tab, ts: Date.now() })
      );
      if (tab === "bowings") {
        setTimeout(() => {
          window.dispatchEvent(new Event("bowings-tab:show"));
        }, 0);
      }
      if (tab === "roster") {
        setTimeout(() => {
          window.dispatchEvent(new Event("roster-tab:show"));
        }, 0);
      }
      if (tab === "assignments") {
        setTimeout(() => {
          window.dispatchEvent(new Event("assignments-tab:show"));
        }, 0);
      }
    },
  };
};

window.programChecklist = function programChecklist(
  programId,
  initialChecklist = null
) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    checklist: initialChecklist || {},
    loading: false,
    error: null,
    showDeliveryModal: false,
    deliverySaving: false,
    deliveryError: null,
    init() {
      if (!this._checklistRefreshListener) {
        this._checklistRefreshListener = () => {
          this.fetchChecklist();
        };
        window.addEventListener(
          "program-checklist:refresh",
          this._checklistRefreshListener
        );
      }
    },
    isStepComplete(completedOnField) {
      return Boolean(this.checklist?.[completedOnField]);
    },
    statusLabel(completedOnField) {
      return this.isStepComplete(completedOnField) ? "✅ Complete" : "⏳ Pending";
    },
    completedOnLabel(completedOnField) {
      const completedOn = this.checklist?.[completedOnField];
      if (!completedOn) {
        return "-";
      }
      const parsedDate = new Date(completedOn);
      if (Number.isNaN(parsedDate.getTime())) {
        return "-";
      }
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(parsedDate);
    },
    completedByLabel(completedByField) {
      const completedBy = this.checklist?.[completedByField];
      if (!completedBy) {
        return "-";
      }
      const firstName = completedBy.first_name || "";
      const lastName = completedBy.last_name || "";
      const fullName = `${firstName} ${lastName}`.trim();
      return fullName || "-";
    },
    get completed() {
      return (
        this.isStepComplete("pieces_completed_on") &&
        this.isStepComplete("roster_completed_on") &&
        this.isStepComplete("overrides_completed_on") &&
        this.isStepComplete("bowings_completed_on") &&
        this.isStepComplete("assignments_completed_on") &&
        this.isStepComplete("delivery_sent_on")
      );
    },
    get canDeliverParts() {
      return (
        this.isStepComplete("assignments_completed_on") &&
        !this.isStepComplete("delivery_sent_on")
      );
    },
    openDeliveryModal() {
      this.deliveryError = null;
      this.showDeliveryModal = true;
    },
    closeDeliveryModal() {
      if (this.deliverySaving) {
        return;
      }
      this.showDeliveryModal = false;
    },
    async confirmDeliverySent() {
      this.deliverySaving = true;
      this.deliveryError = null;
      try {
        const response = await fetch(`/api/programs/${this.programId}/checklist`, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify({ delivery_sent: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to send delivery");
        }
        this.checklist = await response.json();
        this.showDeliveryModal = false;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.deliveryError = "Unable to send delivery right now.";
      } finally {
        this.deliverySaving = false;
      }
    },
    async fetchChecklist() {
      if (this.loading) {
        return;
      }
      this.loading = true;
      this.error = null;
      try {
        const response = await fetch(`/api/programs/${this.programId}/checklist`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch checklist");
        }
        this.checklist = await response.json();
      } catch (error) {
        this.error = "Unable to refresh checklist right now.";
      } finally {
        this.loading = false;
      }
    },
  };
};

window.programPieces = function programPieces(
  programId,
  initialPieces = [],
  initialChecklist = null
) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    title: "",
    composer: "",
    results: [],
    selectedPieces: initialPieces,
    completed: Boolean(
      initialChecklist?.pieces_completed ?? initialChecklist?.pieces_completed_on
    ),
    deliverySent: Boolean(
      initialChecklist?.delivery_sent ?? initialChecklist?.delivery_sent_on
    ),
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
        const payload = await response.json();
        this.results = Array.isArray(payload) ? payload : (payload?.data || []);
      } catch (error) {
        this.error = "Unable to fetch pieces right now.";
        this.results = [];
      } finally {
        this.loading = false;
        this.hasSearched = true;
      }
    },
    clearSearch() {
      this.title = "";
      this.composer = "";
      this.results = [];
      this.error = null;
      this.hasSearched = false;
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
          `/api/programs/${this.programId}/pieces/${piece.id}`,
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
          `/api/programs/${this.programId}/pieces/${piece.id}`,
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
    async markAsComplete() {
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/checklist`,
          {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ pieces_completed: true }),
          }
        );
        if (!response.ok) {
          throw new Error("Failed to mark as completed");
        }
        this.completed = true;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark as completed right now.";
      } finally {
        this.saving = false;
      }
    },
    async markAsIncomplete() {
      if (this.deliverySent) {
        return;
      }
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/checklist`,
          {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ pieces_completed: false }),
          }
        );
        if (!response.ok) {
          throw new Error("Failed to mark as completed");
        }
        this.completed = false;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark as completed right now.";
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

window.programRoster = function programRoster(programId, initialChecklist = null) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    completed: Boolean(
      initialChecklist?.roster_completed ?? initialChecklist?.roster_completed_on
    ),
    deliverySent: Boolean(
      initialChecklist?.delivery_sent ?? initialChecklist?.delivery_sent_on
    ),
    name: "",
    instrument: "",
    results: [],
    rosterInstruments: {},
    tagifyInstances: new Map(),
    isActive: false,
    rootEl: null,
    loadingSearch: false,
    error: null,
    hasSearched: false,
    saving: false,
    saveError: null,
    initProgramRoster() {
      this.rootEl = this.$el;
      if (!this._wrappedRosterFetch && typeof this.fetch === "function") {
        const originalFetch = this.fetch.bind(this);
        this.fetch = async (...args) => {
          await originalFetch(...args);
          if (this.isActive) {
            this.resetRosterTagify();
          }
        };
        this._wrappedRosterFetch = true;
      }
      if (!this._rosterTabListener) {
        this._rosterTabListener = () => {
          this.isActive = true;
          this.resetRosterTagify();
        };
        window.addEventListener("roster-tab:show", this._rosterTabListener);
      }
      this.isActive = this.$el && this.$el.offsetParent !== null;
    },
    async refreshRosterTable() {
      await this.fetch();
      this.$nextTick(() => this.resetRosterTagify());
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
          if (this.completed) {
            return;
          }
          const selectedInstrument = event?.detail?.data?.value;
          if (selectedInstrument) {
            this.updateMusicianInstrument(programMusicianId, selectedInstrument, method);
          }
        };

        tagify.on("add", (event) => onTagChange(event, "PUT"));
        tagify.on("remove", (event) => onTagChange(event, "DELETE"));
      });
    },
    async loadPrincipals() {
      if (this.completed) {
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
          body: JSON.stringify({ principals: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to load principals");
        }
        await this.refreshRosterTable();
      } catch (error) {
        this.saveError = "Unable to load principals right now.";
      } finally {
        this.saving = false;
      }
    },
    async loadCoreMembers() {
      if (this.completed) {
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
          body: JSON.stringify({ core_members: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to load core members");
        }
        await this.refreshRosterTable();
      } catch (error) {
        this.saveError = "Unable to load core members right now.";
      } finally {
        this.saving = false;
      }
    },
    async updateMusicianInstrument(programMusicianId, instrument, method) {
      if (this.completed) {
        return;
      }
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
        await this.refreshRosterTable();
      } catch (error) {
        this.saveError = "Unable to update musician instruments.";
      }
    },
    async search() {
      this.loadingSearch = true;
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
        this.loadingSearch = false;
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
        const payload = await response.json();
        this.results = Array.isArray(payload) ? payload : (payload?.data || []);
      } catch (error) {
        this.error = "Unable to fetch musicians right now.";
        this.results = [];
      } finally {
        this.loadingSearch = false;
        this.hasSearched = true;
      }
    },
    clearSearch() {
      this.name = "";
      this.instrument = "";
      this.results = [];
      this.error = null;
      this.hasSearched = false;
      this.saveError = null;
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
      return (this.rows || []).some((member) => member.musician_id === musician.id);
    },
    async addMusician(musician) {
      if (this.completed || this.isInRoster(musician)) {
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
        await this.refreshRosterTable();
      } catch (error) {
        this.saveError = "Unable to add musician right now.";
      } finally {
        this.saving = false;
      }
    },
    async removeMusician(musician) {
      if (this.completed) {
        return;
      }
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
        await this.refreshRosterTable();
      } catch (error) {
        this.saveError = "Unable to remove musician right now.";
      } finally {
        this.saving = false;
      }
    },
    async markAsComplete() {
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(`/api/programs/${this.programId}/checklist`, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify({ roster_completed: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark roster as completed");
        }
        this.completed = true;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark roster as completed right now.";
      } finally {
        this.saving = false;
      }
    },
    async markAsIncomplete() {
      if (this.deliverySent) {
        return;
      }
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(`/api/programs/${this.programId}/checklist`, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken(),
          },
          body: JSON.stringify({ roster_completed: false }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark roster as incomplete");
        }
        this.completed = false;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark roster as incomplete right now.";
      } finally {
        this.saving = false;
      }
    },
  };
};


window.programBowings = programBowings;
window.programOverrides = programOverrides;
window.programAssignments = programAssignments;
window.magicDelivery = magicDelivery;
window.magicAssignments = magicAssignments;
