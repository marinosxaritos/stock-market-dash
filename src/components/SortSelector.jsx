const SortSelector = ({sortBy, onShortChange}) => {
    return ( 
        <div className="controls">
            <label htmlFor="sort">Sort By</label>
            <select 
                value={sortBy} 
                id="sort"
                onChange={(e) => onShortChange(e.target.value)}>
                    <option value="market_cap_asc">Market Cap (Low To High) </option>
                    <option value="market_cap_desc">Market Cap (High To Low) </option>
                    <option value="price_desc">Price (High to Low) </option>
                    <option value="price_asc">Price (Low To High) </option>
                    <option value="change_desc">24h Change (High To Low) </option>
                    <option value="change_asc">24h Change (Low To High) </option>
                </select>
        </div>
    );
}
 
export default SortSelector;