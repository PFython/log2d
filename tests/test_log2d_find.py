#!/usr/bin/env python3
"""
test_log2d_find.py
pytest module for "Find" function testing

"""

import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

import pytest

from log2d import Log


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
    """ SHUTDOWN doesn't do what you think.  Use 'log.handlers.clear()' """
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
    mylog = Log("mylog", to_file=True, to_stdout=True, mode="a")
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
            print(f"\n### {function.__name__} ###")
            result = function(*args, **kwargs)
            cleanup()
        except AssertionError:
            cleanup()
            raise
        return result
    return wrapper

def date_generator(start: int, delta: int, fmt: str="%Y/%m/%dT%H:%M:%S.%f") -> str:
    """
       Yields date/time string starting (start-1) + delta days ago to start-1 days ago
       formatted by fmt
    """
    start_day = datetime.now() - timedelta(days=start+delta)
    for index in range(delta):
        day = start_day + timedelta(index)
        yield day.strftime(fmt)

def create_dummy_log(path: Path="mylog.log", start: int=0, delta: int=10):
    """
        Create a large log of data
    """
    levels = ['DEBUG', 'INFO', 'WARNING', 'SUCCESS', 'ERROR', 'CRITICAL']
    line_to_write = "MyTestApp|{:<8}|{}|This is {} message #{}\n"
    midpoint = delta//2

    with open(path, mode='a') as log_file:
        for index, timestamp in enumerate(date_generator(start, delta)):
            level = levels[index % 6]
            log_file.write(line_to_write.format(level, timestamp, level.lower(), index))
            if index == midpoint:
                log_file.write("Here's another line\nand another also\n\n")
    global mylog
    print("Dummy log created: mylog.log")

# common assert fail string
expected = lambda x,f : f"Expected {x}, found {f}"


@create_mylog
def test_find_ignorecase():
    create_dummy_log()
    result = mylog.find("Message", ignorecase=False)
    assert not result, f"FIND9: Found 'message' with case sensitive search using 'Message'"
    result = mylog.find("message", ignorecase=False)
    assert result, f"FIND9: Failed to find 'message' with case sensitive search"

@create_mylog
def test_find_twodates():
    """Check logs with multiple number/date elements"""
    create_dummy_log()
    mylog.logger.info("Info message #1")
    mylog.logger.info("Info message #2")
    mylog.logger.warning("Warning message #3")
    mylog.logger.info("This message contains a second date: 05/01/2023")
    mylog.logger.info("Info message #5")
    result = mylog.find()
    assert len(result) == 11, expected(11, len(result))

# ########################## NEW FIND TESTS ################################


@create_mylog
def test_find_mtfile():
    """ Check empty file gives sensible ([]) response."""
    Path("mylog.log").touch()   #  Create MT file
    assert mylog.find() == [], "mylog.log not empty!"
    assert Log("mylog").find() == [], "mylog.log not empty!"
    assert Log.find(path='mylog.log') == [], "mylog.log not empty!"
    assert Log('').find(path='mylog.log') == [], "mylog.log not empty!"

def test_find_no_file() -> bool:
    """Check no log file gives exception"""
    mylog = Log("mylog")
    mylog.logger.info("A log message - console only")
    try:
        with pytest.raises(Exception):
            result = mylog.find()
        with pytest.raises(Exception):
            result = Log.find(path='mylog.log')
    finally:
        cleanup()

@create_mylog
def test_find_default():
    """Default: Class and instance default find last 7 days"""
    create_dummy_log()
    res = len(mylog.find())
    assert res == 6, f'Instance: {expected(6, res)}'
    res = len(Log.find(path='mylog.log'))
    assert res == 6, f'Class: {expected(6, res)}'

@create_mylog
def test_find_date_1():
    """Find all entries for last day - should be 1"""
    create_dummy_log()
    Log.mylog.critical(f"Message: New last line")
    time.sleep(1)
    timestamp = datetime.now()
    result = mylog.find(date=timestamp, deltadays=-1)
    assert len(result) == 1, f"Instance: {expected(1, len(result))}"
    result = Log.find(path="mylog.log", date=timestamp, deltadays=-1)
    assert len(result) == 1, f"Class: {expected(1, len(result))}"
    assert "CRITICAL" in result[0], f"Find_Date_1: CRITICAL message not found"

