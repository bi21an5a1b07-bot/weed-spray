/** How `<video>` attaches to the MediaMTX HLS playlist. */
export type HlsPlayback = "hls.js" | "native";

/**
 * Choose the player for `/hls/cam/index.m3u8`.
 *
 * Chrome reports `canPlayType("application/vnd.apple.mpegurl")` as `"maybe"`
 * and then fails to demux MediaMTX low-latency fMP4
 * (`DEMUXER_ERROR_COULD_NOT_PARSE`). hls.js is used whenever it can attach.
 * A native source is only for browsers where hls.js cannot run (Safari).
 *
 * @param hlsSupported - `Hls.isSupported()` from hls.js.
 * @returns `"hls.js"` when the library can attach, otherwise `"native"`.
 */
export function chooseHlsPlayback(hlsSupported: boolean): HlsPlayback {
  return hlsSupported ? "hls.js" : "native";
}
