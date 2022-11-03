import logging
import logging.handlers
import sys
from pathlib import Path


class Log():
    """
    Convenience class for creating and using logging objects e.g.
    Log.progress.warning("Danger, Will Robinson!")
    """
    index = {}
    date_formats = {
        "date_and_time": "%Y-%m-%d %H:%M:%S",
        "time": "%H:%M:%S",
        "iso8601": "%Y-%m-%dT%H:%M:%S%z",
        "am_pm": "%d/%m/%Y %I:%M:%S %p",
    }
    presets = {
        "name_level_time": "%(name)s|%(levelname)-8s|%(asctime)s|%(message)s",
        "name_and_time": "%(name)s|%(asctime)s|%(message)s",
        "timestamp_only": "%(asctime)s|%(message)s",
        "file_func_name": "%(levelname)-8s|%(asctime)s|line %(lineno)s of function: %(funcName)s in %(filename)s|%(message)s",
        "relative_time": "%(levelname)-8s|%(relativeCreated)d|%(pathname)s|%(funcName)s|%(lineno)s|%(message)s",
    }
    path = ""
    level = "debug"
    fmt = presets["name_level_time"]
    datefmt = date_formats['iso8601']
    to_file = False
    to_stdout = True
    path = Path.cwd()
    mode = "a"
    backup_count = 0

    def __init__(self, name, **kwargs):
        self.name = name
        self.logger = logging.getLogger(self.name)
        for key in "path level fmt datefmt to_file to_stdout mode backup_count".split():
            value = kwargs.get(key) if key in kwargs else getattr(Log, key)
            setattr(self, key, value)
        self.path = Path(self.path)
        self.mode = self.mode.lower()
        self.level_int = getattr(logging, self.level.upper())
        self.logger.setLevel(level=self.level_int)
        if "path" in kwargs and "to_file" not in kwargs:
            self.to_file = True
        if kwargs.get("to_file") and "to_stdout" not in kwargs:
            self.to_stdout = False
        for handler in self.get_handlers():
            self.logger.addHandler(handler)
        setattr(Log, self.name, self.logger)
        Log.index[self.name] = self

    def get_handlers(self):
        handlers = []
        if self.to_file:
            filepath = self.path / f"{self.name}.log"
            if self.mode == "w":
                handler = logging.handlers.RotatingFileHandler(filepath, mode='w', backupCount=self.backup_count, delay=True)
                if filepath.is_file():
                    handler.doRollover()
            else:
                handler = logging.FileHandler(filename=filepath, mode=self.mode)
            logFileFormatter = logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)
            handler.setFormatter(logFileFormatter)
            handler.setLevel(level=self.level_int)
            handlers += [handler]
        if self.to_stdout:
            logStreamFormatter = logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)
            handler = logging.StreamHandler(stream=sys.stdout)
            handler.setFormatter(logStreamFormatter)
            handler.setLevel(level=self.level_int)
            handlers += [handler]
        return handlers

    def __call__(self, *args, **kwargs):
        """
        Shortcut to log at effective logging level using easy syntax e.g.

        mylog = Log("mylog")
        mylog("This text gets added to the logger output - no fuss!")
        """
        level = logging.getLevelName(self.logger.getEffectiveLevel()).lower()
        getattr(self.logger, level)(*args, **kwargs)

    @staticmethod
    def preview(fmt="", datefmt="", text=""):
        """Send a preview of the supplied format string to stdout"""
        logger = logging.getLogger("temp_preview")
        logger.setLevel(level=10)
        datefmt = datefmt or Log.datefmt
        fmt = fmt or Log.fmt
        fmt = fmt.replace("{TITLE}", "PREVIEW")
        logStreamFormatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logStreamFormatter)
        handler.setLevel(level=30)
        logger.addHandler(handler)
        logger.warning(text or "This is a preview log entry.")
        logger.removeHandler(handler)

    @staticmethod
    def preview_all():
        for key1, fmt in Log.presets.items():
            for key2, datefmt in Log.date_formats.items():
                text = f"This is a preview using  and "
                print(f'\nfmt="{key1}", datefmt="{key2}"')
                Log.preview(fmt, datefmt)

    @staticmethod
    def disable_rootlogger():
        root = logging.Logger.root
        for handler in root.handlers:
            root.removeHandler(handler)
