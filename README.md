## INTRODUCTION
`log2d` is a simple but powerful wrapper around Python's `logging` module in the standard library and can be installed via PIP in the normal way:
```
python -m pip install log2d --upgrade
```

It aims to provide the best parts of `logging` (like automatic, rotating backup files) to users who don't want or need to learn every nuance of the module itself and perhaps simply want to wean themselves off `print()` statements and organise their output in a better "2 Dimensional" way (hence the name - `log2d`).

If you've dipped into the standard `logging` documentation you'd be forgiven for thinking you can only log output according to the prescribed log levels: DEBUG, INFO, WARNING, ERROR, or CRITICAL.  Such an approach is linear or "1 Dimensional" since it's based solely on the *importance* of a message.

A very common use case however is the need to capture different *types* of message.  Hence TWO dimensions - imagine a graph with "Type" on one axis and "Importance" on the other...  Each log message is given a destination on the graph based on these two values.

In web-scraping apps for example, it's useful to collect the HTTP requests which succeeded or failed or needed a few retries, quite apart from any general Exceptions arising from your actual code.  You might also want a nice (separate) log of overall progress and timings i.e. how long particular scrapers take to complete.

`log2d` makes it simple to create, customise, and use a new logger for each of these types of output, for example sending `progress` messages just to the console, and creating separate `.log` files for `successes`, `failures`, `retries`, `exceptions`, and `timings`.

It does so in a concise, readable, and (dare I claim?) "Pythonic" way, that doesn't require mastery of the `logging` module itself.  It allows you to create a sophisticated logger with powerful default features enabled in just one line of code, then send output to that logger whenever and from wherever you like - also in just one line.

## SETUP
Simply import the `Log` class into your Python script:
```
from log2d import Log
```

## BASIC USE

### Create a named logger that only outputs to the console ("stdout") using default message formatting and date format:

```
Log("main")
Log.main.warning("Danger, Will Robinson!")

Output:
main|WARNING|2022-09-25 12:38:07|Danger, Will Robinson!
```

> _In place of `.warning` you can use any of the standard log levels, either upper or lower case: DEBUG, INFO, WARNING, ERROR, and CRITICAL_

### Set a minimum level of message to capture (in plain English rather than using numeric values):

```
Log("my_title", level="WARNING")
```
### Create your own shortcut to log a message at the default level:
For simple scripts with no or few imports you might like to create your own shortcut functions like this:
```
log_failure = Log("failures")
log_failure("Insert your failure message here")

Output:
failures|DEBUG  |2022-09-25 12:37:33|Insert your failure message here
```
> _Normal considerations regarding _namespaces_ apply however, and for longer/more complex scripts it might be wiser to stick with the explicit naming convention `Log.logger_name()`._
>
> _You could use this shortcut feature to overwrite the `print` functions in existing code, and convert every old `print()` line into a logging command.  `_print = print; print = Log("print")`_
>
> _The default log level used by `log2d` is actually DEBUG, whereas the `logging` default is WARNING.  This change is intended to make things safer and more predictable for new users who might otherwise be sending DEBUG and INFO level messages and wondering why they're not being logged._


### Create a logger that just outputs to a file:

```
log_success = Log("success", to_file=True, to_stdout=False)
log_success("log2d for the win!")
Log.success.critical("Alert! Alert!")

(Creates and updates ./success.log)
```
### Specify a folder/directory for a specific logger:
```
Log("my_title", path="./output")
```
> _NB `to_file` is automatically set to True if a `path` is supplied._
>
> _The default path is the current working directory `""` or `"."`_
>
> _If a non-existent folder/directory is specified, `FileNotFoundError` will be raised._

## ABOUT LOGGER NAMES

1) You **can** create a logger name with spaces and other characters rather than underscores, but you wouldn't then be able to use Python's nice `.attribute` notation.  If your log name was "my main log" you'd need to use `getattr(Log, "my main log").warning("...")` instead, which is a bit messy.  Best to just use underscores if you can.


2) Just as in the standard `logging` module, the name "root" is reserved for a special type of logger which actually inherits from other loggers.  This can be very helpful if you want a single "master" logger that records absolutely everything, but also a bit annoying if you weren't aware of it and have already explicitly disabled output at a particular level, only to see it appear in your "root" logger.  Here's a quick example to demonstrate how this works:

```
Log("main")
Log.main.info("This is the MAIN logger")

Output:
main|INFO   |2022-10-08T23:47:08+0100|This is the MAIN logger

Log("root", fmt=Log.presets['timestamp_only'])
Log.root.info("This message is for ROOT only")

Output:
2022-10-08T23:52:09+0100|This message is for ROOT only

Log.main.info("This message will be echoed by BOTH loggers")

Output:
main|INFO   |2022-10-08T23:49:23+0100|This message will be echoed by BOTH loggers
2022-10-08T23:49:23+0100|This message will be echoed by BOTH loggers
```
If you don't want to use this 'inheritance' feature, just avoid using the name "root" for any of your `log2d` loggers.

