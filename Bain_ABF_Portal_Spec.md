# Bain Capital Credit - ABF/Structured Credit Analytics Portal
## Product Specification for Brett Wilzbach

---

# Executive Summary

**Purpose:** Create an interactive analytics portal/dashboard to assist Bain Capital Credit's product management team in:
1. Tracking structured credit & ABF market developments
2. Modeling example waterfall triggers and deal structures
3. Monitoring collateral groupings, issuance, and spreads
4. Supporting client communication and investor education

**Context:** This tool supports the Lincoln Bain Capital Total Credit Fund launch and broader ABF/structured credit initiatives.

---

# Section 1: Bain Capital Credit ABF Context

## Recent Developments

### Lincoln Bain Capital Total Credit Fund (Sept 2025)
- **Partnership:** Lincoln Financial + Bain Capital Credit
- **Focus:** Evergreen fund for individual investors
- **Strategy:** Direct lending + Asset-Based Finance + Structured Credit
- **Distribution:** Lincoln Financial Distributors
- **Relationship:** 10-year non-exclusive investment management agreement
- **Equity investment:** Bain acquired 9.9% stake in Lincoln for $825M

Source: [Lincoln Financial Press Release](https://www.lincolnfinancial.com/public/aboutus/newsroom/pressreleases/Lincoln-Financial-and-Bain-Capital-launch-new-private-market-fund)

### Legacy Corporate Lending (May 2023)
- ABL platform launched with Bain Capital Credit equity investment
- Focus: Middle market ($10-40M facilities)
- Collateral: A/R, inventory, equipment, real estate, IP
- Location: Dallas-Fort Worth

Source: [Bain Capital News](https://www.baincapital.com/news/legacy-corporate-lending-new-asset-based-lending-company-launches-investment-bain-capital)

### Structured Credit Fund
- AUM: ~$270M
- PM: Marc Touboul
- Strategy: CLO debt/equity, structured products
- Status: Subscale, potential growth opportunity

---

## ABF Market Overview

### Market Size
| Metric | Value |
|--------|-------|
| Total ABF Market | $20T+ |
| Private ABF | ~$6T (doubled since 2008) |
| 2024 Private ABS Issuance | $130B (40% of total ABS) |
| Projected Private ABS (5yr) | $200B |

Source: [KKR ABF Research](https://www.kkr.com/insights/abf-private-credit)

### Collateral Categories

| Category | Examples |
|----------|----------|
| **Consumer Finance** | Auto loans, credit cards, consumer loans, BNPL |
| **Hard Assets** | Aircraft, equipment, rail, shipping, infrastructure |
| **Real Estate** | Residential mortgages, commercial mortgages, HELOCs |
| **Financial/Esoteric** | Royalties (music, pharma, IP), trade finance, litigation funding |
| **Specialty** | Data centers, digital infra, subscription/SaaS, sports finance |

### Private ABF vs. Public ABS

| Feature | Public ABS | Private ABF |
|---------|-----------|-------------|
| Pool type | Static | Revolving |
| Liquidity | Traded | Held to maturity |
| Structure | Standardized tranches | Customized |
| Pricing | Market spreads | Negotiated |
| Reporting | Public filings | Private |

---

# Section 2: Portal Features & Modules

## Module 1: ABS/CLO New Issuance Tracker

### Purpose
Real-time tracking of new deals across structured credit sectors

### Data Fields
| Field | Description |
|-------|-------------|
| Deal name | Issuer + Series (e.g., ACMAT 2025-4) |
| Issuer | Sponsor/originator |
| Collateral type | Auto, consumer, equipment, esoteric, etc. |
| Deal size | Total issuance ($M) |
| Tranche breakdown | Class A/B/C sizes, ratings, spreads, coupons |
| WAL | Weighted average life by tranche |
| Credit enhancement | Subordination %, OC levels |
| Bookrunner(s) | Lead arrangers |
| Pricing date | When deal priced |
| Format | 144A, Reg S, private placement |

### Filters
- By collateral type
- By rating (AAA to unrated)
- By date range
- By issuer/shelf
- By spread range

### Visualizations
- Issuance volume by sector (bar chart, time series)
- Spread trends by rating tier (line chart)
- Deal count by month/quarter
- Heatmap: Sector × Rating × Spread

---

## Module 2: Spread Monitor

### Purpose
Track relative value across structured credit vs. corporates

### Sectors Tracked
| Sector | Benchmark |
|--------|-----------|
| CLO AAA | vs. IG Corps, Treasuries |
| CLO Mezz (AA-BBB) | vs. BBB Corps |
| CLO BB/Equity | vs. HY Index |
| Prime Auto ABS | vs. IG Corps |
| Subprime Auto ABS | vs. HY Corps |
| Consumer ABS | vs. IG/HY |
| Esoteric ABS | vs. IG Corps |
| Equipment ABS | vs. IG Corps |

### Visualizations
- Spread time series (interactive, selectable sectors)
- Spread differential: Structured vs. Corporate
- Z-score: Current spread vs. historical average
- Correlation matrix across sectors

---

## Module 3: Waterfall Modeler (Interactive)

### Purpose
Educational tool showing how ABS/CLO cash flows work

### Key Concepts to Model

#### 3a. Payment Priority Waterfall
```
1. Senior Fees (trustee, servicer, admin)
2. Class A Interest
3. Class A Principal (if sequential)
4. Class B Interest
5. Class B Principal (if sequential)
6. OC Test - if fails, trap cash
7. Class C Interest
8. Class C Principal
9. Subordinated Fees
10. Residual/Equity
```

#### 3b. Trigger Events
| Trigger | Description | Consequence |
|---------|-------------|-------------|
| **OC Test Breach** | Collateral value / Notes < threshold | Redirect cash to senior paydown |
| **IC Test Breach** | Interest coverage falls below threshold | Redirect cash to senior paydown |
| **Delinquency Trigger** | 60+ day delinquencies > X% | Switch to sequential pay |
| **Cumulative Loss Trigger** | CNL exceeds threshold | Accelerate senior amortization |
| **Excess Spread Trigger** | 3-month avg excess spread < 0 | Trap cash in reserve |

#### 3c. Interactive Inputs
| Input | User Can Adjust |
|-------|-----------------|
| Default rate | 0-30% |
| Recovery rate | 0-100% |
| Prepayment speed | 0-50% CPR |
| Interest rate | SOFR + spread |
| Collateral yield | Gross WAC |

#### 3d. Outputs
- Cash flow to each tranche over time
- Break-even default rate by tranche
- IRR/yield by tranche under scenario
- Trigger breach timing
- Credit enhancement remaining

### Visualization
- Animated waterfall showing cash flow priority
- Scenario comparison (base vs. stress)
- Tranche paydown chart over time

---

## Module 4: Collateral Deep Dives

### Purpose
Sector-specific analysis for key ABF collateral types

### 4a. Auto ABS Dashboard

| Metric | Description |
|--------|-------------|
| Issuance by shelf | ACM, Exeter, Westlake, DriveTime, etc. |
| Delinquency trends | 30/60/90 day buckets |
| CNL curves | Cumulative net loss by vintage |
| Recovery rates | Repo proceeds / balance |
| Manheim Index | Used car value overlay |
| Subprime vs. Prime | Spread differential |

### 4b. Equipment ABS Dashboard

| Metric | Description |
|--------|-------------|
| Collateral mix | Construction, medical, tech, ag |
| Obligor concentration | Top 10 exposure |
| Depreciation curves | Asset value over time |
| Utilization rates | Equipment usage metrics |

### 4c. Consumer ABS Dashboard

| Metric | Description |
|--------|-------------|
| FICO distribution | Score buckets |
| DTI trends | Debt-to-income ratios |
| Payment rates | Monthly payment rate |
| Charge-off trends | Net charge-offs by vintage |

### 4d. Esoteric ABS Dashboard

| Metric | Description |
|--------|-------------|
| Collateral types | Royalties, litigation, solar, PACE, timeshare |
| Structural features | Reserve funds, triggers, enhancement |
| Sponsor track record | Historical deal performance |
| Rating agency views | KBRA, DBRS, S&P, Moody's |

---

## Module 5: Deal Comparison Tool

### Purpose
Side-by-side comparison of deals for relative value

### Comparison Fields
| Field | Deal A | Deal B | Deal C |
|-------|--------|--------|--------|
| Issuer | | | |
| Collateral | | | |
| Rating | | | |
| Spread | | | |
| WAL | | | |
| Credit Enhancement | | | |
| OC Trigger | | | |
| Loss Trigger | | | |
| Historical CNL | | | |

### Output
- Relative value score
- Risk-adjusted spread ranking
- Recommendation summary

---

## Module 6: Client Communication Templates

### Purpose
Pre-built content for investor education and updates

### Templates
1. **Market Update** - Weekly/monthly ABF market summary
2. **Sector Spotlight** - Deep dive on specific collateral type
3. **Deal Highlight** - New issuance analysis
4. **Waterfall Explainer** - How structures protect investors
5. **Relative Value** - Why ABF vs. corporates

### Format
- Exportable to PDF/PowerPoint
- Branded templates (Bain/Lincoln)
- Editable text + auto-populated charts

---

# Section 3: Data Sources

## Public Data
| Source | Data |
|--------|------|
| Bloomberg | ABS/CLO pricing, issuance |
| Intex | Deal structures, waterfalls, cash flows |
| EDGAR/SEC | ABS-15G filings, prospectuses |
| Rating Agencies | Presales, surveillance reports |
| Manheim | Used car index |
| Fed/Treasury | Base rates, economic data |

## Subscription Data
| Source | Data |
|--------|------|
| LCD/PitchBook | CLO new issue, spreads |
| Asset Securitization Report | ABS news, deal flow |
| Finsight | ABS pricing, comps |
| CoreLogic | Consumer credit data |

## Internal Data (If Accessible)
- Bain deal pipeline
- Portfolio holdings
- Proprietary loss curves
- Client feedback

---

# Section 4: Technical Architecture

## Stack Recommendation

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit (Python) or React |
| Backend | Python (pandas, numpy) |
| Database | PostgreSQL or SQLite |
| Visualization | Plotly, Altair |
| Hosting | Streamlit Cloud, AWS, or internal |
| Export | PDF (reportlab), PPTX (python-pptx) |

## MVP Scope (Phase 1)

**Build first:**
1. Issuance tracker (static data, manual updates)
2. Spread monitor (key sectors)
3. Simple waterfall modeler (one structure type)
4. Deal comparison (3-5 deals)

**Phase 2:**
- Live data feeds
- Multiple waterfall templates
- Client export functionality
- Full collateral dashboards

---

# Section 5: Key Metrics & KPIs

## For Investors
| Metric | Why It Matters |
|--------|----------------|
| Spread vs. Corporates | Relative value |
| Credit Enhancement | Downside protection |
| WAL | Duration risk |
| Historical CNL | Loss experience |
| Break-even Default | Stress capacity |

## For Product Team
| Metric | Why It Matters |
|--------|----------------|
| Issuance Volume | Market activity |
| Spread Trends | Timing of investments |
| Oversubscription | Demand signal |
| New Issuer Entry | Market expansion |
| Sector Rotation | Where capital is flowing |

---

# Section 6: Sample Use Cases

## Use Case 1: Lincoln Fund Client Meeting
> "Show me how a subprime auto ABS protects my investment in a downturn"

**Portal solution:**
- Pull up waterfall modeler
- Show OC test trigger at 20% losses
- Demonstrate sequential pay redirect
- Compare to corporate bond (no structural protection)

## Use Case 2: Investment Committee
> "What's the relative value in CLO mezz vs. BBB corps?"

**Portal solution:**
- Spread monitor: CLO BBB at +350 vs. Corp BBB at +150
- Historical Z-score: CLO mezz 1.5 std devs wide
- Show credit enhancement differential

## Use Case 3: Market Update
> "What priced this week in ABS?"

**Portal solution:**
- Issuance tracker filtered to last 7 days
- Summary by sector
- Notable deals flagged
- Export to PDF for distribution

---

# Section 7: Competitive Differentiation

## What Makes This Valuable

1. **Waterfall Visualization** - Most portals show data; this shows *how structures work*
2. **ABF + Structured Credit** - Covers private AND public markets
3. **Client-Ready Exports** - Not just internal analytics; supports distribution
4. **Lincoln Integration** - Tailored for retail investor education
5. **Interactive Scenarios** - Users can stress test, not just observe

## What Competitors Have

| Competitor | Strengths | Gaps |
|------------|-----------|------|
| Bloomberg | Data depth | No ABF focus, expensive |
| Intex | Waterfall modeling | Complex, not client-facing |
| LCD | CLO coverage | Limited ABS/ABF |
| Internal tools | Customization | Often siloed, no visualization |

---

# Section 8: Next Steps

## For Brett

1. **Send email to Jeff** (done - awaiting response)
2. **Build MVP** - Start with issuance tracker + simple waterfall
3. **Populate with real data** - ACMAT, recent CLOs, key sectors
4. **Demo-ready version** - 2-3 screens, interactive
5. **Present to team** - Show value, get feedback

## Timeline (Suggested)

| Week | Deliverable |
|------|-------------|
| 1 | Wireframes + data model |
| 2 | Issuance tracker MVP |
| 3 | Spread monitor + waterfall v1 |
| 4 | Polish + demo prep |

---

# Appendix: ABF Collateral Taxonomy

## Consumer Assets
- Prime auto loans
- Subprime auto loans
- Credit card receivables
- Student loans (private)
- Personal loans / marketplace lending
- BNPL (Buy Now Pay Later)

## Commercial Assets
- Equipment leases (construction, medical, tech)
- Fleet/vehicle leases
- Small business loans
- Franchise loans
- Inventory finance

## Hard Assets
- Aircraft (operating leases, loans)
- Railcar
- Shipping containers
- Solar panels / PACE
- Data centers / digital infrastructure

## Real Estate
- Residential mortgages (non-QM, jumbo)
- Home equity (HELOCs, HEIs)
- Commercial mortgages (CRE CLO)
- Single-family rental (SFR)

## Financial / Esoteric
- Music royalties
- Pharma royalties
- Litigation finance
- Whole business securitization
- Sports franchise finance
- Insurance-linked securities
- Timeshare receivables
- Cell tower / spectrum
- Subscription / SaaS revenue

---

**Document prepared for discussion with Bain Capital Credit**

*Sources: Bain Capital press releases, KKR ABF research, PIMCO ABF research, Structured Credit Investor, Lincoln Financial announcements, NAIC primers*
