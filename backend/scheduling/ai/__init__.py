"""
scheduling.ai — AI schedule generation package.

Public API (imported by scheduling.views):
    generate_schedule()        blocking wrapper, used by the Django test suite
    stream_generate_schedule() streaming generator, used by the SSE view path
"""

from ._generate import generate_schedule, stream_generate_schedule

__all__ = ["generate_schedule", "stream_generate_schedule"]
