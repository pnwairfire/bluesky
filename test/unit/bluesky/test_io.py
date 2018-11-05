"""Unit tests for bluesky.io"""

__author__ = "Joel Dubowy"

import time

from py.test import raises

from bluesky import io
from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)

##
## io.wait_for_availability
##

class TestWaitForAvailabilityBase(object):

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

        successful()
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

        successful()
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
