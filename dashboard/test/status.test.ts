import assert from "node:assert/strict";
import test from "node:test";

import {
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
} from "../src/status.ts";

const idle: ActionContext = {
  phase: "idle",
  connected: false,
  fenceSet: false,
  selectedCount: 0,
  confirmedCount: 0,
};

test("idle emphasizes connect and keeps kill available", () => {
  assert.equal(primaryAction(idle), "connect");
  assert.equal(actionEnabled("kill", idle), true);
  assert.equal(actionEnabled("scan", idle), false);
  assert.equal(actionEnabled("fence", idle), false);
});

test("a connected vehicle without a fence emphasizes set fence", () => {
  const ctx: ActionContext = { ...idle, phase: "connected", connected: true };
  assert.equal(primaryAction(ctx), "fence");
  assert.equal(actionEnabled("scan", ctx), false);
  assert.equal(actionEnabled("fence", ctx), true);
});

test("an uploaded fence emphasizes scan until the mission is busy", () => {
  const ready: ActionContext = {
    ...idle,
    phase: "fence_set",
    connected: true,
    fenceSet: true,
  };
  assert.equal(primaryAction(ready), "scan");
  assert.equal(actionEnabled("scan", ready), true);
  const scanning: ActionContext = { ...ready, phase: "scanning" };
  assert.equal(actionEnabled("scan", scanning), false);
  assert.equal(actionEnabled("confirm", { ...scanning, selectedCount: 1 }), false);
});

test("awaiting confirm emphasizes confirm, then visit", () => {
  const base: ActionContext = {
    phase: "awaiting_confirm",
    connected: true,
    fenceSet: true,
    selectedCount: 0,
    confirmedCount: 1,
  };
  assert.equal(primaryAction(base), "visit");
  assert.equal(primaryAction({ ...base, selectedCount: 2 }), "confirm");
  assert.equal(actionEnabled("visit", { ...base, phase: "scanning" }), false);
});

test("pack tone uses the lower of the voltage and percent floors", () => {
  assert.equal(packTone(null, null), "stale");
  assert.equal(packTone(16.2, 80), "nominal");
  assert.equal(packTone(14.5, 50), "caution");
  assert.equal(packTone(16.2, 25), "caution");
  assert.equal(packTone(13.9, 50), "warning");
  assert.equal(packTone(16.2, 19), "warning");
  assert.equal(packTone(Number.NaN, 80), "nominal");
});

test("ground tone treats a missing rangefinder as no height", () => {
  assert.equal(groundTone(true, 0.27), "stale");
  assert.equal(groundTone(false, null), "stale");
  assert.equal(groundTone(false, 0.27), "nominal");
  assert.equal(groundTone(false, 0.5), "caution");
});

test("pump, radio, and armed readings", () => {
  assert.equal(pumpTone(0, "spraying"), "nominal");
  assert.equal(pumpTone(1, "spraying"), "caution");
  assert.equal(pumpTone(1, "rtl"), "warning");
  assert.deepEqual(radioReading(null, "sitl"), { tone: "stale", label: "no sample" });
  assert.deepEqual(radioReading(false, "hw"), { tone: "caution", label: "no RC" });
  assert.deepEqual(radioReading(false, "sitl"), { tone: "stale", label: "no RC" });
  assert.equal(armedReading(true, false).tone, "caution");
  assert.equal(armedReading(true, true).tone, "nominal");
});

test("speed and plan geometry", () => {
  assert.equal(horizontalSpeed(3, 4), 5);
  assert.equal(horizontalSpeed(null, 4), null);
  const fence = { north_m: 10, south_m: 0, east_m: 10, west_m: 0 };
  const center = planPercent(fence, 5, 5);
  assert.ok(center);
  assert.ok(Math.abs(center.x - 50) < 0.01);
  assert.ok(Math.abs(center.y - 50) < 0.01);
  const northWest = planPercent(fence, 10, 0);
  assert.ok(northWest);
  assert.ok(Math.abs(northWest.x - 8) < 0.01);
  assert.ok(Math.abs(northWest.y - 8) < 0.01);
  assert.equal(planPercent({ ...fence, east_m: 0 }, 1, 1), null);
  const north = headingOffset(0, 10);
  assert.ok(Math.abs(north.dx) < 1e-9);
  assert.ok(Math.abs(north.dy + 10) < 1e-9);
  const east = headingOffset(90, 10);
  assert.ok(Math.abs(east.dx - 10) < 1e-9);
  assert.ok(Math.abs(east.dy) < 1e-9);
});
