# Implementation notes

## Deviations (reviewed at Verify — each is fine, a spec bug, or a missed unknown)

- **D1 (2026-08-10): Static-JSON read paths instead of Worker+D1 serving.** SPEC §11 said Worker+D1 serves all reads. Data is tiny + precomputed (126 districts, 2556 forecasts), so read paths ship as static JSON from Pages; Worker is used only for the agent. Lighter, more deterministic, free, and buildable/verifiable with zero installs on the 4GB machine. Reversible. Approved by user.
- **D2 (2026-08-10): Circle markers instead of choropleth for the map slice.** SPEC §10/§11 said Leaflet choropleth + district TopoJSON. District boundary GeoJSON is unsourced fog; lat/lon for all 126 districts is already in the data. Proportional circle markers (colored by tier, sized by burden) give an honest, readable map with no external boundary dependency. Choropleth is a later upgrade if a cleanly-licensed boundary set is sourced.
- **D3 (2026-08-10): Facility coverage-vs-risk gap (T4) CUT.** Sub-spike: district facility counts exist only in RHS PDFs (parse + name-match rabbit hole); state-level distribution to districts would be circular; Census population is clean but redundant with case-burden. Cut per the pre-agreed graceful-degradation order. The agent still flags highest-risk districts from the forecast. Facility-per-capita = documented future work.
- **D4 (2026-08-10): Agent deterministic-first.** T8 grounded briefing/explain/flag is built deterministically (verifiable with zero install); the LLM prose + free-form NL layer (provider-abstracted: Workers AI default, MeshAPI optional) is wired at deploy (T12) behind the wrangler install gate. Grounding + retrieval (the hard part) is real now; the LLM enriches, it isn't load-bearing.

## Design discipline (anti-slop, applied inline per lifecycle MUST)
- No purple/indigo gradient, no cream+serif default, no glassmorphism. Restrained gov-tech palette: slate/ink neutrals + a deliberate 3-step risk ramp. System font stack, tabular numbers for all figures, generous spacing. Formal `devibe_scan.py` to run at Review (Stage 6).
