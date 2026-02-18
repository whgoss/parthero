import Tagify from "@yaireo/tagify";

export function programBowings(
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
