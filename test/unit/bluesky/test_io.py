"""Unit tests for bluesky.io"""

__author__ = "Joel Dubowy"

import logging
import sys
import time
from collections import defaultdict

from py.test import raises

from bluesky import io
from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError,
    BlueSkySubprocessError
)

##
## io.wait_for_availability
##

class TestWaitForAvailabilityBase():

    def setup(self):
        self.counter = 0

    def monkeypatch_sleep(self, monkeypatch):
        self.sleepcount = 0
        self.total_sleep = 0.0

        def mock_sleep(seconds):
            self.sleepcount += 1
            self.total_sleep += seconds

        monkeypatch.setattr(time, 'sleep', mock_sleep)


class TestWaitForAvailabilityBadConfig(TestWaitForAvailabilityBase):

    def test_no_valid_config_options(self):
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"foo": "bar"})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG

    def test_partial_config(self):
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed"})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"time": 1})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"max_attempts": 10})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed", "time": 1})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed", "max_attempts": 3})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"time": 1, "max_attempts": 3})
        assert e_info.value.args[0] == io.INVALID_WAIT_CONFIG_MSG

    def test_invalid_strategy(self):
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "foo",
                "time": 0.1, "max_attempts": 2})
        assert e_info.value.args[0] == io.INVALID_WAIT_STRATEGY_MSG

    def test_invalid_time(self):
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed",
                "time": "1", "max_attempts": 2})
        assert e_info.value.args[0] == io.INVALID_WAIT_TIME_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed",
                "time": -0.1, "max_attempts": 2})
        assert e_info.value.args[0] == io.INVALID_WAIT_TIME_MSG

    def test_invalid_max_attempts(self):
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed",
                "time": 0.1, "max_attempts": -2})
        assert e_info.value.args[0] == io.INVALID_WAIT_MAX_ATTEMPTS_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"strategy": "fixed",
                "time": 0.1, "max_attempts": 2.4})
        assert e_info.value.args[0] == io.INVALID_WAIT_MAX_ATTEMPTS_MSG

