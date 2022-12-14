import logging
import logging.handlers
import sys
import os
from re import compile as reCompile
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import parser

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

    def find(self, text: str="", path=None, date=None, deltadays: int=-7,
             level: str='NOTSET', separator: str="|",
             ignorecase: bool=True, autoparse: bool=False):
        """
        Search log for:

        text:        text to seach for. Default '' means return everything
        path:     path/to/another/log.log to search. Default=None, search this log
        date:        Date(time) object/str anchor for search. Default None = NOW
        deltadays:   number of days prior to (-ve) or after date. Default 1 week prior
        level:       log level below which results are ignored. Default NOTSET
        separator:   field separator character in log record. Default |
        ignorecase:  set case insensitivity. Default True
        autoparse:   if True, parses the log to find separator, time and level.
                     if False (default), looks at log2d fmt string.

        Return:

        List of search results, or None
        """
        def _auto_parse(path):
            """Attempts to automatically parse log file to return [separator, date, level] fields"""
            query_str ='r"|CRITICAL\s*|INFO\s*|DEBUG\s*|WARNING\s*|NOTSET\s*|ERROR\s*|"'
            separator = group = split_line = ''
            level = timestamp = -1
            # Find the LEVEL which then gives surrounding separator
            query = reCompile(query_str)
            try:
                with open(path, mode='r') as log_file:
                    for line in log_file:
                        try:
                            match = query.search(line)
                            start, end = match.span() if match else (0, 0)
                            if start - end == 0:
                            # start & end are the same so not found
                                continue
                            if start == 0:
                                if end > len(line) - 2:
                                    continue
                                separator = line[end]
                            else:
                                separator = line[start-1]
                            split_line = line.split(separator)
                            group = match.group().strip(separator)
                            # LEVEL found
                            break
                        except:
                            continue
            except Exception as end:
                return ['', -1, -1]
            if separator != '':
                try:
                    level = split_line.index(group)  # Level field index
                    for index, field in enumerate(split_line):
                        try:
                            _ = parser.parse(field, ignoretz=True)
                            timestamp = index
                            break
                        except:
                            continue
                except:
                    pass
            # TODO: Further check result?
            return [separator, level, timestamp]

        def _get_format_fields():
            """
            Check the fmt string to find level and time fields.
            Return: (separator, level, asctime)
            """
            _fmt = self.fmt.split(separator)
            level = asctime = -1
            for index, field in enumerate(_fmt):
                if "levelname" in field:
                    level = index
                if "asctime" in field:
                    asctime = index
            return (separator, level, asctime)

        def _query_level(level_str: str) -> bool:
            """Is record above required level? Return True/False """
            level_not_found = 50  # i.e. CRITICAL
            return log_levels.get("level_str", level_not_found) >= search_level

        def _query_text(record_str: str) -> bool:
            """Does record contain text?"""
            try:
                return (new_text in record_str.casefold()) if ignorecase else (new_text in record_str)
            except:
                return False

        def _check_path(path):
            if path is None:
                path = Path(self.path) / f"{self.name}.log"
            else:
                path = Path(path)
                autoparse = True  # Always autoparse external files
            if not path.is_file():
                raise Exception(f'No log file at {path}')
            return path

        def _initial_arguments():
            separator, level, timestamp = _auto_parse(path) if autoparse else _get_format_fields()
            if separator == '' or timestamp == -1 or level == -1:
                raise Exception(f"Error parsing log format: Found '{separator}', {timestamp}, {level}")
            return separator, level, timestamp

        def _get_times():
            try:
                if not date:
                    start_time = datetime.now()
                elif isinstance(date, str):
                    start_time = parser.parse(date)
                else:
                    start_time = date
                end_time = start_time + timedelta(days=deltadays)
                if start_time > end_time:
                    start_time, end_time = end_time, start_time
            except:
                raise Exception(f"Find start/End time error: {date}|{deltadays}")
            # TODO: Better way to get this (private) internal variable?
            return start_time, end_time

        def _find_results():
            with open(path, mode='r') as log_file:
                for line in log_file:
                    split_line = line.split(separator)
                    try:
                        _level = split_line[level].strip()
                        _timestamp = parser.parse(split_line[timestamp], ignoretz=True)
                    except:  # Timestamp/level not found
                        _timestamp = _last_timestamp
                        _level = _last_level
                    _last_timestamp = _timestamp
                    _last_level = _level
                    if start_time <= _timestamp:
                        if _timestamp > end_time:
                            break
                        if new_text:
                            line = line if (_query_text(line) and _query_level(_level)) else ''
                        else:
                            line = line if _query_level(_level) else ''
                        if line:
                            results.append(line.strip())
            return results

        path = _check_path(path)
        separator, level, timestamp = _initial_arguments()
        start_time, end_time = _get_times()
        log_levels = logging._nameToLevel
        try:
            search_level = log_levels[level.upper()]  # log level to search for
        except Exception:
            search_level = 0
        new_text = text.casefold() if ignorecase else text
        results = []
        _last_timestamp = start_time - timedelta(days=1)
        _last_level = "INFO"
        return _find_results()

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
