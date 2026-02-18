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

window.programBowings = function programBowings(
  programId,
  pieces = [],
  stringInstruments = [],
  initialChecklist = null
) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;
  const stringInstrumentSet = new Set(stringInstruments || []);

  return {
    programId,
    pieces,
    completed: Boolean(
      initialChecklist?.bowings_completed ?? initialChecklist?.bowings_completed_on
    ),
    deliverySent: Boolean(
      initialChecklist?.delivery_sent ?? initialChecklist?.delivery_sent_on
    ),
    saving: false,
    saveError: null,
    openPieceIds: [],
    pieceStates: {},
    tagifyInstances: new Map(),
    rootEl: null,
    init() {
      this.rootEl = this.$el;
      this.syncPieceStates();

      if (!this._bowingsRefreshHandler) {
        this._bowingsRefreshHandler = () => {
          this.refreshOpenPieces();
        };
        window.addEventListener("part-assets:refresh", this._bowingsRefreshHandler);
      }
      if (!this._bowingsTabShowListener) {
        this._bowingsTabShowListener = () => {
          this.reloadPieces();
        };
        window.addEventListener("bowings-tab:show", this._bowingsTabShowListener);
      }

      // Always preload bowings for all pieces; accordion remains collapsed until user opens.
      this.fetchAllBowings();
    },
    syncPieceStates() {
      const pieceIds = new Set(this.pieces.map((piece) => piece.id));
      Object.keys(this.pieceStates).forEach((pieceId) => {
        if (!pieceIds.has(pieceId)) {
          delete this.pieceStates[pieceId];
        }
      });
      this.pieces.forEach((piece) => {
        if (!this.pieceStates[piece.id]) {
          this.pieceStates[piece.id] = {
            loading: false,
            loaded: false,
            error: null,
            partAssets: [],
            stringPartOptions: [],
          };
        }
      });
      this.openPieceIds = this.openPieceIds.filter((pieceId) => pieceIds.has(pieceId));
    },
    async reloadPieces() {
      try {
        const response = await fetch(`/api/programs/${this.programId}/pieces`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch program pieces");
        }
        this.pieces = await response.json();
        this.syncPieceStates();
        await this.fetchAllBowings();
        this.$nextTick(() => {
          this.openPieceIds.forEach((pieceId) => this.initPieceTagify(pieceId));
          window.initializeFilePonds?.(this.rootEl);
        });
      } catch (error) {
        this.saveError = "Unable to refresh bowings pieces right now.";
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
          body: JSON.stringify({ bowings_completed: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark bowings as completed");
        }
        this.completed = true;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark bowings as completed right now.";
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
          body: JSON.stringify({ bowings_completed: false }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark bowings as incomplete");
        }
        this.completed = false;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark bowings as incomplete right now.";
      } finally {
        this.saving = false;
      }
    },
    pieceState(pieceId) {
      if (!this.pieceStates[pieceId]) {
        this.pieceStates[pieceId] = {
          loading: false,
          loaded: false,
          error: null,
          partAssets: [],
          stringPartOptions: [],
        };
      }
      return this.pieceStates[pieceId];
    },
    isPieceOpen(pieceId) {
      return this.openPieceIds.includes(pieceId);
    },
    async togglePiece(pieceId) {
      if (this.isPieceOpen(pieceId)) {
        this.openPieceIds = this.openPieceIds.filter((id) => id !== pieceId);
        return;
      }
      this.openPieceIds = [...this.openPieceIds, pieceId];
      this.$nextTick(() => {
        this.initPieceTagify(pieceId);
        window.initializeFilePonds?.(this.rootEl);
      });
    },
    summaryText(pieceId) {
      const state = this.pieceState(pieceId);
      if (state.loading) {
        return "Loading...";
      }
      if (state.stringPartOptions.length === 0) {
        return "No string parts";
      }
      const required = this.getRequiredStringPartCount(pieceId);
      const bowed = this.getBowedStringPartCount(pieceId);
      const missing = this.getMissingStringPartCount(pieceId);
      if (missing > 0) {
        return `${missing} missing (${bowed}/${required} bowed)`;
      }
      return `Complete (${bowed}/${required} bowed)`;
    },
    async fetchAllBowings() {
      await Promise.all(this.pieces.map((piece) => this.fetchBowings(piece.id)));
    },
    hasStringInstrument(part) {
      if (!part?.instruments?.length) {
        return false;
      }
      return part.instruments.some((entry) => {
        const instrumentName = entry?.instrument?.name;
        return instrumentName && stringInstrumentSet.has(instrumentName);
      });
    },
    getStringPartOptions(payload) {
      const partsById = new Map();
      (payload.missing_parts || []).forEach((part) => {
        partsById.set(part.id, part);
      });
      (payload.part_assets || []).forEach((partAsset) => {
        (partAsset.parts || []).forEach((part) => {
          partsById.set(part.id, part);
        });
      });

      return (payload.part_options || []).filter((option) => {
        const part = partsById.get(option.id);
        return this.hasStringInstrument(part);
      });
    },
    getRequiredStringPartCount(pieceId) {
      const state = this.pieceState(pieceId);
      return state.stringPartOptions.length;
    },
    getBowedStringPartCount(pieceId) {
      const state = this.pieceState(pieceId);
      const validPartIds = new Set((state.stringPartOptions || []).map((option) => option.id));
      const bowedPartIds = new Set();
      (state.partAssets || []).forEach((partAsset) => {
        (partAsset.parts || []).forEach((part) => {
          if (validPartIds.has(part.id)) {
            bowedPartIds.add(part.id);
          }
        });
      });
      return bowedPartIds.size;
    },
    getMissingStringPartCount(pieceId) {
      const required = this.getRequiredStringPartCount(pieceId);
      const bowed = this.getBowedStringPartCount(pieceId);
      return Math.max(required - bowed, 0);
    },
    isPieceInvalid(pieceId) {
      const required = this.getRequiredStringPartCount(pieceId);
      if (required === 0) {
        return false;
      }
      return this.getMissingStringPartCount(pieceId) > 0;
    },
    async fetchBowings(pieceId) {
      const state = this.pieceState(pieceId);
      if (state.loading) {
        return;
      }

      state.loading = true;
      state.error = null;
      try {
        const response = await fetch(`/api/pieces/${pieceId}/assets?asset_type=Bowing`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch bowings");
        }
        const payload = await response.json();
        state.partAssets = payload.part_assets || [];
        state.stringPartOptions = this.getStringPartOptions(payload);
        state.loaded = true;
      } catch (error) {
        state.error = "Unable to load bowings for this piece.";
      } finally {
        state.loading = false;
      }
    },
    refreshOpenPieces() {
      this.openPieceIds.forEach(async (pieceId) => {
        await this.fetchBowings(pieceId);
        this.$nextTick(() => this.initPieceTagify(pieceId));
      });
    },
    initPieceTagify(pieceId) {
      const scope = this.rootEl || this.$el || document;
      const state = this.pieceState(pieceId);
      const selector = `.bowing-part-asset[data-piece-id="${pieceId}"]`;
      const inputs = scope.querySelectorAll(selector);

      inputs.forEach((input) => {
        if (input._tagify || input.dataset.tagifyInitialized === "true") {
          return;
        }

        const initialParts = JSON.parse(input.dataset.initial || "[]") || [];
        const initial = initialParts.map((part) => ({
          value: part.display_name,
          id: part.id,
        }));
        const whitelist = (state.stringPartOptions || []).map((option) => ({
          value: option.value,
          id: option.id,
        }));
        const partAssetId = input.dataset.partAssetId;

        const tagify = new Tagify(input, {
          whitelist,
          enforceWhitelist: true,
          dropdown: { enabled: 0, closeOnSelect: false },
          originalInputValueFormat: (valuesArr) =>
            valuesArr.map((tag) => tag.value).join(","),
        });

        tagify.loadOriginalValues(initial);
        input.dataset.tagifyInitialized = "true";
        this.tagifyInstances.set(input, tagify);

        let debouncedSave = null;
        const saveParts = () => {
          const partIds = tagify.value.map((entry) => entry.id).filter(Boolean);
          fetch(`/api/pieces/${pieceId}/asset/${partAssetId}`, {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ part_ids: partIds }),
          })
            .then((response) => {
              if (!response.ok) {
                throw new Error("Failed to update bowing parts");
              }
              return response.json();
            })
            .then((updatedPartAsset) => {
              const index = state.partAssets.findIndex((asset) => asset.id === partAssetId);
              if (index === -1) {
                return;
              }
              const resolvedParts =
                updatedPartAsset?.parts ||
                tagify.value
                  .map((tag) => {
                    const option = state.stringPartOptions.find((entry) => entry.id === tag.id);
                    return option ? { id: option.id, display_name: option.value } : null;
                  })
                  .filter(Boolean);
              state.partAssets[index] = {
                ...state.partAssets[index],
                parts: resolvedParts,
              };
            })
            .catch(() => {
              state.error = "Unable to update bowing parts.";
            });
        };

        tagify.on("change", () => {
          clearTimeout(debouncedSave);
          debouncedSave = setTimeout(saveParts, 300);
        });
      });
    },
    async deletePartAsset(pieceId, partAssetId) {
      const state = this.pieceState(pieceId);
      try {
        const response = await fetch(`/api/pieces/${pieceId}/asset/${partAssetId}`, {
          method: "DELETE",
          credentials: "same-origin",
          headers: {
            "X-CSRFToken": csrfToken(),
          },
        });
        if (!response.ok) {
          throw new Error("Failed to delete bowing");
        }
      } catch (error) {
        state.error = "Unable to delete this bowing.";
      } finally {
        await this.fetchBowings(pieceId);
        this.$nextTick(() => {
          this.initPieceTagify(pieceId);
          window.initializeFilePonds?.(this.rootEl);
        });
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
        this.results = await response.json();
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
    async loadPrincipals() {
      if (this.completed) {
        return;
      }
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/musicians`,
          {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ principals: true }),
          }
        );
        if (!response.ok) {
          throw new Error("Failed to load principals");
        }
        this.fetchRoster();
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
        const response = await fetch(
          `/api/programs/${this.programId}/musicians`,
          {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ core_members: true }),
          }
        );
        if (!response.ok) {
          throw new Error("Failed to load core members");
        }
        this.fetchRoster();
      } catch (error) {
        this.saveError = "Unable to load core members right now.";
      } finally {
        this.saving = false;
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
          if (this.completed) {
            return;
          }
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
      return this.roster.some((member) => member.musician_id === musician.id);
    },
    async addMusician(musician) {
      if (this.completed) {
        return;
      }
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
        this.roster = await response.json();
        this.resetRosterTagify();
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

window.programOverrides = function programOverrides(programId, initialChecklist = null) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    completed: Boolean(
      initialChecklist?.overrides_completed ?? initialChecklist?.overrides_completed_on
    ),
    deliverySent: Boolean(
      initialChecklist?.delivery_sent ?? initialChecklist?.delivery_sent_on
    ),
    saving: false,
    saveError: null,
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
          body: JSON.stringify({ overrides_completed: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark overrides as completed");
        }
        this.completed = true;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark overrides as completed right now.";
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
          body: JSON.stringify({ overrides_completed: false }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark overrides as incomplete");
        }
        this.completed = false;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark overrides as incomplete right now.";
      } finally {
        this.saving = false;
      }
    },
  };
};

window.programAssignments = function programAssignments(
  programId,
  initialChecklist = null
) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    programId,
    checklist: initialChecklist || {},
    statusPayload: {
      pieces: [],
      principals: [],
      roster_musicians: [],
      summary: { total_parts: 0, assigned_parts: 0, all_assigned: false },
    },
    loadingStatus: false,
    sending: false,
    completingAssignments: false,
    savingAssignmentPartId: null,
    showSendModal: false,
    saveError: null,
    openPieceIds: [],
    principalStatusSectionOpen: true,
    tagifyInstances: new Map(),
    rootEl: null,
    init() {
      this.rootEl = this.$el;
      if (!this._checklistRefreshListener) {
        this._checklistRefreshListener = () => {
          this.fetchChecklist();
          this.fetchAssignments();
        };
        window.addEventListener(
          "program-checklist:refresh",
          this._checklistRefreshListener
        );
      }
      if (!this._assignmentsTabShowListener) {
        this._assignmentsTabShowListener = () => {
          this.fetchChecklist();
          this.fetchAssignments();
        };
        window.addEventListener(
          "assignments-tab:show",
          this._assignmentsTabShowListener
        );
      }
      this.fetchChecklist();
      this.fetchAssignments();
    },
    musicianLabel(musician) {
      const fullName = `${musician.first_name} ${musician.last_name}`.trim();
      return `${fullName} (${musician.email})`;
    },
    getRosterMusicianById(musicianId) {
      return (this.statusPayload?.roster_musicians || []).find((m) => m.id === musicianId);
    },
    getPartById(partId) {
      for (const piece of this.statusPayload?.pieces || []) {
        for (const part of piece.parts || []) {
          if (part.id === partId) return part;
        }
      }
      return null;
    },
    assignmentValue(part) {
      const assignedId = part?.assigned_musician?.id || null;
      const musician = this.getRosterMusicianById(assignedId);
      if (!musician) return [];
      return [{ value: this.musicianLabel(musician), id: musician.id }];
    },
    whitelist() {
      return (this.statusPayload?.roster_musicians || []).map((musician) => ({
        value: this.musicianLabel(musician),
        id: musician.id,
      }));
    },
    resetTagify() {
      this.tagifyInstances.forEach((instance, input) => {
        instance.destroy();
        if (input?.dataset) {
          delete input.dataset.tagifyInitialized;
        }
      });
      this.tagifyInstances.clear();
      this.$nextTick(() => this.initTagify());
    },
    initTagify() {
      const scope = this.rootEl || this.$root || this.$el;
      if (!scope) return;
      const inputs = scope.querySelectorAll(".librarian-assignment-input");
      const whitelist = this.whitelist();
      inputs.forEach((input) => {
        if (input._tagify || input.dataset.tagifyInitialized === "true") return;
        const partId = input.dataset.partId;
        const initial = this.assignmentValue(this.getPartById(partId));
        const tagify = new Tagify(input, {
          whitelist,
          enforceWhitelist: true,
          maxTags: 1,
          dropdown: { enabled: 0, closeOnSelect: true },
          originalInputValueFormat: (valuesArr) => valuesArr.map((tag) => tag.value).join(","),
        });
        tagify.loadOriginalValues(initial);
        input.dataset.tagifyInitialized = "true";
        this.tagifyInstances.set(input, tagify);

        const save = (musicianId) => this.savePartAssignment(partId, musicianId);
        tagify.on("add", (event) => save(event?.detail?.data?.id || null));
        tagify.on("remove", () => save(null));
      });
    },
    isStepComplete(completedOnField) {
      return Boolean(this.checklist?.[completedOnField]);
    },
    get assignmentsSent() {
      if (this.isStepComplete("assignments_sent_on")) {
        return true;
      }
      const principals = this.statusPayload?.principals || [];
      return principals.some((principal) => principal.status && principal.status !== "Not Sent");
    },
    get canSendToPrincipals() {
      return (
        this.isStepComplete("pieces_completed_on") &&
        this.isStepComplete("roster_completed_on") &&
        this.isStepComplete("bowings_completed_on") &&
        this.isStepComplete("overrides_completed_on") &&
        !this.assignmentsSent
      );
    },
    get canMarkAsCompleted() {
      return (
        this.isStepComplete("pieces_completed_on") &&
        this.isStepComplete("roster_completed_on") &&
        this.isStepComplete("bowings_completed_on") &&
        this.isStepComplete("overrides_completed_on") &&
        this.assignmentsSent &&
        !this.isStepComplete("assignments_completed_on")
      );
    },
    get canActuallyCompleteAssignments() {
      const summary = this.statusPayload?.summary || {};
      return Boolean(summary.all_assigned);
    },
    isPieceOpen(pieceId) {
      return this.openPieceIds.includes(pieceId);
    },
    togglePiece(pieceId) {
      if (this.isPieceOpen(pieceId)) {
        this.openPieceIds = this.openPieceIds.filter((id) => id !== pieceId);
        return;
      }
      this.openPieceIds = [...this.openPieceIds, pieceId];
    },
    togglePrincipalStatusSection() {
      this.principalStatusSectionOpen = !this.principalStatusSectionOpen;
    },
    formatDateTime(value) {
      if (!value) {
        return "-";
      }
      const parsedDate = new Date(value);
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
    openSendModal() {
      this.saveError = null;
      this.showSendModal = true;
    },
    closeSendModal() {
      if (this.sending) {
        return;
      }
      this.showSendModal = false;
    },
    async confirmSendToPrincipals() {
      this.sending = true;
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
          body: JSON.stringify({ assignments_sent: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to send assignments to principals");
        }
        this.checklist = await response.json();
        this.showSendModal = false;
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to send assignments to principals right now.";
      } finally {
        this.sending = false;
      }
    },
    async markAssignmentsAsCompleted() {
      if (!this.canActuallyCompleteAssignments) {
        return;
      }
      this.completingAssignments = true;
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
          body: JSON.stringify({ assignments_completed: true }),
        });
        if (!response.ok) {
          throw new Error("Failed to mark assignments as completed");
        }
        this.checklist = await response.json();
        window.dispatchEvent(new Event("program-checklist:refresh"));
      } catch (error) {
        this.saveError = "Unable to mark assignments as completed right now.";
      } finally {
        this.completingAssignments = false;
      }
    },
    async fetchChecklist() {
      try {
        const response = await fetch(`/api/programs/${this.programId}/checklist`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch checklist");
        }
        this.checklist = await response.json();
      } catch (error) {
        this.saveError = "Unable to refresh assignments state right now.";
      }
    },
    async fetchAssignments() {
      if (this.loadingStatus) {
        return;
      }
      this.loadingStatus = true;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/assignments`,
          {
            headers: { Accept: "application/json" },
          }
        );
        if (!response.ok) {
          throw new Error("Failed to fetch assignments status");
        }
        this.statusPayload = await response.json();
        this.resetTagify();
      } catch (error) {
        this.saveError = "Unable to refresh assignment statuses right now.";
      } finally {
        this.loadingStatus = false;
      }
    },
    async savePartAssignment(partId, musicianId) {
      this.savingAssignmentPartId = partId;
      this.saveError = null;
      try {
        const response = await fetch(
          `/api/programs/${this.programId}/assignments/part/${partId}`,
          {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
              "Accept": "application/json",
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ musician_id: musicianId }),
          }
        );
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data?.detail || "Failed to save assignment");
        }
        this.statusPayload = await response.json();
      } catch (error) {
        this.saveError = error?.message || "Unable to save assignment right now.";
      } finally {
        this.savingAssignmentPartId = null;
      }
    },
  };
};

