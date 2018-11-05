"""Unit tests for bluesky.io"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky import io
from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)

##
## io.wait_for_availability
##

class TestWaitForAvailabilityBadConfig(object):

    def test_no_valid_config_options(self):
        with raises(BlueSkyConfigurationError) as e_info:
            io.wait_for_availability({"foo": bar})
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

class TestWaitForAvailabilityDisabled(object):

    def test_no_exception(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        io.wait_for_availability({})
        def no_exception():
            return 1
        assert no_exception() == 1
        assert sleepcount == 0
        assert total_sleep == 0.0

    def test_bskur_error(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        io.wait_for_availability({})
        def bskur_error():
            raise BlueSkyUnavailableResourceError()

        with raises(BlueSkyUnavailableResourceError) as e_info:
            bskur_error()
        assert sleepcount == 0
        assert total_sleep == 0.0

    def test_other_error(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        io.wait_for_availability({})
        def other_error():
            raise RuntimeError()

        with raises(RuntimeError) as e_info:
            other_error()
        assert sleepcount == 0
        assert total_sleep == 0.0

class TestWaitForAvailabilityFixed(object):

    def setup(self):
        self.wait_decorator = io.wait_for_availability({
            "strategy": "fixed",
            "time": 0.01,
            "max_attempts": 5
        })

    def test_no_exception(self, monkeypatch):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def successful():
            counter += 1

        successful()
        assert counter == 1
        assert sleepcount == 0
        assert total_sleep == 0.0

    def test_bskur_error_all(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def bskur_error():
            counter += 1
            raise BlueSkyUnavailableResourceError()
        bskur_error()
        assert counter = 5
        assert sleepcount == 4 # slept max_attempts - 1 times
        assert total_sleep == 0.04 # slept (max_attempts - 1) * 0.01 seconds

    def test_bskur_first_two_times(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def bskur_error():
            counter += 1
            if counter <= 2:
                raise BlueSkyUnavailableResourceError()
        bskur_error()
        assert counter = 2
        assert sleepcount == 2
        assert total_sleep == 0.02 # slept 2 * 0.01 seconds

    def test_other_error(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def other_error():
            counter += 1
            raise RuntimeError()
        bskur_error()
        assert counter = 1
        assert sleepcount == 0
        assert total_sleep == 0.0


class TestWaitForAvailabilityBackoff(object):

    def setup(self):
        self.wait_decorator = io.wait_for_availability({
            "strategy": "test_backoff_wait",
            "time": 0.01,
            "max_attempts": 5
        })

    def test_no_exception(self, monkeypatch):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def successful():
            counter += 1

        successful()
        assert counter == 1
        assert sleepcount == 0
        assert total_sleep == 0.0

    def test_bskur_error_all(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def bskur_error():
            counter += 1
            raise BlueSkyUnavailableResourceError()
        bskur_error()
        assert counter = 5
        assert sleepcount == 4 # slept max_attempts - 1 times
        assert total_sleep == 0.15 # slept 0.01+0.02+0.04+0.08

    def test_bskur_first_two_times(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def bskur_error():
            counter += 1
            if counter <= 2:
                raise BlueSkyUnavailableResourceError()
        bskur_error()
        assert counter = 2
        assert sleepcount == 2
        assert total_sleep == 0.03 # slept 0.01+0.02

    def test_other_error(self):
        sleepcount = 0
        total_sleep = 0.0
        monkeypatch.setattr(time, 'sleep', lambda i: sleepcount+=1, total_sleep+=i)

        counter = 0
        @self.wait_decorator
        def other_error():
            counter += 1
            raise RuntimeError()
        bskur_error()
        assert counter = 1
        assert sleepcount == 0
        assert total_sleep == 0.0
