import "./styles.css";
import Alpine from "alpinejs";

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

Alpine.start();
