## INTRODUCTION
`log2d` is a simple but powerful wrapper around Python's `logging` module in the standard library and can be installed via PIP in the normal way:
```
python -m pip install log2d --upgrade
```

It aims to provide the best parts of `logging` (like automatic, rotating backup files) to users who don't want or need to learn every nuance of the module itself and perhaps simply want to wean themselves off `print()` statements and organise their output in a better "2 Dimensional" way (hence the name - `log2d`).

What I mean by this is that unless you delve quite deeply into the `logging` module, you'd be forgiven for thinking you can only log your output according to the standard log levels, namely: DEBUG, INFO, WARNING, ERROR, or CRITICAL.  Such an approach is linear or "1 Dimensional" since it's based solely on the *importance* of a message.

A very common use case however is the need to capture different *types* of message.  Hence TWO dimensions - imagine a graph with "Type" on one axis and "Importance" on the other...

In web-scraping apps for example, it's useful to collect the HTTP requests which succeeded or failed or needed a few retries, quite apart from any general Exceptions arising from your actual code.  You might also want a nice (separate) log of overall progress and timings i.e. how long particular scrapers take to complete.

`log2d` makes it simple to create, customise, and use a new logger for each of these types of output, for example sending `progress` messages just to the console, and creating separate `.log` files for `successes`, `failures`, `retries`, `exceptions`, and `timings`.

It does so in a concise, readable, and (dare I claim?) "Pythonic" way, that doesn't require mastery of the `logging` module itself.

## SETUP
Simply import the `Log` class into your Python script:
```
from log2d import Log
```

## BASIC USE

### Create a named logger that only outputs to the console ("stdout") using default message formatting and date format:

```
Log("root")
Log.root.warning("Danger, Will Robinson!")

Output: root|WARNING|2022-09-25 12:38:07|Danger, Will Robinson!
```

> _In place of `.warning` you can use any of the standard log levels, either upper or lower case: DEBUG, INFO, WARNING, ERROR, and CRITICAL_

### Create your own shortcut to log a message at the default level:

```
log_failures = Log("failures")
log_failures("Insert your failure message here")

Output: FAILURES|DEBUG  |2022-09-25 12:37:33|Insert your failure message here
```
> _The default log level used by `Log` is actually DEBUG.  This change to the `logging` default of WARNING is intended to make things safer and more predictable for unfamiliar users who might otherwise be sending DEBUG and INFO level messages and wondering why they're not being logged._

### Create a logger that just outputs to a file each time:

```
log_successes = Log("success", to_file=True, to_stdout=False)
log_successes("log2d for the win!")
Log.success.critical("Alert! Alert!")

(Creates and updates ./success.log)
```
> _You **could** specify a logger name with spaces and other characters rather than underscores, but you wouldn't then be able to use Python's nice `.attribute` notation.  If your log name was "my main log" you'd need to use `getattr(Log, "my main log").warning("...")` instead._

## OTHER KEYWORD OPTIONS AND UTILITY METHODS

### Create a new log file for each session and automatically create 10 rotating backups:

```
results = Log("session_results", to_file=True, mode="a", backup_count=10)
```
> _The current log file will always be `session_results.log` but for subsequent sessions this will be copied to `session_results.log.1` then `session_results.log.2` etc until the backup count is reached, then start again on a rotating basis.
>
> _If `backup_count` is not specified, the default number of backups is 5._

### Set a minimum level of message to capture (in plain English rather than using numeric values):

```
Log("my_title", level="WARNING")
```


### Preview a particular message format and/or date format - either one of the supplied presets, or one of your own design:

```
Log.preview(fmt=Log.presets[2], datefmt=Log.date_formats[1])

Output: 13:10:06|This is a preview log entry.

Log.preview(datefmt="%m-%d::%H:%M")

Output: temp_preview|WARNING|09-25::15:36|This is a preview log entry.
```


### Preview all combinations of message/date presets:

```
Log.preview_presets()
```

### Create a logger using a preset message/date format or one of your own design:

```
Log("my_title", fmt=Log.presets[4], datefmt=Log.date_formats[1])
```
### Add a new date format or message format preset at the class level, such that future instances can use them:
```
Log.date_formats["my_date_format"] = "%m-%d %H:%M"
Log.presets["my_message_format"] = "%(asctime)s (%(name)s): %(message)s"
```
>_For more information on composing your own formats see:_
>
> _https://docs.python.org/3/library/logging.html#formatter-objects_
>
> _https://docs.python.org/3/library/logging.html#logging.LogRecord_

### Specify a folder/directory for a specific logger:
```
Log("my_title", path="./output")
```
> _NB `to_file` is automatically set to True if a `path` is supplied._
>
> _The default path is the current working directory `""` or `"."`_
>
> _If a non-existent folder/directory is specified, `FileNotFoundError` will be raised._


In general terms, the values of attributes such as `level`, `fmt`, `datefmt`, `to_file`, `to_stdout`, `path`, `mode`, and `backup_count` can be set for a specific logger by supplying them as keyword arguments on initialisation.  Where no argument is supplied for a new logger, the class level defaults will be used.  Default attributes can also be set at a class level in the normal way:

```
Log.path = "./my_logs"
```


### Access a list of all `Log` instances:

```
Log.index
```
