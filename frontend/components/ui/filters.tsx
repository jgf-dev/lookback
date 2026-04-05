const DEFAULT_FILTERS = ["voice", "search", "screenshots", "insights"];

export function Filters() {
  return (
    <div className="card">
      <strong>Filters</strong>
      <div>
        {DEFAULT_FILTERS.map((filter) => (
          <label key={filter} style={{ display: "inline-flex", gap: "0.25rem", marginRight: "0.75rem" }}>
            <input type="checkbox" defaultChecked />
            {filter}
          </label>
        ))}
      </div>
    </div>
  );
}
