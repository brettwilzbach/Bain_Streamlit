# Streamlit to shadcn/Next.js Migration Review

**Date:** December 17, 2025  
**Reviewer:** Auto (AI Assistant)  
**Status:** ⚠️ **INCOMPLETE - Only Project Scaffold Created**

---

## Executive Summary

A Next.js project has been initialized, but **no actual migration work has been completed**. The project is still using the default Next.js template with no shadcn/ui components installed and no Streamlit functionality migrated.

---

## Current State

### ✅ What Has Been Done

1. **Next.js Project Initialized**
   - Location: `abf-portal-react/`
   - Next.js 16.0.10
   - React 19.2.1
   - TypeScript 5
   - Tailwind CSS v4

2. **Basic Configuration**
   - `tsconfig.json` configured
   - `next.config.ts` created (empty)
   - ESLint configured
   - PostCSS configured for Tailwind

### ❌ What Has NOT Been Done

1. **shadcn/ui Not Installed**
   - No `components.json` file
   - No shadcn/ui dependencies in `package.json`
   - No Radix UI components
   - No `lib/utils.ts` with `cn()` helper
   - No component library setup

2. **No Migration of Streamlit Functionality**
   - No pages/components for:
     - Home page
     - Waterfall Modeler
     - Spread Monitor
     - Market Tracker
     - Deal Analyzer
   - No API routes for backend functionality
   - No data fetching logic migrated
   - No Bloomberg integration migrated

3. **No Component Structure**
   - No `components/` directory
   - No `lib/` directory
   - No shared utilities
   - No hooks for data fetching

4. **No Backend Integration**
   - No API routes (`app/api/`)
   - No connection to Python backend
   - No data models/types migrated

---

## Detailed Analysis

### Project Structure

```
abf-portal-react/
├── src/
│   └── app/
│       ├── layout.tsx      # Default Next.js layout
│       ├── page.tsx         # Default Next.js template page
│       └── globals.css      # Basic Tailwind setup
├── package.json             # Missing shadcn/ui dependencies
├── tsconfig.json           # ✅ Properly configured
└── next.config.ts          # Empty (needs configuration)
```

### Missing Components

The Streamlit app has these major features that need migration:

1. **Home Page** (`bain_abf_portal/app.py`)
   - Navigation sidebar
   - Overview metrics
   - Module descriptions
   - ABF Collateral Universe
   - Key Concepts (OC Test, IC Test, CNL Trigger, etc.)

2. **Waterfall Modeler** (`bain_abf_portal/pages/waterfall_modeler.py`)
   - Deal input (templates, manual entry, JSON)
   - Cash flow engine
   - Trigger configuration
   - Scenario analysis
   - Visualization with Plotly

3. **Spread Monitor** (`bain_abf_portal/pages/spread_monitor.py`)
   - Bloomberg/FRED data integration
   - Spread charts
   - Z-score analysis
   - Relative value scorecard

4. **Market Tracker** (`bain_abf_portal/pages/market_tracker.py`)
   - Deal database
   - Issuance analytics
   - Filtering and search

5. **Deal Analyzer** (`bain_abf_portal/pages/deal_analyzer.py`)
   - Educational tool
   - Deal structure visualization

### Backend Dependencies

The Streamlit app uses these Python modules that need API endpoints:

- `models/bloomberg_client.py` - Bloomberg API integration
- `models/data_fetcher.py` - FRED API, spread estimation
- `models/cashflow_engine.py` - Cash flow calculations
- `models/deal_structure.py` - Deal data models
- `models/deal_database.py` - Deal storage

---

## Required Next Steps

### Phase 1: Setup shadcn/ui

1. **Initialize shadcn/ui**
   ```bash
   npx shadcn@latest init
   ```

2. **Install Core Components**
   ```bash
   npx shadcn@latest add button
   npx shadcn@latest add card
   npx shadcn@latest add table
   npx shadcn@latest add tabs
   npx shadcn@latest add sidebar
   npx shadcn@latest add dialog
   npx shadcn@latest add select
   npx shadcn@latest add input
   npx shadcn@latest add chart  # For recharts integration
   ```

3. **Update Dependencies**
   - Add `class-variance-authority`
   - Add `clsx` and `tailwind-merge`
   - Add `lucide-react` for icons
   - Add `recharts` or `@tanstack/react-charts` for visualizations

### Phase 2: Create Project Structure

```
abf-portal-react/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Home page
│   │   ├── waterfall/
│   │   │   └── page.tsx          # Waterfall Modeler
│   │   ├── spreads/
│   │   │   └── page.tsx          # Spread Monitor
│   │   ├── market/
│   │   │   └── page.tsx          # Market Tracker
│   │   ├── analyzer/
│   │   │   └── page.tsx          # Deal Analyzer
│   │   └── api/
│   │       ├── bloomberg/
│   │       ├── fred/
│   │       ├── deals/
│   │       └── calculations/
│   ├── components/
│   │   ├── ui/                    # shadcn components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── waterfall/
│   │   ├── spreads/
│   │   └── market/
│   ├── lib/
│   │   ├── utils.ts
│   │   ├── api.ts                 # API client
│   │   └── calculations.ts
│   └── types/
│       ├── deal.ts
│       ├── tranche.ts
│       └── market.ts
```

