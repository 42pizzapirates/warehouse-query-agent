import sys
from pathlib import Path

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import request_id_ctx_var

log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def inject_request_id(record):
    record["extra"]["request_id"] = request_id_ctx_var.get()


logger.remove()

logger = logger.patch(inject_request_id)

if app_config.logging.console.enable:
    logger.add(sink=sys.stdout, level=app_config.logging.console.level, format=log_format)

if app_config.logging.file.enable:
    PROJECT_ROOT = Path(__file__).parents[2]
    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_FILE = LOG_DIR / "app.log"

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.add(
        sink=LOG_FILE,
        level=app_config.logging.file.level,
        format=log_format,
        rotation=app_config.logging.file.rotation,
        retention=app_config.logging.file.retention,
        encoding="utf-8"
    )
