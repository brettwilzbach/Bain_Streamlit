# Complete Migration Prompt: Streamlit to Next.js + shadcn/ui

## Context & Current State

You are migrating a **Bain Capital Credit ABF/Structured Credit Analytics Portal** from Streamlit (Python) to Next.js 16 + shadcn/ui + TypeScript.

### Current Streamlit App Location
- **Path:** `bain_abf_portal/`
- **Main entry:** `bain_abf_portal/app.py`
- **Pages:** 
  - Home (`app.py` - main page)
  - Waterfall Modeler (`pages/waterfall_modeler.py`)
  - Spread Monitor (`pages/spread_monitor.py`)
  - Market Tracker (`pages/market_tracker.py`)
  - Deal Analyzer (`pages/deal_analyzer.py`)

### Current React Project Location
- **Path:** `abf-portal-react/`
- **Status:** Only default Next.js template exists - NO migration work done
- **Stack:** Next.js 16.0.10, React 19.2.1, TypeScript 5, Tailwind CSS v4

### Backend Models (Python - Keep These)
- `bain_abf_portal/models/bloomberg_client.py` - Direct Bloomberg API client (working, pandas 2.0+ compatible)
- `bain_abf_portal/models/data_fetcher.py` - FRED API, spread estimation
- `bain_abf_portal/models/cashflow_engine.py` - Cash flow calculations
- `bain_abf_portal/models/deal_structure.py` - Deal data models
- `bain_abf_portal/models/deal_database.py` - Deal storage

---

## Your Mission

**Migrate the Streamlit app to a modern Next.js + shadcn/ui application while keeping Python backend logic intact.**

---

## Architecture Decision

**Use a Hybrid Architecture:**
- **Frontend:** Next.js 16 + shadcn/ui + TypeScript (React 19)
- **Backend:** FastAPI (Python) - Keep all calculation logic in Python
- **Communication:** REST API between Next.js and FastAPI
- **Why:** Python models are complex (pandas, numpy, blpapi) - easier to keep than rewrite

---

## Step-by-Step Migration Plan

### PHASE 1: Foundation Setup (Do This First)

#### 1.1 Install shadcn/ui
```bash
cd abf-portal-react
npx shadcn@latest init
# Choose: TypeScript, Default style, App Router, Tailwind CSS
```

#### 1.2 Install Required shadcn Components
```bash
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add table
npx shadcn@latest add tabs
npx shadcn@latest add sidebar
npx shadcn@latest add dialog
npx shadcn@latest add select
npx shadcn@latest add input
npx shadcn@latest add textarea
npx shadcn@latest add label
npx shadcn@latest add checkbox
npx shadcn@latest add radio-group
npx shadcn@latest add slider
npx shadcn@latest add switch
npx shadcn@latest add accordion
npx shadcn@latest add dropdown-menu
npx shadcn@latest add sheet
npx shadcn@latest add badge
npx shadcn@latest add alert
npx shadcn@latest add separator
```

#### 1.3 Install Additional Dependencies
```bash
npm install recharts                    # For charts (alternative to Plotly)
npm install axios                      # For API calls
npm install @tanstack/react-query     # For server state management
npm install zustand                    # For client state (optional)
npm install date-fns                   # For date formatting
npm install lucide-react               # Icons (usually auto-installed with shadcn)
```

