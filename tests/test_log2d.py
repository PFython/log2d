import pytest
import time

from log2d import Log, Path

def test_add_level():
    """Test by visual inspection of console output"""
    mylog = Log("mylog")
    Log.mylog.debug("Debugging message...")
    mylog.add_level("SUCCESS", 25)
    Log.mylog.success("Success message...")

def test_cant_add_existing_level():
    with pytest.raises(AttributeError):
        mylog = Log("mylog")
        mylog.add_level("DEBUG", 20)

def test_add_level_above_or_below():
    mylog = Log("mylog")
    mylog.add_level("PreError", below="ERROR")
    Log.mylog.preerror(f"New log level {logging.PREERROR} below ERROR")
    mylog.add_level("PostInfo", above="INFO")
    Log.mylog.postinfo(f"New log level {logging.POSTINFO} above INFO ")

def test_defaults():
    main = Log("main")
    assert main.name == 'main'
    assert main.mode == 'a'
    assert main.path
    assert main.level == 'debug'
    assert main.fmt == '%(name)s|%(levelname)-8s|%(asctime)s|%(message)s'
    assert main.datefmt == '%Y-%m-%dT%H:%M:%S%z'
    assert main.to_file == False
    assert main.to_stdout == True
    assert main.backup_count == 0
    assert main.logger

def test_file_log():
    test_log = Log("Test", to_file=True, to_stdout=False)
    test_log("Entry 1")
    path = Path("Test.log")
    assert path.is_file()
    assert path.read_text().endswith("|Entry 1\n")
    path.unlink()

def test_shortcut():
    shortcut = Log("shortcut")
    shortcut("This should be logged at the default log level (DEBUG)")
    Log.shortcut.setLevel('CRITICAL')
    shortcut("This should be logged at the new CRITICAL level")
    Log.shortcut.info("This should not be logged")

def test_output_destination(capfd):
    progress_log = Log("Progress", to_file=True)
    progress_log("Starting")
    out, err = capfd.readouterr()
    assert out.endswith("Starting\n")
    selenium_log = Log("Selenium", to_file=True, to_stdout=False)
    selenium_log("Started")
    out, err = capfd.readouterr()
    assert out == ""

def test_coexist_with_logging():
    import logging
    logging.warning("This creates a 'root' logger")
    from log2d import Log
    other = Log("other")
    other("This will be echoed twice - 'root' and 'other'")
    Log.disable_rootlogger()
    other("This should only appear once now")

def test_set_level() -> bool:
    mylog = Log("mylog")
    success = mylog.add_level("Success", above="INFO")
    assert success == "New log level 'success' added with value: 21"
    fail = mylog.add_level("Fail", above="SUCCESS")
    assert fail == "New log level 'fail' added with value: 22"

    msg = "This should appear in all log levels above DEBUG"
    mylog.logger.success(f"{msg}: Success!")
    mylog.logger.info(f"{msg}: Info!")
    mylog.logger.fail(f"{msg}: Fail!")

    mylog.logger.setLevel('CRITICAL')
    msg = "This should NOT appear in log levels below CRITICAL"
    mylog.logger.success(f"{msg}: Success!")
    mylog.logger.info(f"{msg}: Info!")
    mylog.logger.fail(f"{msg}: Fail!")


