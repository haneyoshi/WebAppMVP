import React, { useState, useEffect } from "react";
import SearchBar from "../components/SearchBar";
import CategoryAccordion from "../components/CategoryAccordion";
import SupplyItemRow from "../components/SupplyItemRow";

function SuppliesRequestPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [isFolded, setIsFolded] = useState(true);
  //This is array destructuring, meaning:
  //const result = useState('');
  //const searchTerm = result[0];
  //const setSearchTerm = result[1] (internal function changes result[0] when update);

  const [suppliesData, setSuppliesData] = useState({});

  useEffect(() => {
    // Simulate backend fetch
    const mockData = {
      Cleaner: ["Toilet Bowl Cleaner", "Glass Cleaner"],
      Papers: ["Paper Towel", "Toilet Paper"],
      Garbage: ["Large", "Medium", "Small"],
    };

    setSuppliesData(mockData); // load mock data into state
  }, []); // only run once on component mount

  return (
    // Search Bar:
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

        {/* Content in an accordion format by category */}
        {Object.entries(suppliesData).map(([category, items]) => (
          <CategoryAccordion
            key={category}
            label={category}
            isFolded={isFolded}
            setIsFolded={setIsFolded}
          >
            {items.map((item) => (
              <SupplyItemRow key={item} itemName={item} />
            ))}
          </CategoryAccordion>
        ))}
      </div>

      {/* Render the SearchBar component and give it these 2 props(properties), "searchTerm" and "setSearchTerm" */}
      {/* {} is used to get the value/ function stored in the variable */}
      <section>
        <p>
          You are searching for: <strong>{searchTerm}</strong>
        </p>
      </section>
    </div>
  );
}

export default SuppliesRequestPage;
