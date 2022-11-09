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

def stop_handler(logger):
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()

def test_defaults():
    main = Log("main")
    assert main.name == 'main'
    assert main.mode == 'a'
    assert main.path
    assert main.level == 'debug'
    assert main.fmt == '%(name)s|%(levelname)-7s|%(asctime)s|%(message)s'
    assert main.datefmt == '%Y-%m-%dT%H:%M:%S%z'
    assert main.to_file == False
    assert main.to_stdout == True
    assert main.backup_count == 5
    assert main.logger

def test_file_log():
    test_log = Log("Test", to_file=True, to_stdout=False)
    test_log("Entry 1")
    path = Path("Test.log")
    assert path.is_file()
    assert path.read_text().endswith("|Entry 1\n")
    stop_handler(Log.Test)
    path.unlink()

def test_shortcut():
    shortcut = Log("shortcut")


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