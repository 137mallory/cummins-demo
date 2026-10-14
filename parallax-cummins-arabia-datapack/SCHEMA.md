# 137Parallax data pack schema (Cummins Arabia configuration)

Client: Cummins Arabia (Cummins + Olayan JV distributor, KSA / UAE / Kuwait). Products: Cummins diesel and gas gensets 2.5 kW to 3,500 kW, engines, BESS, parts, service.
Region of interest: Saudi Arabia (60 Hz grid), UAE (50 Hz), Kuwait (50 Hz). Bahrain/Qatar/Oman only as context.

RULES
- Every fact carries a source_url. No invented figures. If a spec is not on a datasheet or official page, write null. Never estimate.
- Dates ISO (YYYY-MM-DD, or YYYY-MM if day unknown).
- Analysis text: plain, no AI phrasing, no em dashes, no hedging fillers. Write for a CEO. Observations and implications, precisely scoped.
- Threat levels: THREAT (direct loss risk for Cummins Arabia), WATCH (monitor), OPPORTUNITY (Cummins Arabia can exploit).
- Keep summaries 1 to 3 sentences.

## competitor file: data/competitors/<id>.json
{
  "id": "caterpillar",
  "name": "Caterpillar",
  "legal_name": "Caterpillar Inc.",
  "brands": ["Cat", "Perkins", "FG Wilson"],
  "hq": "Irving, Texas, USA",
  "founded": 1925,
  "employees": "…as stated with date",
  "revenue": "…with year and source",
  "sector": "…",
  "positioning_text": "2 to 4 sentences on what they are and how they play in KSA/UAE/Kuwait power gen",
  "leadership": [{"name": "", "title": "", "scope": "global|region", "source_url": ""}],
  "regional_entities": [{"name": "Zahid Tractor", "country": "KSA", "role": "exclusive dealer", "since": "", "hq_city": "", "source_url": ""}],
  "movements": [
    {"date": "2026-05-12", "headline": "", "summary": "", "category": "Contract|Expansion|Product|Partnership|Leadership|Financial|Pricing|Capacity|Regulatory", "country": "KSA|UAE|Kuwait|Global|GCC", "source_url": "", "source_domain": "",
     "relevance": {"level": "THREAT|WATCH|OPPORTUNITY", "analysis": "why this matters to Cummins Arabia, what it signals, what Cummins Arabia can do"}}
  ],
  "products": [
    {"model": "", "series": "", "category": "Diesel genset|Gas genset|BESS|Engine", "frequency_hz": 50, "standby_kva": null, "standby_kw": null, "prime_kva": null, "prime_kw": null, "continuous_kw": null,
     "engine_model": "", "cylinders": null, "displacement_l": null, "aspiration": "", "bore_stroke_mm": "", "rated_rpm": null, "fuel": "Diesel|Natural gas",
     "fuel_consumption_lph_100": null, "fuel_consumption_lph_75": null, "fuel_consumption_lph_50": null,
     "length_mm": null, "width_mm": null, "height_mm": null, "dry_weight_kg": null,
     "emissions": "", "alternator": "", "controller": "", "voltage": "", "ambient_derate_note": "", "data_center_rating": "",
     "source_url": "", "datasheet_url": "", "spec_confidence": "datasheet|brochure|secondary"}
  ],
  "partnerships": [
    {"partner": "", "partner_type": "Dealer|OEM|Packager|EPC|Rental|Government|Utility|Hyperscaler|Consultant|Financier|Academic",
     "relationship_label": "EXCLUSIVE_DISTRIBUTOR|DEALER|JV|OEM_SUPPLIER|PACKAGER|FRAMEWORK_SUPPLIER|MOU|LOCALIZATION_PARTNER|SERVICE_PARTNER|KEY_ACCOUNT|RENTAL_FLEET_SUPPLY|TECHNOLOGY_LICENCE",
     "since": "", "country": "", "scope": "", "source_url": "",
     "why_it_matters": {"level": "THREAT|WATCH|OPPORTUNITY", "analysis": ""}}
  ],
  "geo_footprint": [
    {"country": "KSA", "city": "Dammam", "facility_type": "Dealer branch|Service centre|Warehouse|Rebuild centre|Manufacturing|Regional HQ|Training centre|Rental depot", "entity": "", "notes": "", "source_url": ""}
  ],
  "gulf_reference_projects": [{"date": "", "project": "", "country": "", "segment": "Data centre|Utility|Oil & gas|Defense|Healthcare|Rental|Construction|Marine|Mining", "capacity": "", "summary": "", "source_url": ""}],
  "sources": ["…all URLs used"]
}

## client file: data/client/cummins.json
Same product schema. Include every relevant product in 50 Hz and 60 Hz, 500 kVA and above, plus Centum series, HSK78G gas, QSK95 based, BESS. Add "positioning_text", "regional_entities" (Cummins Arabia branches), "leadership".

## tenders file: data/tenders.json
{
  "tenders": [
    {"id": "", "title": "", "issuer": "", "country": "", "portal": "Etimad|CAPT|ADNOC|DEWA|EtihadWE|SEC|MEW|Aramco|Other", "segment": "", "status": "Open|Prequalification|Awarded|Expected", "published": "", "closes": "", "value": "", "scope_summary": "", "genset_relevance": "what power equipment is required, kVA band, fuel, quantity if stated", "source_url": "",
     "cummins_fit": {"fit": "STRONG|PARTIAL|WEAK", "matching_products": ["C2750D5"], "analysis": "", "likely_competitors": []}}
  ],
  "pipeline_signals": [
    {"date": "", "signal": "", "project": "", "country": "", "segment": "", "stage": "Land|Grid tender|EPC award|Design|Genset package expected", "expected_power_need": "", "source_url": "", "analysis": ""}
  ]
}
