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
        0: "%Y-%m-%d %H:%M:%S",
        1: "%H:%M:%S",
    }
    presets = {
        0: "%(name)s|%(levelname)-7s|%(asctime)s|%(message)s",
        1: "%(name)s|%(asctime)s|%(message)s",
        2: "%(asctime)s|%(message)s",
        3: "%(levelname)-8s %(asctime)s \t %(filename)s @function %(funcName)s line %(lineno)s - %(message)s",
        4: "%(levelname)-8s %(asctime)s (%(relativeCreated)d) \t %(pathname)s F%(funcName)s L%(lineno)s - %(message)s",
    }
    path = ""
    level = "debug"
    fmt = presets[0]
    datefmt = date_formats[0]
    to_file = None
    to_stdout = True
    path = Path.cwd()
    mode = "a"
    backup_count = 5

    def __init__(self, name, **kwargs):
        self.name = name
        for keyword in "path level fmt datefmt to_file to_stdout path mode backup_count".split():
            setattr(self, keyword, kwargs.get(keyword) or getattr(Log, keyword))
        self.mode = self.mode.lower()
        logger = logging.getLogger(name)
        level_int = getattr(logging, self.level.upper())
        logger.setLevel(level=level_int)
        if kwargs.get("path") and self.to_file is None:
            self.to_file = True
        if self.to_file:
            logFileFormatter = logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)
            self.path = Path(self.path)
            filepath = self.path / f"{name}.log"
            if self.mode == "w":
                fileHandler = logging.handlers.RotatingFileHandler(filepath, mode='w', backupCount=self.backup_count, delay=True)
                if filepath.is_file():
                    fileHandler.doRollover()
            else:
                fileHandler = logging.FileHandler(filename=filepath, mode=self.mode)
            fileHandler.setFormatter(logFileFormatter)
            fileHandler.setLevel(level=level_int)
            logger.addHandler(fileHandler)
        if self.to_stdout:
            logStreamFormatter = logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)
            consoleHandler = logging.StreamHandler(stream=sys.stdout)
            consoleHandler.setFormatter(logStreamFormatter)
            consoleHandler.setLevel(level=level_int)
            logger.addHandler(consoleHandler)
        setattr(Log, name, logger)
        self.logger = logger
        Log.index[name] = self


    def __call__(self, text):
        """
        Shortcut to log at effective logging level using easy syntax e.g.
        Log.mylogger("Some text")
        """
        level = logging.getLevelName(self.logger.getEffectiveLevel()).lower()
        getattr(self.logger, level)(text)

    @staticmethod
    def preview(fmt="", datefmt="", text=""):
        """Send a preview of the supplied format string to stdout"""
        logger = logging.getLogger("temp_preview")
        logger.setLevel(level=10)
        datefmt = datefmt or Log.date_formats[0]
        fmt = fmt or Log.presets[0]
        fmt = fmt.replace("{TITLE}", "PREVIEW")
        logStreamFormatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        consoleHandler = logging.StreamHandler(stream=sys.stdout)
        consoleHandler.setFormatter(logStreamFormatter)
        consoleHandler.setLevel(level=30)
        logger.addHandler(consoleHandler)
        logger.warning(text or "This is a preview log entry.")
        logger.removeHandler(consoleHandler)

    @staticmethod
    def preview_presets():
        for key1,fmt in Log.presets.items():
            for key2,datefmt in Log.date_formats.items():
                text = f"This is a preview using  and "
                print(f"\nPreset {key1} / Date Format {key2}:")
                Log.preview(fmt, datefmt)
