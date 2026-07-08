const { useState, useEffect, useCallback } = React;

const API_BASE = (window.__FNOL_CONFIG__ && window.__FNOL_CONFIG__.apiBase) || "/api";

const ROUTE_CLASS = {
  "Fast-Track": "route-Fast-Track",
  "Manual Review": "route-Manual-Review",
  "Investigation Flag": "route-Investigation-Flag",
  "Specialist Queue": "route-Specialist-Queue",
  "Standard Review": "route-Standard-Review",
};

const FIELD_LABELS = {
  policyNumber: "Policy Number",
  policyholderName: "Policyholder Name",
  effectiveDates: "Effective Dates",
  incidentDate: "Incident Date",
  incidentTime: "Incident Time",
  incidentLocation: "Incident Location",
  incidentDescription: "Description",
  claimant: "Claimant",
  thirdParties: "Third Parties",
  contactDetails: "Contact Details",
  assetType: "Asset Type",
  assetId: "Asset ID",
  estimatedDamage: "Estimated Damage",
  claimType: "Claim Type",
  attachments: "Attachments",
  initialEstimate: "Initial Estimate",
};

const SAMPLE_FILES = [
  { label: "Fast-Track", file: "sample1_fasttrack.txt" },
  { label: "Missing Fields", file: "sample2_missing_fields.txt" },
  { label: "Fraud Flag", file: "sample3_fraud_flag.txt" },
  { label: "Injury", file: "sample4_injury.txt" },
  { label: "Large Damage", file: "sample5_large_damage.txt" },
];

function RouteBadge({ route }) {
  const cls = ROUTE_CLASS[route] || "route-Standard-Review";
  return <span className={`route-badge ${cls}`}>{route}</span>;
}

