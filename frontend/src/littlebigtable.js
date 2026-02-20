export function littleBIGtable(options = {}) {
  return {
    settings: {
      url: null,
      key_prefix: "lBt",
      limit: 25,
      multisort: false,
      args: {
        limit: "limit",
        offset: "offset",
        search: "search",
        sort: "sort",
      },
      messages: {
        loading: "Loading...",
        failed: "Loading failed",
        summary: "rows",
      },
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "littleBIGtable",
      },
      formatters: {},
    },
    meta: {
      loading: false,
      status: null,
    },
    params: {
      limit: 25,
      offset: 0,
      search: null,
      total: 0,
    },
    rows: [],
    sort: {},
    init() {
      // Apply caller options first so key_prefix/limit overrides are respected.
      this.settings = { ...this.settings, ...options };
      if (!this.settings.limit) {
        this.settings.limit = 25;
      }
      const defaultLimit = parseInt(this.settings.limit, 25);
      const savedLimit = parseInt(
        localStorage.getItem(`${this.settings.key_prefix}.limit`),
        10
      );
      if (!Number.isNaN(savedLimit) && savedLimit >= 1 && savedLimit <= 100) {
        this.params.limit = savedLimit;
      } else {
        this.params.limit = defaultLimit;
      }
      this.fetch();
    },
    async fetch() {
      if (!this.settings.url) {
        this.meta.status = "Missing endpoint url";
        return;
      }
      this.meta.loading = true;
      this.meta.status = this.settings.messages.loading;
      try {
        const response = await fetch(
          `${this.settings.url}${this.getUrlParams()}`,
          { headers: this.settings.headers }
        );
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        this.params.total = json.total || 0;
        this.rows = [];
        for (const row of json.data || []) {
          this.addRow(row);
        }
        this.meta.status = this.getSummary(this.settings.messages.summary);
      } catch (error) {
        this.meta.status = this.settings.messages.failed;
        console.error("littleBIGtable fetch failed", error);
      } finally {
        this.meta.loading = false;
      }
    },
    addRow(data) {
      const row = {};
      for (const key in data) {
        if (typeof this.settings.formatters[key] === "function") {
          row[key] = this.settings.formatters[key](data[key], data);
        } else {
          row[key] = data[key];
        }
      }
      for (const key in this.settings.formatters) {
        if (!Object.prototype.hasOwnProperty.call(row, key)) {
          row[key] = this.settings.formatters[key](data[key], data);
        }
      }
      this.rows.push(row);
    },
    getUrlParams() {
      const args = this.settings.args;
      let str = `?${args.limit}=${this.params.limit}&${args.offset}=${this.params.offset}`;
      if (this.params.search) {
        str += `&${args.search}=${encodeURIComponent(this.params.search)}`;
      }
      let sort = null;
      for (const col in this.sort) {
        sort = `${col}:${this.sort[col]}`;
      }
      if (sort) {
        str += `&${args.sort}=${encodeURIComponent(sort)}`;
      }
      return str;
    },
    getCurrentPage() {
      if (this.params.offset === 0) return 1;
      return parseInt(this.params.offset / this.params.limit + 1, 10);
    },
    getTotalPages() {
      return parseInt(Math.ceil(this.params.total / this.params.limit), 10) || 1;
    },
    getFirstPageOffset() {
      return 0;
    },
    getPrevPageOffset() {
      return Math.max((this.getCurrentPage() - 2) * this.params.limit, 0);
    },
    getNextPageOffset() {
      return this.getCurrentPage() * this.params.limit;
    },
    getLastPageOffset() {
      return Math.max((this.getTotalPages() - 1) * this.params.limit, 0);
    },
    getFirstDisplayedRow() {
      return this.params.total === 0 ? 0 : this.params.offset + 1;
    },
    getLastDisplayedRow() {
      const value = this.params.offset + this.params.limit;
      return value > this.params.total ? this.params.total : value;
    },
    getSummary(type = "rows", name = "results") {
      if (!this.rows.length) return "No results";
      if (type.toLowerCase() === "pages") {
        return `Showing page <strong>${this.getCurrentPage()}</strong> of <strong>${this.getTotalPages()}</strong>`;
      }
      return `Showing <strong>${this.getFirstDisplayedRow()}</strong> to <strong>${this.getLastDisplayedRow()}</strong> of <strong>${this.params.total}</strong> ${name}`;
    },
    setLimit() {
      const parsed = parseInt(this.params.limit, 10);
      this.params.limit = Number.isNaN(parsed) ? this.settings.limit : parsed;
      this.params.limit = Math.min(Math.max(this.params.limit, 1), 100);
      this.params.offset = 0;
      localStorage.setItem(`${this.settings.key_prefix}.limit`, this.params.limit);
      this.fetch();
    },
    goFirstPage() {
      this.params.offset = this.getFirstPageOffset();
      this.fetch();
    },
    goLastPage() {
      this.params.offset = this.getLastPageOffset();
      this.fetch();
    },
    goNextPage() {
      if (this.getCurrentPage() >= this.getTotalPages()) return;
      this.params.offset = this.getNextPageOffset();
      this.fetch();
    },
    goPrevPage() {
      if (this.getCurrentPage() <= 1) return;
      this.params.offset = this.getPrevPageOffset();
      this.fetch();
    },
    doSearch() {
      this.params.offset = 0;
      this.fetch();
    },
  };
}

window.littleBIGtable = littleBIGtable;
