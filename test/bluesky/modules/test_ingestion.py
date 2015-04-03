from py.test import raises

from bluesky.modules import ingestion

class TestIngester(object):

    def setup(self):
        self.ingester = ingestion.Ingester()

    def test_fire_missing_required_fields(self):
        with raises(ValueError) as e:
            self.ingester.ingest({})

        with raises(ValueError) as e:
            self.ingester.ingest({"location": {}})
        assert expected = self.ingester.ingest({})

    def test_fire_was_aready_ingested(self):
        with raises(RuntimeError) as e:
            self.ingester.ingest({'input':{}})

    def test_fire_with_minimum_fields(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
            "location": {
                "perimeter": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [-121.4522115, 47.4316976],
                                [-121.3990506, 47.4316976],
                                [-121.3990506, 47.4099293],
                                [-121.4522115, 47.4099293],
                                [-121.4522115, 47.4316976]
                            ]
                        ]
                    ]
                },
                "ecoregion": "southern"
            },
            "time": {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z"
            }
        }
        # TODO: implement...

    def test_fire_with_maximum_optional_fields(self):
        pass

    def test_fire_with_ignored_fields(self):
        pass

    def test_fire_with_perimeter_and_lat_lng(self):
        pass

