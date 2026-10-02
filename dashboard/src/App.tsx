import { useEffect, useMemo, useRef, useState } from "react";
import Hls from "hls.js";

import { chooseHlsPlayback } from "./playback";
import {
  SCAN_AGL_M,
  STALE_MS,
  actionEnabled,
  armedReading,
  groundTone,
  headingOffset,
  horizontalSpeed,
  packTone,
  planPercent,
  primaryAction,
  pumpTone,
  radioReading,
  type ActionContext,
  type ActionName,
  type Tone,
  type YardFence,
} from "./status";
import { attachStateSocket, type MissionSocket } from "./stateSocket";

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

type PumpOff = { t: string; type: string; pump_commanded_off: boolean };
type PhaseLog = { t: string; name: string };
type PumpPulse = { t: string; duration_s: number; detection_id: string };

/** Subset of backend AppState the operator UI renders. */
type State = {
  phase: string;
  last_error: string | null;
  kind: string | null;
  arm_source: string | null;
  fence: YardFence | null;
  rtsp_url: string;
  webrtc_url: string;
  mavsdk_address: string;
  telemetry: {
    connected: boolean;
    armed: boolean;
    in_air: boolean;
    flight_mode: string | null;
    rc_available: boolean | null;
    north_m: number | null;
    east_m: number | null;
    vn_m_s: number | null;
    ve_m_s: number | null;
    heading_deg: number | null;
    relative_alt_m: number | null;
    distance_sensor_m: number | null;
    distance_sensor_missing: boolean;
    battery_voltage_v: number | null;
    battery_remaining_pct: number | null;
    pump_value: number;
  };
  detections: Detection[];
  pump_off_events: PumpOff[];
  pump_pulses: PumpPulse[];
  phase_log: PhaseLog[];
};

type Picture = "starting" | "playing" | "stalled";
type SocketMode = "live" | "polling" | "down";
type VisionLink = { up: boolean; mode: string; camera: boolean };

/** Idle snapshot shown before the first WebSocket / poll payload. */
const empty: State = {
  phase: "idle",
  last_error: null,
  kind: null,
  arm_source: null,
  fence: null,
  rtsp_url: "",
  webrtc_url: "",
  mavsdk_address: "",
  telemetry: {
    connected: false,
    armed: false,
    in_air: false,
    flight_mode: null,
    rc_available: null,
    north_m: null,
    east_m: null,
    vn_m_s: null,
    ve_m_s: null,
    heading_deg: null,
    relative_alt_m: null,
    distance_sensor_m: null,
    distance_sensor_missing: true,
    battery_voltage_v: null,
    battery_remaining_pct: null,
    pump_value: 0,
  },
  detections: [],
  pump_off_events: [],
  pump_pulses: [],
  phase_log: [],
};

/** One camera-plane box from GET /vision/boxes. No north/east. */
type PixelBox = {
  id?: string;
  class?: string;
  conf?: number;
  cx: number;
  cy: number;
  w: number;
  h: number;
};

/**
 * Fill defaults so a partial snapshot still has every field the console reads.
 *
 * @param raw - JSON object from `/ws` or `GET /api/state`.
 */
function asState(raw: Partial<State> | null): State {
  if (!raw) return empty;
  return {
    ...empty,
    ...raw,
    telemetry: { ...empty.telemetry, ...(raw.telemetry ?? {}) },
    detections: raw.detections ?? [],
    pump_off_events: raw.pump_off_events ?? [],
    pump_pulses: raw.pump_pulses ?? [],
    phase_log: raw.phase_log ?? [],
  };
}

/**
 * Adapt a browser `WebSocket` to the DOM-free mission socket.
 *
 * Message data is passed as text. Close, open, and error stay on the
 * underlying socket so `attachStateSocket` can defer a connecting close.
 *
 * @param ws - Socket opened against `/ws`.
 * @returns A `MissionSocket` whose handlers forward to `ws`.
 */
function missionSocket(ws: WebSocket): MissionSocket {
  return {
    get readyState() {
      return ws.readyState;
    },
    close() {
      ws.close();
    },
    set onmessage(handler: MissionSocket["onmessage"]) {
      ws.onmessage = handler ? (ev) => handler({ data: String(ev.data) }) : null;
    },
    get onmessage(): MissionSocket["onmessage"] {
      return null;
    },
    set onerror(handler: MissionSocket["onerror"]) {
      ws.onerror = handler ? () => handler() : null;
    },
    get onerror(): MissionSocket["onerror"] {
      return null;
    },
    set onopen(handler: MissionSocket["onopen"]) {
      ws.onopen = handler ? () => handler() : null;
    },
    get onopen(): MissionSocket["onopen"] {
      return null;
    },
  };
}

