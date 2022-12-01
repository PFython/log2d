import pytest

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
    lg = Log("testlog")
    success = lg.add_level("Success", above="INFO")
    assert success == "New log level 'success' added with value: 21"
    fail = lg.add_level("Fail", above="SUCCESS")
    assert fail == "New log level 'fail' added with value: 22"

    msg = "This should appear in all log levels above DEBUG"
    lg.logger.success(f"{msg}: Success!")
    lg.logger.info(f"{msg}: Info!")
    lg.logger.fail(f"{msg}: Fail!")

    lg.logger.setLevel('CRITICAL')
    msg = "This should NOT appear in log levels below CRITICAL"
    lg.logger.success(f"{msg}: Success!")
    lg.logger.info(f"{msg}: Info!")
    lg.logger.fail(f"{msg}: Fail!")

   
def test_find() -> bool:
    """Testing find method"""
    _log = "findlog"
    _HPath="."

    _fn = os.path.join(_HPath, _log + ".log")
    # remove existing log
    try:
        os.remove(_fn)
    except:
        pass

    lg = Log(_log)
    lg.logger.info("A log message - console only")
    Res = lg.find()
    assert Res[0][:14] == "No log file at", f"FIND1: Found a log file - should be absent!"

    # Create dummy log
    aWhileAgo = datetime.now()- timedelta(days=8)
    with open(_fn, "w") as dummyLog:
        for I in range(6):
            T = aWhileAgo + timedelta(days=I)
            dummyLog.write(f"dummylg|INFO    |{T.strftime('%Y-%m-%dT%H:%M:%S%z+0000')}|Log message\n") 
        dummyLog.write("  Here is additional line 1\n   Additional line 2 followed by a blank line\n\n")

    lg = Log(_log, path=_HPath)
    msg ="Should be line in log"
    lg.logger.info(f"{msg}: Last line")
    Res = lg.find()
    assert ": Last line" in Res[-1], f"FIND2: Incorrect last record"
    sleep(1)  # wait a bit
    T = datetime.now()
    sleep(1)
    lg.logger.critical(f"{msg}: New last line")
    # Search from T:+1day
    Res = lg.find(date=T, deltadays=1)
    assert len(Res) == 1, f"FIND3: Expected 1 record, found {len(Res)}"
    assert "CRITICAL" in Res[0], f"FIND4: CRITICAL message not found"

    lg.logger.error(f"{msg}: Yet another last line")
    Res = lg.find(text="error")
    assert "ERROR" in Res[0], f"FIND5: ERROR message not found"
    Res = lg.find(text="error", ignorecase=False)
    assert not Res
    Res = lg.find(level="error")
    assert len(Res) == 2, f"FIND6: Expected 2 records, found {len(Res)}"

    # Text searches
    lg.logger.warning("This line won't be in search")
    Res = lg.find('should')
    assert len(Res) > 0, f"FIND7: 'Should' not found"
    for ln in Res:
        assert "won't" not in ln, f'FIND8: Found "Won\'t" in "{ln}"'
    Res = lg.find("should", ignorecase=False)
    assert not Res, f"FIND9: Found 'Should' with case sensitive search"
    Res = lg.find(text='new')
    assert len(Res) == 1, f"FIND10: Expected 1 record, found {len(Res)}"

    # Search -5 to -8 days ago
    T -= timedelta(days=3)
    Res = lg.find(date=T, deltadays=-3)
    assert len(Res) == 6, f"FIND11: Olddates - Expected 6 records, got {len(Res)}"
    assert not Res[-1], f"FIND12: olddates - found last record was '{Res[-1]}''"
    Res2 = lg.find(date=T, deltadays=-3, autoparse=True)
    assert Res == Res2, f"FIND13: Autoparse - Gives different result"

    lg1 = Log('anotherlog')
    Res = lg1.find(logname=_fn, date=T, deltadays=-3)
    assert len(Res) == 6, f"FIND14: Anotherlog - Expected 6 lines found {len(Res)}"
    assert not Res[-1], f"FIND15: Anotherlog - found last line was '{Res[-1]}'"

    # Tidy up if OK
    os.remove(_fn)

    print("FIND passes 15 tests OK")
    return True