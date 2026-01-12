from __future__ import annotations

import logging
from logging.handlers import SysLogHandler
from typing import Tuple

from pythonjsonlogger import jsonlogger

from config import settings


def _parse_destinations(raw: str) -> list[Tuple[str, int]]:
    out: list[Tuple[str, int]] = []
    for item in (raw or "").split(","):
        item = item.strip()
        if not item or ":" not in item:
            continue
        host, port_s = item.rsplit(":", 1)
        host = host.strip()
        try:
            port = int(port_s.strip())
        except ValueError:
            continue
        out.append((host, port))

    # dedupe
    seen = set()
    deduped: list[Tuple[str, int]] = []
    for hp in out:
        if hp in seen:
            continue
        seen.add(hp)
        deduped.append(hp)
    return deduped


def setup_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_configured", False):
        return

    root.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    stream_handler.setFormatter(stream_formatter)
    root.addHandler(stream_handler)

    for host, port in _parse_destinations(settings.rsyslog_destinations):
        try:
            h = SysLogHandler(address=(host, port))
            h.setLevel(logging.INFO)
            h.setFormatter(stream_formatter)
            root.addHandler(h)
        except Exception:
            root.warning("Failed to attach syslog handler", extra={"syslog_host": host, "syslog_port": port})

    root._configured = True  # type: ignore[attr-defined]


logger = logging.getLogger("s3-service")
