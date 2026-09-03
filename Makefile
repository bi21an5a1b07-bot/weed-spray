# Host-side shortcuts. `make sitl` starts Docker only (PX4 SIH + RTSP).
# Backend / vision / dashboard stay on the host. See docs/cli.md.
# Python gate: `make check` (ruff + pytest). See docs/testing.md.
.PHONY: sitl sitl-down smoke-video inbox-frames promote-inbox app vision backend dashboard accept down test lint fmt check

smoke-video: media/smoke.mp4

media/smoke.mp4:
	mkdir -p media
	ffmpeg -y -f lavfi -i testsrc=duration=8:size=1280x720:rate=15 -pix_fmt yuv420p -an $@

sitl: smoke-video
	docker compose up -d

sitl-down:
	docker compose down

backend:
	uv run weed-spray

vision:
	uv run weed-spray-vision

dashboard:
	cd dashboard && npm install && npm run dev

accept:
	uv run weed-spray-accept --out var/last-run.md

down: sitl-down

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
