import React from "react";
import ReactMarkdown from "react-markdown"; // 1. ΠΡΟΣΘΗΚΗ IMPORT

const AnalysisModal = ({ isOpen, onClose, analysis, loading, symbol }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={styles.overlay}>
      <div className="modal-content" style={styles.content}>
        <div style={styles.header}>
          <h2>🤖 AI Analysis: {symbol}</h2>
          <button onClick={onClose} style={styles.closeBtn}>
            X
          </button>
        </div>

        <div style={styles.body}>
          {loading ? (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              <p style={{ fontSize: "1.2rem" }}>🧠 The Groq is thinking...</p>
              <p style={{ color: "#666" }}>
                Reading the data for {symbol}...
              </p>
            </div>
          ) : (
            /* 2. ΑΛΛΑΓΗ ΕΔΩ: Αντικαθιστούμε το div με το ReactMarkdown */
            <div className="markdown-body">
              <ReactMarkdown>{analysis}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.6)", // Λίγο πιο διαφανές για μοντέρνο look
    backdropFilter: "blur(5px)", // Θολώνει το background από πίσω
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 1000,
  },
  content: {
    backgroundColor: "white",
    color: "#1a202c",
    padding: "0", // Το padding το βάζουμε στο body/header για καλύτερο έλεγχο
    borderRadius: "16px", // Πιο στρογγυλεμένες γωνίες
    width: "90%",
    maxWidth: "700px",
    maxHeight: "85vh",
    display: "flex",
    flexDirection: "column",
    boxShadow: "0 20px 50px rgba(0,0,0,0.3)",
    overflow: "hidden", // Για να κόβει τις γωνίες στα παιδιά
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #eee",
    padding: "20px 25px",
    backgroundColor: "#f8fafc", // Ελαφρύ γκρι στο header
  },
  body: {
    padding: "25px",
    overflowY: "auto", // Scroll μόνο στο κείμενο, όχι στο header
  },
  closeBtn: {
    background: "white",
    border: "1px solid #ddd",
    borderRadius: "50%",
    width: "32px",
    height: "32px",
    cursor: "pointer",
    color: "#666",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: "bold",
  },
};

export default AnalysisModal;
