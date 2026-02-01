import "./styles.css";
import Alpine from "alpinejs";
import Tagify from "@yaireo/tagify";

window.Alpine = Alpine;

window.domoPieceSearch = function domoPieceSearch() {
  return {
    title: "",
    composer: "",
    results: [],
    loading: false,
    error: null,
    hasSearched: false,
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

      const url = `/api/domo/search?${params.toString()}`;
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
    resultHref(piece) {
      return `/create_piece?domo_id=${encodeURIComponent(piece.id)}`;
    },
  };
};

window.partAssets = function partAssets(pieceId) {
  const csrfToken = () =>
    document.querySelector('meta[name="csrf-token"]')?.content;

  return {
    pieceId,
    partAssets: [],
    missingParts: [],
    partOptions: [],
    loading: false,
    error: null,
    tagifyInstances: new Map(),
    refreshTimer: null,
    rootEl: null,
    init() {
      this.rootEl = this.$el;
      this.requestRefresh(true);
      if (!this._refreshHandler) {
        this._refreshHandler = () => this.requestRefresh(false);
        window.addEventListener("part-assets:refresh", this._refreshHandler);
      }
    },
    requestRefresh(immediate = false) {
      if (immediate) {
        this.fetchAssets();
        return;
      }
      clearTimeout(this.refreshTimer);
      this.refreshTimer = setTimeout(() => {
        this.fetchAssets();
      }, 400);
    },
    async fetchAssets() {
      if (this.loading) {
        return;
      }

      this.loading = true;
      this.error = null;
      try {
        const response = await fetch(`/api/piece/${this.pieceId}/assets`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch part assets");
        }
        const data = await response.json();
        this.partAssets = data.part_assets || [];
        this.missingParts = data.missing_parts || [];
        this.partOptions = data.part_options || [];
      } catch (error) {
        this.error = "Unable to load parts.";
      } finally {
        this.loading = false;
        this.destroyTagify();
        this.$nextTick(() => this.initTagify());
      }
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
    initTagify() {
      const scope = this.rootEl || this.$root || this.$el;
      if (!scope) return;
      scope.querySelectorAll(".part-asset").forEach((input) => {
        if (input._tagify || input.dataset.tagifyInitialized === "true") return;
        const initial = JSON.parse(input.dataset.initial || "[]").map((part) => ({
          value: part.display_name,
          id: part.id,
        }));
        const whitelist = JSON.parse(input.dataset.options || "[]").map((part) => ({
          value: part.display_name ?? part.value ?? part.name ?? "",
          id: part.id,
        }));
        const partAssetId = input.dataset.partAssetId;
        const pieceId = input.dataset.pieceId;

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

        let timeoutId = null;
        const save = () => {
          if (!pieceId || !partAssetId) return;
          const partIds = tagify.value
            .map((tag) => tag.id)
            .filter((id) => id != null);
          fetch(`/api/piece/${pieceId}/asset/${partAssetId}`, {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken(),
            },
            body: JSON.stringify({ part_ids: partIds }),
          });
        };

        tagify.on("change", () => {
          clearTimeout(timeoutId);
          timeoutId = setTimeout(save, 300);
        });
      });
    },
    async deletePartAsset(partAssetId) {
      if (!partAssetId) return;
      try {
        const response = await fetch(
          `/api/piece/${this.pieceId}/asset/${partAssetId}`,
          {
            method: "DELETE",
            credentials: "same-origin",
            headers: {
              "X-CSRFToken": csrfToken(),
            },
          }
        );
        if (!response.ok) {
          throw new Error("Failed to delete part asset");
        }
        
      } catch (error) {
        this.error = "Unable to delete that part asset.";
      } finally {
        this.fetchAssets();
      }
    },
  };
};

Alpine.start();
