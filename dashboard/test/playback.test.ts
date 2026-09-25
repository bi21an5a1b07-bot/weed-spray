import assert from "node:assert/strict";
import test from "node:test";

import { chooseHlsPlayback } from "../src/playback.ts";
import { attachStateSocket, CONNECTING, OPEN } from "../src/stateSocket.ts";

class FakeSocket {
  readyState = CONNECTING;
  closed = 0;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onopen: (() => void) | null = null;

  close(): void {
    this.closed += 1;
  }

  open(): void {
    this.readyState = OPEN;
    this.onopen?.();
  }

  fail(): void {
    this.onerror?.();
  }
}

test("hls.js is used when it can attach, including Chrome maybe-native", () => {
  assert.equal(chooseHlsPlayback(true), "hls.js");
});

test("native HLS is only the fallback when hls.js cannot attach", () => {
  assert.equal(chooseHlsPlayback(false), "native");
});

test("cleanup while CONNECTING does not close until open", () => {
  const socket = new FakeSocket();
  const stop = attachStateSocket(socket, {
    onMessage: () => undefined,
    onSocketError: () => undefined,
  });
  stop();
  assert.equal(socket.closed, 0);
  socket.open();
  assert.equal(socket.closed, 1);
});

test("cleanup of an open socket closes it now", () => {
  const socket = new FakeSocket();
  socket.readyState = OPEN;
  const stop = attachStateSocket(socket, {
    onMessage: () => undefined,
    onSocketError: () => undefined,
  });
  stop();
  assert.equal(socket.closed, 1);
});

test("a socket error after dispose does not start the poll", () => {
  const socket = new FakeSocket();
  let polls = 0;
  const stop = attachStateSocket(socket, {
    onMessage: () => undefined,
    onSocketError: () => {
      polls += 1;
    },
  });
  stop();
  socket.fail();
  assert.equal(polls, 0);
});

test("a socket error before dispose starts the poll once", () => {
  const socket = new FakeSocket();
  let polls = 0;
  attachStateSocket(socket, {
    onMessage: () => undefined,
    onSocketError: () => {
      polls += 1;
    },
  });
  socket.fail();
  socket.fail();
  assert.equal(polls, 1);
});
