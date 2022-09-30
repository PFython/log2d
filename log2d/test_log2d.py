import pytest

from log2d import Log

class Test_Log:
    def test_defaults(self):
        root = Log("root")
        assert root.name == 'root'
        assert root.mode == 'a'
        assert root.path
        assert root.level == 'debug'
        assert root.fmt == '%(name)s|%(asctime)s|%(message)s'
        assert root.datefmt == '%Y-%m-%dT%H:%M:%S%z'
        assert root.to_file == False
        assert root.to_stdout == True
        assert root.backup_count == 5
        assert root.logger

    def test_shortcut(self):
        shortcut = Log("shortcut")
        shortcut("This should get logged at default log level")