#### 1.4 Create Project Structure
```
abf-portal-react/
├── src/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout with sidebar
│   │   ├── page.tsx                   # Home page
│   │   ├── waterfall/
│   │   │   └── page.tsx               # Waterfall Modeler
│   │   ├── spreads/
│   │   │   └── page.tsx               # Spread Monitor
│   │   ├── market/
│   │   │   └── page.tsx               # Market Tracker
│   │   ├── analyzer/
│   │   │   └── page.tsx               # Deal Analyzer
│   │   └── api/
│   │       └── [...next].ts          # API proxy (optional)
│   ├── components/
│   │   ├── ui/                        # shadcn components (auto-generated)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx            # Navigation sidebar
│   │   │   ├── Header.tsx             # Top header (optional)
│   │   │   └── MainLayout.tsx         # Wrapper layout
│   │   ├── waterfall/
│   │   │   ├── DealInputForm.tsx
│   │   │   ├── TriggerConfig.tsx
│   │   │   ├── ScenarioAnalysis.tsx
│   │   │   └── WaterfallChart.tsx
│   │   ├── spreads/
│   │   │   ├── SpreadChart.tsx
│   │   │   ├── SpreadTable.tsx
│   │   │   └── RelativeValueCard.tsx
│   │   └── market/
│   │       ├── DealTable.tsx
│   │       └── IssuanceChart.tsx
│   ├── lib/
│   │   ├── utils.ts                   # cn() helper (auto-generated)
│   │   ├── api.ts                     # API client functions
│   │   └── calculations.ts            # Client-side calculations (if any)
│   ├── types/
│   │   ├── deal.ts                    # Deal structure types
│   │   ├── tranche.ts                 # Tranche types
│   │   ├── market.ts                  # Market data types
│   │   └── api.ts                     # API response types
│   └── hooks/
│       ├── useBloomberg.ts            # Bloomberg data hook
│       ├── useDeals.ts                # Deal data hook
│       └── useCalculations.ts         # Calculation hook
```

---

### PHASE 2: Backend API Setup (Critical - Do This Before Frontend)

#### 2.1 Create FastAPI Backend
Create a new directory: `abf-portal-backend/`

**File: `abf-portal-backend/main.py`**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent / "bain_abf_portal"))

from models.bloomberg_client import BloombergClient, BloombergSpreadProvider
from models.data_fetcher import get_unified_provider, FREDClient
from models.cashflow_engine import CashFlowEngine, ScenarioAssumptions
from models.deal_structure import DealStructure, DEAL_TEMPLATES
from models.deal_database import DealDatabase