class TestWaitForAvailabilityDisabled(TestWaitForAvailabilityBase):

    def test_no_exception(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        io.wait_for_availability({})
        def no_exception():
            return 1

        assert no_exception() == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

    def test_bskur_error(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        io.wait_for_availability({})
        def bskur_error():
            raise BlueSkyUnavailableResourceError()

        with raises(BlueSkyUnavailableResourceError) as e_info:
            bskur_error()
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

    def test_other_error(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        io.wait_for_availability({})
        def other_error():
            raise RuntimeError()

        with raises(RuntimeError) as e_info:
            other_error()

        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

fixed_wait = io.wait_for_availability({
    "strategy": "fixed",
    "time": 2.0,
    "max_attempts": 5
})

class TestWaitForAvailabilityFixed(TestWaitForAvailabilityBase):

    def test_no_exception(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @fixed_wait
        def successful():
            self.counter += 1
            return 2

        assert successful() == 2
        assert self.counter == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

    def test_bskur_error_all(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @fixed_wait
        def bskur_error():
            self.counter += 1
            raise BlueSkyUnavailableResourceError()

        with raises(BlueSkyUnavailableResourceError) as e:
            bskur_error()

        assert self.counter == 5
        assert self.sleepcount == 4 # slept max_attempts - 1 times
        assert self.total_sleep == 8.0 # slept (max_attempts - 1) * 2.0 seconds

    def test_bskur_first_two_times(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @fixed_wait
        def bskur_error():
            self.counter += 1
            if self.counter <= 2:
                raise BlueSkyUnavailableResourceError()

        bskur_error()

        assert self.counter == 3
        assert self.sleepcount == 2
        assert self.total_sleep == 4.0 # slept 2 * 2.0 seconds

    def test_other_error(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @fixed_wait
        def other_error():
            self.counter += 1
            raise RuntimeError()

        with raises(RuntimeError) as e:
            other_error()

        assert self.counter == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

backoff_wait = io.wait_for_availability({
    "strategy": "backoff",
    "time": 2.0,
    "max_attempts": 5
})

class TestWaitForAvailabilityBackoff(TestWaitForAvailabilityBase):

    def test_no_exception(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @backoff_wait
        def successful():
            self.counter += 1
            return 2

        assert successful() == 2
        assert self.counter == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

    def test_bskur_error_all(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @backoff_wait
        def bskur_error():
            self.counter += 1
            raise BlueSkyUnavailableResourceError()

        with raises(BlueSkyUnavailableResourceError) as e:
            bskur_error()

        assert self.counter == 5
        assert self.sleepcount == 4 # slept max_attempts - 1 times
        assert self.total_sleep == 30.0 # slept 2.0+4.0+8.0+16.0

    def test_bskur_first_two_times(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @backoff_wait
        def bskur_error():
            self.counter += 1
            if self.counter <= 2:
                raise BlueSkyUnavailableResourceError()

        bskur_error()

        assert self.counter == 3
        assert self.sleepcount == 2
        assert self.total_sleep == 6.0 # slept 2.0+4.0

    def test_other_error(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)

        @backoff_wait
        def other_error():
            self.counter += 1
            raise RuntimeError()

        with raises(RuntimeError) as e:
            other_error()

        assert self.counter == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0


class TestCaptureStdout():

    def test(self):
        with io.capture_stdout() as stdout_buffer:
            assert sys.stdout == stdout_buffer
            assert "" == stdout_buffer.read()
            print("sdf")
            stdout_buffer.seek(0)
            assert "sdf\n" == stdout_buffer.read()
            sys.stdout.write("322342")
            stdout_buffer.seek(0)
            assert "sdf\n322342" == stdout_buffer.read()
            assert sys.stdout == stdout_buffer
        assert sys.stdout != stdout_buffer
        assert sys.stdout == sys.__stdout__


class TestSubprocessExecutor():

    def monkeypatch_logging(self, monkeypatch):
        self.msgs = []

        def mock_log(*args, **kwargs):
            self.msgs.append((args, kwargs))

        monkeypatch.setattr(logging, 'log', mock_log)

    def test_invalid_args(self):
        with raises(ValueError) as e_info:
            io.SubprocessExecutor().execute(123)
        assert e_info.value.args[0] == "Invalid args for SubprocessExecutor.execute: (123,)"

    ## Realtime output logging

    def test_invalid_executable_realtime_logging(self, monkeypatch):
        self.monkeypatch_logging(monkeypatch)

        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute(['sdfsdfsdf', 'sdf'], realtime_logging=True)
        assert e_info.value.args[0] == "[Errno 2] No such file or directory: 'sdfsdfsdf'"
        assert self.msgs == [
            ((logging.ERROR, '%s: %s', 'sdfsdfsdf', "No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('sdfsdfsdf', 'sdf', realtime_logging=True)
        assert e_info.value.args[0] == "[Errno 2] No such file or directory: 'sdfsdfsdf'"
        assert self.msgs == [
            ((logging.ERROR, '%s: %s', 'sdfsdfsdf', "No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('sdfsdfsdf sdf', realtime_logging=True)
        assert e_info.value.args[0] == "[Errno 2] No such file or directory: 'sdfsdfsdf'"
        assert self.msgs == [
            ((logging.ERROR, '%s: %s', 'sdfsdfsdf', "No such file or directory"), {})
        ]

    def test_invalid_command_realtime_logging(self, monkeypatch):
        self.monkeypatch_logging(monkeypatch)

        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute(['ls', 'dfjre'], realtime_logging=True)
        assert e_info.value.args[0] == "ls: cannot access 'dfjre': No such file or directory"
        assert self.msgs == [
            ((logging.ERROR, '%s: %s', 'ls', "ls: cannot access 'dfjre': No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('ls', 'dfjre', realtime_logging=True)
        assert e_info.value.args[0] == "ls: cannot access 'dfjre': No such file or directory"
        assert self.msgs == [
            ((logging.ERROR, '%s: %s', 'ls', "ls: cannot access 'dfjre': No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('ls dfjre', realtime_logging=True)
        assert e_info.value.args[0] == "ls: cannot access 'dfjre': No such file or directory"
        assert self.msgs == [
            ((logging.ERROR, '%s: %s', 'ls', "ls: cannot access 'dfjre': No such file or directory"), {})
        ]

    def test_success_realtime_logging(self, monkeypatch):
        self.monkeypatch_logging(monkeypatch)

        io.SubprocessExecutor().execute(['echo', 'hello'], realtime_logging=True)
        assert self.msgs == [
            ((10, '%s: %s', 'echo', 'hello'), {})
        ]

        self.msgs = []  # reset
        io.SubprocessExecutor().execute('echo', 'hello', realtime_logging=True)
        assert self.msgs == [
            ((10, '%s: %s', 'echo', 'hello'), {})
        ]

        self.msgs = []  # reset
        io.SubprocessExecutor().execute('echo hello', realtime_logging=True)
        assert self.msgs == [
            ((10, '%s: %s', 'echo', 'hello'), {})
        ]

    ## Post-execution output logging

    def test_invalid_executable_post_logging(self, monkeypatch):
        self.monkeypatch_logging(monkeypatch)

        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute(['lsdflsdf', 'sdf'], realtime_logging=False)
        assert e_info.value.args[0] == "[Errno 2] No such file or directory: 'lsdflsdf'"
        assert self.msgs == [
            ((40, '%s: %s', 'lsdflsdf', "No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('lsdflsdf', 'sdf', realtime_logging=False)
        assert e_info.value.args[0] == "[Errno 2] No such file or directory: 'lsdflsdf'"
        assert self.msgs == [
            ((40, '%s: %s', 'lsdflsdf', "No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('lsdflsdf sdf', realtime_logging=False)
        assert e_info.value.args[0] == "[Errno 2] No such file or directory: 'lsdflsdf'"
        assert self.msgs == [
            ((40, '%s: %s', 'lsdflsdf', "No such file or directory"), {})
        ]

    def test_invalid_command_post_logging(self, monkeypatch):
        self.monkeypatch_logging(monkeypatch)

        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute(['ls', 'dfjre'], realtime_logging=False)
        assert e_info.value.args[0] == "ls: cannot access 'dfjre': No such file or directory"
        assert self.msgs == [
            # it's DEBUG because the log-after-execution code doesn't (yet)
            # distinguish between stdout and stderr when the command returns
            # error (as opposed to trying to run an invalid executable)
            ((logging.DEBUG, '%s: %s', 'ls', "ls: cannot access 'dfjre': No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('ls', 'dfjre', realtime_logging=False)
        assert e_info.value.args[0] == "ls: cannot access 'dfjre': No such file or directory"
        assert self.msgs == [
            ((logging.DEBUG, '%s: %s', 'ls', "ls: cannot access 'dfjre': No such file or directory"), {})
        ]

        self.msgs = []  # reset
        with raises(BlueSkySubprocessError) as e_info:
            io.SubprocessExecutor().execute('ls dfjre', realtime_logging=False)
        assert e_info.value.args[0] == "ls: cannot access 'dfjre': No such file or directory"
        assert self.msgs == [
            ((logging.DEBUG, '%s: %s', 'ls', "ls: cannot access 'dfjre': No such file or directory"), {})
        ]

    def test_success_post_logging(self, monkeypatch):
        self.monkeypatch_logging(monkeypatch)

        io.SubprocessExecutor().execute(['echo', 'hello'], realtime_logging=False)
        assert self.msgs == [
            ((10, '%s: %s', 'echo', 'hello'), {})
        ]

        self.msgs = []  # reset
        io.SubprocessExecutor().execute('echo', 'hello', realtime_logging=False)
        assert self.msgs == [
            ((10, '%s: %s', 'echo', 'hello'), {})
        ]

        self.msgs = []  # reset
        io.SubprocessExecutor().execute('echo hello', realtime_logging=False)
        assert self.msgs == [
            ((10, '%s: %s', 'echo', 'hello'), {})
        ]
