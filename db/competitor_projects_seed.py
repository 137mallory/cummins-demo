"""Writes <pack>/competitor_projects.json: the curation of what each competitor is working on.

A project is a deal, programme, build or reference the record names. The curation says which records form
one project and adds what the records do not hold as a field (kind, stage, scale, a dated timeline). Text,
dates, links and the assessment are read from the records at build time by db/competitor_projects.py:
  move    a headline in competitors[cid].profile.moves   (summary, analysis, level, url)
  news    a title in competitorNews[cid]                  (description, analysis, level, url)
  ref     a project in competitors[cid].profile.refs     (the Gulf reference projects)
  partner a partner row id                                (note, the analyst's read in `mean`, sources)

stage: 1 Planned, 2 Committed (contracted or funded), 3 In progress (delivering or being built), 4 Delivered or in service.
Run:  python db/competitor_projects_seed.py <pack_dir>
"""
import json
import os
import sys

G, W = "Gulf", "Worldwide"
P = []


def add(cid, pid, name, kind, region, customer, location, stage, note, refs, timeline, specs, mw=None, stance=None):
    P.append({"id": pid, "cid": cid, "name": name, "kind": kind, "region": region, "customer": customer, "location": location,
              "stage": stage, "stageNote": note, "refs": refs, "timeline": timeline, "specs": specs, "mw": mw, "stance": stance})


# ------------------------------------------------------------------ Caterpillar
C = "CATERPIL"
add(C, "cat-joule-utah", "Joule / Wheeler 4 GW data centre campus, Utah", "Customer project", W, "Joule Capital Partners (dealer Wheeler Machinery)", "Central Utah, USA",
    2, "Agreement announced Aug 2025 for a 4,000-acre campus; launch is targeted for 2026.", {"move": ["Joule, Caterpillar and Wheeler"], "partner": ["JOULECAP"]},
    [["2025-08-07", "Joule, Caterpillar and Wheeler announce the agreement"], ["2026", "Launch targeted"]],
    [["Equipment", "Cat G3520K gas gensets with combined cooling, heat and power"], ["Storage", "1.1 GWh grid-forming battery"], ["Scale", "4 GW total energy, 4,000 acre campus"]], 4000)
add(C, "cat-monarch", "Monarch Compute Campus, 2 GW gas power (AIP Corp, Boyd CAT)", "Customer project", W, "American Intelligence & Power Corp (dealer Boyd CAT)", "West Virginia, USA",
    2, "Alliance formed 28 Jan 2026. Deliveries run Sep 2026 to Aug 2027 with 2 GW online in 2027; 8 GW is planned in total.", {"move": ["AIP Corp, Caterpillar and Boyd CAT"], "partner": ["AMERICAN"]},
    [["2026-01-28", "Alliance announced"], ["2026-09", "Deliveries begin"], ["2027-08", "Deliveries complete; 2 GW online in 2027"]],
    [["Equipment", "Cat G3516 fast-response natural gas gensets with battery storage and SCR"], ["Scale", "2 GW now, 8 GW planned"]], 2000)
add(C, "cat-propwr", "ProPetro (PROPWR) 1.5 GW gas generation framework", "Framework supply", W, "ProPetro, PROPWR division", "Not stated (record: global)",
    2, "Framework signed 29 Apr 2026: at least 1.5 GW over five years, option to about 2.1 GW; 550 MW already ordered.", {"move": ["PROPWR signs framework"], "partner": ["PROPETRO"]},
    [["2026-04-29", "Framework agreement signed"], ["2031", "About 2.6 GW operating by end 2031, including the 550 MW already ordered"]],
    [["Equipment", "Cat gas generation assets"], ["Scale", "1.5 GW minimum, about 2.1 GW with option"], ["Uses", "Data centres, oil and gas, industry"]], 1500)
add(C, "cat-onepwr", "OnePWR / Vero3 500 MW gas power with carbon capture", "Customer project", W, "OnePWR Solutions (owner-operator), Vero3 (CO2 storage)", "Not stated (record: global)",
    1, "Collaboration announced Mar 2026; the inaugural 500 MW prime power project is targeted to launch in 2026. Caterpillar supplies generation and leads front-end engineering for the capture.", {"move": ["Caterpillar, OnePWR Solutions and Vero3"], "partner": ["ONEPWRSO"]},
    [["2026-03", "Collaboration announced"], ["2026", "Inaugural project targeted to launch"]],
    [["Scope", "Gas generation, carbon capture, battery storage, permanent CO2 sequestration"], ["Scale", "500 MW prime power (inaugural project)"]], 500)
add(C, "cat-energyvault-texas", "Energy Vault 1.25 GW hyperscaler power, Texas", "Customer project", W, "Energy Vault (for an unnamed AI data centre operator)", "Texas, USA",
    2, "Signed Aug 2026, Energy Vault's largest contract. A power-generation EPC deploys Cat gensets with Energy Vault grid-forming batteries; first deployments within 4 to 12 months.", {"move": ["Energy Vault signs 1.25 GW"]},
    [["2026-08-07", "Contract announced"], ["2027-08", "First deployments due within 4 to 12 months of signing"]],
    [["Equipment", "Cat gensets plus Energy Vault grid-forming BESS"], ["Scale", "1.25 GW integrated power"]], 1250)
add(C, "cat-stella", "Stella Power Titan 130 turbine packages", "Customer project", W, "Stella Power Company", "North America",
    2, "Large order placed Aug 2026 with Caterpillar's Solar Turbines for onsite power.", {"move": ["Stella Power orders"]},
    [["2026-08-04", "Order announced"]],
    [["Equipment", "Solar Turbines PGM130 packages (Titan 130, over 16 MW each, 90 second start)"], ["Uses", "Data centres, industrial sites, oil and gas"]])
