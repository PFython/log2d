# `log2d` - Simple, sane, and sensible logging

![](https://media.giphy.com/media/xT8qBsOjMOcdeGJIU8/giphy.gif)

## **INTRODUCTION**
`log2d` is an incredibly helpful wrapper around Python's `logging` module in the standard library and can be installed via PIP in the normal way:
```
python -m pip install log2d --upgrade
```

It aims to provide the best parts of `logging` (like automatic, rotating backup files) to users who don't want or need to learn every nuance of the module itself and perhaps simply want to wean themselves off `print()` statements and organise their output in a better "2 Dimensional" way (hence the name - `log2d`).

If you've dipped into the standard `logging` documentation you'd be forgiven for thinking you can only log output according to the prescribed log levels: DEBUG, INFO, WARNING, ERROR, or CRITICAL/FATAL.  Such an approach is linear or "1 Dimensional" since it's based solely on the *importance* of a message.

A very common use case however is the need to capture different *types* of message.  Hence TWO dimensions.

In web-scraping apps for example, it's useful to collect the HTTP requests which succeeded or failed or needed a few retries, quite apart from any general Exceptions arising from your actual code.  You might also want a nice (separate) log of overall progress and timings i.e. how long particular scrapers take to complete.

`log2d` makes it simple to create, customise, and use a new logger for each of these types of output, for example sending `progress` messages just to the console, and creating separate `.log` files for `successes`, `failures`, `retries`, `exceptions`, and `timings`. It also lets you search these logs for specific message text, level or over specific time periods.


It does so in a concise, readable, and (dare I claim?) "Pythonic" way, that doesn't require mastery of the `logging` module itself.  It allows you to create a sophisticated logger with powerful default features enabled in just one line of code, then send output to that logger whenever and from wherever you like - also in just one line.

At the end of this README there are some simple Cookbook recipes for dynamically creating a log for any given Module, Class, or Instance.
## **SETUP**
Simply import the `Log` class into your Python script:
```
from log2d import Log
```

## **BASIC USE**

### **Create a named logger that only outputs to the console ("stdout") using default message formatting and date format:**

```
Log("main")
Log.main.warning("Danger, Will Robinson!")

Output:
main|WARNING |2022-10-25T19:34:30+0100|Danger, Will Robinson!
```

> _In place of `.warning` you can use any of the standard log levels, either upper or lower case: DEBUG, INFO, WARNING, ERROR, and CRITICAL/FATAL_

### **Create a logger that just outputs to a file:**

```
log_success = Log("success", to_file=True)
log_success("log2d for the win!")
Log.success.critical("Alert! Alert!")

(Creates and updates ./success.log)
```

> _NB The 'sensible' default logic of `log2d` assumes that if you ONLY specify `to_file` as a parameter, you ONLY want output to go to file, and output to the console (`to_stdout`) is automatically set to `False`_
>
> _The default values for `to_stdout` and `to_file` are `True` and `False` respectively.  In other words if you provide neither parameter, logging is to the console only._
>
> _The default file logging `mode` is `a` - append log messages to the existing log mode indefiintely.  See below for file logging mode `w` which overwrites the log file each time the script is run._
### **Specify a folder/directory for a specific logger:**
```
Log("my_title", path="./output")
```
> _NB `to_file` is automatically set to True if a `path` is supplied._
>
> _The default path is the current working directory `""` or `"."`_
>
> _If a non-existent folder/directory is specified, `FileNotFoundError` will be raised._


### **Set a minimum level of message to capture (in plain English rather than using numeric values):**

```
Log("my_title", level="WARNING")
```
### **Create your own shortcut to log a message at the default level:**
For simple scripts with no or few imports you might like to create your own shortcut functions like this:
```
log_failure = Log("failures")
log_failure("Insert your failure message here")

Output:
failures|DEBUG   |2022-10-25T19:35:06+0100|Insert your failure message here
```
> _Normal considerations regarding _namespaces_ apply however, and for longer/more complex scripts it might be wiser to stick with the explicit naming convention `Log.logger_name()`._
>
> _You could use this shortcut feature to overwrite the `print` functions in existing code, and convert every old `print()` line into a logging command.  `_print = print; print = Log("print")`_
>
> _The default log level used by `log2d` is actually DEBUG, whereas the `logging` default is WARNING.  This change is intended to make things safer and more predictable for new users who might otherwise be sending DEBUG and INFO level messages and wondering why they're not being logged._

## **ABOUT LOGGER NAMES**

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

## **OTHER KEYWORD OPTIONS AND UTILITY METHODS**

### **Search your log**
The `.find()` method helps you easily search for text in messages above a particular level and/or within a particular time period:
```
log_to_search = Log("MyApp", path="./output")
results = log_to_search.find(level="error")
# Returns a list of all ERROR and above messages in last 7 days

results = log_to_search.find(text="except", ignorecase=True, deltadays=-31)
# Case insensitive search for all messages containing 'except' within the last month

results = log_search.find(logname="/path/to/logfile")
# Returns all entries in the named logfile in the last 7 days
```

### **Add Custom logging levels**

```
from log2d import Log, logging

mylog = Log("mylog")

mylog.add_level("NewError", below="ERROR")
mylog.add_level("NewInfo", above="INFO")

Log.mylog.newerror(f"New log level {logging.NEWERROR} below ERROR")
Log.mylog.newinfo(f"New log level {logging.NEWINFO} above INFO ")

Output:
"New log level 'newerror' added with value: 39"
"New log level 'newinfo' added with value: 21"
mylog|NEWERROR|2022-11-09T06:17:00+0000|New log level 39 below ERROR
mylog|NEWINFO |2022-11-09T06:17:17+0000|New log level 21 above INFO
```

This method returns a confirmation message rather than logging its own output and potentially messing up your pristine logging schema.  You can suppress it by assigning a dummy variable e.g.

```
_ = mylog.add_level("NewError", below="ERROR")
```

`.add_level()` will also overwrite previous log levels at a given value if they already exist, and create the new log level _immediately_ above or below the reference log level i.e. without leaving any gaps.  For explicit control over the postion of log levels, you can also specify the log level value numerically:

```
mylog.add_level("TRACE", 15)
Log.mylog.trace("Trace message...")
```

### **Search a log**
```
from log2d import Log

mylog = Log("testlog", to_file=True)
Log.testlog.info("Test info message")

Res = mylog.find()   # Default: all entries for last seven days

Output: Res is a list containing 8 items
testlog|FAIL    |2022-11-14T19:25:45+0000|Test error message at added level: Fail!
testlog|INFO    |2022-11-18T11:17:49+0000|Test info message
testlog|ERROR   |2022-11-18T11:22:37+0000|Test error message
testlog|INFO    |2022-11-19T08:39:40+0000|Test info message
testlog|SUCCESS |2022-11-19T08:40:04+0000|Three line message
    with more data on this line
      and also on this line too!
testlog|INFO    |2022-11-19T08:40:48+0000|Test info message
```
### **Search above level**
```
...
Res = mylog.find(level="error")
Output:  Res is
testlog|ERROR   |2022-11-18T11:22:37+0000|Test error message
```

### **Search for text**
```
...
Res = mylog.find(text="error")
Output:  Res is
testlog|FAIL    |2022-11-14T19:25:45+0000|Test error message at added level: Fail!
testlog|ERROR   |2022-11-18T11:22:37+0000|Test error message

```
### **Create a new log file for each session overwriting the previous file each time:**

```
results = Log("session_results", to_file=True, mode="w")
```

### **Create a new log file for each session and automatically create 10 rotating backups:**

```
results = Log("session_results", to_file=True, mode="w", backup_count=10)
```
> _The current log file will always be `session_results.log` but for subsequent sessions this will be copied to `session_results.log.1` then `session_results.log.2` etc until the backup count is reached, then start again on a rotating basis._
>
> _If `backup_count` is not specified, the default number of backups is 5._


### **Preview a particular message format and/or date format - either one of the supplied presets, or one of your own design:**

```
Log.preview(fmt=Log.presets["timestamp_only"], datefmt=Log.date_formats["time"])

Output:
13:10:06|This is a preview log entry.

Log.preview(datefmt="%m-%d::%H:%M")

Output:
temp_preview|09-25::15:36|This is a preview log entry.
```


### **Preview all combinations of message/date presets:**

```
Log.preview_all()
```

### **List all `Log` instances:**
```
Log.index
```

### **Access the underlying `logging.Logger` object for even more control**
```
logger = Log("main").logger

type(logger)
<class 'logging.Logger'>

dir(logger)
[...
'addFilter', 'addHandler', 'callHandlers', 'critical', 'debug', 'disabled', 'error', 'exception', 'fatal', 'filter', 'filters', 'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'handlers', 'hasHandlers', 'info', 'isEnabledFor', 'level', 'log', 'makeRecord', 'manager', 'name', 'parent', 'propagate', 'removeFilter', 'removeHandler', 'root', 'setLevel', 'warn', 'warning']
```
## **COOKBOOK**

### **Recipe 1: Create one log file per Module**

```
from log2d import Log, Path

if __name__ == '__main__':
    log = Log(Path(__file__).stem, to_file=True).logger

    # Then just reuse the log object elsewhere in your script e.g.:
    file_name = Path(__file__).name
    log.critical(f'critical message from: {file_name}')
    log.error(f'error message from: {file_name}')
    log.warning(f'new warning message from: {file_name}')
    log.info(f'info message from: {file_name}')
    log.debug(f'debug message from: {file_name}')

"""
OUTPUT:
my_file|CRITICAL|2022-10-25T16:32:50+0100|critical message from: my_file.py
my_file|ERROR   |2022-10-25T16:32:50+0100|error message from: my_file.py
my_file|WARNING |2022-10-25T16:32:50+0100|new warning message from: my_file.py
my_file|INFO    |2022-10-25T16:32:50+0100|info message from: my_file.py
my_file|DEBUG   |2022-10-25T16:32:50+0100|debug message from: my_file.py
"""
 ```

### **Recipe 2: Create one log file per Instance**

```
from log2d import Log

class MyClass:
    def __init__(self, name):
        params = {"fmt": Log.presets["name_and_time"]}
        self.log = Log.index.get(name) or Log(name, **params)

    def method_1(self):
        # Do something
        self.log("method_1 did something!")

x = MyClass("Instance 1")
x.method_1()
y = MyClass("Instance 2")
y.method_1()
x.log("This message was logged directly")
y.log("Likewise, but different instance")

"""
OUTPUT:
Instance 1|2022-10-16T08:50:29+0100|method_1 did something!
Instance 2|2022-10-16T08:29:05+0100|method_1 did something!
Instance 1|2022-10-16T08:53:17+0100|This message was logged directly
Instance 2|2022-10-16T08:54:06+0100|Likewise, but different instance
"""
```

### **Recipe 3: Create one log file per Module**

```
from log2d import Log

class MyAbstractClass:
    def __init__(self, name, *args, **kwargs):
        params = {"fmt": Log.presets["name_and_time"]}
        self.log = Log.index.get(name) or Log(name, **params)

class MyClass(MyAbstractClass):
    def __init__(self, name, *args, **kwargs):
        super().__init__(self.__class__.__name__, *args, **kwargs)
        self.name = name

    def method_1(self):
        # Do something
        self.log(f"method_1 of {self.name} did something!")

x = MyClass("Instance X")
x.method_1()
y = MyClass("Instance Y")
y.method_1()
x.log(f"This message was logged by {x.name}")
y.log(f"And this one by {y.name}")

"""
OUTPUT:
MyClass|2022-10-16T08:43:31+0100|method_1 of Instance X did something!
MyClass|2022-10-16T08:43:45+0100|method_1 of Instance Y did something!
MyClass|2022-10-16T08:57:52+0100|This message was logged by Instance X
MyClass|2022-10-16T08:58:18+0100|And this one by Instance Y
"""


```
### **Recipe 4: Use a preset message/date format, or supply your own:**

```
fmt = Log.presets["file_func_name"]
datefmt = Log.date_formats["date_and_time"]

Log("main", fmt=fmt, datefmt=datefmt)
```
```
fmt = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
datefmt = '%d/%m/%Y %I:%M:%S %p'

Log("main", fmt=fmt, datefmt=datefmt)
```

>_For more information on composing your own formats see:_
>
> _https://docs.python.org/3/library/logging.html#formatter-objects_
>
> _https://docs.python.org/3/library/logging.html#logging.LogRecord_

### **Recipe 5: Add a new date format or message format preset at the Class level, so that future instances can use them:**
```

fmt = "%(asctime)s (%(name)s): %(message)s"
datefmt = "%m-%d %H:%M"

Log.presets["my_message_format"] = fmt
Log.date_formats["my_date_format"] = datefmt
```

### **Recipe 6: Example web-scraping setup**

As shown earlier, values for `level`, `fmt`, `datefmt`, `to_file`, `to_stdout`, `path`, `mode`, and `backup_count` can be set for a specific logger by supplying them as keyword arguments on initialisation.

Where no argument is supplied for a new logger, the Class level defaults will be used.  Default attributes can also be set at a class level so that all subsequent loggers have the same or similar settings:

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

Log("main", to_stdout=True)
Log("selenium")
Log("requests")
Log("timings")
Log("results")
Log("retries")
Log("errors")
```


## **USING LOGGING AND LOG2D AT THE SAME TIME**

You may find yourself using code that already has `logging` enabled.  This won't interfere with any loggers you *subsequently* create with `log2d` but you might find that some `log2d` messages are repeated (inhrerited) by the existing RootLogger `logging.Logger.root`, for example echoing WARNING level messages to stdout even though you've explicitly disabled this in your `log2d` logger.

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

If neither of these approaches give you what you need, you can dive a bit deeper into the `Log.get_handlers` method of `log2d` or see above for accessubg the underlying `logging.Logger` object.

If you find yourself doing this, you'll inevitably find yourself reading the standard library `logging` documentation which of course goes against the very reason for `log2d`'s existence - to offer simple, sane, and sensible logging _without_ the pain of having to learn its innner workings.  So if you've reached this point and need more control or sophistication with your logging, then `log2d` has probably served it's purpose and you're ready to move onwards and upwards!

## **FEEDBACK AND CONTRIBUTING**

I'd be delighted to hear any suggestions, bug reports, or comments in the form of a Github ISSUE, and if you've found `log2d` useful or merely interesting please do click the "Star" button.  It really raises my spirits to see that kind of feedback.

If you're in paid employment and `log2d` has saved you even a few minutes' effort, please consider how much this gift is worth based on your daily/hourly earnings, and whether it might feel good to at least leave a nice comment on BuyMeaCoffee.com?  Thank you.

<a href="https://www.buymeacoffee.com/pfython" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/arial-yellow.png" alt="Buy Me A Coffee" width="217px" ></a>

**Special Thanks** to [Mike Pollard](https://github.com/MikeDP) for the `.find()` utility.
