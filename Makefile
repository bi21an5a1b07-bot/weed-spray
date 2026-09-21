# Host-side shortcuts. `make sitl` starts Docker only (PX4 SIH + RTSP).
# Backend / vision / dashboard stay on the host. See docs/cli.md.
# Python gate: `make check` (ruff + pytest). See docs/testing.md.
# SIH and Gazebo both use host networking — start targets tear the other down first.
.PHONY: sitl sitl-down sitl-gz sitl-gz-down smoke-video inbox-frames promote-inbox app vision backend backend-gz dashboard accept down test lint fmt check

smoke-video: media/smoke.mp4

media/smoke.mp4:
	mkdir -p media
	ffmpeg -y -f lavfi -i testsrc=duration=8:size=1280x720:rate=15 -pix_fmt yuv420p -an $@

sitl: smoke-video
	$(MAKE) sitl-gz-down
	docker compose -p weed-spray-sih -f compose.yaml up -d

sitl-down:
	docker compose -p weed-spray-sih -f compose.yaml down

# Opt-in Gazebo accurate profile (issue #19). Does not replace make sitl.
sitl-gz:
	$(MAKE) sitl-down
	docker compose -p weed-spray-gz -f compose.gazebo.yaml up -d

sitl-gz-down:
	docker compose -p weed-spray-gz -f compose.gazebo.yaml down

backend:
	uv run weed-spray

# Gazebo accurate profile (issue #19 / #27). Do not use on SIH.
backend-gz:
	WEED_HOVER_ALTITUDE_MODE=offboard_agl WEED_LIDAR_EXPECTED=true \
		WEED_LIDAR_MOUNT_DOWN_M=0.28 WEED_TAKEOFF_TIMEOUT_S=90 \
		uv run weed-spray

vision:
	uv run weed-spray-vision

dashboard:
	cd dashboard && npm install && npm run dev

accept:
	uv run weed-spray-accept --out var/last-run.md

down: sitl-down sitl-gz-down

inbox-frames:
	uv run python scripts/extract_clip_inbox.py

promote-inbox:
	uv run python scripts/promote_inbox.py

lint:
	uv run ruff check src tests scripts

fmt:
	uv run ruff format src tests scripts

test:
	uv run pytest -q

check: lint
	uv run ruff format --check src tests scripts
	uv run pytest -q