app = FastAPI(title="ABF Portal API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class DealRequest(BaseModel):
    deal_data: Dict[str, Any]

class ScenarioRequest(BaseModel):
    deal_data: Dict[str, Any]
    assumptions: Dict[str, Any]

# API Routes
@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/market/spreads")
async def get_spreads():
    """Get structured credit spreads"""
    provider = get_unified_provider()
    if provider.bloomberg_available:
        spreads = provider.get_structured_spreads()
        return {"source": "bloomberg", "data": spreads}
    else:
        # Fallback to FRED estimates
        spreads = provider.get_structured_spreads()
        return {"source": "fred", "data": spreads}

@app.get("/api/market/sofr")
async def get_sofr():
    """Get current SOFR rate"""
    provider = get_unified_provider()
    sofr, source = provider.get_sofr()
    return {"rate": sofr, "source": source}

@app.post("/api/waterfall/calculate")
async def calculate_waterfall(request: ScenarioRequest):
    """Calculate waterfall cash flows"""
    try:
        # Convert request to DealStructure and ScenarioAssumptions
        # Run CashFlowEngine
        # Return results
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deals")
async def get_deals():
    """Get all deals from database"""
    db = DealDatabase()
    deals = db.get_all_deals()
    return {"deals": deals}

@app.get("/api/deals/templates")
async def get_templates():
    """Get available deal templates"""
    return {"templates": list(DEAL_TEMPLATES.keys())}

# Add more routes as needed...
```

**File: `abf-portal-backend/requirements.txt`**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
# All dependencies from bain_abf_portal/requirements.txt
```

#### 2.2 Test Backend
```bash
cd abf-portal-backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

### PHASE 3: Frontend - Layout & Navigation

#### 3.1 Create Sidebar Component
**File: `src/components/layout/Sidebar.tsx`**
- Replicate Streamlit sidebar navigation
- Use shadcn Sidebar component
- Include: Home, Waterfall Modeler, Spread Monitor, Market Tracker, Deal Analyzer
- Match styling from Streamlit app

#### 3.2 Create Main Layout
**File: `src/app/layout.tsx`**
- Wrap with Sidebar
- Set up theme provider (if using dark mode)
- Configure fonts (keep Geist or use Inter)
- Add metadata

#### 3.3 Create API Client
**File: `src/lib/api.ts`**
```typescript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const getSpreads = () => api.get('/api/market/spreads');
export const getSOFR = () => api.get('/api/market/sofr');
export const calculateWaterfall = (data: any) => api.post('/api/waterfall/calculate', data);
export const getDeals = () => api.get('/api/deals');
export const getTemplates = () => api.get('/api/deals/templates');
```

---

### PHASE 4: Migrate Pages (One at a Time)

#### 4.1 Home Page (Easiest - Start Here)
**File: `src/app/page.tsx`**

**What to migrate:**
- Overview metrics (4 columns: Total ABF Market, Private ABF, 2024 Private ABS, SOFR)
- Module descriptions (3 columns: Waterfall Modeler, Spread Monitor, Market Tracker)
- ABF Collateral Universe (2 columns)
- Key Concepts (Accordion with: OC Test, IC Test, CNL Trigger, Sequential vs Pro-Rata)

**Components needed:**
- shadcn Card for metrics
- shadcn Accordion for key concepts
- Grid layout with Tailwind

**Data:**
- Static content (no API calls needed initially)
- SOFR can be fetched from API later

#### 4.2 Market Tracker (Second Easiest)
**File: `src/app/market/page.tsx`**

**What to migrate:**
- Deal database table
- Filtering by collateral type, date, size
- Issuance analytics charts
- Export to CSV/Excel functionality

**Components needed:**
- shadcn Table for deals
- shadcn Select for filters
- shadcn Input for search
- Recharts for charts
- shadcn Button for export

**Data:**
- Fetch from `/api/deals`
- Use React Query for data fetching

#### 4.3 Spread Monitor (Medium Complexity)
**File: `src/app/spreads/page.tsx`**

**What to migrate:**
- Real-time spread data display
- Spread charts (CLO, ABS, Corporate benchmarks)
- Z-score analysis
- Relative value scorecard
- Bloomberg connection status

**Components needed:**
- Recharts for line/bar charts
- shadcn Card for metrics
- shadcn Badge for status indicators
- shadcn Table for spread data

**Data:**
- Fetch from `/api/market/spreads`
- Poll every 5 minutes or use WebSocket
- Show data source (Bloomberg vs FRED)

#### 4.4 Deal Analyzer (Medium Complexity)
**File: `src/app/analyzer/page.tsx`**

**What to migrate:**
- Educational tool interface
- Deal structure visualization
- Interactive explanations

**Components needed:**
- shadcn Card for sections
- Custom visualization components
- shadcn Accordion for explanations

#### 4.5 Waterfall Modeler (Most Complex - Do Last)
**File: `src/app/waterfall/page.tsx`**

**What to migrate:**
- Deal input (3 methods: Template, Manual Entry, JSON Paste)
- Trigger configuration (OC, IC, CNL, DSCR)
- Scenario analysis (CPR, CDR inputs)
- Cash flow waterfall visualization
- Break-even CDR analysis
- CNL sensitivity heatmaps

**Components needed:**
- Complex form with shadcn Input, Select, Slider
- shadcn Tabs for different views
- Recharts for waterfall visualization
- shadcn Table for results
- JSON editor component

**Data:**
- POST to `/api/waterfall/calculate`
- Handle large response data
- Show loading states

---

## Key Implementation Details

### Styling
- Use Tailwind CSS (already configured)
- Match color scheme from Streamlit: `#1E3A5F` for primary
- Use shadcn theme system
- Responsive design (mobile-friendly)

### State Management
- **Server State:** React Query (`@tanstack/react-query`)
  - Automatic caching
  - Refetching
  - Loading/error states
- **Client State:** React useState/useReducer
  - Form inputs
  - UI state
  - Optional: Zustand for complex client state

### Data Fetching Pattern
```typescript
// Example with React Query
import { useQuery } from '@tanstack/react-query';
import { getSpreads } from '@/lib/api';

function SpreadMonitor() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['spreads'],
    queryFn: () => getSpreads().then(res => res.data),
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  });
  
  // Render component
}
```

### Charts
- Use **Recharts** (React-native, easier than Plotly.js)
- Alternative: Plotly.js if you need exact Plotly Python features
- For complex 3D: Keep Plotly.js

### Forms
- Use **React Hook Form** with shadcn components
- Validation with Zod (shadcn compatible)
```bash
npm install react-hook-form zod @hookform/resolvers
```

### Error Handling
- API errors: Show shadcn Alert components
- Loading states: shadcn Skeleton components
- Toast notifications: shadcn Toast (install separately)

---

## Migration Checklist

### Foundation
- [ ] Install shadcn/ui
- [ ] Install all required components
- [ ] Install additional dependencies (recharts, axios, react-query, etc.)
- [ ] Create project folder structure
- [ ] Set up API client (`src/lib/api.ts`)

### Backend
- [ ] Create FastAPI backend
- [ ] Set up CORS
- [ ] Create API routes for:
  - [ ] Market data (spreads, SOFR)
  - [ ] Waterfall calculations
  - [ ] Deal CRUD operations
  - [ ] Templates
- [ ] Test all API endpoints
- [ ] Document API with FastAPI docs

### Frontend - Layout
- [ ] Create Sidebar component
- [ ] Create MainLayout wrapper
- [ ] Update root layout.tsx
- [ ] Set up routing

### Frontend - Pages
- [ ] Home page (static content)
- [ ] Market Tracker (table, filters, charts)
- [ ] Spread Monitor (real-time data, charts)
- [ ] Deal Analyzer (educational content)
- [ ] Waterfall Modeler (complex forms, calculations)

### Polish
- [ ] Add loading states (Skeleton)
- [ ] Add error handling (Alert)
- [ ] Add toast notifications
- [ ] Responsive design testing
- [ ] Dark mode (if desired)
- [ ] Performance optimization

---

## Testing Strategy

1. **Backend First:** Test all API endpoints with Postman/curl
2. **Frontend Components:** Test in isolation
3. **Integration:** Test full flows (form → API → display)
4. **Edge Cases:** Error handling, empty states, loading states

---

## Environment Variables

**File: `abf-portal-react/.env.local`**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**File: `abf-portal-backend/.env`**
```
BLOOMBERG_HOST=localhost
BLOOMBERG_PORT=8194
FRED_API_KEY=your_fred_api_key_here
```

---

## Running the Application

### Development
```bash
# Terminal 1: Backend
cd abf-portal-backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd abf-portal-react
npm run dev
```

### Production
```bash
# Build frontend
cd abf-portal-react
npm run build
npm start

# Run backend
cd abf-portal-backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Success Criteria

✅ All Streamlit pages migrated to Next.js  
✅ All functionality preserved  
✅ Python backend logic intact (FastAPI)  
✅ Modern, responsive UI with shadcn/ui  
✅ Real-time data updates working  
✅ Charts and visualizations functional  
✅ Forms and calculations accurate  
✅ Error handling and loading states  
✅ Production-ready code  

---

## Important Notes

1. **Don't rewrite Python logic** - Keep it in FastAPI backend
2. **Start simple** - Home page first, then Market Tracker
3. **Test as you go** - Don't build everything then test
4. **Match Streamlit UX** - Users should feel familiar
5. **Performance matters** - Use React Query caching, optimize renders
6. **Type safety** - Use TypeScript properly, define all types
7. **Error boundaries** - Wrap pages in error boundaries

---

## Reference Files to Study

Before starting, read these Streamlit files to understand functionality:
- `bain_abf_portal/app.py` - Home page structure
- `bain_abf_portal/pages/waterfall_modeler.py` - Complex waterfall logic
- `bain_abf_portal/pages/spread_monitor.py` - Data fetching patterns
- `bain_abf_portal/pages/market_tracker.py` - Table and filtering
- `bain_abf_portal/models/` - Backend models to expose via API

---

## Final Reminder

**This is a REAL migration project. Make actual progress:**
- Create real components
- Write real API routes
- Migrate real functionality
- Test real functionality
- Don't just create empty files or templates

**Start with Phase 1 (Foundation) and work through systematically. Don't skip steps.**

Good luck! 🚀

