import { useEffect, useMemo, useState } from "react";

/** One plant row from backend AppState (JSON key is `class`). */
type Detection = {
  id: string;
  class?: string;
  class_name?: string;
  north_m: number;
  east_m: number;
  confirmed: boolean;
  visited: boolean;
  sprayed: boolean;
};

/** Subset of backend AppState the operator UI renders. */
type State = {
  phase: string;
  last_error: string | null;
  rtsp_url: string;
  mavsdk_address: string;
  telemetry: {
    connected: boolean;
    armed: boolean;
    in_air: boolean;
    relative_alt_m: number | null;
    distance_sensor_m: number | null;
    distance_sensor_missing: boolean;
    pump_value: number;
  };
  detections: Detection[];
};

/** Idle snapshot shown before the first WebSocket / poll payload. */
const empty: State = {
  phase: "idle",
  last_error: null,
  rtsp_url: "",
  mavsdk_address: "",
  telemetry: {
    connected: false,
    armed: false,
    in_air: false,
    relative_alt_m: null,
    distance_sensor_m: null,
    distance_sensor_missing: true,
    pump_value: 0,
  },
  detections: [],
};

/** POST/GET the backend via the Vite ``/api`` proxy (strips the prefix). */
async function api(path: string, init?: RequestInit) {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) throw new Error(`${path} ${res.status} ${await res.text()}`);
  return res.json();
}

/** Localhost GCS: fence, scan, confirm/reject, visit, RTL, people hold, kill. */
export default function App() {
  const [state, setState] = useState<State>(empty);
  const [north, setNorth] = useState(20);
  const [south, setSouth] = useState(-5);
  const [east, setEast] = useState(15);
  const [west, setWest] = useState(-15);
  const [picked, setPicked] = useState<string[]>([]);
  const [armSource, setArmSource] = useState<"dashboard" | "rc">("dashboard");
  const [err, setErr] = useState<string | null>(null);
  const [preflight, setPreflight] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/preflight")
      .then((r) => r.json())
      .then((p) =>
        setPreflight(
          "Not legal advice. RC in hand. VLOS. Confirm every spray. Check B4UFLY. Weigh ≥250 g → register/Remote ID. Part 137 open before a real spray. SITL is not authorization.",
        ),
      )
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onmessage = (ev) => setState(JSON.parse(ev.data));
    ws.onerror = () => {
      const id = setInterval(() => {
        fetch("/api/state")
          .then((r) => r.json())
          .then(setState)
          .catch(() => undefined);
      }, 500);
      return () => clearInterval(id);
    };
    return () => ws.close();
  }, []);

  const t = state.telemetry;
  const error = err || state.last_error;
  const selected = useMemo(() => new Set(picked), [picked]);

  /** Add or remove a detection id from the confirm/reject selection. */
  function toggle(id: string) {
    setPicked((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));
  }

  /** Run an API call and surface HTTP errors in the banner. */
  async function run(fn: () => Promise<unknown>) {
    setErr(null);
    try {
      await fn();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <main>
      <h1>weed-spray</h1>
      <p className="meta phase">
        phase <strong>{state.phase}</strong>
        {" · "}
        mav {t.connected ? "up" : "down"}
        {" · "}
        {t.armed ? "armed" : "disarmed"}
        {" · "}
        alt {t.relative_alt_m?.toFixed(2) ?? "—"} m
        {" · "}
        lidar {t.distance_sensor_missing ? "missing" : `${t.distance_sensor_m?.toFixed(2)} m`}
        {" · "}
        pump {t.pump_value}
      </p>
      <p className="meta">
        {state.mavsdk_address} · {state.rtsp_url}
      </p>
      {preflight ? <p className="meta">{preflight}</p> : null}
      {error ? <p className="meta">{error}</p> : null}

      <div className="row">
        <label>
          arm
          <select
            value={armSource}
            onChange={(e) => setArmSource(e.target.value as "dashboard" | "rc")}
          >
            <option value="dashboard">dashboard-first</option>
            <option value="rc">RC-first (already in air)</option>
          </select>
        </label>
      </div>

      <div className="row">
        <button type="button" onClick={() => run(() => api("/connect", { method: "POST" }))}>
          Connect
        </button>
        <button
          type="button"
          onClick={() =>
            run(() =>
              api("/fence", {
                method: "POST",
                body: JSON.stringify({
                  north_m: north,
                  south_m: south,
                  east_m: east,
                  west_m: west,
                }),
              }),
            )
          }
        >
          Set fence
        </button>
        <button
          type="button"
          onClick={() =>
            run(() =>
              api("/scan", { method: "POST", body: JSON.stringify({ source: armSource }) }),
            )
          }
        >
          Scan
        </button>
        <button
          type="button"
          onClick={() =>
            run(() => api("/confirm", { method: "POST", body: JSON.stringify({ ids: picked }) }))
          }
        >
          Confirm selected
        </button>
        <button
          type="button"
          onClick={() =>
            run(() =>
              api("/confirm", {
                method: "POST",
                body: JSON.stringify({
                  decisions: picked.map((id) => ({ detection_id: id, decision: "reject" })),
                }),
              }),
            )
          }
        >
          Reject selected
        </button>
        <button type="button" onClick={() => run(() => api("/visit", { method: "POST" }))}>
          Visit confirmed
        </button>
        <button type="button" onClick={() => run(() => api("/rtl", { method: "POST" }))}>
          RTL
        </button>
        <button
          type="button"
          onClick={() => run(() => api("/hold-people", { method: "POST" }))}
        >
          People/pets — hold
        </button>
        <button className="kill" type="button" onClick={() => run(() => api("/kill", { method: "POST" }))}>
          Kill (pump off)
        </button>
      </div>

      <div className="row">
        <label>
          north m
          <input type="number" value={north} onChange={(e) => setNorth(Number(e.target.value))} />
        </label>
        <label>
          south m
          <input type="number" value={south} onChange={(e) => setSouth(Number(e.target.value))} />
        </label>
        <label>
          east m
          <input type="number" value={east} onChange={(e) => setEast(Number(e.target.value))} />
        </label>
        <label>
          west m
          <input type="number" value={west} onChange={(e) => setWest(Number(e.target.value))} />
        </label>
      </div>

      <h2>Detections</h2>
      <table>
        <thead>
          <tr>
            <th></th>
            <th>id</th>
            <th>class</th>
            <th>N</th>
            <th>E</th>
            <th>flags</th>
          </tr>
        </thead>
        <tbody>
          {state.detections.map((d) => (
            <tr key={d.id}>
              <td>
                <input
                  type="checkbox"
                  checked={selected.has(d.id)}
                  onChange={() => toggle(d.id)}
                />
              </td>
              <td>{d.id}</td>
              <td>{d.class ?? d.class_name}</td>
              <td>{d.north_m}</td>
              <td>{d.east_m}</td>
              <td>
                {[d.confirmed && "confirmed", d.visited && "visited", d.sprayed && "sprayed"]
                  .filter(Boolean)
                  .join(" ") || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