add(C, "cat-kazakh-mine", "Off-grid gold mine power, Aktobe, Kazakhstan", "Customer project", W, "West Gold Mining (dealer Borusan Cat)", "Aktobe, Kazakhstan",
    2, "Two Cat G3500K gas gensets selected for a site nearly 300 km from the nearest city; small in scale.", {"news": ["Caterpillar G3500K gas gensets selected"]},
    [["2026-10-07", "Selection reported"]],
    [["Equipment", "2 x Cat G3500K gas gensets"], ["Use", "Prime off-grid power"]])
add(C, "cat-engine-capacity", "Large-engine capacity expansion (Lafayette and gas-engine restart)", "Capacity expansion", W, "Caterpillar (own investment)", "Lafayette, Indiana, USA, and other large-engine sites",
    3, "USD 725m Lafayette expansion committed Oct 2025; plan raised in Apr 2026 to about 3x 2024 large-engine capacity (about 15 GW a year more); the 10 MW gas engine restarts with shipments from Q4 2026.",
    {"move": ["Caterpillar commits USD 725 million", "Q1 2026: Caterpillar triples"], "news": ["Caterpillar restarts 10 MW"]},
    [["2025-10-21", "USD 725m Lafayette expansion committed"], ["2026-04-30", "Capacity plan raised to about 3x 2024 levels, investment mainly 2027 to 2029"], ["2026-09-28", "10 MW gas engine restart reported, about 1.5 GW of capacity back online"], ["2026-10", "Shipments from the restarted line expected from Q4 2026"]],
    [["Investment", "USD 725m (Lafayette) plus USD 100m workforce pledge"], ["Capacity", "About 15 GW a year of added large-engine capacity"], ["Order book", "Large gas-engine orders booked into 2028-29 (Trefis)"]], stance="threat")
add(C, "cat-red-sea", "The Red Sea Project construction power", "Gulf reference", G, "Red Sea Global (via Zahid Tractor)", "Saudi Arabia, west coast",
    4, "Delivered (record dated Jun 2022): 69 Cat gensets for the construction phase.", {"ref": ["The Red Sea Project construction power"], "partner": ["REDSEAGL"]},
    [["2022-06", "69 gensets supplied by Zahid Tractor"]],
    [["Equipment", "69 Cat gensets, diesel or B100 biodiesel, with Cat Connect remote monitoring"], ["Scale", "32 MW prime"], ["Segment", "Construction"]], 32)
add(C, "cat-neom", "NEOM earthworks fleet (The Line)", "Gulf reference", G, "NEOM (via Zahid Tractor)", "NEOM, Saudi Arabia",
    3, "Ongoing: about 5,000 Cat machines supported on site, expected to double the following year. No genset scope is stated.", {"ref": ["NEOM earthworks fleet"], "partner": ["NEOMVIAZ"]},
    [["2023-01", "About 5,000 Cat machines on site, supported by Zahid Tractor"]],
    [["Scope", "Machines, customer value agreements, technician training, 24/7 support"], ["Genset scope", "Not stated"]])
add(C, "cat-tanajib", "Aramco Tanajib Gas Plant temporary power", "Gulf reference", G, "Saudi Aramco (via Altaaqa, Zahid Group)", "Tanajib, Saudi Arabia",
    4, "Delivered for one month; the genset brand is not named in the source.", {"ref": ["Aramco Tanajib Gas Plant"], "partner": ["ALTAAQAA"]},
    [["Undated", "Temporary power delivered by Altaaqa"]],
    [["Scale", "1.94 MW (2 x 970 kW), one month"], ["Voltage", "460 V and 380 V with a 50 kVA transformer and LV panel"], ["Segment", "Oil and gas"]], 1.94)
add(C, "cat-themar", "Themar Al Emarat greenhouse hybrid power, Sharjah", "Gulf reference", G, "Themar Al Emarat LLC (via Al-Bahar)", "Sharjah, UAE",
    4, "Delivered Feb 2020 as a single-supplier microgrid, then extended with 3516E sets for a 5.94 MW hybrid.", {"ref": ["Themar Al Emarat greenhouse"], "partner": ["THEMARAL"]},
    [["2020-02", "6 MW microgrid delivered by Al-Bahar"]],
    [["Equipment", "Cat PV, five 3412 gensets, Cat energy storage and Master Microgrid Controller; later 3516E 50 and 60 Hz HV ratings"], ["Scale", "5.94 MW hybrid; earlier 6 MW (2.7 MW PV, 3.24 MW gensets, 286 kWh storage)"], ["Segment", "Utility"]], 5.94)
add(C, "cat-lamprell", "Lamprell jack-up rig power (LeTourneau Super 116E)", "Gulf reference", G, "Lamprell (via Al-Bahar)", "UAE",
    4, "First of two rigs commissioned Nov 2022; the second rig is in development.", {"ref": ["Lamprell jack-up rig power"], "partner": ["LAMPRELL"]},
    [["2020-01", "Order placed"], ["2022-11", "First rig's power package commissioned"]],
    [["Equipment", "5 x Cat 3516C (1,530 ekW, 60 Hz, 600 V) and 1 x 3512C (1,310 ekW)"], ["Segment", "Marine"]])
