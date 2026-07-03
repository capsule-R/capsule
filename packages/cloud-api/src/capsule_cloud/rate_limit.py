"""Shared rate limiter.

A single module-level Limiter instance so both main.py (which registers it
on the app and wires the 429 handler) and individual routers (which apply
per-endpoint @limiter.limit(...) decorators) share the same counters.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