function ResultView({ result }) {
  if (!result) {
    return (
      <div className="empty-state">
        Paste FNOL text or upload a document, then click "Process Claim"
        to see extracted fields and the routing decision here.
      </div>
    );
  }

  const { extractedFields, missingFields, recommendedRoute, reasoning } = result;

  return (
    <div>
      <RouteBadge route={recommendedRoute} />

      <div className="reasoning-box">{reasoning}</div>

      {missingFields && missingFields.length > 0 && (
        <div className="missing-fields-box">
          <strong style={{ fontSize: 13 }}>Missing Fields:</strong>
          <div style={{ marginTop: 6 }}>
            {missingFields.map((f) => (
              <span className="missing-chip" key={f}>
                {FIELD_LABELS[f] || f}
              </span>
            ))}
          </div>
        </div>
      )}

      <table className="fields-table">
        <tbody>
          {Object.keys(FIELD_LABELS).map((key) => {
            const value = extractedFields ? extractedFields[key] : null;
            const isMissing = missingFields && missingFields.includes(key);
            return (
              <tr key={key}>
                <th>{FIELD_LABELS[key]}</th>
                <td className={isMissing ? "field-missing" : ""}>
                  {value || (isMissing ? "— missing —" : "—")}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function HistoryList({ history, onSelect }) {
  if (!history || history.length === 0) {
    return <p style={{ color: "var(--muted)", fontSize: 13 }}>No claims processed yet.</p>;
  }
  return (
    <div>
      {history.map((item) => (
        <div className="history-row" key={item.id} onClick={() => onSelect(item.id)}>
          <div className="h-left">
            <span className="h-policy">
              {item.policyNumber || `Claim #${item.id}`}
            </span>
            <span className="h-meta">
              {item.source_filename} &middot; {new Date(item.created_at).toLocaleString()}
            </span>
          </div>
          <span
            className={`route-pill ${ROUTE_CLASS[item.recommended_route] || ""}`}
          >
            {item.recommended_route}
          </span>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [mode, setMode] = useState("paste"); // "paste" | "upload"
  const [rawText, setRawText] = useState("");
  const [sourceFilename, setSourceFilename] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  const loadHistory = useCallback(() => {
    fetch(`${API_BASE}/claims/`)
      .then((res) => res.json())
      .then((data) => setHistory(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const loadSample = (filename) => {
    setMode("paste");
    setError(null);
    fetch(`${API_BASE}/samples/${filename}/`)
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Could not load sample.");
        return data;
      })
      .then((data) => {
        setRawText(data.rawText);
        setSourceFilename(filename);
      })
      .catch((err) => setError(err.message));
  };

  const handleProcessText = () => {
    if (!rawText.trim()) {
      setError("Please paste some FNOL text first.");
      return;
    }
    setError(null);
    setLoading(true);
    fetch(`${API_BASE}/claims/process-text/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rawText,
        sourceFilename: sourceFilename || "(pasted text)",
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to process claim.");
        return data;
      })
      .then((data) => {
        setResult(data);
        loadHistory();
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleProcessFile = () => {
    if (!file) {
      setError("Please choose a .txt or .pdf file first.");
      return;
    }
    setError(null);
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    fetch(`${API_BASE}/claims/process-file/`, {
      method: "POST",
      body: formData,
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Failed to process claim.");
        return data;
      })
      .then((data) => {
        setResult(data);
        loadHistory();
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleSelectHistory = (id) => {
    setLoading(true);
    fetch(`${API_BASE}/claims/${id}/`)
      .then((res) => res.json())
      .then((data) => setResult(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Autonomous Insurance Claims Processing Agent</h1>
        <p>
          Django + Django REST Framework backend &middot; SQLite database &middot; React frontend
        </p>
      </div>

      <div className="layout">
        {/* LEFT: input panel */}
        <div>
          <div className="panel">
            <h2>Submit an FNOL Document</h2>

            <div className="tabs">
              <button
                className={`tab-btn ${mode === "paste" ? "active" : ""}`}
                onClick={() => setMode("paste")}
              >
                Paste Text
              </button>
              <button
                className={`tab-btn ${mode === "upload" ? "active" : ""}`}
                onClick={() => setMode("upload")}
              >
                Upload File
              </button>
            </div>

            {mode === "paste" ? (
              <div>
                <textarea
                  placeholder="Paste the raw FNOL document text here (Policy Number: ..., Description: ..., etc.)"
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                />
                <input
                  className="filename-input"
                  placeholder="Label for this claim (optional), e.g. sample1_fasttrack.txt"
                  value={sourceFilename}
                  onChange={(e) => setSourceFilename(e.target.value)}
                />

                <div className="sample-list">
                  <p>Quick test with a bundled sample document:</p>
                  {SAMPLE_FILES.map((s) => (
                    <span
                      key={s.file}
                      className="sample-chip"
                      title={s.file}
                      onClick={() => loadSample(s.file)}
                    >
                      {s.label}
                    </span>
                  ))}
                </div>

                <button className="submit-btn" onClick={handleProcessText} disabled={loading}>
                  {loading ? "Processing…" : "Process Claim"}
                </button>
              </div>
            ) : (
              <div>
                <label className={`file-drop ${file ? "has-file" : ""}`}>
                  {file ? `Selected: ${file.name}` : "Click to choose a .txt or .pdf file"}
                  <input
                    type="file"
                    accept=".txt,.pdf"
                    style={{ display: "none" }}
                    onChange={(e) => setFile(e.target.files[0] || null)}
                  />
                </label>
                <button className="submit-btn" onClick={handleProcessFile} disabled={loading}>
                  {loading ? "Processing…" : "Process Claim"}
                </button>
              </div>
            )}

            {error && <div className="error-box">{error}</div>}
          </div>

          <div className="panel history-panel">
            <h2>Claim History ({history.length})</h2>
            <HistoryList history={history} onSelect={handleSelectHistory} />
          </div>
        </div>

        {/* RIGHT: result panel */}
        <div className="panel result-panel">
          <h2>Extraction &amp; Routing Result</h2>
          <ResultView result={result} />
        </div>
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