add(C, "cat-dubai-metro", "Dubai Metro emergency backup power", "Gulf reference", G, "Roads & Transport Authority, Dubai (via Al-Bahar)", "Dubai, UAE",
    4, "Delivered for phases 1 and 2 (2009), with a three-year maintenance contract. Caterpillar is the incumbent reference for the Gold Line expansion that Cummins Arabia is tracking.", {"ref": ["Dubai Metro emergency backup power"], "partner": ["DUBAIROA"]},
    [["2009", "20 gensets supplied, installed and commissioned"]],
    [["Equipment", "20 Cat gensets: 8 x 3516, 8 x 3512, 2 x C18, 2 x C15"], ["Rating", "320 to 1,820 kW each, 50 Hz"], ["Service", "Staff training and a three-year maintenance contract"]])
add(C, "cat-covid", "COVID-19 emergency power, Abu Dhabi and Kuwait", "Gulf reference", G, "Quarantine and test facilities (via Al-Bahar)", "Abu Dhabi, UAE, and Kuwait",
    4, "Delivered Apr 2020 as rental power.", {"ref": ["COVID-19 emergency power"], "partner": ["MOHAMEDA"]},
    [["2020-04", "17 MW of rental power deployed"]],
    [["Equipment", "10 x C15 500 kVA, 4 x C32 1,000 kVA, 8 x 3512 1,500 kVA; plus C13 sets with ATS for five test centres; two C18 and one C13 in Kuwait"], ["Scale", "17 MW rental"], ["Segment", "Healthcare"]], 17)

# ------------------------------------------------------------------ Rolls-Royce Power Systems
R = "ROLLSROY"
add(R, "rr-energyvault", "Energy Vault 275 MW mtu engine capacity for AI sites", "Customer project", W, "Energy Vault (financed by Eagle Point Credit Management)", "Not stated",
    2, "Fully contracted 10 Sep 2026. Deliveries run from H2 2027 to H1 2028.", {"news": ["Energy Vault contracts 275 MW"]},
    [["2026-09-10", "Capacity secured and fully contracted"], ["2027-07", "Deliveries start (H2 2027)"], ["2028-06", "Deliveries finish (H1 2028)"]],
    [["Equipment", "Reciprocating engine generation using Rolls-Royce mtu technology"], ["Scale", "275 MW"]], 275)
add(R, "rr-kuwait-t2", "Kuwait International Airport Terminal 2 backup power", "Gulf reference", G, "DGCA and Ministry of Public Works (builder Limak), via Al Mulla Power Solutions", "Kuwait",
    3, "Awarded Nov 2025; units were due for delivery in early 2026, then commissioning. Completion has not been reported.", {"move": ["Seven mtu 20V4000 DS3600"], "ref": ["Kuwait International Airport Terminal 2"], "partner": ["LIMAKTUR"]},
    [["2025-11-05", "Award announced"], ["2026-03", "Delivery due (early 2026), then commissioning"]],
    [["Equipment", "7 x mtu 20V4000 DS3600 diesel gensets (3,580 to 3,730 kVA class)"], ["Design", "55 C ambient"], ["Scope", "Catering building and central energy infrastructure"]])
add(R, "rr-saudi-trains", "Dammam to Riyadh high-speed trains, mtu rail engines", "Gulf reference", G, "Stadler Bussnang AG", "Saudi Arabia",
    2, "Ordered Aug 2025, with an option for 40 more. A rail engine order, not a genset sale.", {"move": ["50 mtu 12V4000 R64 engines"], "ref": ["Dammam to Riyadh high-speed trains"], "partner": ["STADLERB"]},
    [["2025-08-21", "50 engines ordered, 10 trains"]],
    [["Equipment", "50 x mtu 12V4000 R64 rail engines, 1,500 kW each, EU Stage V"], ["Option", "40 more engines"], ["Trains", "10 trains, up to 200 km/h"]])
add(R, "rr-kaust", "KAUST supercomputing facility dynamic UPS", "Gulf reference", G, "King Abdullah University of Science and Technology", "Thuwal, Saudi Arabia",
    4, "Delivered; won in Apr 2021 after discussions since 2016, with substantial local content.", {"ref": ["KAUST supercomputing facility"], "partner": ["KINGABDU"]},
    [["2016", "Discussions begin"], ["2021-04-07", "Contract announced"], ["2021-07", "Delivery in summer 2021"]],
    [["Equipment", "12 x mtu Kinetic PowerPacks (16V4000 G74S, 1.6 MW each)"], ["Scale", "19.2 MW"], ["Segment", "Data centre"]], 19.2)
add(R, "rr-makeen", "Makeen: mtu licence and exclusive Saudi distribution", "Programme", G, "Saudi Engines Manufacturing Company (Makeen: Aramco, HD Hyundai, Dussur)", "Saudi Arabia",
    2, "Exclusive stationary-power distribution effective 1 Oct 2025; individual licence for mtu Series 2000 marine engines signed Oct 2026. No volumes, investment or start date are disclosed.",
    {"move": ["Makeen becomes exclusive mtu distributor"], "news": ["Rolls-Royce licenses MAKEEN"], "partner": ["SAUDIENG"]},
    [["2023-11", "Framework agreement (the partner record dates it 14 Dec 2023)"], ["2025-10-01", "Exclusive distribution extended to stationary power across Saudi Arabia"], ["2026-10-01", "Individual licence for Series 2000 marine engines"]],
    [["Scope", "Local manufacture and assembly, parts, factory-certified MRO, integrated power solutions"], ["Next target", "Rail, after marine"]], stance="threat")
