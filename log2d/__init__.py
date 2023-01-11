import logging
import logging.handlers
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import parser
from functools import wraps


class ClassOrMethod(object):
    """Make method work as class or instance"""
    def __init__(self, func):
        self.func = func
    def __get__(self, obj, cls):
        context = obj if obj is not None else cls
        @wraps(self.func)
        def hybrid(*args, **kw):
            return self.func(context, *args, **kw)
        return hybrid

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

        while len(self.logger.handlers) > 0:
            self.logger.removeHandler(self.logger.handlers[0])

        for handler in self.get_handlers():
            self.logger.addHandler(handler)
        setattr(Log, self.name, self.logger)
        Log.index[self.name] = self

    def get_handlers(self):
        """Get all handlers for log"""
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

    def add_level(self, level_name, level_value=20, below="", above=""):
        """
        Add a custom log level at a specific numeric value or below/above
        an existing log level
        """
        if below:
            level_value = getattr(logging, below.upper()) - 1
        if above:
            level_value = getattr(logging, above.upper()) + 1
        upper_name = level_name.upper()
        lower_name = level_name.lower()
        names = [upper_name, lower_name, level_name]
        if any(hasattr(logging, x) for x in names):
            raise AttributeError(f'{upper_name} level already defined')
        setattr(logging, upper_name, level_value)
        logging.addLevelName(level_value, upper_name)
        def log_message(message, *args):
            if self.logger.isEnabledFor(level_value):
                return self.logger._log(level_value, message, args)
        setattr(self.logger, lower_name, log_message)
        return f"New log level '{lower_name}' added with value: {level_value}"

    @ClassOrMethod
    def find(self, text: str="", path=None, date=None, deltadays: int=-7,
             level: str='NOTSET', ignorecase: bool=True):
        """ Search log for:
               text:        text to seach for. Default '' means return everything
               path:        FULL 'path/to/another/log.log' to search. Default=None, search this log
               date:        Date(time) object/str anchor for search. Default None = NOW
               deltadays:   number of days prior to (-ve) or after date. Default 1 week prior
               level:       log level below which results are ignored. Default 'NOTSET'
               ignorecase:  set case insensitivity. Default True
            Returns [MSG[, ...]], [error message] or []
        """

        def _check_path(path: str) -> tuple:
            """ Get the logs path name and check the log exists"""
            if path is None:
                full_path = Path((self.path), f"{self.name}.log")
            else:
                full_path = Path(path)
            if not full_path.is_file():
                raise Exception(f'No log file at {full_path}')
            return full_path

        def _get_dates(date, deltadays) -> tuple:
            """Get the start and end dates/times for the search period"""
            try:
                if not date:
                    start_date = datetime.now()
                elif isinstance(date, str):
                    start_date = parser.parse(date)
                else:
                    start_date = date
                end_date = start_date + timedelta(days=deltadays)
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
            except:
                raise Exception(f"Find start/End date error: {date}|{deltadays}")
            return (start_date, end_date)

        def _get_difficult_date(record_str) -> datetime:
            """Find first date in difficult lines with multiple numbers"""
            date_pattern = "(\d{2}(:\d{2}){0,2}[ T])?\d{1,4}[./-]\d{1,2}[./-]\d{1,4}([ T]\d{2}(:\d{2}){0,2})?"
            try:
                _re_date = re.search(date_pattern, record_str)
                return parser.parse(_re_date.group(0), fuzzy=True, ignoretz=True)
            except:
                return None

        def _get_search_level(level):
            """Get the minimum search level as an int"""
            try:
                return _log_levels[level.upper()]  # log level to search for
            except:
                return 0

        def _get_line_level(record_str: str) -> bool:
            """Returns level found on this line or '' """
            for level in _log_levels:
                if level in record_str:
                    return level
            return ""

        def _query_level(level_str: str) -> bool:
            """Is record above required level? Return True/False """
            if level_str:
                level_not_found = 50  # i.e. CRITICAL
                return _log_levels.get(level_str, level_not_found) >= _search_level
            return True   #  Level was ""

        def _query_text(record_str: str) -> bool:
            """Does record contain text? Return True/False"""
            if _search_text:
                try:
                    return (_search_text in record_str.casefold()) if _ignorecase else (_search_text in record_str)
                except:
                    return False  # TODO: should we receive an exception?
            return True   # search text was ""

        # Get the arguments
        _ignorecase = ignorecase
        _search_text = text.casefold() if _ignorecase else text
        _log_path = _check_path(path)
        _start_date, _end_date = _get_dates(date, deltadays)
        _log_levels = logging._nameToLevel
        _search_level = _get_search_level(level)  # 0 if no level specified

        result = []
        _last_found_values = _start_date - timedelta(days=1), ""  # Initialise to 1 day before start and Null level
        # ...and search the file
        with open(_log_path, mode='r') as _log_file:
            for new_line in _log_file:
                if new_line == "\n":  # we don't need completely blank lines
                    continue
                try:  # Get timestamp and level
                    _level = _get_line_level(new_line)
                    _timestamp = parser.parse(new_line, fuzzy=True, ignoretz=True)
                except Exception as excpt:  # Timestamp/level not found
                    if "Unknown string" in excpt.args[0]:
                        _timestamp = _get_difficult_date(new_line)
                        if not _timestamp:
                            _timestamp, _level = _last_found_values
                    else:
                        _timestamp, _level = _last_found_values  # Recover last good timestamp/level

                _last_found_values = _timestamp, _level   # save timestamp and level for next line
                #  within time period?
                if _start_date <= _timestamp:
                    if _timestamp > _end_date:
                        break   # No need to read any more, past end time
                    new_line = new_line if (_query_text(new_line) and _query_level(_level)) else ''
                    if new_line:
                        result.append(new_line)
        return result

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
