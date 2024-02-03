from functools import wraps
import pytest
import logging
from datetime import datetime, timedelta

from log2d import Log, Path

def cleanup():
    """ Delete global `mylog` and its log file; delete Handler """
    if "mylog" in globals():
        global mylog
        for handler in mylog.logger.handlers:
            mylog.logger.removeHandler(handler)
            handler.close()
        del mylog
    if Log.index.get('mylog'):
        del Log.index['mylog']
    path = Path("mylog.log")
    logging.shutdown()
    if path.is_file():
        print("Deleting: mylog.log")
        path.unlink()

def create():
    """
    Create a global log2d instance `mylog`
    Output to file and console; overwrite mode
    """
    cleanup()
    global mylog
    mylog = Log("mylog", to_file=True, to_stdout=True, mode="w")
    print("Logging to console and mylog.log")

def create_mylog(function):
    """
    A decorator to create and eventually clean up a generic test logger object.
    Simply insert a line `@create_mylog` above `def test_X():`
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        create()
        try:
            result = function(*args, **kwargs)
            cleanup()
        except AssertionError:
            cleanup()
            raise
        return result
    return wrapper

def create_dummy_log():
    cleanup()
    a_while_ago = datetime.now()- timedelta(days=8)
    with open("mylog.log", "w") as file:
        for index in range(6):
            timestamp = a_while_ago + timedelta(days=index)
            file.write(f"mylog|INFO    |{timestamp.strftime('%Y-%m-%dT%H:%M:%S%z+0000')}|Log message\n")
        file.write("  Here is additional line 1\n   Additional line 2 followed by a blank line\n\n")
    global mylog
    mylog = Log("mylog", to_file=True, to_stdout=True)
    print("Dummy log created: mylog.log")

@create_mylog
def test_add_level():
    """Test by visual inspection of console output"""
    Log.mylog.debug("Debugging message...")
    mylog.add_level("SUCCESS", 25)
    Log.mylog.success("Success message...")

@create_mylog
def test_cant_add_existing_level():
    with pytest.raises(AttributeError):
        mylog.add_level("DEBUG", 20)

@create_mylog
def test_add_level_above_or_below():
    mylog.add_level("PreError", below="ERROR")
    Log.mylog.preerror(f"New log level {logging.PREERROR} below ERROR")
    mylog.add_level("PostInfo", above="INFO")
    Log.mylog.postinfo(f"New log level {logging.POSTINFO} above INFO ")

def test_defaults():
    mylog = Log("mylog")
    assert mylog.name == 'mylog'
    assert mylog.mode == 'a'
    assert mylog.path
    assert mylog.level == 'debug'
    assert mylog.fmt == '%(name)s|%(levelname)-8s|%(asctime)s|%(message)s'
    assert mylog.datefmt == '%Y-%m-%dT%H:%M:%S%z'
    assert mylog.to_file == False
    assert mylog.to_stdout == True
    assert mylog.backup_count == 0
    assert mylog.logger
    cleanup()

@create_mylog
def test_file_log():
    mylog("Entry 1")
    path = Path("mylog.log")
    assert path.is_file()
    assert path.read_text().endswith("|Entry 1\n")

@create_mylog
def test_shortcut():
    mylog("This should be logged at the default log level (DEBUG)")
    Log.mylog.setLevel('CRITICAL')
    mylog("This should be logged at the new CRITICAL level")
    Log.mylog.info("This should not be logged")

@create_mylog
def test_output_destination(capfd):
    mylog("Starting")
    out, err = capfd.readouterr()
    assert out.endswith("Starting\n")
    selenium_log = Log("Selenium", to_file=True, to_stdout=False)
    selenium_log("Started")
    out, err = capfd.readouterr()
    assert out == ""

@create_mylog
def test_coexist_with_logging():
    import logging
    logging.warning("This creates a 'root' logger")
    from log2d import Log
    mylog("This will be echoed twice - 'root' and 'mylog'")
    Log.disable_rootlogger()
    mylog("This should only appear once now")

@create_mylog
def test_set_level() -> bool:
    success = mylog.add_level("Success", above="INFO")
    assert success == "New log level 'success' added with value: 21"
    fail = mylog.add_level("Fail", above="SUCCESS")
    assert fail.startswith("New log level 'fail' added with value:")

    msg = "This should appear in all log levels above DEBUG"
    mylog.logger.success(f"{msg}: Success!")
    mylog.logger.info(f"{msg}: Info!")
    mylog.logger.fail(f"{msg}: Fail!")

    mylog.logger.setLevel('CRITICAL')
    msg = "This should NOT appear in log levels below CRITICAL"
    mylog.logger.success(f"{msg}: Success!")
    mylog.logger.info(f"{msg}: Info!")
    mylog.logger.fail(f"{msg}: Fail!")
    mylog.logger.critical(f"{msg}: Fail!")


