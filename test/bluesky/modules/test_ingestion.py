import copy

from py.test import raises

from bluesky.modules import ingestion

class TestIngester(object):

    def setup(self):
        self.ingester = ingestion.FireIngester()

    ##
    ## Tests for _set_derived_name
    ##

    def test_set_derived_name(self):
        ## These cases whould never happen in practice, since 'location' will
        ## always be defined, but it simplifies testing these various cases

        # name already defined (noop)
        f = {"name": "Ssdfsdf"}
        self.ingester._set_derived_name(f)
        assert "Ssdfsdf" == f["name"]

        # no info
        f = {"location": {}}
        self.ingester._set_derived_name(f)
        assert "Unnamed fire" == f['name']

        # id
        f = {"location": {}, "id": "123"}
        self.ingester._set_derived_name(f)
        assert "Fire 123" == f['name']

        # event_id
        f = {"location": {}, "event_id": "345"}
        self.ingester._set_derived_name(f)
        assert "Unnamed fire from event 345" == f['name']

        # id + event_id
        f = {"location": {}, "id": "123", "event_id": "345"}
        self.ingester._set_derived_name(f)
        assert "Fire 123 from event 345" == f['name']

        ## More realistic cases

        # perimeter
        f = {
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
                }
            }
        }
        self.ingester._set_derived_name(f)
        assert "Unnamed fire near 47.43170, -121.45221" == f['name']

        # perimeter + id
        f.pop('name')
        f.update(id="123")
        self.ingester._set_derived_name(f)
        assert "Fire 123 near 47.43170, -121.45221" == f['name']

        # perimeter + id + event_id
        f.pop('name')
        f.update(event_id="345")
        self.ingester._set_derived_name(f)
        assert "Fire 123 from event 345 near 47.43170, -121.45221" == f['name']

        # perimeter + event_id
        f.pop('name')
        f.pop('id')
        self.ingester._set_derived_name(f)
        assert "Unnamed fire from event 345 near 47.43170, -121.45221" == f['name']

        # lat/lng
        f = {
            "location": {
                "latitude": 47.4316976,
                "longitude": -121.4522115
            }
        }
        self.ingester._set_derived_name(f)
        assert "Unnamed fire near 47.43170, -121.45221" == f['name']

        # perimeter + id
        f.pop('name')
        f.update(id="123")
        self.ingester._set_derived_name(f)
        assert "Fire 123 near 47.43170, -121.45221" == f['name']

        # perimeter + id + event_id
        f.pop('name')
        f.update(event_id="345")
        self.ingester._set_derived_name(f)
        assert "Fire 123 from event 345 near 47.43170, -121.45221" == f['name']

        # perimeter + event_id
        f.pop('name')
        f.pop('id')
        self.ingester._set_derived_name(f)
        assert "Unnamed fire from event 345 near 47.43170, -121.45221" == f['name']

    ##
    ## Tests For ingest
    ##

    def test_fire_missing_required_fields(self):
        with raises(ValueError) as e:
            self.ingester.ingest({})

        with raises(ValueError) as e:
            self.ingester.ingest({"location": {}})

    def test_fire_was_aready_ingested(self):
        with raises(RuntimeError) as e:
            self.ingester.ingest({'input':{}})

    def test_fire_with_minimum_fields(self):
        f = {
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
                }
            }
        }
        expected = {
            'input': copy.deepcopy(f),
            'location': copy.deepcopy(f['location']),
            "name": "Unnamed fire near 47.43170, -121.45221"
        }
        self.ingester.ingest(f)
        assert expected == f

    def test_fire_with_maximum_optional_fields(self):
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
                "end": "20150120T000000Z",
                "timezone": -0.7
            }
        }
        expected = {
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
            'input': copy.deepcopy(f),
            'location': copy.deepcopy(f['location']),
            'time': copy.deepcopy(f['time'])
        }
        self.ingester.ingest(f)
        assert expected == f

    def test_flat_fire(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
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
            "ecoregion": "southern",
            "start": "20150120T000000Z",
            "end": "20150120T000000Z",
            "timezone": -0.7
        }
        expected = {
            'input': copy.deepcopy(f),
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
            'location': {
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
                "ecoregion": "southern",
            },
            'time': {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z",
                "timezone": -0.7
            }
        }
        self.ingester.ingest(f)
        assert expected == f

    def test_flat_and_nested_fire(self):
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
                }
            },
            "ecoregion": "southern",
            "time":{
                "start": "20150120T000000Z",
                "end": "20150120T000000Z"
            },
            "timezone": -0.7
        }
        expected = {
            'input': copy.deepcopy(f),
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
            'location': {
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
            'time': {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z",
                "timezone": -0.7
            }
        }
        self.ingester.ingest(f)
        assert expected == f


    def test_fire_with_ignored_fields(self):
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
                "ecoregion": "southern",
                "foo": "bar"
            },
            "time": {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z",
                "timezone": -0.7
            },
            "bar": "baz"
        }
        expected = {
            'input': copy.deepcopy(f),
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
            'location': copy.deepcopy(f['location']),
            'time': copy.deepcopy(f['time'])
        }
        expected['location'].pop('foo')
        self.ingester.ingest(f)
        assert expected == f

    def test_fire_with_perimeter_and_lat_lng(self):
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
                "longitude": -77.379,
                "latitude": 25.041,
                "area": 200
            }
        }
        expected = {
            'input': copy.deepcopy(f),
            "id": "SF11C14225236095807750",
            "event_id": "SF11E826544",
            "name": "Natural Fire near Snoqualmie Pass, WA",
            'location': {
                'perimeter': copy.deepcopy(f['location']['perimeter'])
            }
        }
        self.ingester.ingest(f)
        assert expected == f
