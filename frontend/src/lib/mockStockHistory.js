// Fallback stock history generator matching stocks 2.jpeg & realistic Indian defence market dynamics

export function getMockStockHistory({ cid, name, ticker, range = "1y" }) {
  const company = name || "Larsen & Toubro";
  const sym = ticker || "LT.NS";
  
  // Base parameters per company (LT matches stocks 2.jpeg exactly)
  let basePrice = 3692.10;
  let high = 4418.10;
  let low = 3342.40;
  let changePct = 0.59;
  
  if (cid === "adani-defence" || sym.includes("ADANI")) {
    basePrice = 3140.50;
    high = 3480.00;
    low = 2650.00;
    changePct = 2.84;
  } else if (cid === "bel" || sym.includes("BEL")) {
    basePrice = 312.40;
    high = 340.50;
    low = 245.00;
    changePct = 8.12;
  } else if (cid === "bharat-dynamics" || sym.includes("BDL")) {
    basePrice = 1280.20;
    high = 1520.00;
    low = 1110.00;
    changePct = 4.35;
  } else if (cid === "beml" || sym.includes("BEML")) {
    basePrice = 4120.00;
    high = 4850.00;
    low = 3620.00;
    changePct = -1.25;
  } else if (cid === "ashok-leyland" || sym.includes("ASHOK")) {
    basePrice = 228.60;
    high = 255.00;
    low = 195.00;
    changePct = 5.20;
  }

  // Adjust high/low and change based on range
  if (range === "1mo" || range === "1M") {
    changePct = -1.80;
    high = Math.round(basePrice * 1.04 * 100) / 100;
    low = Math.round(basePrice * 0.96 * 100) / 100;
  } else if (range === "6mo" || range === "6M") {
    changePct = 7.45;
    high = Math.round(basePrice * 1.12 * 100) / 100;
    low = Math.round(basePrice * 0.91 * 100) / 100;
  } else if (range === "5y" || range === "5Y") {
    changePct = 142.80;
    high = Math.round(basePrice * 1.18 * 100) / 100;
    low = Math.round(basePrice * 0.38 * 100) / 100;
  }

  // Generate points tracing the curve shown in stocks 2.jpeg
  const points = [];
  const days = range === "1mo" || range === "1M" ? 30 : range === "6mo" || range === "6M" ? 90 : range === "5y" || range === "5Y" ? 180 : 120;
  const endDate = new Date(2026, 9, 1); // 01 Oct 2026

  for (let i = 0; i < days; i++) {
    const d = new Date(endDate);
    d.setDate(d.getDate() - (days - 1 - i));
    const iso = d.toISOString().slice(0, 10);
    
    // Non-linear trajectory with dip in April and peak in June matching stocks 2.jpeg
    const progress = i / (days - 1);
    let val;
    if (range === "1y" || range === "1Y") {
      if (progress < 0.25) {
        val = 3880.25 + (3550.00 - 3880.25) * (progress / 0.25) + Math.sin(i * 0.4) * 40;
      } else if (progress < 0.5) {
        val = 3550.00 + (3342.40 - 3550.00) * ((progress - 0.25) / 0.25) + Math.sin(i * 0.5) * 45;
      } else if (progress < 0.7) {
        val = 3342.40 + (4418.10 - 3342.40) * ((progress - 0.5) / 0.2) + Math.sin(i * 0.6) * 55;
      } else {
        val = 4418.10 + (3692.10 - 4418.10) * ((progress - 0.7) / 0.3) + Math.sin(i * 0.4) * 40;
      }
      // Scale if not LT
      if (basePrice !== 3692.10) {
        val = (val / 3692.10) * basePrice;
      }
    } else {
      const wobble = Math.sin(i * 0.35) * 0.05 + Math.cos(i * 0.2) * 0.04;
      val = basePrice * (1 - (changePct / 100) * (1 - progress) + wobble);
    }
    
    val = Math.max(low, Math.min(high, Math.round(val * 100) / 100));
    points.push({ t: iso, c: val });
  }

  // Ensure last point matches basePrice
  if (points.length > 0) {
    points[points.length - 1].c = basePrice;
  }

  // 8 biggest moves matching stocks 2.jpeg with dates and news
  const moves = [
    {
      date: "2026-06-12",
      from: Math.round(basePrice * 1.045 * 100) / 100,
      to: Math.round(basePrice * 1.096 * 100) / 100,
      pct: 4.85,
      dir: "rise",
      news: [
        {
          title: `$988M Upstream Contract in Kuwait Planned for Official Award to ${company} within 30 days`,
          source: "Construction Review",
          date: "2026-06-09"
        },
        {
          title: "Sustainable Infrastructure and Defence Modernisation Order Inflow",
          source: `${company}`,
          date: "2026-06-11"
        },
        {
          title: `${company} among top Nifty gainers as shares rise on strategic defence programme execution`,
          source: "TradingView",
          date: "2026-06-11"
        }
      ]
    },
    {
      date: "2026-04-07",
      from: Math.round(basePrice * 0.98 * 100) / 100,
      to: Math.round(basePrice * 0.94 * 100) / 100,
      pct: -3.85,
      dir: "drop",
      news: [
        {
          title: "Global Supply Chain Realignments Impact Near-Term Component Deliveries",
          source: "Defence Market Wire",
          date: "2026-04-05"
        },
        {
          title: "Market Pullback Across Capital Goods and Heavy Engineering Indices",
          source: "The Economic Times",
          date: "2026-04-06"
        }
      ]
    },
    {
      date: "2026-05-18",
      from: Math.round(basePrice * 0.97 * 100) / 100,
      to: Math.round(basePrice * 1.01 * 100) / 100,
      pct: 3.92,
      dir: "rise",
      news: [
        {
          title: `MoD Clears Acquisition Council Approvals Benefiting ${company}`,
          source: "Defence News India",
          date: "2026-05-16"
        },
        {
          title: `${company} Reports Strong Margin Expansion in Annual Earnings Call`,
          source: "Financial Express",
          date: "2026-05-17"
        }
      ]
    },
    {
      date: "2026-03-14",
      from: Math.round(basePrice * 0.99 * 100) / 100,
      to: Math.round(basePrice * 0.96 * 100) / 100,
      pct: -3.15,
      dir: "drop",
      news: [
        {
          title: "Raw Material Price Fluctuations Weigh on Intermediate Platform Assemblies",
          source: "Industry Monitor",
          date: "2026-03-12"
        }
      ]
    },
    {
      date: "2026-07-22",
      from: Math.round(basePrice * 1.08 * 100) / 100,
      to: Math.round(basePrice * 1.12 * 100) / 100,
      pct: 3.65,
      dir: "rise",
      news: [
        {
          title: `${company} Secures Strategic Export Order for High-Tech Subsystems`,
          source: "Global Defence Report",
          date: "2026-07-20"
        },
        {
          title: "Export Clearances Accelerated Under Make-in-India Defense Push",
          source: "Livemint",
          date: "2026-07-21"
        }
      ]
    },
    {
      date: "2026-02-19",
      from: Math.round(basePrice * 1.01 * 100) / 100,
      to: Math.round(basePrice * 0.98 * 100) / 100,
      pct: -2.85,
      dir: "drop",
      news: [
        {
          title: "Quarterly Sector Rebalancing by Domestic Institutional Investors",
          source: "CNBC TV18",
          date: "2026-02-17"
        }
      ]
    },
    {
      date: "2026-08-30",
      from: Math.round(basePrice * 1.02 * 100) / 100,
      to: Math.round(basePrice * 1.05 * 100) / 100,
      pct: 2.95,
      dir: "rise",
      news: [
        {
          title: `${company} Commissions State-of-the-Art Precision Testing Complex`,
          source: "Business Standard",
          date: "2026-08-28"
        }
      ]
    },
    {
      date: "2025-11-25",
      from: Math.round(basePrice * 1.03 * 100) / 100,
      to: Math.round(basePrice * 1.06 * 100) / 100,
      pct: 2.70,
      dir: "rise",
      news: [
        {
          title: `Tri-Services Modernisation Roadmap Outlines Expanded Role for ${company}`,
          source: "India Strategic",
          date: "2025-11-23"
        }
      ]
    }
  ];

  // Adjust dates for moves to ensure they match points in the range
  const validPointDates = new Set(points.map((p) => p.t));
  moves.forEach((m) => {
    if (!validPointDates.has(m.date)) {
      // Find closest date in points
      let closest = points[0].t;
      let minDiff = Infinity;
      const targetTime = new Date(m.date).getTime();
      points.forEach((p) => {
        const diff = Math.abs(new Date(p.t).getTime() - targetTime);
        if (diff < minDiff) {
          minDiff = diff;
          closest = p.t;
        }
      });
      m.date = closest;
    }
  });

  return {
    symbol: sym,
    name: company,
    searchedAs: company,
    currency: "INR",
    exchange: "NSE",
    price: basePrice,
    range,
    rangeChangePct: changePct,
    high,
    low,
    points,
    moves,
    fetchedAt: new Date().toISOString()
  };
}
