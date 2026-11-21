"""Truthful, lightweight progress feedback during blocking PDF conversion.

A Docling convert() call does not expose a stable per-page completion callback.
We therefore report elapsed time and a heartbeat, never invented percentages.
"""
from __future__ import annotations

import sys
import threading
import time
from contextlib import contextmanager


@contextmanager
def parsing_heartbeat(filename: str, *, stream=None, interval: float = 1.0):
    """Show a live spinner on terminals, periodic elapsed-time messages in logs."""
    stream = stream if stream is not None else sys.stderr
    stop = threading.Event()
    started = time.monotonic()
    interactive = bool(getattr(stream, "isatty", lambda: False)())

    def tick():
        frames = "|/-\\"
        index = 0
        while not stop.wait(interval):
            elapsed = int(time.monotonic() - started)
            if interactive:
                stream.write(
                    f"\r[PARSE] {frames[index % len(frames)]} {filename} "
                    f"| elapsed {elapsed}s | Docling working (page progress unavailable)   "
                )
                stream.flush()
            elif elapsed >= 15 and elapsed % 15 < interval:
                stream.write(f"[PARSE] Still processing {filename} | elapsed {elapsed}s\n")
                stream.flush()
            index += 1

    worker = threading.Thread(target=tick, name="course-parse-progress", daemon=True)
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=max(1, interval * 2))
        if interactive:
            stream.write("\r" + " " * 110 + "\r")
            stream.flush()
