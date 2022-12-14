import pytest
import logging
import time
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


def test_find_no_file() -> bool:
    """Testing find method"""
    cleanup()
    mylog = Log("mylog")
    mylog.logger.info("A log message - console only")
    with pytest.raises(Exception):
        result = mylog.find()
    cleanup()

@create_mylog
def test_find_text_1():
    create_dummy_log()
    mylog.logger.info(f"Message: Last line")
    result = mylog.find()
    assert ": Last line" in result[-1], f"FIND2: Incorrect last record"


@create_mylog
def test_find_text_2():
    create_dummy_log()
    mylog.logger.warning("This line won't be in search")
    result = mylog.find('Message')
    assert len(result) > 0, f"FIND7: 'Message' not found"
    for line in result:
        assert "won't" not in line, f'FIND8: Found "Won\'t" in "{line}"'


@create_mylog
def test_find_date_1():
    create_dummy_log()
    timestamp = datetime.now()
    Log.mylog.critical(f"Message: New last line")
    result = mylog.find(date=timestamp, deltadays=1)
    assert len(result) == 1, f"FIND3: Expected 1 record, found {len(result)}"
    assert "CRITICAL" in result[0], f"FIND4: CRITICAL message not found"

@create_mylog
def test_find_by_date_2():
    create_dummy_log()
    timestamp = datetime.now()
    time.sleep(1)
    timestamp -= timedelta(days=3)
    result = mylog.find(date=timestamp, deltadays=-3)
    assert len(result) == 6, f"FIND11: Olddates - Expected 6 records, got {len(result)}"
    result2 = mylog.find(date=timestamp, deltadays=-3, autoparse=True)
    assert result == result2, f"FIND13: Autoparse - Gives different result"

# TODO: Currently fails...
@create_mylog
def test_find_by_level():
    create_dummy_log()
    mylog.logger.error(f"Message: Yet another last line")
    result = mylog.find(text="error")
    assert "ERROR" in result[0], f"FIND5: ERROR message not found"
    result = mylog.find(text="error", ignorecase=False)
    assert not result
    result = mylog.find(level="error")
    assert len(result) == 6, f"FIND6: Expected 6 records, found {len(result)}"

@create_mylog
def test_find_ignorecase():
    create_dummy_log()
    result = mylog.find("Message", ignorecase=False)
    assert not result, f"FIND9: Found 'message' with case sensitive search using 'Message'"
    result = mylog.find("message", ignorecase=False)
    assert result, f"FIND9: Failed to find 'message' with case sensitive search"

@create_mylog
def test_find_path_original():
    create_dummy_log()
    timestamp = datetime.now()
    result = mylog.find(path="mylog.log", date=timestamp, deltadays=-3)
    assert len(result) == 4, f"FIND14: Anotherlog - Expected 4 lines found {len(result)}"

def test_find_path_class_method():
    create_dummy_log()
    timestamp = datetime.now()
    result = Log.find(path="mylog.log", date=timestamp, deltadays=-3)
    assert len(result) == 6, f"FIND14: Anotherlog - Expected 6 lines found {len(result)}"

# TODO: Currently fails...
@create_mylog
def test_find_multiline():
    Log.mylog.info("Three line message\n\twith more data on this line\n\t\tand also on this line too!")
    r = mylog.find()
    assert len(r) == 2
    assert r.count("\t") == 3
    assert r.count("\n") == 2

# TODO: Currently fails...
@create_mylog
def test_find_levels():
    Log.mylog.info("Oneline")
    assert mylog.find(level="error") == []
    assert mylog.find(level="ERRor") == []
    assert len(mylog.find(level="info")) == 1
    assert len(mylog.find(level="InFo")) == 1

# TODO: Currently fails...
def test_find_without_loglevel():
    """ fmt may not include loglevel e.g. ERROR.  Test that .find still works"""
    fmt = Log.presets['name_and_time']
    mylog = Log("mylog", to_file=True, mode="w", to_stdout=True, fmt=fmt)
    mylog("This format has no log level")
    assert len(mylog.find()) == 1
    cleanup()

