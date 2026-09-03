"""Fetch CC0/CC-BY iNaturalist research-grade photos into weeds/inbox/.

Operator-approved ingest. Skips CC-BY-NC and ShareAlike. Not a full archive dump.
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "weeds" / "inbox"
UA = "weed-spray/0.1 (hobby GCS; iNaturalist API; no commercial redistribution)"
API = "https://api.inaturalist.org/v1/observations"
PER_CLASS = 25

# bot_files/weeds_sources.md taxon ids
TAXA: dict[str, list[int]] = {
    "dandelion": [47602],  # Taraxacum
    "clover": [55745, 51875],  # T. repens, T. pratense
    "thistle": [60132, 52989, 76007],  # C. arvense, C. vulgare, C. nutans
}

# Prefer US, then anywhere. Prefer CC0, then CC-BY (not NC, not SA).
QUERIES = [
    {"photo_license": "cc0", "place_id": "1"},
    {"photo_license": "cc0"},
    {"photo_license": "cc-by", "place_id": "1"},
    {"photo_license": "cc-by"},
]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_obs(taxon_id: int, extra: dict[str, str], page: int = 1) -> list[dict]:
    params = {
        "taxon_id": str(taxon_id),
        "quality_grade": "research",
        "photos": "true",
        "order_by": "votes",
        "per_page": "30",
        "page": str(page),
        **extra,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    data = json.loads(_get(url))
    return list(data.get("results") or [])


def photo_ok(photo: dict) -> str | None:
    lic = (photo.get("license_code") or "").lower().replace(" ", "")
    if lic in {"cc0", "cc-0"}:
        return "cc0"
    if lic in {"cc-by", "ccby", "cc-by-4.0", "cc-by-3.0", "cc-by-2.0"}:
        return "cc-by"
    return None


def download_one(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())


def collect_class(name: str, taxon_ids: list[int], n: int) -> list[dict]:
    seen: set[int] = set()
    rows: list[dict] = []
    for extra in QUERIES:
        if len(rows) >= n:
            break
        for taxon_id in taxon_ids:
            if len(rows) >= n:
                break
            try:
                results = fetch_obs(taxon_id, extra)
            except urllib.error.URLError as exc:
                print(f"warn {name} taxon={taxon_id} {extra}: {exc}", file=sys.stderr)
                time.sleep(1.0)
                continue
            time.sleep(1.0)
            for obs in results:
                if len(rows) >= n:
                    break
                for photo in obs.get("photos") or []:
                    pid = photo.get("id")
                    if pid in seen:
                        continue
                    lic = photo_ok(photo)
                    if lic is None:
                        continue
                    url = photo.get("url") or ""
                    # iNat thumb URLs use square; request medium
                    url = url.replace("/square.", "/medium.").replace("/square/", "/medium/")
                    if not url.startswith("http"):
                        continue
                    seen.add(int(pid))
                    rows.append(
                        {
                            "class": name,
                            "obs_id": obs.get("id"),
                            "photo_id": pid,
                            "license": lic,
                            "attribution": photo.get("attribution")
                            or obs.get("user", {}).get("login")
                            or "",
                            "taxon_id": taxon_id,
                            "place": extra.get("place_id") or "global",
                            "url": url,
                            "obs_url": f"https://www.inaturalist.org/observations/{obs.get('id')}",
                        }
                    )
                    if len(rows) >= n:
                        break
    return rows


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict] = []
    for name, taxa in TAXA.items():
        folder = INBOX / name
        folder.mkdir(parents=True, exist_ok=True)
        rows = collect_class(name, taxa, PER_CLASS)
        print(f"{name}: {len(rows)} photos queued")
        for row in rows:
            ext = ".jpg"
            dest = folder / f"{name}_{row['obs_id']}_{row['photo_id']}{ext}"
            try:
                download_one(row["url"], dest)
            except urllib.error.URLError as exc:
                print(f"skip {dest.name}: {exc}", file=sys.stderr)
                time.sleep(0.5)
                continue
            row["file"] = str(dest.relative_to(ROOT))
            manifest_rows.append(row)
            print(f"  {dest.name} {row['license']}")
            time.sleep(0.35)
    man = INBOX / "SOURCES.csv"
    if manifest_rows:
        with man.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(manifest_rows[0].keys()))
            w.writeheader()
            w.writerows(manifest_rows)
    readme = INBOX / "SOURCES.md"
    readme.write_text(
        "# Downloaded public photos (inbox)\n\n"
        "Source: iNaturalist API, research-grade, **CC0 or CC-BY only** "
        "(no CC-BY-NC, no ShareAlike). Unlabeled intake — box before train.\n\n"
        f"Count: {len(manifest_rows)} iNat files in `dandelion/` `clover/` `thistle/`. "
        "Manifest: `SOURCES.csv`.\n"
        "Operator backyard stills are **not** in this CSV; see `backyard_weeds/SOURCE.md`.\n"
        "CC-BY requires keeping the attribution column if you publish derivatives.\n"
        "Do not mix these into `dataset/` by cropping one photo into train and val.\n"
    )
    print(f"wrote {len(manifest_rows)} files + {man}")
    return 0 if manifest_rows else 2


if __name__ == "__main__":
    sys.exit(main())
