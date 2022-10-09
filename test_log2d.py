import pytest
from pathlib import Path

from log2d import Log

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
    shortcut("This should get logged at default log level")

def test_multiples(capfd):
    progress_log = Log("Progress", to_file=True)
    progress_log("Starting")
    out, err = capfd.readouterr()
    assert out.endswith("Starting\n")
    selenium_log = Log("Selenium", to_file=True, to_stdout=False)
    selenium_log("Started")
    out, err = capfd.readouterr()
    assert out == ""

    http_log = Log("HTTP", to_file=True, to_stdout=False)
    timing_log = Log("Timing", to_file=True, to_stdout=False)
    retry_log = Log("Retry", to_file=True, to_stdout=False)

def test_coexist_with_logging():
    import logging
    logging.warning("This creates a 'root' logger")
    from log2d import Log
    other = Log("other")
    other("This will be echoed twice - 'root' and 'other'")
    Log.disable_rootlogger()
    other("This should only appear once now")