window.magicDelivery = function magicDelivery(token, initialPayload = null) {
  return {
    token,
    payload: initialPayload || { pieces: [] },
    downloading: false,
    saveError: null,
    successMessage: null,
    triggerDownloads(files) {
      files.forEach((file) => {
        const link = document.createElement("a");
        link.href = file.url;
        link.download = file.filename || "";
        link.rel = "noopener";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      });
    },
    async requestDownloads(pieceId = null) {
      const suffix = pieceId
        ? `/downloads/piece/${pieceId}`
        : "/downloads";
      const response = await fetch(`/api/magic/${this.token}/delivery${suffix}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        throw new Error("Failed to prepare download links");
      }
      return response.json();
    },
    async downloadAll() {
      this.downloading = true;
      this.saveError = null;
      this.successMessage = null;
      try {
        const payload = await this.requestDownloads();
        const files = payload?.files || [];
        if (!files.length) {
          this.saveError = "No downloadable files are currently available.";
          return;
        }
        this.triggerDownloads(files);
        this.successMessage = "Download started. If some files were blocked, use piece links below.";
      } catch (error) {
        this.saveError = error?.message || "Unable to start downloads.";
      } finally {
        this.downloading = false;
      }
    },
    async downloadPiece(pieceId) {
      this.downloading = true;
      this.saveError = null;
      this.successMessage = null;
      try {
        const payload = await this.requestDownloads(pieceId);
        const files = payload?.files || [];
        if (!files.length) {
          this.saveError = "No downloadable files are available for this piece.";
          return;
        }
        this.triggerDownloads(files);
        this.successMessage = "Piece download started.";
      } catch (error) {
        this.saveError = error?.message || "Unable to start piece downloads.";
      } finally {
        this.downloading = false;
      }
    },
  };
};

window.magicAssignments = function magicAssignments(token, initialPayload = null) {
  return {
    token,
    payload: initialPayload || { pieces: [], eligible_musicians: [], all_assigned: false },
    loading: false,
    saving: false,
    saveError: null,
    confirmOpen: false,
    confirming: false,
    confirmed: false,
    tagifyInstances: new Map(),
    rootEl: null,
    init() {
      this.rootEl = this.$el;
      this.$nextTick(() => this.initTagify());
    },
    get allAssigned() {
      return Boolean(this.payload?.all_assigned);
    },
    musicianLabel(musician) {
      const fullName = `${musician.first_name} ${musician.last_name}`.trim();
      return `${fullName} (${musician.email})`;
    },
    getMusicianById(musicianId) {
      return (this.payload?.eligible_musicians || []).find((m) => m.id === musicianId);
    },
    assignmentValue(part) {
      const musician = this.getMusicianById(part.assigned_musician_id);
      if (!musician) return [];
      return [{ value: this.musicianLabel(musician), id: musician.id }];
    },
    getPartById(partId) {
      for (const piece of this.payload?.pieces || []) {
        for (const part of piece.parts || []) {
          if (part.id === partId) return part;
        }
      }
      return null;
    },
    whitelist() {
      return (this.payload?.eligible_musicians || []).map((musician) => ({
        value: this.musicianLabel(musician),
        id: musician.id,
      }));
    },
    resetTagify() {
      this.tagifyInstances.forEach((instance, input) => {
        instance.destroy();
        if (input?.dataset) {
          delete input.dataset.tagifyInitialized;
        }
      });
      this.tagifyInstances.clear();
      this.$nextTick(() => this.initTagify());
    },
    initTagify() {
      const scope = this.rootEl || this.$root || this.$el;
      if (!scope) return;
      const inputs = scope.querySelectorAll(".assignment-musician-input");
      const whitelist = this.whitelist();
      inputs.forEach((input) => {
        if (input._tagify || input.dataset.tagifyInitialized === "true") return;
        const partId = input.dataset.partId;
        const initial = this.assignmentValue(this.getPartById(partId));
        const tagify = new Tagify(input, {
          whitelist,
          enforceWhitelist: true,
          maxTags: 1,
          dropdown: { enabled: 0, closeOnSelect: true },
          originalInputValueFormat: (valuesArr) => valuesArr.map((tag) => tag.value).join(","),
        });
        tagify.loadOriginalValues(initial);
        input.dataset.tagifyInitialized = "true";
        this.tagifyInstances.set(input, tagify);

        const save = (musicianId) => this.savePartAssignment(partId, musicianId);
        tagify.on("add", (event) => save(event?.detail?.data?.id || null));
        tagify.on("remove", () => save(null));
      });
    },
    async refresh() {
      this.loading = true;
      this.saveError = null;
      try {
        const response = await fetch(`/api/magic/${this.token}/assignments`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to refresh assignments");
        }
        this.payload = await response.json();
        this.resetTagify();
      } catch (error) {
        this.saveError = "Unable to refresh assignments right now.";
      } finally {
        this.loading = false;
      }
    },
    async savePartAssignment(partId, musicianId) {
      this.saving = true;
      this.saveError = null;
      try {
        const response = await fetch(`/api/magic/${this.token}/assignments/part/${partId}`, {
          method: "PATCH",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ musician_id: musicianId }),
        });
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data?.detail || "Failed to save assignment");
        }
        this.payload = await response.json();
      } catch (error) {
        this.saveError = error?.message || "Unable to save assignment.";
      } finally {
        this.saving = false;
      }
    },
    openConfirm() {
      if (!this.allAssigned) return;
      this.confirmOpen = true;
    },
    closeConfirm() {
      if (this.confirming) return;
      this.confirmOpen = false;
    },
    async confirmAssignments() {
      this.confirming = true;
      this.saveError = null;
      try {
        const response = await fetch(`/api/magic/${this.token}/assignments/confirm`, {
          method: "POST",
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data?.detail || "Failed to confirm assignments");
        }
        this.confirmed = true;
        this.confirmOpen = false;
      } catch (error) {
        this.saveError = error?.message || "Unable to confirm assignments.";
      } finally {
        this.confirming = false;
      }
    },
  };
};
