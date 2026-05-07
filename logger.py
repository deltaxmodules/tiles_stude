import structlog
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(
        file=open("logs/cognitive.jsonl", "a")
    ),
)

log = structlog.get_logger()
