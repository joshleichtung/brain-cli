# Brain CLI Dashboard

Real-time observability dashboard for monitoring multi-agent orchestration.

## Status: Initial Implementation ✅

**Location**: `~/brain/brain-dashboard/`

## Tech Stack

- **React 18** + **TypeScript**
- **Tailwind CSS** v3
- **Vite** - Dev server
- **WebSocket** - Real-time events

## Features Implemented

- ✅ WebSocket connection to observability API
- ✅ Real-time event stream display
- ✅ Event type color coding (completed=green, failed=red, started=blue)
- ✅ Connection status indicator
- ✅ REST API integration for historical events
- ✅ TypeScript interfaces for type safety

## Running the Dashboard

```bash
# 1. Start observability API
cd ~/brain/brain-cli
source venv/bin/activate
python -m brain.observability.server

# 2. Start dashboard (in new terminal)
cd ~/brain/brain-dashboard
npm install  # first time only
npm run dev

# 3. Run agents to see live events (in new terminal)
cd ~/brain/brain-cli
python -m brain
```

Dashboard will be available at `http://localhost:5173`

## Architecture

```
React Dashboard (port 5173)
      ↓
WebSocket + REST
      ↓
FastAPI Server (port 8000)
      ↓
Event Storage (SQLite)
      ↑
Hook System
      ↑
Agent Fleet Manager
```

## Next Steps (Future Enhancements)

- [ ] shadcn/ui component library integration
- [ ] Upgrade to Tailwind v4 (when Vite 7 support lands)
- [ ] Project selector dropdown
- [ ] Agent timeline visualization
- [ ] Cost tracking charts (Chart.js or Recharts)
- [ ] Tool usage statistics
- [ ] Export functionality (CSV/JSON)
- [ ] Dark/light mode toggle
- [ ] Agent control actions (pause/resume)

## Notes

- Dashboard is currently read-only
- Using Tailwind v3 for stability (v4 has Vite version conflicts)
- WebSocket auto-reconnects on disconnect
- Events limited to 50 most recent for performance
- All components are functional (not class-based)
