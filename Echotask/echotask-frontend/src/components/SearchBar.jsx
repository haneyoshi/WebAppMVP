import React from "react";

function SearchBar({searchTerm, onSearchChange}){
    // searchTerm: Value from the parent (the text in the box)
    // onSearchChange(...): Callback to notify parent when user types
    return(
        <div style={{marginBottom: '20px'}}>
            <input
            type = "text"
            placeholder="Search supplies..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            //e.target.value: The actual text the user typed
            style={{
                width: '95%',
                padding: '10px',
                fontSize: '16px',
                borderRadius: '8px',
                border: '1px solid #ccc'
            }}
            />
        </div>
    );
}

export default SearchBar;