add(R, "rr-almulla-mro", "Al Mulla Power Solutions mtu MRO headquarters, Ahmadi", "Gulf reference", G, "Al Mulla Power Solutions", "Ahmadi, Kuwait",
    3, "Under construction with completion due September 2026; an opening has not been reported.", {"move": ["Al Mulla Power Solutions builds mtu MRO"]},
    [["2024", "Agreement describes stage 4 overhaul capability for four engines at once"], ["2026-03-05", "Build announced"], ["2026-09", "Completion due"]],
    [["Site", "5,000 sqm plot, over 3,600 sqm built up, Ahmadi industrial zone"], ["Scope", "MRO centre, workshops, spare parts, technical support, training centre, offices"]])
add(R, "rr-ignitis", "Ignitis 582 MWh mtu battery order, Lithuania", "Customer project", W, "Ignitis Group (Lithuania); Sunly (Latvia) separately", "Lithuania",
    2, "Ordered Sep 2025, Rolls-Royce's largest battery order; operational from 2027.", {"move": ["Largest ever mtu battery order"], "partner": ["IGNITISG"]},
    [["2025-09-16", "Order announced"], ["2027", "Sites operational"]],
    [["Equipment", "mtu EnergyPack with EnergetIQ Manager controller"], ["Scale", "582 MWh / 291 MW at three sites (wind farms and a pumped storage plant)"]], 291)
add(R, "rr-avk", "AVK five-year Series 4000 capacity agreement", "Framework supply", W, "AVK (UK and Ireland packager)", "United Kingdom and Ireland",
    2, "Signed Dec 2025: guaranteed Series 4000 emergency genset capacity for five years.", {"move": ["Five-year guaranteed Series 4000"], "partner": ["AVKUKAND"]},
    [["2025-12-04", "Five-year capacity agreement signed"]],
    [["Equipment", "mtu Series 4000 emergency gensets, HVO-ready"], ["Track record", "AVK has taken over 600 mtu gensets in a decade"]])
add(R, "rr-us-capacity", "US Series 4000 capacity expansion (Mankato and Aiken)", "Capacity expansion", W, "Rolls-Royce Power Systems (own investment)", "Mankato, Minnesota, and Aiken, South Carolina, USA",
    3, "Mankato logistics centre opened Jul 2026 (genset capacity to more than double by end 2026). Aiken engine machining starts production July 2027.",
    {"move": ["USD 24 million Mankato expansion", "USD 75 million Aiken", "Mankato logistics centre opens"]},
    [["2025-06-03", "USD 24m Mankato expansion announced"], ["2025-07-15", "USD 75m Aiken expansion announced"], ["2026-01", "Aiken construction starts (Q1 2026)"], ["2026-07-09", "Mankato logistics centre opens"], ["2026-12", "Genset capacity more than doubles by end 2026"], ["2027-07", "Aiken production starts"]],
    [["Investment", "USD 24m (Mankato) and USD 75m (Aiken)"], ["Output", "Series 4000 genset production up more than 120% versus the prior year"], ["Frequency", "Mankato builds 60 Hz sets"]], stance="watch")
add(R, "rr-dubai-airport", "Dubai International Airport standby power", "Gulf reference", G, "Dubai International Airport", "Dubai, UAE",
    4, "Long-running: mtu gensets and combined heat and power have operated at the airport for many years; quantity not stated.", {"ref": ["Dubai International Airport standby power"], "partner": ["ALMASAOO"]},
    [["2025-11-05", "Cited by Rolls-Royce among major airports it secures"]],
    [["Equipment", "mtu gensets and CHP systems"], ["Quantity", "Not stated"]])
add(R, "rr-saudi-naval", "Saudi naval and government fleets, mtu marine engines", "Gulf reference", G, "Saudi naval and government fleets", "Saudi Arabia",
    3, "450 mtu marine engines in service, serviced with local partners; cited in the World Defense Show 2026 localisation statement.", {"ref": ["Saudi naval and government fleets"], "partner": ["SAUDIENG"]},
    [["2026-02-06", "450 engines in service reported"]],
    [["Equipment", "450 mtu marine engines"], ["Local content", "Over 80% Saudisation reported"], ["Segment", "Defence"]])
add(R, "rr-adports", "Abu Dhabi Ports Group fast ferries", "Gulf reference", G, "Abu Dhabi Ports Group (built by Penguin Shipyard International)", "Abu Dhabi, UAE",
    4, "Delivered: two high-speed aluminium ferries.", {"ref": ["Abu Dhabi Ports Group fast ferries"], "partner": ["SAUDIENG"]},
    [["2023-09-04", "Vessels announced"]],
    [["Equipment", "8 x mtu 16V4000 engines (four per vessel)"], ["Power", "Over 10,000 kW per vessel"], ["Segment", "Marine"]])

# ------------------------------------------------------------------ Rehlko
H = "REHLKO"
add(H, "reh-innio", "INNIO 1.25 GW gas-engine framework", "Framework supply", W, "INNIO Group (Jenbacher), delivered through Clarke Energy", "Clarke Energy's authorised territories (no KSA, UAE or Kuwait office)",
    2, "Three-year framework signed Apr 2026 allocating 1.25 GW of INNIO gas engine capacity to Rehlko.", {"move": ["Rehlko and INNIO sign"], "partner": ["INNIOGRO"]},
    [["2026-04-09", "Framework signed"], ["2029-04", "Framework term ends (three years)"]],
    [["Equipment", "INNIO gas engines as integrated gas genset plus battery hybrids"], ["Scale", "1.25 GW over three years"], ["Markets", "Hyperscale, colocation, enterprise data centres; flexible generation"]], 1250)