@create_mylog
def test_find() -> bool:
    """Testing find method"""
    mylog = Log("findlog")

    mylog.logger.info("A log message - console only")
    result = mylog.find()
    assert result[0][:14] == "No log file at", f"FIND1: Found a log file - should be absent!"

    # Create dummy log
    aWhileAgo = datetime.now()- timedelta(days=8)
    with open(_fn, "w") as dummyLog:
        for I in range(6):
            T = aWhileAgo + timedelta(days=I)
            dummyLog.write(f"dummylg|INFO    |{T.strftime('%Y-%m-%dT%H:%M:%S%z+0000')}|Log message\n")
        dummyLog.write("  Here is additional line 1\n   Additional line 2 followed by a blank line\n\n")

    mylog = Log(_log, path=_HPath)
    msg ="Should be line in log"
    mylog.logger.info(f"{msg}: Last line")
    result = mylog.find()
    assert ": Last line" in result[-1], f"FIND2: Incorrect last record"
    sleep(1)  # wait a bit
    T = datetime.now()
    sleep(1)
    mylog.logger.critical(f"{msg}: New last line")
    # Search from T:+1day
    result = mylog.find(date=T, deltadays=1)
    assert len(result) == 1, f"FIND3: Expected 1 record, found {len(result)}"
    assert "CRITICAL" in result[0], f"FIND4: CRITICAL message not found"

    mylog.logger.error(f"{msg}: Yet another last line")
    result = mylog.find(text="error")
    assert "ERROR" in result[0], f"FIND5: ERROR message not found"
    result = mylog.find(text="error", ignorecase=False)
    assert not result
    result = mylog.find(level="error")
    assert len(result) == 2, f"FIND6: Expected 2 records, found {len(result)}"

    # Text searches
    mylog.logger.warning("This line won't be in search")
    result = mylog.find('should')
    assert len(result) > 0, f"FIND7: 'Should' not found"
    for ln in result:
        assert "won't" not in ln, f'FIND8: Found "Won\'t" in "{ln}"'
    result = mylog.find("should", ignorecase=False)
    assert not result, f"FIND9: Found 'Should' with case sensitive search"
    result = mylog.find(text='new')
    assert len(result) == 1, f"FIND10: Expected 1 record, found {len(result)}"

    # Search -5 to -8 days ago
    T -= timedelta(days=3)
    result = mylog.find(date=T, deltadays=-3)
    assert len(result) == 6, f"FIND11: Olddates - Expected 6 records, got {len(result)}"
    assert not result[-1], f"FIND12: olddates - found last record was '{result[-1]}''"
    Res2 = mylog.find(date=T, deltadays=-3, autoparse=True)
    assert result == Res2, f"FIND13: Autoparse - Gives different result"

    lg1 = Log('anotherlog')
    result = lg1.find(path=_fn, date=T, deltadays=-3)
    assert len(result) == 6, f"FIND14: Anotherlog - Expected 6 lines found {len(result)}"
    assert not result[-1], f"FIND15: Anotherlog - found last line was '{result[-1]}'"

    # Tidy up if OK
    os.remove(_fn)

    print("FIND passes 15 tests OK")
    return True

def cleanup():
    """ Delete global `mylog` and its log file; delete Handler """
    print("Deleting: mylog.log")
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

@create_mylog
def test_find_multiline():
    Log.mylog.info("Three line message\n\twith more data on this line\n\t\tand also on this line too!")
    r = mylog.find()
    assert len(r) == 2
    assert r.count("\t") == 3
    assert r.count("\n") == 2

@create_mylog
def test_find_levels():
    Log.mylog.info("Oneline")
    assert mylog.find(level="error") == []
    assert mylog.find(level="ERRor") == []
    assert len(mylog.find(level="info")) == 1
    assert len(mylog.find(level="InFo")) == 1

def test_find_without_loglevel():
    """ fmt may not include loglevel e.g. ERROR.  Test that .find still works"""
    fmt = Log.presets['name_and_time']
    mylog = Log("mylog", to_file=True, mode="w", to_stdout=True, fmt=fmt)
    mylog("This format has no log level")
    assert len(mylog.find()) == 1


"""
PF Changes:

.find now raises errors rather than returning error messages in a list
"logname" argument renamed to "path" (shorter, and consistent with Pathlib)
Test added to check .find keeps individual message strings intact e.g. doesn't strip out \t or \n
Test added to change `mylog.find(path="another log file.log")` to Classmethod i.e. `Log.find(path="another log file.log")` - that way you don't have to create an instance (mylog) to use it, and also it doesn't make sense to bind a different log file to mylog.
Variables given longer more descriptive PEP8/snake-case names
Replaced os.join etc. with pathlib.Path methods
Added create() and cleanup() utilities to test_log2d for testing
Added @create_mylog decorator function to test_log2d
"""

