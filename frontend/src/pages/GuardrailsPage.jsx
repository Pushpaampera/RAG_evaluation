import { useCallback, useEffect, useState } from "react";
import "./GuardrailsPage.css";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const CATEGORIES = [
  "input",
  "retrieval",
  "output",
  "scope",
  "safety",
  "ingestion",
];

const EMPTY_FORM = {
  name: "",
  description: "",
  category: "input",
  rule_text: "",
  enabled: true,
};

function GuardrailsPage() {
  const [rules, setRules] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadRules = useCallback(async () => {
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/guardrails/`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load guardrails.");
      }

      setRules(data.rules || []);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  function updateField(event) {
    const { name, value, type, checked } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function openCreateForm() {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setShowForm(true);
    setError("");
    setMessage("");
  }

  function openEditForm(rule) {
    setForm({
      name: rule.name,
      description: rule.description,
      category: rule.category,
      rule_text: rule.rule_text,
      enabled: rule.enabled,
    });

    setEditingId(rule.id);
    setShowForm(true);
    setError("");
    setMessage("");
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        editingId
          ? `${API_URL}/guardrails/${editingId}`
          : `${API_URL}/guardrails/`,
        {
          method: editingId ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...form,
            name: form.name.trim(),
            description: form.description.trim(),
            rule_text: form.rule_text.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to save guardrail.");
      }

      closeForm();
      setMessage(
        editingId
          ? "Guardrail updated successfully."
          : "Guardrail created successfully."
      );

      await loadRules();
    } catch (err) {
      setError(err.message || "Unable to save guardrail.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleRule(rule) {
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/guardrails/${rule.id}/enabled`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled: !rule.enabled }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to update status.");
      }

      setMessage(data.message || "Rule status updated.");
      await loadRules();
    } catch (err) {
      setError(err.message || "Unable to update status.");
    }
  }

  async function deleteRule(rule) {
    if (!window.confirm(`Delete "${rule.name}"?`)) return;

    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/guardrails/${rule.id}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to delete guardrail.");
      }

      if (editingId === rule.id) closeForm();

      setMessage("Guardrail deleted successfully.");
      await loadRules();
    } catch (err) {
      setError(err.message || "Unable to delete guardrail.");
    }
  }

  const enabledCount = rules.filter((rule) => rule.enabled).length;

  return (
    <section className="page gr-page">
      <div className="gr-header">
        <div className="page-heading">
          <span className="eyebrow">SAFETY &amp; CONTROL</span>
          <h2>Guardrails</h2>
          <p>
            Manage rules that help control document processing and AI responses.
          </p>
        </div>

        <button
          className="gr-add-button"
          type="button"
          onClick={openCreateForm}
        >
          + Add rule
        </button>
      </div>

      <div className="gr-summary">
        <div>
          <span>Total rules</span>
          <strong>{rules.length}</strong>
        </div>

        <div>
          <span>Active</span>
          <strong>{enabledCount}</strong>
        </div>

        <div>
          <span>Inactive</span>
          <strong>{rules.length - enabledCount}</strong>
        </div>
      </div>

      {error && <div className="gr-notice gr-error">{error}</div>}
      {message && <div className="gr-notice gr-success">{message}</div>}

      {showForm && (
        <section className="content-card gr-editor">
          <div className="gr-editor-heading">
            <h3>{editingId ? "Edit rule" : "Create a rule"}</h3>

            <button
              type="button"
              className="gr-close-button"
              onClick={closeForm}
              aria-label="Close form"
            >
              ×
            </button>
          </div>

          <form className="gr-form" onSubmit={handleSubmit}>
            <label>
              Rule name
              <input
                name="name"
                value={form.name}
                onChange={updateField}
                placeholder="Enter rule name"
                maxLength={150}
                required
              />
            </label>

            <label>
              Description
              <input
                name="description"
                value={form.description}
                onChange={updateField}
                placeholder="Briefly explain the rule"
                required
              />
            </label>

            <label>
              Category
              <select
                name="category"
                value={form.category}
                onChange={updateField}
              >
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Rule instructions
              <textarea
                name="rule_text"
                value={form.rule_text}
                onChange={updateField}
                placeholder="Describe what the rule should check"
                rows={3}
                required
              />
            </label>

            <label className="gr-enable-option">
              <input
                type="checkbox"
                name="enabled"
                checked={form.enabled}
                onChange={updateField}
              />
              Enable rule
            </label>

            <div className="gr-form-actions">
              <button
                type="button"
                className="gr-cancel-button"
                onClick={closeForm}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="gr-add-button"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : editingId
                    ? "Save changes"
                    : "Create rule"}
              </button>
            </div>
          </form>
        </section>
      )}

      <div className="gr-list-heading">
        <div>
          <h3>Configured rules</h3>
          <p>Manage each rule individually.</p>
        </div>

        <button
          type="button"
          className="gr-refresh-button"
          onClick={loadRules}
          disabled={loading}
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <p className="gr-empty">Loading rules...</p>
      ) : rules.length === 0 ? (
        <div className="content-card gr-empty">
          <h4>No rules yet</h4>
          <p>Add your first guardrail to get started.</p>
          <button
            type="button"
            className="gr-add-button"
            onClick={openCreateForm}
          >
            + Create first rule
          </button>
        </div>
      ) : (
        <div className="gr-rule-list">
          {rules.map((rule) => (
            <article className="content-card gr-rule-card" key={rule.id}>
              <div className="gr-rule-main">
                <div className="gr-rule-name">
                  <h4>{rule.name}</h4>
                  <span className="gr-category">{rule.category}</span>
                </div>

                <p>{rule.description}</p>
              </div>

              <div className="gr-rule-footer">
                <span
                  className={
                    rule.enabled
                      ? "gr-status gr-status-active"
                      : "gr-status gr-status-inactive"
                  }
                >
                  <span className="gr-status-dot" />
                  {rule.enabled ? "Active" : "Inactive"}
                </span>

                <div className="gr-actions">
                  <button
                    type="button"
                    className="gr-action-button"
                    onClick={() => openEditForm(rule)}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="gr-action-button"
                    onClick={() => toggleRule(rule)}
                  >
                    {rule.enabled ? "Disable" : "Enable"}
                  </button>

                  <button
                    type="button"
                    className="gr-action-button gr-delete"
                    onClick={() => deleteRule(rule)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default GuardrailsPage;