add(H, "reh-hyperscale-us", "1.7 GW of North American hyperscale backup orders", "Customer project", W, "Multiple North American hyperscale campuses", "North America",
    2, "Orders secured within 60 days to 29 Apr 2026, for diesel modular backup generator solutions.", {"move": ["Rehlko secures another 1.7 GW"]},
    [["2026-04-29", "Orders announced"]],
    [["Equipment", "Diesel modular backup generator solutions, repeatable architectures"], ["Scale", "1.7 GW"]], 1700)
add(H, "reh-jordan-dc", "Jordan data centre backup power", "Customer project", W, "Jordan data centre (via Alghanem Trading and Contracting)", "Jordan",
    4, "Delivered; capacity and models were not published.", {"move": ["Rehlko and Alghanem deliver"], "ref": ["Data centre backup power, Jordan"], "partner": ["ALGHANEM"]},
    [["2025-11-11", "Delivery reported"]],
    [["Equipment", "Rehlko generators (models not published)"], ["Channel", "Alghanem, exclusive Jordan distributor for over 25 years"]])
add(H, "reh-changzhou", "Changzhou capacity doubling, 5.5 GW to 11 GW", "Capacity expansion", W, "Rehlko (own investment)", "Changzhou, China",
    3, "Programme launched Sep 2026 to reach 11 GW without expanding the footprint; the plant serves EMEA.", {"news": ["Rehlko launches programme to double Changzhou"]},
    [["2026-09-22", "Programme launched"]],
    [["Output", "From 5.5 GW to 11 GW of backup power"], ["Range", "Generator systems from 6 kW to 4,000 kW and key components"], ["Yield", "First pass yield from 93% to 98%"]])
add(H, "reh-colmar", "Liebherr Colmar engine plant extension for KD Series", "Capacity expansion", W, "Liebherr-Components Colmar (supplier to Rehlko)", "Colmar, France",
    3, "Extension of nearly 12,000 square metres marked in a Jun 2026 ceremony; engine capacity for Rehlko more than doubles once fully ramped.", {"move": ["Liebherr expands Colmar"], "partner": ["LIEBHERR"]},
    [["2026-06-17", "Extension ceremony"]],
    [["Site", "Nearly 12,000 square metre extension"], ["Output", "Engine production for Rehlko to more than double"]])
add(H, "reh-kenosha", "Kenosha eFRAME enclosure assembly", "Capacity expansion", W, "Rehlko (own investment)", "Kenosha, Wisconsin, USA",
    3, "Opened Jun 2026; initial production late 2026, full capacity early 2027.", {"move": ["Rehlko opens Kenosha"]},
    [["2026-06-01", "Facility opened"], ["2026-12", "Initial production (late 2026)"], ["2027-03", "Full capacity (early 2027)"]],
    [["Product", "Integrated eFRAME enclosures for backup generators up to 4 MW"], ["Plan", "Capacity up more than 400% through the decade"]])
add(H, "reh-cholet", "Cholet switchgear plant expansion", "Capacity expansion", W, "Rehlko (own investment)", "Cholet, France",
    3, "EUR 12m expansion, completion due Nov 2026.", {"news": ["Rehlko invests EUR 12 million"]},
    [["2026-07-14", "Investment announced"], ["2026-11", "Completion due"]],
    [["Investment", "EUR 12m"], ["Space", "56% more manufacturing space over five years"], ["Lead time", "30% shorter on completion"]])
add(H, "reh-mdsenergy-ksa", "Mobily telecom sites (MDS Energy reference)", "Gulf reference", G, "Mobily", "Saudi Arabia",
    4, "A customer reference of MDS Energy, the Midis affiliate that distributes Rehlko and Vertiv; equipment scope and capacity not published.", {"ref": ["Mobily (telecom) sites"], "partner": ["MIDISGRO"]},
    [["Undated", "Listed as a customer reference"]], [["Segment", "Data centre"], ["Scope", "Not published"]])
add(H, "reh-mdsenergy-sib", "The Saudi Investment Bank (MDS Energy reference)", "Gulf reference", G, "The Saudi Investment Bank", "Saudi Arabia",
    4, "A customer reference of MDS Energy; equipment scope and capacity not published.", {"ref": ["The Saudi Investment Bank"], "partner": ["MIDISGRO"]},
    [["Undated", "Listed as a customer reference"]], [["Segment", "Data centre"], ["Scope", "Not published"]])
add(H, "reh-mdsenergy-airports", "Abu Dhabi Airport and Al Ain Airport (MDS Energy reference)", "Gulf reference", G, "Abu Dhabi Airport and Al Ain Airport", "UAE",
    4, "A customer reference of MDS Energy; whether the scope was Kohler gensets or Vertiv equipment is not stated.", {"ref": ["Abu Dhabi Airport and Al Ain Airport"], "partner": ["MIDISGRO"]},
    [["Undated", "Listed as a customer reference"]], [["Segment", "Construction"], ["Scope", "Not stated"]])
add(H, "reh-mdsenergy-landmarks", "Sheikh Zayed Grand Mosque and Yas Mall (MDS Energy reference)", "Gulf reference", G, "Sheikh Zayed Grand Mosque; Yas Mall", "Abu Dhabi, UAE",
    4, "Customer references of MDS Energy; equipment scope and capacity not published.", {"ref": ["Sheikh Zayed Grand Mosque and Yas Mall"], "partner": ["MIDISGRO"]},
    [["Undated", "Listed as customer references"]], [["Segment", "Construction"], ["Scope", "Not published"]])
