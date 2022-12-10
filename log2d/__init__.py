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

    def find(self, text: str="", logname=None, date=None, deltadays: int=-7,
             level: str='NOTSET', separator: str="|",
             ignorecase: bool=True, autoparse: bool=False):
        """ Search log for:
               text:        text to seach for. Default '' means return everything
               logname:     path/to/another/log.log to search. Default=None, search this log
               date:        Date(time) object/str anchor for search. Default None = NOW
               deltadays:   number of days prior to (-ve) or after date. Default 1 week prior
               level:       log level below which results are ignored. Default NOTSET
               separator:   field separator character in log record. Default |
               ignorecase:  set case insensitivity. Default True
               autoparse:   if True, parses the log to find separator, time and level fields. 
                            If False, looks at log2d fmt string.  Default False
            Returns [MSG[, ...]], [error message] or []
        """
        def _autoParse(FN):
            """Attempts to automatically parse log file to return [separator, date, level] fields"""
            query ='r"|CRITICAL\s*|INFO\s*|DEBUG\s*|WARNING\s*|NOTSET\s*|ERROR\s*|"'
            SEP = grp = splitln = ''
            LVL = TS = -1
            # Find the LEVEL which then gives surrounding sepatator
            q = reCompile(query)
            try:
                with open(FN, mode='r') as lf:
                    for ln in lf:
                        try:
                            m = q.search(ln)
                            s, e = m.span() if m else (0, 0)
                            if s - e == 0:  # s&e are the same so not found
                                continue
                            if s == 0:
                                if e > len(ln) - 2:
                                    continue
                                SEP = ln[e]
                            else:
                                SEP = ln[s-1]
                            splitln = ln.split(SEP)
                            grp = m.group().strip(SEP)   # LEVEL found
                            break
                        except:
                            continue
            except Exception as e:
                return ['', -1, -1]

            if SEP != '':
                # Now find LEVEL and TIMESTAMP fields
                try:
                    LVL = splitln.index(grp)  # Level field index
                    for I, Fld in enumerate(splitln):
                        try:  # Try to convert each field 'till we get timestamp
                            _ = parser.parse(Fld, ignoretz=True)
                            TS = I
                            break
                        except:
                            continue
                except:
                    pass
            # TODO: Further check result?
            return [SEP, LVL, TS]

        def _getFmtFields():
            """Check the fmt string to find level and time fields. Return as (separator, LVL, TM)"""
            _fmt = self.fmt.split(separator)
            LVL = TM = -1
            for I, F in enumerate(_fmt):
                if "levelname" in F:
                    LVL = I
                if "asctime" in F:
                    TM = I
            return (separator, LVL, TM)

        def _queryLevel(s: str) -> bool:
            """Is record above required level? Return True/False """
            # get numerical value
            try:
                V = LLevels[s]
            except:  # Level not found
                V = 50   # Set as CRITICAL
            return V >= SL

        def _queryText(s: str) -> bool:
            """Does record contain text? Return True/False"""
            try:
                R = (TXT in s.casefold()) if ignorecase else (TXT in s)
            except:
                R = False  # TODO: should we raise an exception?
            # Not found or error
            return R

        # ############ MAIN for find ##############
        # Get the filename
        if logname:  # External log
            FN = logname
            autoparse = True  # Always autoparse external files
        else:
            FN = os.path.join(self.path, self.name + '.log')
        if not os.path.exists(FN):
            return [f'No log file at {FN}'] # log not found!
        # Prepare args
        SEP, LVL, TS = _autoParse(FN) if autoparse else _getFmtFields()

        if SEP == '' or TS == -1 or LVL == -1:
            return [f"Error parsing log format: Found '{SEP}', {TS}, {LVL}"]
        separator = SEP
        try:
            if not date:
                _startTm = datetime.now()
            elif isinstance(date, str):
                _startTm = parser.parse(date)
            else:
                _startTm = date
            _endTm = _startTm + timedelta(days=deltadays)
            if _startTm > _endTm:
                _startTm, _endTm = _endTm, _startTm
        except:
            return [f"Find start/End time error: {date}|{deltadays}"]
        # TODO: Better way to get this (private) internal variable?
        LLevels = logging._nameToLevel
        try:
            SL = LLevels[level.upper()]  # log level to search for
        except Exception as e:
            SL = 0
        TXT = text.casefold() if ignorecase else text  # search text
        # Set initial result state
        RES = []
        _lastTS = _startTm - timedelta(days=1)  # Initialise to before start
        _lastLVL = "INFO"
        with open(FN, mode='r') as _LOG:
            # and search file
            for ln in _LOG:
                splitln = ln.split(separator)
                try:  # Get timestamp and level
                    _LVL = splitln[LVL].strip()
                    _TS = parser.parse(splitln[TS], ignoretz=True)
                except:  # Timestamp/level not found
                    _TS = _lastTS  # Recover last good timestamp and LVL
                    _LVL = _lastLVL
                _lastTS = _TS   # save timestamp and level for next line
                _lastLVL = _LVL
                #  within time period?
                if _startTm <= _TS:
                    if _TS > _endTm:
                        break   # No need to read any more
                    if TXT:
                        ln = ln if (_queryText(ln) and _queryLevel(_LVL)) else ''
                    else:
                        ln = ln if _queryLevel(_LVL) else ''
                    if ln:
                        RES.append(ln.strip())
        # Finally, return anything found or error message
        return RES

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
