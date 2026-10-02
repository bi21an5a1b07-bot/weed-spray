/**
 * Pure dashboard readings: tones, which action is next, and the yard plan.
 *
 * Pack floors are display hints for the planned 4S flight pack. They are not
 * written to PX4 and they do not command return-to-launch.
 */

/** Caution when pack voltage is under this many volts. */
export const PACK_CAUTION_V = 14.8;
/** Warning when pack voltage is under this many volts. */
export const PACK_WARNING_V = 14.0;
/** Caution when remaining percent is under this value (0-100). */
export const PACK_CAUTION_PCT = 30;
/** Warning when remaining percent is under this value (0-100). */
export const PACK_WARNING_PCT = 20;
/** Lawnmower height shown next to barometric altitude. */
export const SCAN_AGL_M = 2.0;
/** Spray-hover band shown next to the rangefinder. */
export const HOVER_MIN_M = 0.24;
export const HOVER_MAX_M = 0.32;
/** A snapshot older than this is marked stale. */
export const STALE_MS = 1000;

/** Visual role for one reading. */
export type Tone = "neutral" | "nominal" | "caution" | "warning" | "stale";

/** Operator command the status logic can enable or emphasize. */
export type ActionName =
  | "connect"
  | "fence"
  | "scan"
  | "confirm"
  | "reject"
  | "visit"
  | "rtl"
  | "hold"
  | "kill";

/** Facts the enable and primary rules need. No DOM. */
export type ActionContext = {
  phase: string;
  connected: boolean;
  fenceSet: boolean;
  selectedCount: number;
  confirmedCount: number;
};

/** Typed or uploaded yard rectangle, metres from home. North is up. */
export type YardFence = {
  north_m: number;
  south_m: number;
  east_m: number;
  west_m: number;
};

const BUSY = new Set(["taking_off", "scanning", "visiting", "hovering", "spraying"]);

/**
 * True while a scan or visit task owns the aircraft.
 *
 * @param phase - Mission phase name from the backend.
 */
export function missionBusy(phase: string): boolean {
  return BUSY.has(phase);
}

/**
 * Whether a command is available for this phase.
 *
 * Kill and the people hold stay available. Scan waits for a connected vehicle
 * and an uploaded fence, and stays inert while a mission task is running.
 *
 * @param name - Command to test.
 * @param ctx - Current phase and selection.
 */
export function actionEnabled(name: ActionName, ctx: ActionContext): boolean {
  if (name === "kill" || name === "hold" || name === "connect") return true;
  const busy = missionBusy(ctx.phase);
  if (name === "fence") return ctx.connected && !busy;
  if (name === "scan") return ctx.connected && ctx.fenceSet && !busy;
  if (name === "confirm" || name === "reject") return ctx.selectedCount > 0 && !busy;
  if (name === "visit") {
    return ctx.connected && ctx.confirmedCount > 0 && !busy && ctx.phase === "awaiting_confirm";
  }
  if (name === "rtl") return ctx.connected;
  return false;
}

/**
 * The single filled command for this phase, or null when none should be emphasized.
 *
 * @param ctx - Current phase and selection.
 */
export function primaryAction(ctx: ActionContext): ActionName | null {
  if (!ctx.connected && !missionBusy(ctx.phase)) return "connect";
  if (ctx.connected && !ctx.fenceSet && !missionBusy(ctx.phase)) return "fence";
  if (
    ctx.connected &&
    ctx.fenceSet &&
    (ctx.phase === "fence_set" || ctx.phase === "connected") &&
    !missionBusy(ctx.phase)
  ) {
    return "scan";
  }
  if (ctx.phase === "awaiting_confirm" && ctx.selectedCount > 0) return "confirm";
  if (ctx.phase === "awaiting_confirm" && ctx.confirmedCount > 0) return "visit";
  return null;
}

function finite(value: number | null | undefined): value is number {
  return value != null && Number.isFinite(value);
}

/**
 * Tone for the flight-pack estimate.
 *
 * No finite voltage and no finite percent is a missing sample. Otherwise the
 * lower of the voltage and percent floors wins.
 *
 * @param voltage - Pack volts, or missing.
 * @param percent - Remaining percent on the 0-100 scale, or missing.
 */