add(H, "reh-mdsenergy-dubai", "Emirates Airlines, Al Jalila Children's Hospital, NYU and Zayed University (MDS Energy reference)", "Gulf reference", G, "Emirates Airlines; Al Jalila Children's Hospital; NYU; Zayed University", "UAE",
    4, "Dubai customer references of MDS Energy; equipment scope and capacity not published.", {"ref": ["Emirates Airlines, Al Jalila"], "partner": ["MIDISGRO"]},
    [["Undated", "Listed as customer references"]], [["Segment", "Healthcare"], ["Scope", "Not published"]])

# ------------------------------------------------------------------ Mitsubishi (MHIET / MGS)
M = "MITSUBIS"
add(M, "mit-amiral", "Amiral cogeneration plant, Jubail: first locally assembled M501JAC", "Gulf reference", G, "TAQA and JERA (serving the SATORP petrochemical complex)", "Jubail, Saudi Arabia",
    3, "First M501JAC turbine assembled at Dammam in Oct 2025, destined for the plant. A Mitsubishi Power group reference, not an MGS genset project.", {"move": ["Mitsubishi Power unveils first locally assembled"], "ref": ["Amiral Cogeneration Plant"], "partner": ["SAUDIARA"]},
    [["2025-10-14", "First locally assembled turbine unveiled at Dammam"]],
    [["Equipment", "Mitsubishi Power M501JAC gas turbine"], ["Scale", "475 MW cogeneration plant"], ["Segment", "Utility"]], 475)
add(M, "mit-jeddah-shuqaiq", "Jeddah South and Shuqaiq power plants fuel conversion", "Gulf reference", G, "Saudi Energy (local EPC Dar Al Balad)", "Jeddah and Shuqaiq, Saudi Arabia",
    2, "Contract won Jul 2026 for dual-fuel conversion of four units at each plant. Boilers, not gensets.", {"move": ["Mitsubishi Power wins boiler supply"], "ref": ["Jeddah South and Shuqaiq"], "partner": ["SAUDIARA"]},
    [["2026-07-13", "Contract announced"]],
    [["Equipment", "Mitsubishi Power boiler components"], ["Scale", "About 2.9 GW per plant, four units each"], ["Agent", "Mitsubishi Corporation Machinery"]])
add(M, "mit-kuwait-dealer", "Kuwait ministry and commercial projects (Al-Sultan & Khalaf)", "Gulf reference", G, "Kuwaiti ministries and commercial clients", "Kuwait",
    4, "The Kuwait MGS dealer states it takes part in ministry and commercial projects; specific sites and MW are not published.", {"ref": ["Kuwait ministry and commercial projects"], "partner": ["ALSULTAN"]},
    [["Undated", "Dealer states participation"]], [["Segment", "Construction"], ["Scope", "Installation, commissioning, training and handover"]])
add(M, "mit-sdec-dc", "Saudi data centre and industrial sites (SDEC MGS-R)", "Gulf reference", G, "Saudi data centre and industrial operators", "Saudi Arabia",
    1, "SDEC markets the MGS-R range as Uptime certified for data centres; no named installations are published.", {"ref": ["Saudi data centre and industrial sites"], "partner": ["SAUDIDIE"]},
    [["Undated", "Range marketed as Uptime certified"]], [["Equipment", "Mitsubishi MGS-R compact and medium range"], ["Segment", "Data centre"]])
add(M, "mit-johor", "MGS assembly plant, Johor Bahru, Malaysia", "Capacity expansion", W, "MHI Engine System Asia (with WDG Assembly)", "Johor Bahru, Malaysia",
    4, "Added Feb 2025 alongside Singapore and Vietnam assembly, to meet data centre demand in Southeast Asia.", {"move": ["MHI-ESA adds MGS assembly plant"], "partner": ["MHIENGIN"]},
    [["2025-02-14", "New production hub announced"]],
    [["Site", "MGS assembly hub, with Singapore and Vietnam"], ["Supply", "MGS assembly plants supply the Middle East"]])

# ------------------------------------------------------------------ Perkins / FG Wilson
F = "PERKINSF"
add(F, "per-shaybah", "Saudi Aramco Shaybah field expansion", "Gulf reference", G, "Saudi Aramco (EPC Samsung Engineering), via TAMGO", "Shaybah, Saudi Arabia",
    4, "Delivered: order secured May 2011 for 128 sets, raised to 140; completion was targeted for 2016.", {"ref": ["Saudi Aramco Shaybah field expansion"], "partner": ["TAMGOZAH"]},
    [["2011-05", "Order secured for 128 sets, later 140"], ["2016", "Completion targeted"]],
    [["Equipment", "140 FG Wilson gensets, 13 to 750 kVA"], ["Service", "Maintenance at 55 C ambient and dust storm conditions"], ["Segment", "Oil and gas"]])
add(F, "per-binquraya", "Bin Quaraya residential camp and Schlumberger oilfield rental", "Gulf reference", G, "A Saudi rental company serving Bin Quaraya camp and Schlumberger (via Abdul Latif Jameel Machinery)", "Salasil, north-east of Riyadh, Saudi Arabia",
    4, "Delivered (record dated 2017).", {"ref": ["Bin Quaraya residential camp"], "partner": ["ABDULLAT"]},
    [["2017", "20 Teksan gensets supplied"]],
    [["Equipment", "20 Perkins-powered Teksan gensets: 8 x 150 kVA, 8 x 350 kVA, 4 x 600 kVA prime"], ["Segment", "Rental"]])