> _(See also USING LOGGING AND LOG2D AT THE SAME TIME below)_

## OTHER KEYWORD OPTIONS AND UTILITY METHODS

### Create a new log file for each session and automatically create 10 rotating backups:

```
results = Log("session_results", to_file=True, mode="a", backup_count=10)
```
> _The current log file will always be `session_results.log` but for subsequent sessions this will be copied to `session_results.log.1` then `session_results.log.2` etc until the backup count is reached, then start again on a rotating basis._
>
> _If `backup_count` is not specified, the default number of backups is 5._


### Preview a particular message format and/or date format - either one of the supplied presets, or one of your own design:

```
Log.preview(fmt=Log.presets["timestamp_only"], datefmt=Log.date_formats["time"])

Output:
13:10:06|This is a preview log entry.

Log.preview(datefmt="%m-%d::%H:%M")

Output:
temp_preview|09-25::15:36|This is a preview log entry.
```


### Preview all combinations of message/date presets:

```
Log.preview_all()
```

### Create a logger using a preset message/date format or one of your own design:

```
Log("my_title", fmt=Log.presets["func_file_name"], datefmt=Log.date_formats["date_and_time"])
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

### Create multiple logs with same/similar settings

As shown above, values for `level`, `fmt`, `datefmt`, `to_file`, `to_stdout`, `path`, `mode`, and `backup_count` can be set for a specific logger by supplying them as keyword arguments on initialisation.

Where no argument is supplied for a new logger, the class level defaults will be used.  Default attributes can also be set at a class level so that all subsequent loggers have the same or similar settings:

```
from log2d import Log

ROOT_DIR = "./my_app_path"

Log.path = f"{ROOT_DIR}/logs/"
Log.fmt = Log.presets["name_and_time"]
Log.datefmt = Log.date_formats["time"]
Log.to_file = True
Log.to_stdout = False
Log.mode = "w"
Log.backup_count = 10

Log("progress", to_stdout=True)
Log("selenium")
Log("http")
Log("timings")
Log("retries")
Log("errors")
```
### Access a list of all `Log` instances:

```
Log.index
```

## USING LOGGING AND LOG2D AT THE SAME TIME

You may find yourself using code that already has `logging` enabled.  This won't interfere with any loggers you subsequently create with `log2d` but you might find that some `log2d` messages are repeated (inhrerited) by the RootLogger `logging.Logger.root`, for example echoing WARNING level messages to stdout even though you've explicitly disabled this in your `log2d` logger.

In case you were wondering, a `log2d` logger called "root" will inherit from other `log2d` loggers in a similar way to RootLogger but it is not the same entity as `logging.Logger.root` created by downstream code you've imported from.  Both can exist at the same time and be configured to behave differently.

So... if you're able to amend the original code where logging is enabled, the best way to ensure consistent behaviour is to replace `logging` with `log2d` entirely:

- Replace `import logging` with `from log2d import Log`
- Create a new "root" logger with `log2d` and specify how you want it to work in the normal way e.g. `Log("root", level="INFO")`
- Replace `logger.info()`, `logger.warning()` etc with `Log.root.info()`, `Log.root.warning()` etc.

Another option is to disable the RootLogger using the `log2d` convenience function:

```
Log.disable_rootlogger()
```

This is a bit of a blunt instrument and basically finds all the Handlers used by RootLogger (`logging.Logger.root.handlers`) and runs the `.removeHandler()` method on them.

If neither of these approaches give you what you need, you can dive a bit deeper into the `Log.get_handler` method of `log2d` or the standard `logging` documentation to learn how to modify the behaviour of a particular Handler.  Of course that goes against the very reason for `log2d`'s existence - to offer simple, sane, and sensible logging _without_ the pain of having to learn its innner workings.  So if you've reached this point and need more control or sophistication with your logging, then `log2d` has probably served it's purpose and you're ready to move onwards and upwards!

## FEEDBACK AND CONTRIBUTING

I'd be delighted to hear any suggestions, bug reports, or comments in the form of a Github ISSUE, and if you've found `log2d` useful or merely interesting please do click the "Star" button.  It really raises my spirites to see that kind of feedback.

If you're in paid employment and `log2d` has saved you even 30 minutes' effort, please consider how much this gift equates to based on your daily/hourly rate, and whether it might feel good to spend a minute of your own time leaving a nice comment on BuyMeaCoffee.com?  Thank you.

<a href="https://www.buymeacoffee.com/pfython" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/arial-yellow.png" alt="Buy Me A Coffee" width="217px" ></a>