export function packTone(
  voltage: number | null | undefined,
  percent: number | null | undefined,
): Tone {
  const hasV = finite(voltage);
  const hasP = finite(percent);
  if (!hasV && !hasP) return "stale";
  if ((hasP && percent < PACK_WARNING_PCT) || (hasV && voltage < PACK_WARNING_V)) return "warning";
  if ((hasP && percent < PACK_CAUTION_PCT) || (hasV && voltage < PACK_CAUTION_V)) return "caution";
  return "nominal";
}

/**
 * Tone for the rangefinder. Missing is not a height.
 *
 * @param missing - Backend `distance_sensor_missing`.
 * @param meters - Trusted short-range metres.
 */
export function groundTone(missing: boolean, meters: number | null | undefined): Tone {
  if (missing || !finite(meters)) return "stale";
  if (meters >= HOVER_MIN_M && meters <= HOVER_MAX_M) return "nominal";
  return "caution";
}

/**
 * Tone for the pump command. A non-zero value during return, land, kill, or
 * error is a warning. A pulse during a visit is a caution.
 *
 * @param value - Last `set_actuator` value.
 * @param phase - Mission phase name.
 */
export function pumpTone(value: number, phase: string): Tone {
  if (value === 0) return "nominal";
  if (phase === "killed" || phase === "rtl" || phase === "land" || phase === "error") {
    return "warning";
  }
  return "caution";
}

/**
 * Radio chip. A missing radio on hardware is a caution. On SITL it is only
 * a missing sample.
 *
 * @param available - `rc_available`, or null before the first sample.
 * @param kind - `sitl` or `hw`.
 */
export function radioReading(
  available: boolean | null | undefined,
  kind: string | null,
): { tone: Tone; label: string } {
  if (available === true) return { tone: "nominal", label: "up" };
  if (available === false && kind === "hw") return { tone: "caution", label: "no RC" };
  if (available === false) return { tone: "stale", label: "no RC" };
  return { tone: "stale", label: "no sample" };
}

/**
 * Armed chip. Armed on the ground is the caution. In the air is nominal.
 *
 * @param armed - PX4 armed flag.
 * @param inAir - PX4 in-air flag.
 */
export function armedReading(armed: boolean, inAir: boolean): { tone: Tone; label: string } {
  if (armed && inAir) return { tone: "nominal", label: "armed · in air" };
  if (armed) return { tone: "caution", label: "armed" };
  if (inAir) return { tone: "caution", label: "in air" };
  return { tone: "neutral", label: "disarmed" };
}

/**
 * Horizontal speed from north and east velocity.
 *
 * @param vn - North metres per second.
 * @param ve - East metres per second.
 * @returns Speed in metres per second, or null when either axis is missing.
 */
export function horizontalSpeed(
  vn: number | null | undefined,
  ve: number | null | undefined,
): number | null {
  if (!finite(vn) || !finite(ve)) return null;
  return Math.hypot(vn, ve);
}

/**
 * Map a NED point into the plan, 0-100, north up. An 8% pad keeps the fence
 * off the SVG edge. Null when the rectangle has no area.
 *
 * @param fence - Yard edges in metres.
 * @param north - Point north metres.
 * @param east - Point east metres.
 */
export function planPercent(
  fence: YardFence,
  north: number,
  east: number,
): { x: number; y: number } | null {
  const width = fence.east_m - fence.west_m;
  const height = fence.north_m - fence.south_m;
  if (!(width > 0) || !(height > 0) || !finite(north) || !finite(east)) return null;
  const pad = 0.08;
  const x = ((east - fence.west_m) / width) * (1 - 2 * pad) + pad;
  const y = ((fence.north_m - north) / height) * (1 - 2 * pad) + pad;
  return { x: x * 100, y: y * 100 };
}

/**
 * Nose tick in plan space. Heading 0 points up (north). Degrees clockwise.
 *
 * @param headingDeg - Clockwise degrees from north.
 * @param length - Tick length in the same units as the plan coordinates.
 */
export function headingOffset(
  headingDeg: number,
  length: number,
): { dx: number; dy: number } {
  const rad = (headingDeg * Math.PI) / 180;
  return { dx: Math.sin(rad) * length, dy: -Math.cos(rad) * length };
}
