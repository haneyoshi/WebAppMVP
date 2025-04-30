import React, {useState} from "react";
import SearchBar from '../components/SearchBar';

function SuppliesRequestPage(){
    const [searchTerm, setSearchTerm] = useState('');
    return(
        <div style={{color: 'white', padding: '20px'}}>
            <h1>Supplies Request Page</h1>
            <SearchBar
            searchTerm = {searchTerm}
            onSearchChange = {setSearchTerm}
            />

            <p>You are searching for: <strong>{searchTerm}</strong></p>
        </div>
    );
}

export default SuppliesRequestPage;