add(F, "per-generac", "Generac US industrial diesel sets on Perkins engines", "Framework supply", W, "Generac Power Systems", "United States",
    3, "Generac standardises its 1,000 to 1,500 kW diesel sets on Perkins 4008 and D46L engines.", {"move": ["Generac standardises"], "partner": ["GENERACP"]},
    [["2025-11", "Standardisation reported"]],
    [["Equipment", "Perkins 4008 (30.6 L) and D46L / 4012 (45.8 L) in Generac SD1000 to SD1250 sets"], ["Controller", "Deep Sea G8601"]])
add(F, "per-tria-hvo", "FG Wilson HVO field trials with Tria Energy", "Programme", W, "Tria Energy", "Ireland",
    3, "Trials reported May 2026: diesel-equivalent performance on HVO with no engine or fuel-system change.", {"move": ["FG Wilson gensets pass HVO"], "partner": ["TRIAENER"]},
    [["2026-05-20", "Trial results published"]],
    [["Fuel", "HVO (EN 15940)"], ["Result", "Diesel-equivalent performance, up to 90% lifecycle CO2 saving"], ["Aimed at", "Data centre, construction, critical infrastructure"]])

# ------------------------------------------------------------------ Generac
N = "GENERAC"
add(N, "gen-amazon", "Amazon long-term backup-generator supply agreement", "Framework supply", W, "Amazon", "Not stated; no Gulf scope named in the filing",
    2, "Signed 16 Sep 2026. Initial deliveries of about USD 2.4bn are expected in 2027 and 2028; the USD 8bn is a warrant-vesting threshold, not a committed order.",
    {"news": ["Generac signs long-term Amazon", "Amazon's USD 8bn", "KeyBanc upgrades Generac"]},
    [["2026-09-16", "Agreement signed; Amazon receives a warrant for up to 1,693,745 shares"], ["2027", "Initial deliveries begin"], ["2028", "Deliveries continue; Amazon seen as about USD 1.6bn of 2028 data-centre revenue (KeyBanc)"]],
    [["Equipment", "Backup generators"], ["Scale", "About USD 2.4bn initial deliveries 2027-2028; payments up to USD 8bn to vest the warrant"]], stance="threat")
add(N, "gen-hyperscale-global", "Global hyperscale supply agreements (Middle East in scope)", "Framework supply", W, "Two unnamed hyperscale data centre operators", "APAC, Europe, Middle East and Latin America",
    2, "First agreement signed Jun 2026 after factory visits; a second was secured in Q2 2026. About USD 700m is committed for 2027.", {"move": ["Generac signs global supply agreement", "Generac Q2 2026"], "partner": ["UNNAMEDH"]},
    [["2026-06-02", "First global supply agreement announced"], ["2026-07-29", "Second hyperscale agreement reported with Q2 results"], ["2027", "About USD 700m committed for delivery"]],
    [["Equipment", "Large diesel data centre sets; production in Wisconsin"], ["Backlog", "Data centre backlog about USD 1.6bn"], ["Scope", "Global frame agreement naming the Middle East"]])
add(N, "gen-belvidere", "Belvidere plant and large-megawatt packaging capacity", "Capacity expansion", W, "Generac (own investment)", "Belvidere, Illinois, USA",
    2, "Plant bought Jun 2026 to add large-megawatt genset packaging capacity from Q1 2027; Generac expects over USD 1.25bn of annual large-megawatt capacity.", {"move": ["Generac buys Belvidere"], "news": ["Generac targets more than $1.25bn"]},
    [["2026-02", "Enercon Engineering (enclosures and switchgear) acquired"], ["2026-06-15", "Belvidere plant acquired"], ["2026-09-24", "Annual capacity target of over USD 1.25bn reported"], ["2027-03", "Packaging capacity from Q1 2027"]],
    [["Jobs", "Over 100"], ["Capacity", "More than USD 1.25bn a year of large-megawatt generators"]], stance="threat")

# ------------------------------------------------------------------ Weichai / Baudouin
W_ = "WEICHAIB"
add(W_, "wei-aidc-ramp", "Data centre genset output ramp (4,000 units in 2026)", "Capacity expansion", W, "Weichai Power (own programme)", "China and Europe",
    3, "H1 2026 data centre genset sales passed 1,400 units, above all of 2025; targets are 4,000 units in 2026 and 6,000 in 2027.", {"news": ["Weichai H1 2026", "Brokerage: Generac-Amazon deal"], "move": ["Weichai 2025 results"]},
    [["2026-03-26", "2025 results: data centre backup power sales up 259%"], ["2026-09-10", "H1 2026: over 1,400 data centre gensets sold"], ["2026-12", "2026 target: 4,000 diesel AIDC gensets"], ["2027-12", "2027 target: 6,000"]],
    [["Output", "4,000 AIDC diesel gensets in 2026, 6,000 in 2027; gas gensets 200 then 2,000"], ["Engines", "M-series large-bore engines: 6,700 units in H1 2026 (+31.5%)"]], stance="threat")
add(W_, "wei-generac-m55", "Baudouin M55 engines in Generac's hyperscale agreement", "Framework supply", W, "Generac, for a hyperscale operator", "APAC, Europe, Middle East and Latin America",
    2, "Generac's SDMD2250 to SDMD3250 sets use Baudouin M55 engines and sit under its global hyperscale supply agreement (signed Jun 2026).", {"move": ["Generac's Baudouin M55"], "partner": ["GENERACP"]},
    [["2026-06-02", "Generac signs the global agreement naming the Middle East"]],
    [["Equipment", "Generac SDMD2250, SDMD2500 (12M55) and SDMD3250 (16M55) with Baudouin M55 engines"], ["Alternator and control", "Marathon DataMAX, DSE G8601"]], stance="threat")
