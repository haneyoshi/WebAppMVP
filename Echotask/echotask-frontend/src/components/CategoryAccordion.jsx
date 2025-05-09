import React from "react";

function CategoryAccordion({isFolded, setIsFolded, label, children}){
    const toggleFold = () => setIsFolded(!isFolded);

    return(
        <div style={{ marginBottom: "20px", borderBottom: "1px solid #ccc", paddingBottom: "10px" }}>
        {/* Header row: label on the left, toggle button on the right */}
            <div
                style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "#333",
                color: "white",
                padding: "10px",
                borderRadius: "6px"
                }}>
                
                <h3 style={{margin:0 }}>{label}</h3>
                <button onClick={toggleFold} style={{background: "none", color: "white", border: "none", cursor: "pointer"}}>
                {isFolded ? "► Unfold" : "▼ Fold"}
                </button>
            </div>

            {/* Children section: visible only when unfolded */}
            {!isFolded && (
                <div style={{padding: "10px 10px 10px 20px"}}>
                    {children}
                </div>
            )}
        </div>
    )

}

export default CategoryAccordion;