# Dashboard

TypeScript + React 19 + Vite. Source: `dashboard/src/`. Localhost only.

## Files

| File | Role |
|---|---|
| `index.html` | Mounts `#root` |
| `src/main.tsx` | `createRoot` + `StrictMode` |
| `src/App.tsx` | All GCS UI and API calls |
| `src/style.css` | Dark, compact operator layout |
| `src/vite-env.d.ts` | Vite client types |
| `vite.config.ts` | Port 8080, `/api` and `/ws` proxies |

## Operator flow

1. **Connect** — `POST /api/connect` (MAVSDK bind).
2. **Set fence** — north/south/east/west metres from home → `POST /api/fence`.
3. **Scan** — `POST /api/scan` with `source` = dashboard-first or RC-first.
4. Select rows in the detections table → **Confirm selected** or **Reject selected**.
5. **Visit confirmed** — XY at scan height, descend, pulse, RTL.
6. **RTL**, **People/pets — hold**, or **Kill (pump off)** at any time.

Telemetry line: phase, MAV up/down, armed, relative altitude, lidar (`missing` on SIH), pump value.

On load, `GET /api/preflight` is fetched only to confirm the backend is up; the banner text is hardcoded (not legal advice). State is pushed over WebSocket `/ws`; if the socket errors, the UI polls `GET /api/state` every 500 ms.

## Types in `App.tsx`

- `Detection` — one plant row (`class` or `class_name`, NED metres, confirm/visited/sprayed flags).
- `State` — subset of backend `AppState` the UI actually renders.
- `empty` — idle default before the first snapshot.

Functions: `api`, `App`, `toggle`, `run`. See [code-reference.md](code-reference.md#dashboardsrcapptsx).
