/** WebSocket.CONNECTING. Kept here so tests do not need the DOM lib. */
export const CONNECTING = 0;

/** WebSocket.OPEN. */
export const OPEN = 1;

/** Minimal socket the mission-state effect can drive without a browser. */
export type MissionSocket = {
  readyState: number;
  close: () => void;
  onmessage: ((ev: { data: string }) => void) | null;
  onerror: (() => void) | null;
  onopen: (() => void) | null;
};

/**
 * Attach mission-state handlers and return a cleanup.
 *
 * A dispose that runs while the socket is still connecting does not call
 * `close` immediately. Chrome logs that close as "closed before the
 * connection is established", and React StrictMode does it on every load.
 * The socket is closed on its open event instead. An error after dispose
 * does not call `onSocketError`, so the HTTP poll is not started for a
 * socket the effect already abandoned. A second error does not call
 * `onSocketError` again.
 *
 * @param socket - Connecting or open mission socket.
 * @param handlers - `onMessage` receives the payload text. `onSocketError` starts the poll.
 * @returns Cleanup. Closes an open socket now, or on the following open.
 */
export function attachStateSocket(
  socket: MissionSocket,
  handlers: {
    onMessage: (data: string) => void;
    onSocketError: () => void;
  },
): () => void {
  let disposed = false;
  let reportedError = false;
  socket.onmessage = (ev) => {
    if (!disposed) handlers.onMessage(ev.data);
  };
  socket.onerror = () => {
    if (disposed || reportedError) return;
    reportedError = true;
    handlers.onSocketError();
  };
  return () => {
    disposed = true;
    if (socket.readyState === CONNECTING) {
      socket.onopen = () => {
        socket.close();
      };
      return;
    }
    socket.close();
  };
}