### Phase 3: Backend API Setup

**Option A: Python FastAPI Backend** (Recommended)
- Keep Python models and calculations
- Create FastAPI endpoints
- Next.js calls FastAPI for data/calculations

**Option B: Next.js API Routes with Python**
- Use Next.js API routes as proxy
- Call Python scripts via subprocess or HTTP

**Option C: Full TypeScript Migration**
- Rewrite all Python logic in TypeScript
- Most work, but best performance

### Phase 4: Component Migration

1. **Layout Components**
   - Sidebar navigation (from Streamlit sidebar)
   - Header with branding
   - Page container

2. **Home Page**
   - Metric cards (shadcn Card)
   - Module descriptions
   - Collapsible sections (shadcn Accordion)

3. **Waterfall Modeler**
   - Form inputs (shadcn Input, Select)
   - Data table (shadcn Table)
   - Charts (recharts or Plotly.js)
   - Tabs for different views

4. **Spread Monitor**
   - Real-time data display
   - Interactive charts
   - Comparison tables

5. **Market Tracker**
   - Data table with filtering
   - Search functionality
   - Export buttons

### Phase 5: Data Integration

1. **Bloomberg API**
   - Create API route to proxy Bloomberg requests
   - Or use WebSocket for real-time data
   - Handle authentication

2. **FRED API**
   - Direct client-side calls (CORS permitting)
   - Or proxy through Next.js API routes

3. **State Management**
   - React Context for global state
   - Or Zustand/Redux for complex state
   - React Query for server state

---

## Critical Issues to Address

### 1. Python Backend Integration

The Streamlit app relies heavily on Python libraries:
- `pandas`, `numpy` for calculations
- `blpapi` for Bloomberg
- `plotly` for visualizations

**Recommendation:** Use FastAPI backend to keep Python logic, expose REST API.

### 2. Real-time Data Updates

Streamlit handles real-time updates automatically. Next.js needs:
- Polling mechanism
- WebSocket connection
- Server-Sent Events (SSE)

### 3. Complex Calculations

Cash flow engine and waterfall calculations are computationally intensive.

**Recommendation:** Keep in Python backend, call via API.

### 4. Plotly Charts

Streamlit uses Plotly Python. Options:
- Use `plotly.js` (same library, JavaScript)
- Use `recharts` (React-native, different API)
- Render Plotly Python charts as images via API

---

## Migration Complexity Estimate

| Component | Complexity | Estimated Time |
|-----------|-----------|----------------|
| Project Setup (shadcn/ui) | Low | 2-4 hours |
| Layout & Navigation | Medium | 4-8 hours |
| Home Page | Low | 4-6 hours |
| Waterfall Modeler | **Very High** | 40-60 hours |
| Spread Monitor | High | 20-30 hours |
| Market Tracker | Medium | 12-16 hours |
| Deal Analyzer | Medium | 12-16 hours |
| Backend API Setup | High | 20-30 hours |
| Testing & Polish | Medium | 16-24 hours |
| **Total** | | **130-194 hours** |

---

## Recommendations

### Immediate Actions

1. **Install shadcn/ui** - This is the foundation
2. **Set up project structure** - Create folders and basic layout
3. **Create API backend** - FastAPI to expose Python functionality
4. **Migrate one page at a time** - Start with Home, then Market Tracker (easiest)

### Architecture Decision

**Recommended Stack:**
- **Frontend:** Next.js 16 + shadcn/ui + TypeScript
- **Backend:** FastAPI (Python) for calculations and Bloomberg
- **State:** React Query for server state, Zustand for client state
- **Charts:** Plotly.js or Recharts
- **Styling:** Tailwind CSS + shadcn/ui

### Alternative: Hybrid Approach

Keep Streamlit for complex pages (Waterfall Modeler), migrate simpler pages to Next.js first.

---

## Conclusion

**Current Status:** Only project scaffold exists. No migration work has been completed.

**Next Steps:**
1. Install and configure shadcn/ui
2. Set up FastAPI backend
3. Create basic layout and navigation
4. Migrate simplest page first (Home or Market Tracker)
5. Iterate page by page

**Estimated Completion:** 3-4 weeks of full-time work for complete migration.

---

## Files to Review

- `abf-portal-react/package.json` - Missing shadcn/ui dependencies
- `abf-portal-react/src/app/page.tsx` - Still default template
- `abf-portal-react/src/app/layout.tsx` - Needs customization
- `bain_abf_portal/` - Source Streamlit app to migrate from

