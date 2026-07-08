const {
  useState,
  useEffect,
  useCallback
} = React;
const API_BASE = window.__FNOL_CONFIG__ && window.__FNOL_CONFIG__.apiBase || "/api";
const ROUTE_CLASS = {
  "Fast-Track": "route-Fast-Track",
  "Manual Review": "route-Manual-Review",
  "Investigation Flag": "route-Investigation-Flag",
  "Specialist Queue": "route-Specialist-Queue",
  "Standard Review": "route-Standard-Review"
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
  initialEstimate: "Initial Estimate"
};
const SAMPLE_FILES = [{
  label: "Fast-Track",
  file: "sample1_fasttrack.txt"
}, {
  label: "Missing Fields",
  file: "sample2_missing_fields.txt"
}, {
  label: "Fraud Flag",
  file: "sample3_fraud_flag.txt"
}, {
  label: "Injury",
  file: "sample4_injury.txt"
}, {
  label: "Large Damage",
  file: "sample5_large_damage.txt"
}];
function RouteBadge({
  route
}) {
  const cls = ROUTE_CLASS[route] || "route-Standard-Review";
  return /*#__PURE__*/React.createElement("span", {
    className: `route-badge ${cls}`
  }, route);
}
function ResultView({
  result
}) {
  if (!result) {
    return /*#__PURE__*/React.createElement("div", {
      className: "empty-state"
    }, "Paste FNOL text or upload a document, then click \"Process Claim\" to see extracted fields and the routing decision here.");
  }
  const {
    extractedFields,
    missingFields,
    recommendedRoute,
    reasoning
  } = result;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(RouteBadge, {
    route: recommendedRoute
  }), /*#__PURE__*/React.createElement("div", {
    className: "reasoning-box"
  }, reasoning), missingFields && missingFields.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "missing-fields-box"
  }, /*#__PURE__*/React.createElement("strong", {
    style: {
      fontSize: 13
    }
  }, "Missing Fields:"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 6
    }
  }, missingFields.map(f => /*#__PURE__*/React.createElement("span", {
    className: "missing-chip",
    key: f
  }, FIELD_LABELS[f] || f)))), /*#__PURE__*/React.createElement("table", {
    className: "fields-table"
  }, /*#__PURE__*/React.createElement("tbody", null, Object.keys(FIELD_LABELS).map(key => {
    const value = extractedFields ? extractedFields[key] : null;
    const isMissing = missingFields && missingFields.includes(key);
    return /*#__PURE__*/React.createElement("tr", {
      key: key
    }, /*#__PURE__*/React.createElement("th", null, FIELD_LABELS[key]), /*#__PURE__*/React.createElement("td", {
      className: isMissing ? "field-missing" : ""
    }, value || (isMissing ? "— missing —" : "—")));
  }))));
}
function HistoryList({
  history,
  onSelect
}) {
  if (!history || history.length === 0) {
    return /*#__PURE__*/React.createElement("p", {
      style: {
        color: "var(--muted)",
        fontSize: 13
      }
    }, "No claims processed yet.");
  }
  return /*#__PURE__*/React.createElement("div", null, history.map(item => /*#__PURE__*/React.createElement("div", {
    className: "history-row",
    key: item.id,
    onClick: () => onSelect(item.id)
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-left"
  }, /*#__PURE__*/React.createElement("span", {
    className: "h-policy"
  }, item.policyNumber || `Claim #${item.id}`), /*#__PURE__*/React.createElement("span", {
    className: "h-meta"
  }, item.source_filename, " · ", new Date(item.created_at).toLocaleString())), /*#__PURE__*/React.createElement("span", {
    className: `route-pill ${ROUTE_CLASS[item.recommended_route] || ""}`
  }, item.recommended_route))));
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
    fetch(`${API_BASE}/claims/`).then(res => res.json()).then(data => setHistory(data)).catch(() => {});
  }, []);
  useEffect(() => {
    loadHistory();
  }, [loadHistory]);
  const loadSample = filename => {
    setMode("paste");
    setError(null);
    fetch(`${API_BASE}/samples/${filename}/`).then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not load sample.");
      return data;
    }).then(data => {
      setRawText(data.rawText);
      setSourceFilename(filename);
    }).catch(err => setError(err.message));
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
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        rawText,
        sourceFilename: sourceFilename || "(pasted text)"
      })
    }).then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to process claim.");
      return data;
    }).then(data => {
      setResult(data);
      loadHistory();
    }).catch(err => setError(err.message)).finally(() => setLoading(false));
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
      body: formData
    }).then(async res => {
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to process claim.");
      return data;
    }).then(data => {
      setResult(data);
      loadHistory();
    }).catch(err => setError(err.message)).finally(() => setLoading(false));
  };
  const handleSelectHistory = id => {
    setLoading(true);
    fetch(`${API_BASE}/claims/${id}/`).then(res => res.json()).then(data => setResult(data)).catch(err => setError(err.message)).finally(() => setLoading(false));
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "app-shell"
  }, /*#__PURE__*/React.createElement("div", {
    className: "app-header"
  }, /*#__PURE__*/React.createElement("h1", null, "Autonomous Insurance Claims Processing Agent"), /*#__PURE__*/React.createElement("p", null, "Django + Django REST Framework backend · SQLite database · React frontend")), /*#__PURE__*/React.createElement("div", {
    className: "layout"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "panel"
  }, /*#__PURE__*/React.createElement("h2", null, "Submit an FNOL Document"), /*#__PURE__*/React.createElement("div", {
    className: "tabs"
  }, /*#__PURE__*/React.createElement("button", {
    className: `tab-btn ${mode === "paste" ? "active" : ""}`,
    onClick: () => setMode("paste")
  }, "Paste Text"), /*#__PURE__*/React.createElement("button", {
    className: `tab-btn ${mode === "upload" ? "active" : ""}`,
    onClick: () => setMode("upload")
  }, "Upload File")), mode === "paste" ? /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("textarea", {
    placeholder: "Paste the raw FNOL document text here (Policy Number: ..., Description: ..., etc.)",
    value: rawText,
    onChange: e => setRawText(e.target.value)
  }), /*#__PURE__*/React.createElement("input", {
    className: "filename-input",
    placeholder: "Label for this claim (optional), e.g. sample1_fasttrack.txt",
    value: sourceFilename,
    onChange: e => setSourceFilename(e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    className: "sample-list"
  }, /*#__PURE__*/React.createElement("p", null, "Quick test with a bundled sample document:"), SAMPLE_FILES.map(s => /*#__PURE__*/React.createElement("span", {
    key: s.file,
    className: "sample-chip",
    title: s.file,
    onClick: () => loadSample(s.file)
  }, s.label))), /*#__PURE__*/React.createElement("button", {
    className: "submit-btn",
    onClick: handleProcessText,
    disabled: loading
  }, loading ? "Processing…" : "Process Claim")) : /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    className: `file-drop ${file ? "has-file" : ""}`
  }, file ? `Selected: ${file.name}` : "Click to choose a .txt or .pdf file", /*#__PURE__*/React.createElement("input", {
    type: "file",
    accept: ".txt,.pdf",
    style: {
      display: "none"
    },
    onChange: e => setFile(e.target.files[0] || null)
  })), /*#__PURE__*/React.createElement("button", {
    className: "submit-btn",
    onClick: handleProcessFile,
    disabled: loading
  }, loading ? "Processing…" : "Process Claim")), error && /*#__PURE__*/React.createElement("div", {
    className: "error-box"
  }, error)), /*#__PURE__*/React.createElement("div", {
    className: "panel history-panel"
  }, /*#__PURE__*/React.createElement("h2", null, "Claim History (", history.length, ")"), /*#__PURE__*/React.createElement(HistoryList, {
    history: history,
    onSelect: handleSelectHistory
  }))), /*#__PURE__*/React.createElement("div", {
    className: "panel result-panel"
  }, /*#__PURE__*/React.createElement("h2", null, "Extraction & Routing Result"), /*#__PURE__*/React.createElement(ResultView, {
    result: result
  }))));
}
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(/*#__PURE__*/React.createElement(App, null));
