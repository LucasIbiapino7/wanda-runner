import structlog
import logging
from fastapi import FastAPI
from wanda_runner.controllers.run_tests_controller import router
from wanda_runner.settings import settings

# LOGS 
logging.basicConfig(level=settings.log_level)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.log_level == "DEBUG" else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level)),
    logger_factory=structlog.PrintLoggerFactory(),
)

# APP 
app = FastAPI(title="wanda-runner", version="0.1.0")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}