# Scraping Workflow & Sources

This document details the data sources and technical steps used to extract telecom outage information for each supported operator.

---

## 1. Telia (Mobile & Fixed)

### **Sources**
- **Mobile Portal:** [https://coverage.ddc.teliasonera.net/coverageportal_se](https://coverage.ddc.teliasonera.net/coverageportal_se)
- **Mobile API:** Enghouse-based API endpoint using `AreaTicketList`.
- **Fixed Network (GLUP):** [https://glu2.han.telia.se/bios/glup](https://glu2.han.telia.se/bios/glup)

### **Scraping Workflow**
1.  **API Extraction (Primary):**
    *   Initialize a session and extract an `ert` token and `cacheKey` from the portal landing page.
    *   Call the `get_messages` endpoint for national-level announcements.
    *   Call `get_admin_areas` to list all Swedish counties.
    *   Iterate through each county and fetch granular area tickets via `AreaTicketList`.
2.  **Portal Scraper (Fallback):**
    *   Uses **Playwright** to load the visual coverage portal.
    *   Simulates clicks on region links to trigger network requests.
    *   Intercepts JSON responses directly from the browser's network stream.
3.  **Fixed Network:**
    *   Queries the GLUP XML/Text endpoint with parameters `affectedCounties` and `importantInfo`.

---

## 2. Telenor (includes Lycamobile, Vimla, Fibio)

### **Sources**
- **Portal:** [https://mboss.telenor.se/coverageportal](https://mboss.telenor.se/coverageportal)
- **API:** Enghouse-based API similar to Telia.

### **Scraping Workflow**
1.  **API Extraction:**
    *   Uses the `telenor_fetcher` (sharing common Enghouse logic).
    *   Fetches current messages and area tickets using a bounding box covering Sweden.
2.  **Selenium Scraper:**
    *   Uses **Selenium (Headless Chrome)** to navigate the portal.
    *   Expands the "Disturbances in following counties" accordion.
    *   Clicks the "Zoom/Search" icon for each county to reveal hidden incident tables.
    *   Parses the resulting HTML tables for Incident IDs, descriptions, and start times.

---

## 3. Tre (3)

### **Sources**
- **Driftinfo Page (Primary):** [https://www.tre.se/varfor-tre/tackning/driftstorningar](https://www.tre.se/varfor-tre/tackning/driftstorningar)
- **Coverage Map (Omitted):** `https://www.tre.se/varfor-tre/tackning/tackningskarta`
    - *Note: This source is intentionally disabled because it contains the exact same data as the Driftinfo page. Using both would result in duplicate incidents in the database.*

### **Scraping Workflow**
1.  **JSON State Extraction:**
    *   Performs a standard HTTP GET request to the page.
    *   Uses **BeautifulSoup** to locate the `<script id="__NEXT_DATA__">` tag.
    *   Parses the inner JSON string which contains the complete initial state of the Next.js application, including a list of all current outages.
    *   Extracts coordinates, titles, and severity directly from this structured data.

### **Technical Note: API Strategy Comparison**
While Tre uses the same **Enghouse MIMCS** backend as Telia and Telenor (hosted at `coverage.tre.se`), our system intentionally uses the **Next.js State Parsing** method instead of direct API calls for the following reasons:
*   **Superior Stability:** The `__NEXT_DATA__` blob is the primary data source for Tre's official website, ensuring it is always up-to-date and highly available.
*   **Total Data Retrieval:** This method returns the entire list of national outages in a single request. Direct Enghouse APIs typically require coordinate-based filtering (Bounding Boxes), which is more complex to orchestrate.
*   **Reduced Authentication Complexity:** Tre's MIMCS portal implements a complex session token system. Using the JSON state from the main site bypasses this overhead while still providing structured data.
*   **Conclusion:** Extracting from the Next.js state is the most robust and efficient "API-like" extraction method for Tre.

---

## 4. Tele2 (includes Comviq)

### **Sources**
- **Outage Map:** [https://www.tele2.se/driftstorning-mobilnatet](https://www.tele2.se/driftstorning-mobilnatet)

### **Scraping Workflow**
1.  **Address Probing:**
    *   Uses **Playwright** to load the search-based map.
    *   Iterates through a `tele2_seed_addresses.json` file (a curated list of major Swedish cities/areas).
    *   Types each address into the search bar and triggers the lookup.
    *   Analyzes the resulting page text/DOM for keywords like "störning" (disturbance) or "pågående" (ongoing).
    *   Captures status details for specific localized areas.

---

## Technical Summary

| Operator | Technology | Data Format | Method |
| :--- | :--- | :--- | :--- |
| **Telia** | Playwright / Requests | JSON / XML | API Interception / Direct API |
| **Telenor** | Selenium / Requests | HTML / JSON | Desktop Simulation / Direct API |
| **Tre** | BeautifulSoup | JSON (__NEXT_DATA__) | Static Page Parsing |
| **Tele2** | Playwright | HTML Text | Address Lookup Probing |
