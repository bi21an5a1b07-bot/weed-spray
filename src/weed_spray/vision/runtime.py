"""Whether the vision worker may leave injector mode. Does not load a model.

``WEED_YOLO_WEIGHTS`` empty or missing keeps the injector. A present file is
still not started here; the RTSP reader is a later story.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger("weed_spray.vision")

_logged_missing = False
_runner_started = False


def configure_logging() -> None:
    """Show vision INFO on stderr. Uvicorn does not attach a handler for this logger.

    Idempotent: a second call does not add another stream handler.
    """
    log.setLevel(logging.INFO)
    if any(isinstance(handler, logging.StreamHandler) for handler in log.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    log.addHandler(handler)


def runner_started() -> bool:
    """True only after a YOLO reader has been started. This story never does."""
    return _runner_started


def reset_for_tests() -> None:
    """Clear the one-shot missing-weights log and the runner flag."""
    global _logged_missing, _runner_started
    _logged_missing = False
    _runner_started = False


def note_configured_weights() -> None:
    """Log once if ``WEED_YOLO_WEIGHTS`` is set but the file is not there.

    Unset or empty is the normal injector and logs nothing. A path that is a
    real file is ignored here so this process does not start a detector.
    """
    global _logged_missing
    raw = os.environ.get("WEED_YOLO_WEIGHTS", "").strip()
    if not raw or Path(raw).is_file():
        return
    if _logged_missing:
        return
    log.info("WEED_YOLO_WEIGHTS %s is missing; staying injector", raw)
    _logged_missing = True
