import mock

from py.test import raises

from bluesky.modules import fuelbeds

class TestEstimatorGetFromShape:
    pass

class TestEstimatorGetFromLatLng:
    pass

class TestEstimatorTruncation:

    def setup(self):
        fire = mock.Mock()
        self.estimator = fuelbeds.Estimator(fire)

    def test_truncate_empty_set(self):
        self.estimator.fire.fuelbeds = []
        self.estimator._truncate()
        assert [] == self.estimator.fire.fuelbeds

    def test_truncate_one_fuelbed(self):
        self.estimator.fire.fuelbeds = [{'fccs_id': 1, 'pct': 100}]
        self.estimator._truncate()
        assert [{'fccs_id': 1, 'pct': 100}] == self.estimator.fire.fuelbeds

        # a single fuelbed's percentage should never be below 100%,
        # let alone the truncation percemtage threshold, but code
        # should handle it
        pct = 99 - fuelbeds.Estimator.TRUNCATION_PERCENTAGE_THRESHOLD
        self.estimator.fire.fuelbeds = [{'fccs_id': 1, 'pct': pct}]
        self.estimator._truncate()
        assert [{'fccs_id': 1, 'pct': pct}] == self.estimator.fire.fuelbeds

    def test_truncate_multiple_fbs_no_truncation(self):
        self.estimator.fire.fuelbeds = [
            {'fccs_id': 1, 'pct': 50},
            {'fccs_id': 2, 'pct': 20},
            {'fccs_id': 3, 'pct': 30}
        ]
        self.estimator._truncate()
        expected = [
            {'fccs_id': 1, 'pct': 50},
            {'fccs_id': 3, 'pct': 30},
            {'fccs_id': 2, 'pct': 20}
        ]
        assert expected == self.estimator.fire.fuelbeds

    def test_truncate_multiple_fbs_truncated(self):
        self.estimator.fire.fuelbeds = [
            {'fccs_id': 3, 'pct': 20},
            {'fccs_id': 1, 'pct': 75},
            {'fccs_id': 2, 'pct': 5}
        ]
        self.estimator._truncate()
        expected = [
            {'fccs_id': 1, 'pct': 75},
            {'fccs_id': 3, 'pct': 20}
        ]
        assert expected == self.estimator.fire.fuelbeds
        self.estimator.fire.fuelbeds = [
            {'fccs_id': 5, 'pct': 16},
            {'fccs_id': 45, 'pct': 3},
            {'fccs_id': 1, 'pct': 75},
            {'fccs_id': 223, 'pct': 5},
            {'fccs_id': 3, 'pct': 1}
        ]
        self.estimator._truncate()
        expected = [
            {'fccs_id': 1, 'pct': 75},
            {'fccs_id': 5, 'pct': 16}
        ]
        assert expected == self.estimator.fire.fuelbeds
