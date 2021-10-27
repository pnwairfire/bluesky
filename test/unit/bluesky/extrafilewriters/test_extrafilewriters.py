from bluesky.config import Config

from bluesky.extrafilewriters import format_date_time

class TestFormatDateTime(object):

    def teardown(self):
        # TODO: figure out why this is required, even with
        #    'reset_config' in each test method's signature
        Config().reset()

    def test_default_date_time(self):
        s = format_date_time("2015-08-04T18:00:00", "-06:00", 'firescsvs')
        assert s == '20150804'

    def test_custom_date_time(self, reset_config):
        Config().set("%Y%m%d%H%M%z", 'extrafiles', 'firescsvs',
            'date_time_format')
        s = format_date_time("2015-08-04T18:00:00", "-06:00", 'firescsvs')
        assert s == '201508041800-0600'

    def test_custom_date_time_missing_offset(self, reset_config):
        Config().set("%Y%m%d%H%M%z", 'extrafiles', 'firescsvs',
            'date_time_format')
        s = format_date_time("2015-08-04T18:00:00", None, 'firescsvs')
        assert s == '201508041800'

    def test_bsf_date_time(self, reset_config):
        Config().set("%Y%m%d0000%z", 'extrafiles', 'firescsvs',
            'date_time_format')
        s = format_date_time("2015-08-04T18:00:00", "-06:00", 'firescsvs')
        assert s == '201508040000-0600'