@create_mylog
def test_find_by_date_2():
    """Find entries between 3 and 6 days ago - should be 5"""
    create_dummy_log()
    timestamp = datetime.now() - timedelta(days=3)
    Log.mylog.critical(f"Message: New last line")
    result = mylog.find(date=timestamp, deltadays=-3)
    assert len(result) == 3, expected(3, len(result))


@create_mylog
def test_find_text_1():
    """Find text in file"""
    create_dummy_log()
    mylog.logger.info(f"Message: LasT line")
    # case insensitive
    result = mylog.find('last line')
    assert len(result) == 1, expected(1, len(result))
    assert "LasT line" in result[0], f"Instance: Incorrect last record"
    result = Log.find('last line', path='mylog.log')
    assert len(result) == 1, expected(1, len(result))
    assert "LasT line" in result[0], f"Class: Incorrect last record"
    # case sensitive
    result = mylog.find('last line', ignorecase=False)
    assert len(result) == 0, expected(0, len(result))
    result = Log.find('last line', path='mylog.log', ignorecase=False)
    assert len(result) == 0, expected(0, len(result))

@create_mylog
def test_find_text_2():
    """Find text in log"""
    create_dummy_log()
    mylog.logger.warning("This line won't be in search")
    result = mylog.find('Message')
    assert len(result) > 0, f"Instance: No records found containing 'Message'"
    for line in result:
        assert "won't" not in line, f'Instance: Found "won\'t" in "{line}"'
    result = Log.find('Message', path='mylog.log')
    assert len(result) > 0, f"Class: No records found containing 'Message'"
    for line in result:
        assert "won't" not in line, f'Class: Found "won\'t" in "{line}"'

@create_mylog
def test_find_new_path():
    """Search log with different path"""
    second_log = Path("second.log")
    create_dummy_log(path=second_log)
    timestamp = datetime.now() - timedelta(days=4)
    try:
        result = mylog.find(path=second_log, date=timestamp, deltadays=-3)
        assert len(result) == 3, f"Instance: {expected(3, len(result))}"
    finally:
        second_log.unlink()

@create_mylog
def test_find_levels():
    """Search for levels"""
    create_dummy_log()
    mylog.logger.info("Oneline")
    # Instance
    #NOT FINDING LEVELS CORRECTLY
    res = mylog.find(level="Error")
    assert len(mylog.find(level="error")) == 3, expected(3, "?")
    assert len(mylog.find(level="ERRor")) == 3, expected(3, "?")
    assert len(mylog.find(level="info")) == 6, expected(6, "?")
    assert len(mylog.find(level="InFo")) == 6, expected(6, "?")
    # Class
    assert len(Log.find(path="mylog.log", level="error")) == 3, expected(3, "?")
    assert len(Log.find(path="mylog.log", level="ERRor")) == 3, expected(3, "?")
    assert len(Log.find(path="mylog.log",level="info")) == 6, expected(6, "?")
    assert len(Log.find(path="mylog.log",level="InFo")) == 6, expected(6, "?")

@create_mylog
def test_find_by_level():
    """Find """
    create_dummy_log()
    mylog.logger.error(f"Message: Penultimate line.")
    mylog.logger.debug(f"Message: Last line of all!")
    result = mylog.find(text="error")
    assert "ERROR" in result[0], f"FIND5: ERROR message not found"
    assert len(result) == 2, expected(2, len(result))
    result = mylog.find(text="error", ignorecase=False)
    assert len(result) == 1, expected(1, len(result))
    result = mylog.find(level="info")
    assert len(result) == 6, expected(6, len(result))

def test_find_without_loglevel():
    """ fmt may not include loglevel e.g. ERROR.  Test that .find still works"""
    fmt = Log.presets['name_and_time']
    mylog = Log("mylog", to_file=True, mode="w", to_stdout=False, fmt=fmt)
    mylog("This format has no log level")
    assert len(mylog.find()) == 1
    # check class search
    assert len(Log.find(path="mylog.log")) == 1, expected(1, "?")
    cleanup()

@create_mylog
def test_find_userlevel():
    """Find a user defined level"""
    create_dummy_log()
    mylog.add_level("fail", above="warning")
    mylog.logger.fail("This is a 'fail' message")
    result = mylog.find(level="fail")
    assert len(result) == 4, expected(4, len(result))



