import Tagify from "@yaireo/tagify";

export function programAssignments(
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


export function magicDelivery(token, initialPayload = null) {
  return {
    token,
    payload: initialPayload || { pieces: [] },
    downloadingFileId: null,
    saveError: null,
    successMessage: null,
    triggerDownload(file) {
      const link = document.createElement("a");
      link.href = file.url;
      link.download = file.filename || "";
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
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
    async downloadFile(pieceId, fileId) {
      this.downloadingFileId = fileId;
      this.saveError = null;
      this.successMessage = null;
      try {
        const payload = await this.requestDownloads(pieceId);
        const file = (payload?.files || []).find((item) => item.id === fileId);
        if (!file) {
          this.saveError = "That file is not currently available for download.";
          return;
        }
        this.triggerDownload(file);
        this.successMessage = "Download started.";
      } catch (error) {
        this.saveError = error?.message || "Unable to start download.";
      } finally {
        this.downloadingFileId = null;
      }
    },
  };
};


export function magicAssignments(token, initialPayload = null) {
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
