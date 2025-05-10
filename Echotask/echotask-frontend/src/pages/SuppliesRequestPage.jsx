import React, { useState, useEffect } from "react";
import SearchBar from "../components/SearchBar";
import CategoryAccordion from "../components/CategoryAccordion";
import SupplyItemRow from "../components/SupplyItemRow";

function SuppliesRequestPage() {
  const [searchTerm, setSearchTerm] = useState("");
  //This is array destructuring, meaning:
  //const result = useState('');
  //const searchTerm = result[0];
  //const setSearchTerm = result[1] (internal function changes result[0] when update);

  const [isFolded, setIsFolded] = useState(true);
  const [suppliesData, setSuppliesData] = useState({});
  const [selectedItems, setSelectedItems] = useState({});

  useEffect(() => {
    // Simulate backend fetch
    const mockData = {
      Cleaner: ["Toilet Bowl Cleaner", "Glass Cleaner"],
      Papers: ["Paper Towel", "Toilet Paper"],
      Garbage: ["Large", "Medium", "Small"],
    };

    setSuppliesData(mockData); // load mock data into state
  }, []); // only run once on component mount

  const handleQuantityChange = (itemName, quantity) => {
    //parameters receive from child
    setSelectedItems((prev) => ({
      ...prev,
      [itemName]: quantity,
    }));
  };

  const filterItems = (items) => {
    if (!searchTerm.trim()) return items;
    return items.filter((item) =>
      item.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const handleSubmit = () => {
    console.log("Submitted items:", selectedItems);
    alert("Request submitted! Check the console for details.");
  };

  return (
    <div className="app-container" style={{ color: "white" }}>
      <header>
        <h1>Supplies Request Sheet</h1>
      </header>

      <div
        style={{
          backgroundColor: "#1e1e1e",
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "20px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        }}
      >
        {/* Search Bar */}
        <SearchBar searchTerm={searchTerm} onSearchChange={setSearchTerm} />

        {/* Accordions */}
        {Object.entries(suppliesData).map(([category, items]) => {
          const filteredItems = filterItems(items);
          if (filteredItems.length === 0) return null;

          return (
            <CategoryAccordion
              key={category}
              label={category}
              isFolded={isFolded}
              setIsFolded={setIsFolded}
            >
              {filteredItems.map((item) => (
                <SupplyItemRow
                  key={item}
                  itemName={item}
                  quantity={selectedItems[item] || 0}
                  onQuantityChange={handleQuantityChange}
                />
              ))}
            </CategoryAccordion>
          );
        })}
      </div>

      {/* Summary */}
      <div
        style={{
          backgroundColor: "#2c2c2c",
          padding: "15px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >
        <h3>Summary</h3>
        {Object.entries(selectedItems).filter(([, qty]) => qty > 0).length === 0 ? (
          <p>No items selected yet.</p>
        ) : (
          <ul>
            {Object.entries(selectedItems)
              .filter(([, qty]) => qty > 0)
              .map(([item, qty]) => (
                <li key={item}>
                  {item}: {qty}
                </li>
              ))}
          </ul>
        )}
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        style={{
          backgroundColor: "#4caf50",
          color: "white",
          padding: "12px 24px",
          fontSize: "16px",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
        }}
      >
        Submit Request
      </button>
    </div>
  );
}

export default SuppliesRequestPage;
