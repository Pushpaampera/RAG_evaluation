import { useRef, useState } from "react";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const MAX_FILE_SIZE = 15 * 1024 * 1024;

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function IngestionPage() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function selectFile(file) {
    setError("");
    setResult(null);

    if (!file) return;

    const extension = file.name.split(".").pop().toLowerCase();

    if (!["pdf", "docx"].includes(extension)) {
      setSelectedFile(null);
      setError("Please select a PDF or DOCX document.");
      return;
    }

    if (file.size === 0) {
      setSelectedFile(null);
      setError("The selected file is empty.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null);
      setError("The maximum file size is 15 MB.");
      return;
    }

    setSelectedFile(file);
  }

  async function uploadDocument() {
    if (!selectedFile || uploading) return;

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${API_URL}/ingestion/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = data.detail;

        const message =
          typeof detail === "string"
            ? detail
            : detail?.message ||
              "The document could not be processed.";

        throw new Error(message);
      }

      if (!data.success || !data.document) {
        throw new Error("The server returned an unexpected response.");
      }

      setResult(data.document);
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (uploadError) {
      setError(
        uploadError instanceof TypeError
          ? "Cannot connect to the backend. Check that FastAPI is running."
          : uploadError.message || "Upload failed. Please try again."
      );
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  return (
    <section className="page ingestion-page">
      <div className="page-heading">
        <span className="eyebrow">DOCUMENT MANAGEMENT</span>
        <h2>Data Ingestion</h2>
        <p>
          Add documents to your knowledge base. DocuLens prepares their
          content for secure, document-grounded retrieval.
        </p>
      </div>

      <div className="ingestion-layout">
        <section className="ingestion-card upload-card">
          <div className="ingestion-card-heading">
            <div>
              <span className="ingestion-section-label">
                KNOWLEDGE BASE
              </span>
              <h3>Add a document</h3>
              <p>Upload a document to prepare it for your RAG system.</p>
            </div>

            <div className="ingestion-heading-icon" aria-hidden="true">
              ↑
            </div>
          </div>

          <div
            className={`upload-dropzone${dragging ? " is-dragging" : ""}`}
            onDragEnter={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={(event) => {
              if (!event.currentTarget.contains(event.relatedTarget)) {
                setDragging(false);
              }
            }}
            onDrop={handleDrop}
          >
            <div className="upload-file-icon" aria-hidden="true">
              <svg
                viewBox="0 0 48 48"
                width="42"
                height="42"
                fill="none"
              >
                <path
                  d="M14 5.5h13l9 9V41H14a3 3 0 0 1-3-3V8.5a3 3 0 0 1 3-3Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinejoin="round"
                />
                <path
                  d="M27 6v10h9M18 25h14M18 31h14"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </div>

            <h4>Drag and drop your document</h4>
            <p>or choose a file from your computer</p>

            <button
              type="button"
              className="secondary-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              Browse files
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              hidden
              onChange={(event) => {
                selectFile(event.target.files?.[0]);
              }}
            />

            <div className="upload-format-note">
              <span>PDF</span>
              <span>DOCX</span>
              <span>Maximum 15 MB</span>
            </div>
          </div>

          {selectedFile && (
            <div className="selected-file">
              <div className="selected-file-icon" aria-hidden="true">
                {selectedFile.name.toLowerCase().endsWith(".pdf")
                  ? "PDF"
                  : "DOC"}
              </div>

              <div className="selected-file-details">
                <strong>{selectedFile.name}</strong>
                <span>{formatFileSize(selectedFile.size)}</span>
              </div>

              <button
                type="button"
                className="remove-file-button"
                aria-label="Remove selected file"
                disabled={uploading}
                onClick={() => {
                  setSelectedFile(null);
                  setError("");

                  if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                  }
                }}
              >
                ×
              </button>
            </div>
          )}

          {error && (
            <div className="ingestion-message error-message" role="alert">
              <strong>Unable to continue</strong>
              <span>{error}</span>
            </div>
          )}

          <button
            type="button"
            className="primary-button upload-submit-button"
            disabled={!selectedFile || uploading}
            onClick={uploadDocument}
          >
            {uploading
              ? "Uploading document..."
              : "Upload and process document"}
            {!uploading && <span aria-hidden="true"> →</span>}
          </button>

          <p className="privacy-note">
            Documents are checked before processing. Detected sensitive
            information is masked before embeddings are generated.
          </p>
        </section>

        <aside className="ingestion-card process-card">
          <span className="ingestion-section-label">
            HOW IT WORKS
          </span>

          <h3>From document to knowledge</h3>

          <p className="process-description">
            Your document is prepared automatically after upload.
          </p>

          <div className="process-steps">
            <div className="process-step">
              <span className="process-step-number">01</span>
              <div>
                <strong>Content preparation</strong>
                <p>Safety checks, text extraction and cleaning.</p>
              </div>
            </div>

            <div className="process-step">
              <span className="process-step-number">02</span>
              <div>
                <strong>Privacy protection</strong>
                <p>Detect and mask supported sensitive information.</p>
              </div>
            </div>

            <div className="process-step">
              <span className="process-step-number">03</span>
              <div>
                <strong>Semantic indexing</strong>
                <p>Create text chunks and their embeddings.</p>
              </div>
            </div>

            <div className="process-step">
              <span className="process-step-number">04</span>
              <div>
                <strong>Knowledge storage</strong>
                <p>Save processed chunks in PostgreSQL with pgvector.</p>
              </div>
            </div>
          </div>

          <div className="supported-format-box">
            <span className="supported-format-check">✓</span>
            <div>
              <strong>Supported documents</strong>
              <p>PDF and Microsoft Word (.docx)</p>
            </div>
          </div>
        </aside>
      </div>

      {result && (
        <section className="ingestion-card result-card" aria-live="polite">
          <div className="result-heading">
            <div className="result-success-icon" aria-hidden="true">
              ✓
            </div>

            <div>
              <span className="ingestion-section-label">
                UPLOAD COMPLETE
              </span>
              <h3>Document added successfully</h3>
              <p>{result.filename}</p>
            </div>

            <span className="result-status">
              {result.status}
            </span>
          </div>

          <div className="result-metrics">
            <div className="result-metric">
              <span>Document ID</span>
              <strong>{result.id}</strong>
            </div>

            <div className="result-metric">
              <span>Text chunks</span>
              <strong>{result.chunk_count}</strong>
            </div>

            <div className="result-metric">
              <span>Embedding dimensions</span>
              <strong>{result.embedding_dimension}</strong>
            </div>

            <div className="result-metric">
              <span>File size</span>
              <strong>{formatFileSize(result.file_size)}</strong>
            </div>

            {result.page_count != null && (
              <div className="result-metric">
                <span>Pages</span>
                <strong>{result.page_count}</strong>
              </div>
            )}

            <div className="result-metric">
              <span>Values masked</span>
              <strong>{result.total_masked_values ?? 0}</strong>
            </div>
          </div>

          {result.masked_categories &&
            Object.keys(result.masked_categories).length > 0 && (
              <div className="masked-categories">
                <strong>Detected sensitive-data categories</strong>

                <div className="category-tags">
                  {Object.entries(result.masked_categories).map(
                    ([category, count]) => (
                      <span key={category}>
                        {category.replaceAll("_", " ")}: {count}
                      </span>
                    )
                  )}
                </div>
              </div>
            )}
        </section>
      )}
    </section>
  );
}

export default IngestionPage;