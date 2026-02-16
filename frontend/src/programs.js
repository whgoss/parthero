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
          const isValidTab =
            parsed?.tab === "pieces" || parsed?.tab === "bowings" || parsed?.tab === "roster";
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
    },
    setTab(tab) {
      this.activeTab = tab;
      window.sessionStorage.setItem(
        "program-active-tab",
        JSON.stringify({ tab, ts: Date.now() })
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
    },
  };
};

window.programBowings = function programBowings(programId, pieces = [], stringInstruments = []) {
  const csrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;
  const stringInstrumentSet = new Set(stringInstruments || []);

  return {
    programId,
    pieces,
    openPieceIds: [],
    pieceStates: {},
    tagifyInstances: new Map(),
    rootEl: null,
    init() {
      this.rootEl = this.$el;
      this.pieces.forEach((piece) => {
        this.pieceStates[piece.id] = {
          loading: false,
          loaded: false,
          error: null,
          partAssets: [],
          stringPartOptions: [],
        };
      });

      if (!this._bowingsRefreshHandler) {
        this._bowingsRefreshHandler = () => {
          this.refreshOpenPieces();
        };
        window.addEventListener("part-assets:refresh", this._bowingsRefreshHandler);
      }

      // Always preload bowings for all pieces; accordion remains collapsed until user opens.
      this.fetchAllBowings();
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
      } catch (error) {
        this.saveError = "Unable to mark as completed right now.";
      } finally {
        this.saving = false;
      }
    },
    async markAsIncomplete() {
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

window.programRoster = function programRoster(programId) {
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
    async loadPrincipals() {
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
