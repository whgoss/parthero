export function programOverrides(programId, initialChecklist = null) {
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

