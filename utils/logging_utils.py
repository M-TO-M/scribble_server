import os
import sys
import logging
import logging.handlers
import logging.config
import coloredlogs
from datetime import datetime
from typing import Any, Mapping, MutableMapping

from pythonjsonlogger.jsonlogger import JsonFormatter

from django.utils.log import AdminEmailHandler


class BraceMessage:
    __slots__ = ("fmt", "args")

    def __init__(self, fmt, args):
        self.fmt = fmt
        self.args = args

    def __str__(self):
        return self.fmt.format(*self.args)


class BraceStyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger._log(level, BraceMessage(msg, args), (), **kwargs)


class CustomJsonFormatter(JsonFormatter):
    def add_fields(
            self,
            log_record: dict[str, Any],
            record: logging.LogRecord,
            message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if loglevel := log_record.get("level"):
            log_record["level"] = loglevel.upper()
        else:
            log_record["level"] = record.levelname.upper()


def setup_console_log_handler(config: Mapping[str, Any]) -> logging.Handler:
    log_formats = {
        "simple": "%(levelname)s %(message)s",
        "verbose": "%(asctime)s %(levelname)s %(name)s [%(lineno)s] %(message)s",
    }
    drv_config = config["console"]
    formatter = coloredlogs.ColoredFormatter(
        log_formats[drv_config["format"]],
        datefmt="%Y-%m-%d %H:%M:%S.%f",
        field_styles={
            "levelname": {"color": 248, "bold": True},
            "name": {"color": 246, "bold": False},
            "lineno": {"color": 246, "bold": False},
            "process": {"color": "cyan"},
            "asctime": {"color": 240},
        },
        level_styles={
            "debug": {"color": "green"},
            "verbose": {"color": "green", "bright": True},
            "info": {"color": "cyan", "bright": True},
            "notice": {"color": "cyan", "bold": True},
            "warning": {"color": "yellow"},
            "error": {"color": "red", "bright": True},
            "success": {"color": 77},
            "critical": {"background": "red", "color": 255, "bold": True},
        },
    )
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setLevel(drv_config["level"])
    console_handler.setFormatter(formatter)
    return console_handler


def setup_file_log_handler(config: Mapping[str, Any]) -> logging.Handler:
    drv_config = config["file"]
    log_format = "%(timestamp) %(level) %(name) %(message)"

    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(drv_config["path"], drv_config["filename"]),
        backupCount=drv_config["backup-count"],
        maxBytes=drv_config["rotation-size"],
        encoding="utf-8",
    )
    file_handler.setLevel(drv_config["level"])
    file_handler.setFormatter(CustomJsonFormatter(log_format))
    return file_handler


def setup_mail_log_handelr(config: Mapping[str, Any]) -> logging.Handler:
    drv_config = config["mail_admin"]
    log_format = "%(timestamp) %(level) %(name) %(processName) %(message)"
    mail_handler = AdminEmailHandler(
        include_html=None,
        email_backend=None,
        reporter_class=None
    )
    return mail_handler


def check_logging_config_driver_exists(config, driver):
    if driver in config and config["handlers"][driver] is None:
        raise Exception(f"{driver} driver is activated but no config given.")


class Logger:
    def __init__(
        self,
        logging_config: MutableMapping[str, Any]
    ) -> None:
        check_logging_config_driver_exists(logging_config, "console")
        check_logging_config_driver_exists(logging_config, "file")
        check_logging_config_driver_exists(logging_config, "mail_admin")

        log_handlers = []
        self.logging_config = logging_config
        if "console" in self.logging_config["drivers"]:
            console_handler = setup_console_log_handler(self.logging_config["handlers"])
            log_handlers.append(console_handler)
        if "file" in self.logging_config["drivers"]:
            file_handler = setup_file_log_handler(self.logging_config["handlers"])
            log_handlers.append(file_handler)
        if "mail_admin" in self.logging_config["drivers"]:
            mail_log_handler = setup_mail_log_handelr(self.logging_config["handlers"])
            log_handlers.append(mail_log_handler)

        self.server_logging_cfg = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "null": {"class": "logging.NullHandler"},
            },
            "loggers": {
                "": {"handlers": [], "level": self.logging_config["level"]},
                **{
                    k: {"handlers": [], "level": v, "propagate": False}
                    for k, v in self.logging_config["packages"].items()
                }
            }
        }
        logging.config.dictConfig(self.server_logging_cfg)

        logger = logging.getLogger()
        for h in log_handlers:
            logger.addHandler(h)
        for pkg in self.logging_config["packages"].keys():
            pkg_logger = logging.getLogger(pkg)
            for h in log_handlers:
                pkg_logger.addHandler(h)

    def __enter__(self):
        pass

    def __exit__(self, *exc_info_args):
        pass
