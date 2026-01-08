const StockCard = ({ stock, onAnalyze }) => {
  const price = stock.price || 0;
  const change = stock.changesPercentage || 0;
  const isPositive = change >= 0;
  const mCap = stock.marketCap || 0;
  const name = stock.name || stock.symbol;

  // URL Εικόνας
  const logoUrl = `https://financialmodelingprep.com/image-stock/${stock.symbol}.png`;

  return (
    <div className="coin-card" style={{ position: "relative" }}>
      <div className="coin-header">
        <img
          src={logoUrl}
          alt={stock.symbol}
          className="coin-image"
          onError={(e) => {
            e.target.src =
              "https://ui-avatars.com/api/?name=" +
              stock.symbol +
              "&background=random";
          }}
        />
        <div style={{ overflow: "hidden" }}>
          <h2 style={{ fontSize: "1.1rem" }}>
            {name.length > 15 ? name.substring(0, 15) + "..." : name}
          </h2>
          <p className="symbol" style={{ color: "#666", fontSize: "0.9rem" }}>
            {stock.symbol}
          </p>
        </div>
      </div>

      <div style={{ marginTop: "10px" }}>
        <p>
          Price: <strong>${price.toFixed(2)}</strong>
        </p>
        <p className={isPositive ? "positive" : "negative"}>
          {change > 0 ? "+" : ""}
          {change.toFixed(2)}%
        </p>
        <p style={{ fontSize: "0.9rem", color: "#555" }}>
          M. Cap: ${(mCap / 1000000000).toFixed(2)} B
        </p>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();

          console.log("Button clicked for:", stock.symbol);

          if (onAnalyze) {
            onAnalyze(stock.symbol);
          } else {
            console.error("Σφάλμα: Η συνάρτηση onAnalyze δεν βρέθηκε!");
            alert("Error: onAnalyze prop is missing");
          }
        }}
        style={{
          marginTop: "12px",
          width: "100%",
          padding: "10px",
          backgroundColor: "#4F46E5",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          fontWeight: "600",
          fontSize: "0.9rem",
          transition: "background 0.2s",
        }}
        onMouseOver={(e) => (e.target.style.backgroundColor = "#4338ca")}
        onMouseOut={(e) => (e.target.style.backgroundColor = "#4F46E5")}
      >
        ✨ Analyze with AI
      </button>
    </div>
  );
};

export default StockCard;
