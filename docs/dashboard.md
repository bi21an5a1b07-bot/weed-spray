# Dashboard

TypeScript + React 19 + Vite. Source: `dashboard/src/`. Localhost only.

## Files

| File | Role |
|---|---|
| `index.html` | Mounts `#root` |
| `src/main.tsx` | `createRoot` + `StrictMode` |
| `src/App.tsx` | Console layout, camera, yard plan, and API calls |
| `src/status.ts` | Tones, which command is next, yard-plan geometry |
| `src/playback.ts` | hls.js vs native playlist choice |
| `src/stateSocket.ts` | Mission WebSocket attach and cleanup |
| `src/style.css` | Dark operator palette and layout |
| `src/vite-env.d.ts` | Vite client types |
| `vite.config.ts` | Port 8080, `/api` and `/ws` proxies |

## Operator flow

1. **Connect** — `POST /api/connect` (MAVSDK bind).
2. **Set fence** — north/south/east/west metres from home → `POST /api/fence`.
3. **Scan** — `POST /api/scan` with `source` = dashboard-first or RC-first.
4. Select rows in the detections table → **Confirm selected** or **Reject selected**.
5. **Visit confirmed** — XY at scan height, descend, pulse, RTL.
6. **RTL**, **People/pets — hold**, or **Kill (pump off)** at any time.

The sticky status bar is the glance row: phase, flight mode, MAVLink link, armed and in-air, radio, flight-pack percent and voltage, height above home, height above ground, pump, vision mode, picture, and session kind. Height above home is `relative_alt_m` (the scan climb). Height above ground is the rangefinder and reads `missing` on SIH. Local NED down is not shown.

Pack numbers come from MAVSDK `telemetry.battery` (`battery_voltage_v`, `battery_remaining_pct` on the 0-100 scale). Until a finite sample arrives the cell says `no sample`. A `sitl` session is labeled `simulated`. Display floors for the planned 4S pack, not written to PX4: caution under 30% or 14.8 V, warning under 20% or 14.0 V. The last voltage seen as the pump turns on is kept as `at pulse`. Those floors do not command RTL.

Color roles: green for a nominal reading, amber for a caution, red for a warning or the Kill control, cyan for a missing or stale sample. A snapshot older than one second marks the link stale. The legal reminder sits in the footer.

Commands are grouped: Prepare (connect, fence, scan), Plants (confirm, reject, visit), Recover (RTL, people/pets hold), and Stop (Kill). The command that matches the phase is filled. Scan stays inert until the fence is uploaded and the vehicle is connected. Kill and the people hold stay available. The yard card draws the fence with north up, the vehicle and nose, and plant dots. A confirmed plant is green. A box on the video uses a light stroke and the class name. Clicking it selects the table row. It does not confirm.

Camera: `<video>` on `/hls/cam/index.m3u8`. hls.js plays the playlist whenever `Hls.isSupported()` is true, including in Chrome, which reports native HLS as `"maybe"` and then fails to demux. A native `video.src` is used only when hls.js cannot attach. Vite proxies `/hls` to MediaMTX `:8888` and strips the `Secure` cookie so HTTP localhost can play. Direct WebRTC on `:8889` fails from a Windows browser (ICE / “peer connection closed”). RTSP `8554/cam` stays the backend/YOLO pull.

The page polls `GET /api/vision/boxes` every 500 ms and draws class and confidence on the video. The line under the video says the picture lags the detection stream. A box with an id selects that table row. It does not confirm. Injector rows have no pixel box, so the overlay stays empty.

On load the footer shows the hardcoded preflight reminder (not legal advice). `GET /api/preflight` still runs, and the footer is cleared only if that payload sets `not_legal_advice` to false. State is pushed over WebSocket `/ws`. If the socket errors, the UI polls `GET /api/state` every 500 ms, and leaving the page clears that timer. A socket that is still connecting is closed when it opens, so StrictMode's first cleanup does not close it mid-handshake.

## Types in `App.tsx`

- `Detection` — one plant row (`class` or `class_name`, NED metres, confirm/visited/sprayed flags).
- `State` — subset of backend `AppState` the UI actually renders.
- `empty` — idle default before the first snapshot.

Functions: `chooseHlsPlayback`, `attachStateSocket`, `missionSocket`, `actionEnabled`, `primaryAction`, `packTone`, `planPercent`, `api`, `App`, `toggle`, `run`. See [code-reference.md](code-reference.md#dashboardsrcapptsx).
