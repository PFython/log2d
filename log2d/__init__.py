import logging
import logging.handlers
import sys
from re import compile as reCompile
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import parser
from functools import wraps


class class_or_method(object):
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

    @class_or_method
    def find(self, text: str="", path=None, date=None, deltadays: int=-7,
             level: str='NOTSET', ignorecase: bool=True, autoparse: bool=False):
        """ Search log for:
               text:        text to seach for. Default '' means return everything
               path:        FULL 'path/to/another/log.log' to search. Default=None, search this log
               date:        Date(time) object/str anchor for search. Default None = NOW
               deltadays:   number of days prior to (-ve) or after date. Default 1 week prior
               level:       log level below which results are ignored. Default NOTSET
               ignorecase:  set case insensitivity. Default True
               autoparse:   if True, parses the log to find separator, time and level fields. 
                            If False, looks at log2d fmt string.  Default False
            Returns [MSG[, ...]], [error message] or []
        """
        def _check_path(autoparse, path: str) -> Path:
            """ Get the path name and check the log exists"""
            if path is None:
                full_path = Path((self.path), f"{self.name}.log")
            else:
                full_path = Path(path)
                autoparse = True  # Always autoparse external files
            if not full_path.is_file():
                raise Exception(f'No log file at {full_path}')
            return full_path, autoparse

        def _initial_arguments():
            #global autoparse
            _separator, _level, _timestamp = _auto_parse(log_path) if autoparse else _get_format_fields()
            if _separator == '' or _timestamp == -1:  # or _level == -1:
                raise Exception(f"Initial argument error: Found '{_separator}', {_timestamp}, {_level}")
            return _separator, _level, _timestamp

        def _get_format_fields():
            """
            Check the fmt string to find level and time fields.
            Return: (separator, level, asctime)
            """
            fquery = reCompile("s.%\(")  # find all separator 'blocks'
            separator_list = fquery.findall(self.fmt)
            separator_set = set(separator_list)
            if len(separator_set) != 1:  # Not just 1 separator
                return ("", -1, -1)
            separator = separator_set.pop()[1]
            _fmt = self.fmt.split(separator)
            level = asctime = -1
            for index, field in enumerate(_fmt):
                if "levelname" in field:
                    level = index
                if "asctime" in field:
                    asctime = index
            return (separator, level, asctime)

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
                            if start - end == 0: # start & end are the same so not found
                                continue
                            if start == 0:
                                if end > len(line) - 2:
                                    continue
                                separator = line[end]
                            else:
                                separator = line[start-1]
                            split_line = line.split(separator)
                            group = match.group().strip(separator) # LEVEL found
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

        def _query_level(level_str: str) -> bool:
            """Is record above required level? Return True/False """
            level_not_found = 50  # i.e. CRITICAL
            return log_levels.get(level_str, level_not_found) >= search_level

        def _query_text(record_str: str) -> bool:
            """Does record contain text? Return True/False"""
            try:
                return (search_text in record_str.casefold()) if ignorecase else (search_text in record_str)
            except:
                return False  # TODO: should we eceive an exception?

        def _find_results() -> list:
            with open(path, mode='r') as log_file:
                results = []
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
                            results.append(line)
            return results

        # ############ MAIN for find ##############
        # Get the log filepath and check it exists
        log_path, autoparse = _check_path(autoparse, path)
        # Prepare args
        separator, level_field, timestamp = _initial_arguments()

        try:
            if not date:
                start_search = datetime.now()
            elif isinstance(date, str):
                start_search = parser.parse(date)
            else:
                start_search = date
            end_search = start_search + timedelta(days=deltadays)
            if start_search > end_search:
                start_search, end_search = end_search, start_search
        except:
            raise Exception(f"Find start/end time error: {date}|{deltadays}")
            #return [f"Find start/End time error: {date}|{deltadays}"]
        # TODO: Better way to get this (private) internal variable?

        log_levels = logging._nameToLevel
        try:
            search_level = log_levels[level.upper()]  # log level to search for
        except Exception as excep:
            search_level = 0

        search_text = text.casefold() if ignorecase else text  # text to search for
        find_result = []   # Set initial result state
        _last_timestamp = start_search - timedelta(days=1)  # Initialise to 1 day before start
        _last_level = "INFO"
        # ...and search the file
        with open(log_path, mode='r') as _log_file:
            for new_line in _log_file:
                splitln = new_line.split(separator)
                try:  # Get timestamp and level
                    _level = splitln[level_field].strip()
                    _timestamp = parser.parse(splitln[timestamp], ignoretz=True)
                except:  # Timestamp/level not found
                    _timestamp = _last_timestamp  # Recover last good timestamp and level
                    _level = _last_level
                _last_timestamp = _timestamp   # save timestamp and level for next line
                _last_level = _level
                #  within time period?
                if start_search <= _timestamp:
                    if _timestamp > end_search:
                        break   # No need to read any more, past end time
                    if search_text:
                        new_line = new_line if (_query_text(new_line) and _query_level(_level)) else ''
                    else:
                        new_line = new_line if _query_level(_level) else ''
                    if new_line:
                        find_result.append(new_line)
        # Finally, return anything found
        return find_result
    '''    
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
        """        def _initial_arguments():
            separator, level, timestamp = _auto_parse(path) if autoparse else _get_format_fields()
            if separator == '' or timestamp == -1 or level == -1:
                raise Exception(f"Error parsing log format: Found '{separator}', {timestamp}, {level}")
            return separator, level, timestamp
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
                            if start - end == 0: # start & end are the same so not found
                                continue
                            if start == 0:
                                if end > len(line) - 2:
                                    continue
                                separator = line[end]
                            else:
                                separator = line[start-1]
                            split_line = line.split(separator)
                            group = match.group().strip(separator) # LEVEL found
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

        def _check_path(path, autoparse):
            if path is None:
                path = Path(self.path) / f"{self.name}.log"
            else:
                path = Path(path)
                autoparse = True  # Always autoparse external files
            if not path.is_file():
                raise Exception(f'No log file at {path}')
            return path, autoparse

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

        path, autoparse = _check_path(path, autoparse)
        separator, level, timestamp = _initial_arguments()
        start_time, end_time = _get_times()
        log_levels = logging._nameToLevel  # TODO: Better way to get this (private) internal variable?
        try:
            search_level = log_levels[level.upper()]  # log level to search for
        except Exception:
            search_level = 0
        new_text = text.casefold() if ignorecase else text
        results = []
        _last_timestamp = start_time - timedelta(days=1)
        _last_level = "INFO"
        return _find_results()
    '''
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