/** Metres, or an em dash when the sample is missing. */
function metres(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value.toFixed(2)} m`;
}

/** One status reading. Tone is a class, and the label is always text. */
function Chip({
  label,
  value,
  detail,
  tone = "neutral",
  strong = false,
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: Tone;
  strong?: boolean;
}) {
  return (
    <div className={`chip tone-${tone}${strong ? " chip-strong" : ""}`}>
      <span className="chip-label">{label}</span>
      <strong>{value}</strong>
      {detail ? <span className="chip-detail">{detail}</span> : null}
    </div>
  );
}

/** Same-origin HLS of the MediaMTX file loop. WebRTC ICE fails from Windows to WSL. */
function CamMonitor({
  rtsp,
  boxes,
  onPick,
  onPicture,
}: {
  rtsp: string;
  boxes: PixelBox[];
  onPick: (id: string) => void;
  onPicture: (picture: Picture) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pictureRef = useRef(onPicture);
  pictureRef.current = onPicture;
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const src = "/hls/cam/index.m3u8";
    const report = () => {
      const tell = pictureRef.current;
      if (video.readyState >= 2 && !video.paused) tell("playing");
      else if (video.readyState < 2) tell("starting");
      else tell("stalled");
    };
    video.addEventListener("playing", report);
    video.addEventListener("waiting", report);
    video.addEventListener("stalled", report);
    video.addEventListener("pause", report);
    video.addEventListener("emptied", report);
    if (chooseHlsPlayback(Hls.isSupported()) === "native") {
      video.src = src;
      return () => {
        video.removeEventListener("playing", report);
        video.removeEventListener("waiting", report);
        video.removeEventListener("stalled", report);
        video.removeEventListener("pause", report);
        video.removeEventListener("emptied", report);
      };
    }
    const hls = new Hls({ lowLatencyMode: true });
    hls.loadSource(src);
    hls.attachMedia(video);
    return () => {
      video.removeEventListener("playing", report);
      video.removeEventListener("waiting", report);
      video.removeEventListener("stalled", report);
      video.removeEventListener("pause", report);
      video.removeEventListener("emptied", report);
      hls.destroy();
    };
  }, []);
  return (
    <section className="card cam">
      <h2>Camera</h2>
      <div className="cam-frame">
        <video ref={videoRef} muted autoPlay playsInline controls />
        {boxes.map((box, index) => {
          const style = {
            left: `${(box.cx - box.w / 2) * 100}%`,
            top: `${(box.cy - box.h / 2) * 100}%`,
            width: `${box.w * 100}%`,
            height: `${box.h * 100}%`,
          };
          const label = `${box.class ?? "weed"}${box.conf != null ? ` ${box.conf.toFixed(2)}` : ""}`;
          if (box.id) {
            return (
              <button
                key={box.id}
                type="button"
                className="box"
                style={style}
                onClick={() => onPick(box.id as string)}
              >
                {label}
              </button>
            );
          }
          return (
            <span key={`${label}-${index}`} className="box" style={style}>
              {label}
            </span>
          );
        })}
      </div>
      <p className="meta">
        The picture lags the detection stream. HLS /hls/cam/ · RTSP{" "}
        {rtsp || "rtsp://127.0.0.1:8554/cam"}
      </p>
    </section>
  );
}

/** Fence rectangle, vehicle, nose, and confirmed plants. North is up. */
function YardPlan({
  fence,
  uploaded,
  north,
  east,
  heading,
  plants,
  speed,
  aboveHome,
  aboveGround,
  groundMissing,
}: {
  fence: YardFence;
  uploaded: boolean;
  north: number | null;
  east: number | null;
  heading: number | null;
  plants: Detection[];
  speed: number | null;
  aboveHome: number | null;
  aboveGround: number | null;
  groundMissing: boolean;
}) {
  const vehicle = north != null && east != null ? planPercent(fence, north, east) : null;
  const nose =
    vehicle && heading != null
      ? headingOffset(heading, 7)
      : null;
  return (
    <section className="card plan">
      <h2>Yard</h2>
      <p className="meta">{uploaded ? "Fence uploaded" : "Typed fence, not uploaded yet"}</p>
      <svg viewBox="0 0 100 100" role="img" aria-label="Yard fence, vehicle, and plants">
        <text className="compass" x="50" y="5.5" textAnchor="middle">
          N
        </text>
        <rect className="fence" x="8" y="8" width="84" height="84" />
        {plants.map((plant) => {
          const at = planPercent(fence, plant.north_m, plant.east_m);
          if (!at) return null;
          return (
            <circle
              key={plant.id}
              cx={at.x}
              cy={at.y}
              r="1.8"
              className={plant.confirmed ? "plant confirmed" : "plant"}
            >
              <title>
                {plant.id} {plant.class ?? plant.class_name ?? ""}
              </title>
            </circle>
          );
        })}
        {vehicle ? <circle className="vehicle" cx={vehicle.x} cy={vehicle.y} r="2.4" /> : null}
        {vehicle && nose ? (
          <line
            className="nose"
            x1={vehicle.x}
            y1={vehicle.y}
            x2={vehicle.x + nose.dx}
            y2={vehicle.y + nose.dy}
          />
        ) : null}
      </svg>
      <dl className="readout">
        <div>
          <dt>Above home</dt>
          <dd>{metres(aboveHome)}</dd>
          <dd className="meta">scan {SCAN_AGL_M.toFixed(1)} m</dd>
        </div>
        <div>
          <dt>Above ground</dt>
          <dd className={`tone-${groundTone(groundMissing, aboveGround)}`}>
            {groundMissing ? "missing" : metres(aboveGround)}
          </dd>
          <dd className="meta">band 0.24-0.32 m</dd>
        </div>
        <div>
          <dt>Speed</dt>
          <dd>{speed == null ? "—" : `${speed.toFixed(1)} m/s`}</dd>
        </div>
        <div>
          <dt>Heading</dt>
          <dd>{heading == null ? "—" : `${heading.toFixed(0)}°`}</dd>
        </div>
        <div>
          <dt>North</dt>
          <dd>{metres(north)}</dd>
        </div>
        <div>
          <dt>East</dt>
          <dd>{metres(east)}</dd>
        </div>
      </dl>
    </section>
  );
}

/** POST/GET the backend via the Vite ``/api`` proxy (strips the prefix). */
async function api(path: string, init?: RequestInit) {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) throw new Error(`${path} ${res.status} ${await res.text()}`);
  return res.json();
}

/** Localhost GCS: status bar, yard, grouped commands, confirm table. */
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
  const [boxes, setBoxes] = useState<PixelBox[]>([]);
  const [vision, setVision] = useState<VisionLink>({ up: false, mode: "injector", camera: false });
  const [picture, setPicture] = useState<Picture>("starting");
  const [socketMode, setSocketMode] = useState<SocketMode>("down");
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [pulseVoltage, setPulseVoltage] = useState<number | null>(null);
  const prevPump = useRef(0);
  const onPicture = useRef(setPicture);
  onPicture.current = setPicture;

  useEffect(() => {
    const reminder =
      "Not legal advice. RC in hand. VLOS. Confirm every spray. Check B4UFLY. Weigh ≥250 g → register/Remote ID. Part 137 open before a real spray. SITL is not authorization.";
    setPreflight(reminder);
    fetch("/api/preflight")
      .then((r) => r.json())
      .then((p) => {
        if (p && p.not_legal_advice === false) setPreflight(null);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let stop = false;
    const tick = () => {
      fetch("/api/vision/boxes")
        .then((r) => r.json())
        .then((body) => {
          if (stop) return;
          setBoxes(body.boxes ?? []);
          setVision({
            up: true,
            mode: typeof body.mode === "string" ? body.mode : "injector",
            camera: Boolean(body.camera),
          });
        })
        .catch(() => {
          if (stop) return;
          setBoxes([]);
          setVision({ up: false, mode: "down", camera: false });
        });
    };
    tick();
    const id = setInterval(tick, 500);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    let pollId: ReturnType<typeof setInterval> | undefined;
    const ws = new WebSocket(`ws://${location.host}/ws`);
    const accept = (data: string) => {
      setState(asState(JSON.parse(data) as Partial<State>));
      setUpdatedAt(Date.now());
      setSocketMode("live");
    };
    const stop = attachStateSocket(missionSocket(ws), {
      onMessage: accept,
      onSocketError: () => {
        setSocketMode("polling");
        if (pollId !== undefined) return;
        pollId = setInterval(() => {
          fetch("/api/state")
            .then((r) => r.json())
            .then((body) => {
              setState(asState(body as Partial<State>));
              setUpdatedAt(Date.now());
              setSocketMode("polling");
            })
            .catch(() => setSocketMode("down"));
        }, 500);
      },
    });
    return () => {
      if (pollId !== undefined) clearInterval(pollId);
      stop();
    };
  }, []);

  useEffect(() => {
    const value = state.telemetry.pump_value;
    if (prevPump.current === 0 && value > 0) {
      setPulseVoltage(state.telemetry.battery_voltage_v);
    }
    prevPump.current = value;
  }, [state.telemetry.pump_value, state.telemetry.battery_voltage_v]);

  const t = state.telemetry;
  const error = err || state.last_error;
  const selected = useMemo(() => new Set(picked), [picked]);
  const confirmedCount = state.detections.filter((d) => d.confirmed).length;
  const ctx: ActionContext = {
    phase: state.phase,
    connected: t.connected,
    fenceSet: state.fence != null,
    selectedCount: picked.length,
    confirmedCount,
  };
  const primary = primaryAction(ctx);
  const stale = updatedAt != null && now - updatedAt > STALE_MS;
  const typedFence: YardFence = {
    north_m: north,
    south_m: south,
    east_m: east,
    west_m: west,
  };
  const planFence = state.fence ?? typedFence;
  const pack = packTone(t.battery_voltage_v, t.battery_remaining_pct);
  const radio = radioReading(t.rc_available, state.kind);
  const armed = armedReading(t.armed, t.in_air);
  const speed = horizontalSpeed(t.vn_m_s, t.ve_m_s);
  const events = [
    ...state.pump_off_events.slice(-3).map((ev) => `Pump off · ${ev.type}`),
    ...state.phase_log.slice(-3).map((ev) => `Phase · ${ev.name}`),
  ];

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

  function command(name: ActionName, className: string, label: string, go: () => Promise<unknown>) {
    const on = actionEnabled(name, ctx);
    return (
      <button
        type="button"
        className={`${className}${primary === name ? " primary" : ""}`}
        disabled={!on}
        onClick={() => run(go)}
      >
        {label}
      </button>
    );
  }

  const packValue =
    pack === "stale"
      ? "no sample"
      : t.battery_remaining_pct != null
        ? `${Math.round(t.battery_remaining_pct)}%`
        : "—";
  const packDetail = [
    t.battery_voltage_v != null ? `${t.battery_voltage_v.toFixed(1)} V` : null,
    state.kind === "sitl" ? "simulated" : state.kind === "hw" ? "PX4 pack" : null,
    pulseVoltage != null ? `at pulse ${pulseVoltage.toFixed(1)} V` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="app">
      <header className="status-bar">
        <Chip label="Phase" value={state.phase} strong />
        <Chip label="Mode" value={t.flight_mode ?? "—"} />
        <Chip
          label="Link"
          value={t.connected ? "up" : "down"}
          detail={stale ? "stale" : socketMode === "polling" ? "polling" : undefined}
          tone={stale ? "stale" : t.connected ? "nominal" : "neutral"}
        />
        <Chip label="Aircraft" value={armed.label} tone={armed.tone} />
        <Chip label="Radio" value={radio.label} tone={radio.tone} />
        <Chip label="Pack" value={packValue} detail={packDetail} tone={pack} strong />
        <Chip
          label="Above home"
          value={metres(t.relative_alt_m)}
          detail={`scan ${SCAN_AGL_M.toFixed(1)} m`}
        />
        <Chip
          label="Above ground"
          value={t.distance_sensor_missing ? "missing" : metres(t.distance_sensor_m)}
          detail="band 0.24-0.32 m"
          tone={groundTone(t.distance_sensor_missing, t.distance_sensor_m)}
        />
        <Chip
          label="Pump"
          value={t.pump_value === 0 ? "off" : "pulsing"}
          detail={
            state.pump_pulses.length
              ? `${state.pump_pulses.length} pulse${state.pump_pulses.length === 1 ? "" : "s"}`
              : undefined
          }
          tone={pumpTone(t.pump_value, state.phase)}
        />
        <Chip
          label="Vision"
          value={vision.up ? vision.mode : "down"}
          detail={vision.camera ? "camera" : "no camera"}
          tone={vision.up ? "nominal" : "stale"}
        />
        <Chip
          label="Picture"
          value={picture}
          tone={picture === "playing" ? "nominal" : "stale"}
        />
        <Chip
          label="Session"
          value={state.kind ?? "—"}
          detail={state.arm_source ?? undefined}
          tone="neutral"
        />
      </header>

      {error ? (
        <p className="banner" role="alert">
          {error}
        </p>
      ) : null}
      {events.length ? (
        <ul className="events">
          {events.map((line, index) => (
            <li key={`${line}-${index}`}>{line}</li>
          ))}
        </ul>
      ) : null}

      <div className="stage">
        <CamMonitor
          rtsp={state.rtsp_url}
          boxes={boxes}
          onPick={toggle}
          onPicture={(next) => onPicture.current(next)}
        />
        <YardPlan
          fence={planFence}
          uploaded={state.fence != null}
          north={t.north_m}
          east={t.east_m}
          heading={t.heading_deg}
          plants={state.detections}
          speed={speed}
          aboveHome={t.relative_alt_m}
          aboveGround={t.distance_sensor_m}
          groundMissing={t.distance_sensor_missing}
        />
      </div>

      <div className="actions">
        <section className="group">
          <h2>Prepare</h2>
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
          {command("connect", "", "Connect", () => api("/connect", { method: "POST" }))}
          {command("fence", "", "Set fence", () =>
            api("/fence", {
              method: "POST",
              body: JSON.stringify({
                north_m: north,
                south_m: south,
                east_m: east,
                west_m: west,
              }),
            }),
          )}
          {command("scan", "", "Scan", () =>
            api("/scan", { method: "POST", body: JSON.stringify({ source: armSource }) }),
          )}
        </section>

        <section className="group">
          <h2>Plants</h2>
          {command("confirm", "", "Confirm selected", () =>
            api("/confirm", { method: "POST", body: JSON.stringify({ ids: picked }) }),
          )}
          {command("reject", "", "Reject selected", () =>
            api("/confirm", {
              method: "POST",
              body: JSON.stringify({
                decisions: picked.map((id) => ({ detection_id: id, decision: "reject" })),
              }),
            }),
          )}
          {command("visit", "", "Visit confirmed", () => api("/visit", { method: "POST" }))}
        </section>

        <section className="group">
          <h2>Recover</h2>
          {command("rtl", "", "RTL", () => api("/rtl", { method: "POST" }))}
          {command("hold", "", "People/pets — hold", () => api("/hold-people", { method: "POST" }))}
        </section>

        <section className="group stop">
          <h2>Stop</h2>
          {command("kill", "kill", "Kill (pump off)", () => api("/kill", { method: "POST" }))}
        </section>
      </div>

      <section className="fence-fields">
        <h2>Fence metres from home</h2>
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
        <p className="meta">{state.mavsdk_address || "udpin://0.0.0.0:14540"}</p>
      </section>

      <section className="detections">
        <h2>Detections</h2>
        <table>
          <thead>
            <tr>
              <th></th>
              <th>id</th>
              <th>class</th>
              <th className="num">N</th>
              <th className="num">E</th>
              <th>flags</th>
            </tr>
          </thead>
          <tbody>
            {state.detections.length === 0 ? (
              <tr>
                <td colSpan={6} className="meta">
                  No detections yet. Inject or a live detector fills this table. A row click selects.
                  Confirm is a separate command.
                </td>
              </tr>
            ) : (
              state.detections.map((d) => (
                <tr key={d.id} className={selected.has(d.id) ? "selected" : undefined}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(d.id)}
                      onChange={() => toggle(d.id)}
                      aria-label={`select ${d.id}`}
                    />
                  </td>
                  <td>{d.id}</td>
                  <td>{d.class ?? d.class_name}</td>
                  <td className="num">{d.north_m}</td>
                  <td className="num">{d.east_m}</td>
                  <td>
                    {[d.confirmed && "confirmed", d.visited && "visited", d.sprayed && "sprayed"]
                      .filter(Boolean)
                      .join(" ") || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <footer>{preflight}</footer>
    </div>
  );
}
