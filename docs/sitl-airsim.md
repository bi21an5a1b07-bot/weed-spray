# Project AirSim spike (issue #66)

Spike only. **Keep SIH** (`make sitl`) as the default SITL path. Accurate lidar+cam stays `make sitl-gz`. Project AirSim **does not replace** either compose until a Windows-host Unreal session proves the hybrid topology, a host camera bridge into `8554/cam`, and a YOLO place-check on spawned weeds.

Official docs (2026-10-01): [Project AirSim](https://iamaisim.github.io/ProjectAirSim/), [PX4 SITL](https://iamaisim.github.io/ProjectAirSim/controllers/px4/px4_sitl.html), [PX4 + WSL 2](https://iamaisim.github.io/ProjectAirSim/controllers/px4/px4_sitl_wsl2.html), [supported PX4](https://iamaisim.github.io/ProjectAirSim/controllers/px4/px4.html).

This session did **not** launch Unreal. The inventory and topology lock are from this repo plus those pages.

## Inventory: what Gazebo actually is here

There is no ROS. There are no `.launch` files. SITL is Docker Compose on operator WSL.

| Piece | Path | Role |
|---|---|---|
| Default SIH | `compose.yaml`, `make sitl` | `px4io/px4-sitl:latest`, `PX4_SIM_MODEL=sihsim_quadx`, MediaMTX + ffmpeg file loop `rtsp://127.0.0.1:8554/cam` |
| Opt-in Gazebo | `compose.gazebo.yaml`, `make sitl-gz` | `px4io/px4-sitl-gazebo:latest`, `PX4_SIM_MODEL=gz_x500_lidar_down`, `HEADLESS=1`, `LIBGL_ALWAYS_SOFTWARE=1` |
| Model overlay | `sitl/gz/models/x500_lidar_down/` | Downward `gpu_lidar` (sensor +X down) + `mono_cam` **forward 15°** (`WEED_CAM_TILT_DEG=15`) |
| Camera ingest | `sitl/mediamtx-gazebo.yml` | GstCameraSystem UDP RTP `:5600` H264 PT 96 → MediaMTX `udp+rtp` + `rtpSDP` → **`8554/cam`** |
| GCS / YOLO | host `weed-spray` + vision | MAVSDK `udpin://0.0.0.0:14540`. YOLO pulls RTSP `8554/cam`. Dashboard plays HLS `:8888`. |
| Accurate GCS | `make backend-gz` | `WEED_HOVER_ALTITUDE_MODE=offboard_agl`, `WEED_LIDAR_EXPECTED=true` |
| CI / AWS | `docs/acceptance-aws.md` | SIH is the cheap path. Gazebo is ~25 GB RAM; do not leave it on a $10/mo host. |

Compose services only: SIH (`compose.yaml`) is PX4 + MediaMTX + **ffmpeg** (file loop). Gazebo (`compose.gazebo.yaml`) is **PX4 + MediaMTX only** — GstCamera RTP → MediaMTX; **no** ffmpeg / `smoke.mp4` on that profile. Backend, vision, and dashboard stay on the host. Hardware later: camera on the airframe to the **laptop**, commands over MAVLink only.

## Topology lock

**Preferred:** Project AirSim / Unreal on the **Windows host** (discrete GPU for cameras). **PX4 SITL in WSL2.** weed-spray / MAVSDK stay in WSL and talk MAVLink.

Documented AirSim WSL2 path:

1. Windows `ipconfig` → `vEthernet (WSL)` IPv4.
2. In WSL: `PX4_SIM_HOST_ADDR=<that IPv4>`.
3. Robot `px4-settings`: `use-tcp: true`, `tcp-port: 4560`, `local-host-ip` = that IPv4, `control-ip-address: "remote"`.
4. Windows firewall: TCP **4560** + UDP **14540**.
5. Scene `sitl_wsl2` / example `px4_quadrotor.py`.

**Out:** Unreal inside WSL2 (not in the support matrix). **Out for vision:** Project AirSim **Runtime** alone — GPS/IMU/baro only; **no cameras, LiDAR, or world meshes**.

GPU: Unreal needs a discrete GPU for the camera path. `-RenderOffScreen` is the headless render switch. `-nullrhi` disables rendering and is useless for YOLO.

## Camera path (host laptop, not flight controller)

Product constraint: the real camera is on the airframe and feeds the **host laptop**. The FC never sees video. Sim must match that split.

| Path | Lands in weed-spray? | Notes |
|---|---|---|
| Gazebo GstCamera → MediaMTX `8554/cam` | Yes today | One GCS URL. Keep this contract if AirSim is ever wired. |
| AirSim client `get_images` | Possible | RGB + segmentation + bbox annotations. Python on the host. Needs a **bridge** (JPEG/raw → ffmpeg → MediaMTX) so YOLO still pulls `8554/cam`. |
| PixelStreaming (WebRTC) | Operator view | H.264 for humans. Not the YOLO ingest. |
| PX4 camera plugin / FC video | No | Do not use. |

AirSim is **not** a MediaMTX drop-in. A later spike on the Windows GPU box should prove: Unreal RGB → host Python → `8554/cam` → existing YOLO reader, while MAVSDK still uses UDP **14540** only.

## PX4 version

| Stack | Version |
|---|---|
| weed-spray SIH / Gazebo images | `px4io/px4-sitl:latest` and `px4io/px4-sitl-gazebo:latest` (PX4 **main**) |
| Hardware first-flight | PX4 **v1.14+ / main** |
| Project AirSim supported SITL | **v1.12.3** ([px4.html](https://iamaisim.github.io/ProjectAirSim/controllers/px4/px4.html)); other versions “may work but are unsupported” |

Pinning sim to 1.12.3 would diverge from the Kakute and from our Docker images. Proving **our** PX4 (`px4_sitl none_*` from current source, or the existing `px4io` images) against AirSim’s TCP 4560 sim connector is a remaining operator-host experiment.

## Do not copy AirSim PX4 sample params

AirSim’s sample robot JSON sets `NAV_RCL_ACT: 0` and `NAV_DLL_ACT: 0` so SITL can fly without RC. This repo **does not write** `NAV_RCL_ACT` or `COM_RCL_EXCEPT` bit 2 (`bot_files/px4_offboard.md`, `GROK.md`). RC-in-hand on hardware; SITL arm-without-radio stays an operator/QGC problem.

## Weed assets and YOLO

AirSim can `spawn_object` plant meshes as **separate actors** (Foliage painter instances share one seg label — unusable for class GT). RGB + segmentation IDs + 2D/3D bbox annotations exist.

No backyard-trained YOLO place-check has been run on sim weeds. Domain gap (asset/lighting vs lawn clips in `weeds/inbox/`) is unmeasured. That check is the go/no-go for **replacing** Gazebo vision SITL.

## CI and licensing

- **CI:** Runtime (no Unreal) is the only plausible smoke: physics + MAVLink, no camera. Vision needs a packaged Unreal binary + GPU. Default `make check` stays FakeVehicle pytest. Do not add Unreal to GitHub Actions.
- **License:** Project AirSim is MIT. Unreal Engine and any marketplace plant packs have separate terms. Do not vendor UE or paid foliage into this repo.

## Setup friction vs `make sitl-gz`

| | `make sitl-gz` | Project AirSim (preferred topology) |
|---|---|---|
| Host | Operator WSL + Docker | Windows GPU + WSL2 PX4 + firewall |
| Camera into YOLO | RTP 5600 already in compose | New bridge; PixelStreaming is not RTSP |
| Lidar hover | Overlay + `backend-gz` ([#19](https://github.com/bi21an5a1b07-bot/weed-spray/issues/19) closed 2026-09-16) | Runtime has no lidar; Unreal lidar is a different sensor |
| RAM / AWS | Heavy; SIH is the UAT path | Heavier; not the $10/mo host |
| PX4 | Same `px4io` images as SIH | Docs pin v1.12.3 |

## Remaining on the Windows GPU host

- [ ] Run Unreal Project AirSim on Windows; PX4 in this WSL2; HEARTBEAT on 14540 from weed-spray.
- [ ] Bridge `get_images` RGB into MediaMTX `8554/cam` without sending video through PX4.
- [ ] Spawn separate plant actors; run backyard YOLO; record precision/recall vs Gazebo `mono_cam`.
- [ ] Prove current PX4 (not only v1.12.3) against TCP 4560.
- [ ] Keep `NAV_RCL_ACT` untouched.

Until those pass, AirSim is optional **offline synthetic-data** (RGB + seg IDs) at most.

## Recommendation

**Keep SIH** default and **Gazebo** as the accurate opt-in. AirSim **does not replace** `make sitl-gz` in this repo yet. Do not add `compose.airsim.yaml`. Do not start Unreal from this Makefile.
