// components/SupplyItemRow.jsx
import React, { useState } from "react";

function SupplyItemRow({ itemName }) {
  const [quantity, setQuantity] = useState(0); // initial quantity

  // Increment and decrement functions
  const increment = () => setQuantity(quantity + 1);
  const decrement = () => setQuantity(quantity > 0 ? quantity - 1 : 0);

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "10px",
        background: "#2e2e2e",
        padding: "10px 14px",
        borderRadius: "8px",
        color: "white",
      }}
    >
      {/* Left: Item Name */}
      <span style={{ flex: 1, fontSize: "1.1em" }}>{itemName}</span>

      {/* Right: Quantity Controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          minWidth: "160px",
          justifyContent: "flex-end",
        }}
      >
        <button
          onClick={decrement}
          style={{
            width: "30px",
            height: "30px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#333",
            color: "white",
            border: "2px solid #555",
            borderRadius: "6px",
            fontSize: "1.3em",
            lineHeight: "30px",
            padding: 0, 
            cursor: "pointer",
          }}
        >
          −
        </button>

        <span style={{ width: "36px", textAlign: "center", fontSize: "1.3em" }}>
          {quantity}
        </span>

        <button
          onClick={increment}
          style={{
            width: "30px",
            height: "30px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#333",
            color: "white",
            border: "2px solid #555",
            borderRadius: "6px",
            fontSize: "1.3em",
            lineHeight: "30px",
            padding: 0, 
            cursor: "pointer",
          }}
        >
          +
        </button>
      </div>
    </div>
  );
}

export default SupplyItemRow;
