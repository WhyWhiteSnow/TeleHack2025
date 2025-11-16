from loguru import logger

logger.add(
    "logs/logfile.{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level:<8} | {message}",
    rotation="1 week",
    encoding="utf-8",
)
