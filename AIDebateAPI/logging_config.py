import logging

# Define ANSI color codes
class LogColors:
    DEBUG = "\033[94m"  # Blue
    INFO = "\033[92m"   # Green
    WARNING = "\033[93m"  # Yellow
    ERROR = "\033[91m"   # Red
    CRITICAL = "\033[95m"  # Magenta
    RESET = "\033[0m"    # Reset to default

# Custom logging formatter with color
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = LogColors.RESET
        if record.levelno == logging.DEBUG:
            color = LogColors.DEBUG
        elif record.levelno == logging.INFO:
            color = LogColors.INFO
        elif record.levelno == logging.WARNING:
            color = LogColors.WARNING
        elif record.levelno == logging.ERROR:
            color = LogColors.ERROR
        elif record.levelno == logging.CRITICAL:
            color = LogColors.CRITICAL
        
        record.msg = f"{color}{record.msg}{LogColors.RESET}"  # Wrap message in color
        return super().format(record)

# Configure logging with the custom formatter
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

for handler in logging.root.handlers:
    handler.setFormatter(ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s"))