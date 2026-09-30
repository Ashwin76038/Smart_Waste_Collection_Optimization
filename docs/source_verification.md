# Source verification receipt

All catalog entries were researched on 2026-09-23 through public web sources. A verified reference is not a verified dataset download. See each catalog row for the exact URL.

| Source IDs | Evidence obtained | Remaining check |
|---|---|---|
| S01, S02 | Readable official department/report-index pages | Dated data release and full recent report contents |
| S03 | Official CPCB PDF search result identifies report | Full PDF and Tamil Nadu table extraction |
| S04 | Readable official catalog, publication/update metadata; empty resource listing | Accessible resource IDs and payloads |
| S05, S06 | Official Census table/handbook metadata with download links | XLSX/PDF contents and matching geographic codes |
| S07, S08 | Official service/layer metadata including CRS and fields | Complete polygon query, effective date, license |
| S09, S10 | Extract offerings and OSM licensing page read | Actual clipped graph quality and restrictions |
| S11, S12 | Official PDF indexed excerpts | Page-level review, units, periods and scope |
| S13, S14 | Official price page and NASA API documentation read | Exact data extraction and coverage |
| S15 | Official product portal identified | Free product and access terms |
| S16, S17 | Official manual/older chapter identified | Relevant current planning sections; no numeric calibration yet |
| S18 | Official municipal-administration overview identified | Reporting jurisdiction and dates |
| S19 | Official dated tender excerpt | Specifications, award and deployment evidence |
| S20 | Official service-procedure page read | Current applicability and conflicts with S01 |
| S21, S22 | Primary technology documentation read | Runtime/account/solver validation in later phases |

## Phase 2 acquisition result

The Phase 1 table above records the **initial discovery state**, not current download status. Phase 2 saved 18 byte-identical raw payloads across 16 source IDs in `03_data/raw/Sxx/2026-09-23/`; exact retrieval URLs, dates, byte counts and SHA256 digests are in `02_research/acquisition_manifest.csv`. The acquired bundle includes both recent TNPCB annual PDFs, 2011 Census workbook/handbook, all 200 GCC ward polygons, GCC cost/tender documents, 2025 NASA weather and a dated Geofabrik Southern Zone PBF. S04's saved catalog HTML still exposes no bin resource; it is **not** a bin inventory. S10 and S21–S22 are documentation references, S15 has no verified free product payload, and S16–S17 returned HTTP 404 at their catalog URLs. These six source IDs have no raw asset. Earlier failed attempts and subsequent corrected URLs for S06 and S12 are retained in `acquisition_attempts.csv`.

Only structured ward, Census, weather and OSM context was transformed into analytical Parquet. The report PDFs/HTML are preserved as original evidence but their numeric tables were not extracted, so no unverified official waste total, cost or fuel price entered the simulation. One Census India TLS certificate exception was logged for the official workbook/PDF download; hash and origin are recorded, and the exception does not establish license or content accuracy. OSM road tags and POIs are incomplete for truck routing; the Phase 2 extract is context, not a validated navigable truck graph. Redistribution terms for most government files remain unresolved.

## Phase 4 references

Official S23 PDF and S24 HTML were downloaded on 2026-09-24 without changing older raw files. Price verified in Annexures I/II; EPA factor verified under diesel consumed. The acquisition manifest now has 20 raw assets across 18 catalog source IDs; the catalog has 24 IDs. S09 was reprocessed locally into a directed access-filtered graph without redownloading or editing its PBF.

## Two-city expansion — 25 September 2026

The six Coimbatore assets S25–S30 were acquired on 2026-09-24 and added to the acquisition manifest/catalog. Total: 30 catalog sources, 26 raw assets across 24 source IDs. HTTP acquisition receipts and SHA256 identify the exact preserved versions; source authority/vintage limitations remain in the catalog. The regional OSM S09 original was reused without mutation. S27 PDF page 17 was checked for the rounded population/area context; S29 scanned quantities were not asserted as verified structured facts. Tests recheck acquired file hashes.
