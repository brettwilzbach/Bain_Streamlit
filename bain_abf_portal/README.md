# Bain Capital Credit - ABF/Structured Credit Analytics Portal

Interactive analytics portal for tracking structured credit & ABF market developments, modeling deal structures, and monitoring spreads.

## Features

### Page 1: Waterfall/Trigger Modeler
- Pre-built deal templates (Subprime Auto, Prime Auto, CLO, Equipment ABS)
- Interactive OC, IC, CNL, and DSCR trigger configuration
- Scenario analysis with customizable CPR and CDR assumptions
- Break-even default rate analysis by tranche
- Cash flow waterfall visualization

### Page 2: Spread Monitor
- Track spreads across CLO, Auto ABS, Consumer ABS, Equipment ABS sectors
- Compare structured credit to corporate benchmarks (IG, HY)
- Z-score analysis vs. historical averages
- Relative value scorecard

### Page 3: Market Tracker
- New issuance database with deal details
- Monthly issuance volume trends
- Deal deep dive with tranche breakdown
- Market news and calendar

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The portal will open at http://localhost:8501

## Data Sources

Currently shows sample/illustrative data. For live data, integrate with:
- **Bloomberg API** - Pricing, issuance (direct connection via blpapi - no server needed)
- **LCD/PitchBook** - CLO new issue, spreads
- **Finsight** - ABS pricing, comps
- **FRED** - Base rates (SOFR, Treasury yields) - Free API available
- **EDGAR/SEC** - ABS-15G filings

### Bloomberg Terminal Setup

The app connects directly to Bloomberg Terminal via the `blpapi` Python library:
1. Install blpapi: `pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple/ blpapi`
2. Make sure Bloomberg Terminal is running with BBComm enabled
3. The app will connect automatically when you run it

No additional server or MCP setup required!

## Project Structure

```
bain_abf_portal/
├── app.py                      # Main application entry point
├── pages/
│   ├── waterfall_modeler.py    # Page 1: Waterfall & triggers
│   ├── spread_monitor.py       # Page 2: Spread tracking
│   └── market_tracker.py       # Page 3: Issuance & news
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Customization

### Adding New Deal Templates
Edit `DEAL_TEMPLATES` in `waterfall_modeler.py` to add new structures.

### Updating Spread Data
Replace `CURRENT_SPREADS` in `spread_monitor.py` with API calls or database queries.

### Adding Deals to Tracker
Update `SAMPLE_DEALS` in `market_tracker.py` or connect to a database.

## Use Cases

1. **Client Meetings**: Show how waterfall structures protect investors
2. **Investment Committee**: Compare relative value across sectors
3. **Market Updates**: Generate weekly/monthly issuance summaries
4. **Education**: Teach junior team members about ABS/CLO structures

---

Built for Bain Capital Credit - ABF/Structured Credit Initiatives