add(W_, "wei-cassis", "Baudouin Cassis plant expansion", "Capacity expansion", W, "Baudouin (own investment)", "Cassis, France",
    1, "Expansion and investment projects were discussed in Sep 2026 with local officials; no figures were given.", {"news": ["Baudouin hosts regional prefect"]},
    [["2026-09-14", "Prefect and mayor tour the plant; expansion projects discussed"]],
    [["Site", "Baudouin's French plant for high-horsepower data centre gensets"], ["Scale", "Not disclosed"]])
add(W_, "wei-eodev", "Baudouin SOFC power with EODev", "Programme", W, "EODev", "France and Poland (exclusive), Europe",
    3, "Commercial launch of Baudouin solid oxide fuel cell baseload power is set for Sep 2026 across Europe.", {"move": ["Baudouin partners with EODev"], "partner": ["EODEVXXX"]},
    [["2025-11", "Weichai deepens its Ceres Power collaboration"], ["2026-07-28", "Partnership announced"], ["2026-09", "Commercial launch"]],
    [["Technology", "Solid oxide fuel cell, over 65% electrical efficiency, CE certified"], ["Rights", "Exclusive in France and Poland"]])
add(W_, "wei-almajd", "Saudi municipal buildings, two Baudouin PowerKit gensets", "Gulf reference", G, "Saudi government (via Almajd Power)", "Saudi Arabia",
    4, "Delivered Feb 2022: a small government purchase of two sets through the local partner Almajd Power.", {"ref": ["Saudi government municipal buildings"], "partner": ["ALMAJDPO"]},
    [["2022-02", "Purchase reported"]],
    [["Equipment", "2 x Baudouin 6M16 PowerKit gensets"], ["Segment", "Utility"]])

# ------------------------------------------------------------------ Volvo Penta
V = "VOLVOPEN"
add(V, "vol-dc-programme", "Data centre backup programme with OEMs and integrators", "Programme", W, "OEMs and system integrators (data centre)", "North America and global",
    3, "Positioning built up from Dec 2025 to Apr 2026: modular Tier 4 Final platform, G17 gas engine and battery solutions. North American industrial engine sales doubled.", {"move": ["Volvo Penta positions itself", "Volvo Penta introduces G17", "Volvo Penta reports doubled", "Volvo Penta publishes data centre"], "partner": ["OEMSANDS"]},
    [["2025-12", "Total power solutions positioning for digital infrastructure (CONEXPO 2026)"], ["2026-01", "G17 natural gas engine introduced"], ["2026-02", "North American industrial engine sales reported doubled"], ["2026-04", "Data centre backup power positioning published"]],
    [["Platform", "Tier 4 Final, stackable modular configurations, HVO100 compatible for engines since 2016"], ["Engines", "G17 gas engine, D17 and D16 genset range"]])
add(V, "vol-kjpower", "KJ Power mobile battery storage", "Customer project", W, "KJ Power Generator (Turkey)", "Turkey",
    4, "Volvo Penta battery system supplied for KJ Power's mobile battery storage for the rental sector.", {"partner": ["KJPOWERG"], "move": ["Volvo Penta positions itself"]},
    [["2025-12", "Referenced as a battery storage win (KJ Power, Aura Clean Energy, SEETEL)"]],
    [["Equipment", "Volvo Penta battery system"], ["Use", "Mobile battery storage for the rental sector"]], stance="watch")

# Dates the record gives as plans, targets or schedules rather than things that happened. They are shown as
# "expected" and never count as the latest milestone.
EXPECTED = {
    "cat-joule-utah": ["2026"], "cat-monarch": ["2026-09", "2027-08"], "cat-propwr": ["2031"], "cat-onepwr": ["2026"],
    "cat-energyvault-texas": ["2027-08"], "cat-engine-capacity": ["2026-10"],
    "rr-energyvault": ["2027-07", "2028-06"], "rr-kuwait-t2": ["2026-03"], "rr-almulla-mro": ["2026-09"], "rr-ignitis": ["2027"],
    "rr-us-capacity": ["2026-01", "2026-12", "2027-07"],
    "reh-innio": ["2029-04"], "reh-kenosha": ["2026-12", "2027-03"], "reh-cholet": ["2026-11"],
    "gen-amazon": ["2027", "2028"], "gen-hyperscale-global": ["2027"], "gen-belvidere": ["2027-03"],
    "wei-aidc-ramp": ["2026-12", "2027-12"], "wei-eodev": ["2026-09"], "per-shaybah": ["2016"],
}
for _p in P:
    _p["timeline"] = [e + ["expected"] if e[0] in EXPECTED.get(_p["id"], []) else e for e in _p["timeline"]]
    for _d in EXPECTED.get(_p["id"], []):
        assert any(e[0] == _d for e in _p["timeline"]), f"{_p['id']}: no event dated {_d}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ids = [p["id"] for p in P]
        assert len(ids) == len(set(ids)), "duplicate project id"
        assert all(1 <= p["stage"] <= 4 and p["timeline"] and p["refs"] for p in P)
        assert all(sorted(e[0] for e in p["timeline"] if e[0][:4].isdigit()) is not None for p in P)
        print(f"ok {len(P)} projects")
        sys.exit()
    out = os.path.join(sys.argv[1], "competitor_projects.json")
    json.dump({"_asOf": "2026-10-13", "projects": P}, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{len(P)} projects -> {out}")
