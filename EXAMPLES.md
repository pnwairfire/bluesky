# Examples

The examples listed here are based on **proposed** changes to the code base.  They
do not represent the current behavior.

## Through Emissions

Assume you have the following input data:

    {
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "growth": [
                    {
                        "start": "2015-01-20T17:00:00",
                        "end": "2015-01-21T17:00:00",
                        "location": {
                            "geojson": {
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
                            "utc_offset": "-09:00"
                        }
                    },
                    {
                        "pct": 40,
                        "start": "20150121",
                        "end": "20150122",
                        "location": {
                            "geojson": {
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
                            "utc_offset": "-09:00"
                        }
                    }
                ]
            }
        ]
    }

Lets say that's in a file called locations.json. piping that into bsp
and running it through ingestion

    cat ./tmp/locations.json | bsp ingestion

would give you:


    {
        "today": "2016-09-15",
        "fire_information": [
            {
                "growth": [
                    {
                        "location": {
                            "ecoregion": "southern",
                            "geojson": {
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ],
                                "type": "MultiPolygon"
                            },
                            "utc_offset": "-09:00"
                        },
                        "end": "2015-01-21T17:00:00",
                        "start": "2015-01-20T17:00:00"
                    },
                    {
                        "location": {
                            "ecoregion": "southern",
                            "geojson": {
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ],
                                "type": "MultiPolygon"
                            },
                            "utc_offset": "-09:00"
                        },
                        "end": "20150122",
                        "start": "20150121"
                    }
                ],
                "fuel_type": "natural",
                "type": "wildfire",
                "event_of": {
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "id": "SF11C14225236095807750"
            }
        ],
        "processing": [
            {
                "module": "bluesky.modules.ingestion",
                "version": "0.1.0",
                "parsed_input": [
                    {
                        "growth": [
                            {
                                "location": {
                                    "ecoregion": "southern",
                                    "geojson": {
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ],
                                        "type": "MultiPolygon"
                                    },
                                    "utc_offset": "-09:00"
                                },
                                "end": "2015-01-21T17:00:00",
                                "start": "2015-01-20T17:00:00"
                            },
                            {
                                "location": {
                                    "ecoregion": "southern",
                                    "geojson": {
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ],
                                        "type": "MultiPolygon"
                                    },
                                    "utc_offset": "-09:00"
                                },
                                "end": "20150122",
                                "start": "20150121",
                                "pct": 40
                            }
                        ],
                        "fuel_type": "natural",
                        "type": "wildfire",
                        "event_of": {
                            "name": "Natural Fire near Snoqualmie Pass, WA",
                            "id": "SF11E826544"
                        },
                        "id": "SF11C14225236095807750"
                    }
                ],
                "module_name": "ingestion"
            }
        ],
        "runtime": {
            "end": "2016-09-15T18:27:22Z",
            "modules": [
                {
                    "total": "0.0h 0.0m 0s",
                    "end": "2016-09-15T18:27:22Z",
                    "start": "2016-09-15T18:27:22Z",
                    "module_name": "ingestion"
                }
            ],
            "start": "2016-09-15T18:27:22Z",
            "total": "0.0h 0.0m 0s"
        },
        "config": {}
    }


Piping that through fuelbeds

    cat ./tmp/locations.json | bsp ingestion fuelbeds
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds

would give you:

    {
        "today": "2016-09-15",
        "summary": {
            "fuelbeds": [
                {
                    "pct": 100.0,
                    "fccs_id": "9"
                }
            ]
        },
        "processing": [
            {
                "version": "0.1.0",
                "module_name": "ingestion",
                "parsed_input": [
                    {
                        "event_of": {
                            "name": "Natural Fire near Snoqualmie Pass, WA",
                            "id": "SF11E826544"
                        },
                        "growth": [
                            {
                                "start": "2015-01-20T17:00:00",
                                "location": {
                                    "utc_offset": "-09:00",
                                    "geojson": {
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ],
                                        "type": "MultiPolygon"
                                    },
                                    "ecoregion": "southern"
                                },
                                "end": "2015-01-21T17:00:00"
                            },
                            {
                                "pct": 40,
                                "end": "20150122",
                                "location": {
                                    "utc_offset": "-09:00",
                                    "geojson": {
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ],
                                        "type": "MultiPolygon"
                                    },
                                    "ecoregion": "southern"
                                },
                                "start": "20150121"
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "type": "wildfire",
                        "fuel_type": "natural"
                    }
                ],
                "module": "bluesky.modules.ingestion"
            },
            {
                "version": "0.1.0",
                "module_name": "fuelbeds",
                "module": "bluesky.modules.fuelbeds",
                "fccsmap_version": "1.0.1"
            }
        ],
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_of": {
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "fuel_type": "natural",
                "growth": [
                    {
                        "start": "2015-01-20T17:00:00",
                        "fuelbeds": [
                            {
                                "pct": 100.0,
                                "fccs_id": "9"
                            }
                        ],
                        "location": {
                            "utc_offset": "-09:00",
                            "geojson": {
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ],
                                "type": "MultiPolygon"
                            },
                            "area": 2398.94477979842,
                            "ecoregion": "southern"
                        },
                        "end": "2015-01-21T17:00:00"
                    },
                    {
                        "start": "20150121",
                        "fuelbeds": [
                            {
                                "pct": 100.0,
                                "fccs_id": "9"
                            }
                        ],
                        "location": {
                            "utc_offset": "-09:00",
                            "geojson": {
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ],
                                "type": "MultiPolygon"
                            },
                            "area": 2398.94477979842,
                            "ecoregion": "southern"
                        },
                        "end": "20150122"
                    }
                ],
                "type": "wildfire"
            }
        ],
        "runtime": {
            "modules": [
                {
                    "module_name": "ingestion",
                    "total": "0.0h 0.0m 0s",
                    "end": "2016-09-15T18:28:07Z",
                    "start": "2016-09-15T18:28:07Z"
                },
                {
                    "module_name": "fuelbeds",
                    "total": "0.0h 0.0m 0s",
                    "end": "2016-09-15T18:28:07Z",
                    "start": "2016-09-15T18:28:07Z"
                }
            ],
            "total": "0.0h 0.0m 0s",
            "end": "2016-09-15T18:28:07Z",
            "start": "2016-09-15T18:28:07Z"
        },
        "config": {}
    }

Piping that through consumption

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption

would give you:

    {
        "summary": {
            "heat": {
                "summary": {
                    "total": 1848147827041.6133,
                    "smoldering": 495568890902.2825,
                    "residual": 663626316677.9128,
                    "flaming": 688952619461.4178
                },
                "smoldering": [
                    495568890902.2825
                ],
                "residual": [
                    663626316677.9128
                ],
                "flaming": [
                    688952619461.4178
                ]
            },
            "fuelbeds": [
                {
                    "fccs_id": "9",
                    "pct": 100.0
                }
            ],
            "consumption": {
                "ground fuels": {
                    "squirrel middens": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "duff upper": {
                        "smoldering": [
                            5198.412774058008
                        ],
                        "residual": [
                            1485.2607925880022
                        ],
                        "flaming": [
                            742.6303962940011
                        ]
                    },
                    "basal accumulations": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "duff lower": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    }
                },
                "summary": {
                    "total": 115509.2391901008,
                    "smoldering": 30973.055681392656,
                    "residual": 41476.64479236955,
                    "flaming": 43059.538716338604
                },
                "woody fuels": {
                    "1000-hr fuels rotten": {
                        "smoldering": [
                            1076.4419085167058
                        ],
                        "residual": [
                            1794.069847527843
                        ],
                        "flaming": [
                            717.6279390111373
                        ]
                    },
                    "stumps rotten": {
                        "smoldering": [
                            1066.935008915951
                        ],
                        "residual": [
                            2133.870017831902
                        ],
                        "flaming": [
                            355.64500297198356
                        ]
                    },
                    "stumps lightered": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "10000-hr fuels rotten": {
                        "smoldering": [
                            5561.213893382337
                        ],
                        "residual": [
                            11122.427786764674
                        ],
                        "flaming": [
                            1853.737964460779
                        ]
                    },
                    "stumps sound": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "10-hr fuels": {
                        "smoldering": [
                            1079.0453619533293
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            9711.408257579964
                        ]
                    },
                    "10k+-hr fuels sound": {
                        "smoldering": [
                            2354.065749083506
                        ],
                        "residual": [
                            2354.065749083506
                        ],
                        "flaming": [
                            1177.032874541753
                        ]
                    },
                    "100-hr fuels": {
                        "smoldering": [
                            482.4277952174623
                        ],
                        "residual": [
                            241.21389760873114
                        ],
                        "flaming": [
                            4100.636259348429
                        ]
                    },
                    "1-hr fuels": {
                        "smoldering": [
                            359.841716969763
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            6836.992622425496
                        ]
                    },
                    "1000-hr fuels sound": {
                        "smoldering": [
                            386.1664508783488
                        ],
                        "residual": [
                            128.72215029278294
                        ],
                        "flaming": [
                            772.3329017566977
                        ]
                    },
                    "piles": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "10k+-hr fuels rotten": {
                        "smoldering": [
                            10680.970072170296
                        ],
                        "residual": [
                            21361.94014434059
                        ],
                        "flaming": [
                            3560.3233573900993
                        ]
                    },
                    "10000-hr fuels sound": {
                        "smoldering": [
                            1710.1488126630436
                        ],
                        "residual": [
                            855.0744063315218
                        ],
                        "flaming": [
                            1710.1488126630436
                        ]
                    }
                },
                "shrub": {
                    "primary dead": {
                        "smoldering": [
                            58.8490499005718
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            529.6414491051462
                        ]
                    },
                    "secondary live": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "primary live": {
                        "smoldering": [
                            166.7389747182867
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            3168.0405196474476
                        ]
                    },
                    "secondary dead": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    }
                },
                "litter-lichen-moss": {
                    "litter": {
                        "smoldering": [
                            722.0823787193243
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            6498.741408473919
                        ]
                    },
                    "lichen": {
                        "smoldering": [
                            0.359841716969763
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            6.836992622425496
                        ]
                    },
                    "moss": {
                        "smoldering": [
                            35.9841716969763
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            683.6992622425496
                        ]
                    }
                },
                "nonwoody": {
                    "primary dead": {
                        "smoldering": [
                            3.3371720831775806
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            63.40626958037403
                        ]
                    },
                    "secondary live": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "primary live": {
                        "smoldering": [
                            30.034548748598233
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            570.6564262233663
                        ]
                    },
                    "secondary dead": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    }
                },
                "canopy": {
                    "understory": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "ladder fuels": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "overstory": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "snags class 3": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "snags class 2": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "snags class 1 wood": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "snags class 1 no foliage": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "snags class 1 foliage": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    },
                    "midstory": {
                        "smoldering": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "flaming": [
                            0.0
                        ]
                    }
                }
            }
        },
        "fire_information": [
            {
                "consumption": {
                    "summary": {
                        "total": 115509.2391901008,
                        "smoldering": 30973.055681392656,
                        "residual": 41476.64479236955,
                        "flaming": 43059.538716338604
                    }
                },
                "growth": [
                    {
                        "end": "2015-01-21T17:00:00",
                        "consumption": {
                            "summary": {
                                "total": 57754.619595050404,
                                "smoldering": 15486.52784069633,
                                "residual": 20738.322396184776,
                                "flaming": 21529.769358169306
                            }
                        },
                        "location": {
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ]
                            },
                            "utc_offset": "-09:00",
                            "area": 2398.94477979842,
                            "ecoregion": "southern"
                        },
                        "heat": {
                            "summary": {
                                "total": 924073913520.8066,
                                "smoldering": 247784445451.14124,
                                "residual": 331813158338.9564,
                                "flaming": 344476309730.7089
                            }
                        },
                        "fuelbeds": [
                            {
                                "fccs_id": "9",
                                "pct": 100.0,
                                "consumption": {
                                    "ground fuels": {
                                        "squirrel middens": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "duff lower": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "basal accumulations": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "duff upper": {
                                            "total": [
                                                3713.151981470006
                                            ],
                                            "smoldering": [
                                                2599.206387029004
                                            ],
                                            "residual": [
                                                742.6303962940011
                                            ],
                                            "flaming": [
                                                371.31519814700056
                                            ]
                                        }
                                    },
                                    "summary": {
                                        "ground fuels": {
                                            "total": [
                                                3713.151981470006
                                            ],
                                            "smoldering": [
                                                2599.206387029004
                                            ],
                                            "residual": [
                                                742.6303962940011
                                            ],
                                            "flaming": [
                                                371.31519814700056
                                            ]
                                        },
                                        "woody fuels": {
                                            "total": [
                                                47772.26338084084
                                            ],
                                            "smoldering": [
                                                12378.628384875372
                                            ],
                                            "residual": [
                                                19995.691999890776
                                            ],
                                            "flaming": [
                                                15397.942996074695
                                            ]
                                        },
                                        "shrub": {
                                            "total": [
                                                1961.634996685726
                                            ],
                                            "smoldering": [
                                                112.79401230942925
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                1848.8409843762968
                                            ]
                                        },
                                        "litter-lichen-moss": {
                                            "total": [
                                                3973.852027736082
                                            ],
                                            "smoldering": [
                                                379.2131960666352
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3594.6388316694474
                                            ]
                                        },
                                        "total": {
                                            "total": [
                                                57754.61959505041
                                            ],
                                            "smoldering": [
                                                15486.527840696328
                                            ],
                                            "residual": [
                                                20738.32239618478
                                            ],
                                            "flaming": [
                                                21529.76935816931
                                            ]
                                        },
                                        "nonwoody": {
                                            "total": [
                                                333.71720831775815
                                            ],
                                            "smoldering": [
                                                16.685860415887905
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                317.0313479018702
                                            ]
                                        },
                                        "canopy": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "woody fuels": {
                                        "10k+-hr fuels rotten": {
                                            "total": [
                                                17801.616786950493
                                            ],
                                            "smoldering": [
                                                5340.485036085148
                                            ],
                                            "residual": [
                                                10680.970072170296
                                            ],
                                            "flaming": [
                                                1780.1616786950497
                                            ]
                                        },
                                        "stumps rotten": {
                                            "total": [
                                                1778.225014859918
                                            ],
                                            "smoldering": [
                                                533.4675044579755
                                            ],
                                            "residual": [
                                                1066.935008915951
                                            ],
                                            "flaming": [
                                                177.82250148599178
                                            ]
                                        },
                                        "stumps lightered": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "10000-hr fuels rotten": {
                                            "total": [
                                                9268.689822303895
                                            ],
                                            "smoldering": [
                                                2780.6069466911686
                                            ],
                                            "residual": [
                                                5561.213893382337
                                            ],
                                            "flaming": [
                                                926.8689822303895
                                            ]
                                        },
                                        "stumps sound": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "10-hr fuels": {
                                            "total": [
                                                5395.2268097666465
                                            ],
                                            "smoldering": [
                                                539.5226809766647
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                4855.704128789982
                                            ]
                                        },
                                        "10k+-hr fuels sound": {
                                            "total": [
                                                2942.5821863543824
                                            ],
                                            "smoldering": [
                                                1177.032874541753
                                            ],
                                            "residual": [
                                                1177.032874541753
                                            ],
                                            "flaming": [
                                                588.5164372708765
                                            ]
                                        },
                                        "100-hr fuels": {
                                            "total": [
                                                2412.138976087311
                                            ],
                                            "smoldering": [
                                                241.21389760873114
                                            ],
                                            "residual": [
                                                120.60694880436557
                                            ],
                                            "flaming": [
                                                2050.3181296742146
                                            ]
                                        },
                                        "1-hr fuels": {
                                            "total": [
                                                3598.41716969763
                                            ],
                                            "smoldering": [
                                                179.9208584848815
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3418.496311212748
                                            ]
                                        },
                                        "1000-hr fuels sound": {
                                            "total": [
                                                643.6107514639145
                                            ],
                                            "smoldering": [
                                                193.0832254391744
                                            ],
                                            "residual": [
                                                64.36107514639147
                                            ],
                                            "flaming": [
                                                386.1664508783488
                                            ]
                                        },
                                        "piles": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "1000-hr fuels rotten": {
                                            "total": [
                                                1794.069847527843
                                            ],
                                            "smoldering": [
                                                538.2209542583529
                                            ],
                                            "residual": [
                                                897.0349237639215
                                            ],
                                            "flaming": [
                                                358.81396950556865
                                            ]
                                        },
                                        "10000-hr fuels sound": {
                                            "total": [
                                                2137.6860158288046
                                            ],
                                            "smoldering": [
                                                855.0744063315218
                                            ],
                                            "residual": [
                                                427.5372031657609
                                            ],
                                            "flaming": [
                                                855.0744063315218
                                            ]
                                        }
                                    },
                                    "shrub": {
                                        "primary dead": {
                                            "total": [
                                                294.245249502859
                                            ],
                                            "smoldering": [
                                                29.4245249502859
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                264.8207245525731
                                            ]
                                        },
                                        "secondary live": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "primary live": {
                                            "total": [
                                                1667.3897471828673
                                            ],
                                            "smoldering": [
                                                83.36948735914335
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                1584.0202598237238
                                            ]
                                        },
                                        "secondary dead": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "litter-lichen-moss": {
                                        "lichen": {
                                            "total": [
                                                3.5984171696976297
                                            ],
                                            "smoldering": [
                                                0.1799208584848815
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3.418496311212748
                                            ]
                                        },
                                        "litter": {
                                            "total": [
                                                3610.4118935966217
                                            ],
                                            "smoldering": [
                                                361.04118935966216
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3249.3707042369597
                                            ]
                                        },
                                        "moss": {
                                            "total": [
                                                359.84171696976296
                                            ],
                                            "smoldering": [
                                                17.99208584848815
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                341.8496311212748
                                            ]
                                        }
                                    },
                                    "nonwoody": {
                                        "primary dead": {
                                            "total": [
                                                33.371720831775804
                                            ],
                                            "smoldering": [
                                                1.6685860415887903
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                31.703134790187015
                                            ]
                                        },
                                        "secondary live": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "primary live": {
                                            "total": [
                                                300.3454874859823
                                            ],
                                            "smoldering": [
                                                15.017274374299117
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                285.32821311168317
                                            ]
                                        },
                                        "secondary dead": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "canopy": {
                                        "understory": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "ladder fuels": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "overstory": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 3": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 2": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 wood": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 no foliage": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 foliage": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "midstory": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    }
                                },
                                "heat": {
                                    "total": [
                                        924073913520.8066
                                    ],
                                    "smoldering": [
                                        247784445451.14124
                                    ],
                                    "residual": [
                                        331813158338.9564
                                    ],
                                    "flaming": [
                                        344476309730.7089
                                    ]
                                },
                                "fuel_loadings": {
                                    "nw_primary_loading": 0.15,
                                    "duff_upper_loading": 11.52,
                                    "snags_c3_loading": 3.445935,
                                    "ecoregion": 240.0,
                                    "shrubs_secondary_loading": 0.0,
                                    "cover_type": 135,
                                    "w_sound_3_9_loading": 2.0,
                                    "w_stump_rotten_loading": 1.4825059999999999,
                                    "w_sound_gt20_loading": 7.0,
                                    "efg_activity": 1,
                                    "moss_loading": 0.15,
                                    "duff_lower_depth": 0.0,
                                    "snags_c2_loading": 4.594579,
                                    "duff_lower_loading": 0.0,
                                    "w_sound_0_quarter_loading": 1.5,
                                    "pile_vdirty_loading": 0.0,
                                    "w_sound_1_3_loading": 2.5,
                                    "lichen_depth": 0.1,
                                    "w_sound_quarter_1_loading": 2.6,
                                    "ladderfuels_loading": 0.5,
                                    "understory_loading": 2.406917,
                                    "snags_c1_foliage_loading": 0.0,
                                    "duff_upper_depth": 1.5,
                                    "w_rotten_9_20_loading": 8.0,
                                    "squirrel_midden_loading": 0.0,
                                    "efg_natural": 8,
                                    "filename": "FB_0009_FCCS.xml",
                                    "w_rotten_gt20_loading": 20.0,
                                    "w_stump_sound_loading": 0.0,
                                    "total_available_fuel_loading": 89.222305,
                                    "nw_secondary_loading": 0.0,
                                    "basal_accum_loading": 0.0,
                                    "litter_loading": 1.505,
                                    "pile_dirty_loading": 0.0,
                                    "shrubs_secondary_perc_live": 0.0,
                                    "midstory_loading": 0.0,
                                    "snags_c1wo_foliage_loading": 0.0,
                                    "overstory_loading": 8.193636,
                                    "snags_c1_wood_loading": 0.0,
                                    "w_rotten_3_9_loading": 4.7,
                                    "litter_depth": 0.5,
                                    "w_sound_9_20_loading": 3.7,
                                    "lichen_loading": 0.0015,
                                    "moss_depth": 0.5,
                                    "nw_primary_perc_live": 0.9,
                                    "nw_secondary_perc_live": 0.0,
                                    "shrubs_primary_loading": 1.7447560000000002,
                                    "shrubs_primary_perc_live": 0.85,
                                    "pile_clean_loading": 0.027473,
                                    "w_stump_lightered_loading": 0.0
                                }
                            }
                        ],
                        "start": "2015-01-20T17:00:00"
                    },
                    {
                        "end": "20150122",
                        "consumption": {
                            "summary": {
                                "total": 57754.619595050404,
                                "smoldering": 15486.52784069633,
                                "residual": 20738.322396184776,
                                "flaming": 21529.769358169306
                            }
                        },
                        "location": {
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ]
                            },
                            "utc_offset": "-09:00",
                            "area": 2398.94477979842,
                            "ecoregion": "southern"
                        },
                        "heat": {
                            "summary": {
                                "total": 924073913520.8066,
                                "smoldering": 247784445451.14124,
                                "residual": 331813158338.9564,
                                "flaming": 344476309730.7089
                            }
                        },
                        "fuelbeds": [
                            {
                                "fccs_id": "9",
                                "pct": 100.0,
                                "consumption": {
                                    "ground fuels": {
                                        "squirrel middens": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "duff lower": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "basal accumulations": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "duff upper": {
                                            "total": [
                                                3713.151981470006
                                            ],
                                            "smoldering": [
                                                2599.206387029004
                                            ],
                                            "residual": [
                                                742.6303962940011
                                            ],
                                            "flaming": [
                                                371.31519814700056
                                            ]
                                        }
                                    },
                                    "summary": {
                                        "ground fuels": {
                                            "total": [
                                                3713.151981470006
                                            ],
                                            "smoldering": [
                                                2599.206387029004
                                            ],
                                            "residual": [
                                                742.6303962940011
                                            ],
                                            "flaming": [
                                                371.31519814700056
                                            ]
                                        },
                                        "woody fuels": {
                                            "total": [
                                                47772.26338084084
                                            ],
                                            "smoldering": [
                                                12378.628384875372
                                            ],
                                            "residual": [
                                                19995.691999890776
                                            ],
                                            "flaming": [
                                                15397.942996074695
                                            ]
                                        },
                                        "shrub": {
                                            "total": [
                                                1961.634996685726
                                            ],
                                            "smoldering": [
                                                112.79401230942925
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                1848.8409843762968
                                            ]
                                        },
                                        "litter-lichen-moss": {
                                            "total": [
                                                3973.852027736082
                                            ],
                                            "smoldering": [
                                                379.2131960666352
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3594.6388316694474
                                            ]
                                        },
                                        "total": {
                                            "total": [
                                                57754.61959505041
                                            ],
                                            "smoldering": [
                                                15486.527840696328
                                            ],
                                            "residual": [
                                                20738.32239618478
                                            ],
                                            "flaming": [
                                                21529.76935816931
                                            ]
                                        },
                                        "nonwoody": {
                                            "total": [
                                                333.71720831775815
                                            ],
                                            "smoldering": [
                                                16.685860415887905
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                317.0313479018702
                                            ]
                                        },
                                        "canopy": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "woody fuels": {
                                        "10k+-hr fuels rotten": {
                                            "total": [
                                                17801.616786950493
                                            ],
                                            "smoldering": [
                                                5340.485036085148
                                            ],
                                            "residual": [
                                                10680.970072170296
                                            ],
                                            "flaming": [
                                                1780.1616786950497
                                            ]
                                        },
                                        "stumps rotten": {
                                            "total": [
                                                1778.225014859918
                                            ],
                                            "smoldering": [
                                                533.4675044579755
                                            ],
                                            "residual": [
                                                1066.935008915951
                                            ],
                                            "flaming": [
                                                177.82250148599178
                                            ]
                                        },
                                        "stumps lightered": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "10000-hr fuels rotten": {
                                            "total": [
                                                9268.689822303895
                                            ],
                                            "smoldering": [
                                                2780.6069466911686
                                            ],
                                            "residual": [
                                                5561.213893382337
                                            ],
                                            "flaming": [
                                                926.8689822303895
                                            ]
                                        },
                                        "stumps sound": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "10-hr fuels": {
                                            "total": [
                                                5395.2268097666465
                                            ],
                                            "smoldering": [
                                                539.5226809766647
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                4855.704128789982
                                            ]
                                        },
                                        "10k+-hr fuels sound": {
                                            "total": [
                                                2942.5821863543824
                                            ],
                                            "smoldering": [
                                                1177.032874541753
                                            ],
                                            "residual": [
                                                1177.032874541753
                                            ],
                                            "flaming": [
                                                588.5164372708765
                                            ]
                                        },
                                        "100-hr fuels": {
                                            "total": [
                                                2412.138976087311
                                            ],
                                            "smoldering": [
                                                241.21389760873114
                                            ],
                                            "residual": [
                                                120.60694880436557
                                            ],
                                            "flaming": [
                                                2050.3181296742146
                                            ]
                                        },
                                        "1-hr fuels": {
                                            "total": [
                                                3598.41716969763
                                            ],
                                            "smoldering": [
                                                179.9208584848815
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3418.496311212748
                                            ]
                                        },
                                        "1000-hr fuels sound": {
                                            "total": [
                                                643.6107514639145
                                            ],
                                            "smoldering": [
                                                193.0832254391744
                                            ],
                                            "residual": [
                                                64.36107514639147
                                            ],
                                            "flaming": [
                                                386.1664508783488
                                            ]
                                        },
                                        "piles": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "1000-hr fuels rotten": {
                                            "total": [
                                                1794.069847527843
                                            ],
                                            "smoldering": [
                                                538.2209542583529
                                            ],
                                            "residual": [
                                                897.0349237639215
                                            ],
                                            "flaming": [
                                                358.81396950556865
                                            ]
                                        },
                                        "10000-hr fuels sound": {
                                            "total": [
                                                2137.6860158288046
                                            ],
                                            "smoldering": [
                                                855.0744063315218
                                            ],
                                            "residual": [
                                                427.5372031657609
                                            ],
                                            "flaming": [
                                                855.0744063315218
                                            ]
                                        }
                                    },
                                    "shrub": {
                                        "primary dead": {
                                            "total": [
                                                294.245249502859
                                            ],
                                            "smoldering": [
                                                29.4245249502859
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                264.8207245525731
                                            ]
                                        },
                                        "secondary live": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "primary live": {
                                            "total": [
                                                1667.3897471828673
                                            ],
                                            "smoldering": [
                                                83.36948735914335
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                1584.0202598237238
                                            ]
                                        },
                                        "secondary dead": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "litter-lichen-moss": {
                                        "lichen": {
                                            "total": [
                                                3.5984171696976297
                                            ],
                                            "smoldering": [
                                                0.1799208584848815
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3.418496311212748
                                            ]
                                        },
                                        "litter": {
                                            "total": [
                                                3610.4118935966217
                                            ],
                                            "smoldering": [
                                                361.04118935966216
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                3249.3707042369597
                                            ]
                                        },
                                        "moss": {
                                            "total": [
                                                359.84171696976296
                                            ],
                                            "smoldering": [
                                                17.99208584848815
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                341.8496311212748
                                            ]
                                        }
                                    },
                                    "nonwoody": {
                                        "primary dead": {
                                            "total": [
                                                33.371720831775804
                                            ],
                                            "smoldering": [
                                                1.6685860415887903
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                31.703134790187015
                                            ]
                                        },
                                        "secondary live": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "primary live": {
                                            "total": [
                                                300.3454874859823
                                            ],
                                            "smoldering": [
                                                15.017274374299117
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                285.32821311168317
                                            ]
                                        },
                                        "secondary dead": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "canopy": {
                                        "understory": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "ladder fuels": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "overstory": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 3": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 2": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 wood": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 no foliage": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 foliage": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        },
                                        "midstory": {
                                            "total": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "flaming": [
                                                0.0
                                            ]
                                        }
                                    }
                                },
                                "heat": {
                                    "total": [
                                        924073913520.8066
                                    ],
                                    "smoldering": [
                                        247784445451.14124
                                    ],
                                    "residual": [
                                        331813158338.9564
                                    ],
                                    "flaming": [
                                        344476309730.7089
                                    ]
                                },
                                "fuel_loadings": {
                                    "nw_primary_loading": 0.15,
                                    "duff_upper_loading": 11.52,
                                    "snags_c3_loading": 3.445935,
                                    "ecoregion": 240.0,
                                    "shrubs_secondary_loading": 0.0,
                                    "cover_type": 135,
                                    "w_sound_3_9_loading": 2.0,
                                    "w_stump_rotten_loading": 1.4825059999999999,
                                    "w_sound_gt20_loading": 7.0,
                                    "efg_activity": 1,
                                    "moss_loading": 0.15,
                                    "duff_lower_depth": 0.0,
                                    "snags_c2_loading": 4.594579,
                                    "duff_lower_loading": 0.0,
                                    "w_sound_0_quarter_loading": 1.5,
                                    "pile_vdirty_loading": 0.0,
                                    "w_sound_1_3_loading": 2.5,
                                    "lichen_depth": 0.1,
                                    "w_sound_quarter_1_loading": 2.6,
                                    "ladderfuels_loading": 0.5,
                                    "understory_loading": 2.406917,
                                    "snags_c1_foliage_loading": 0.0,
                                    "duff_upper_depth": 1.5,
                                    "w_rotten_9_20_loading": 8.0,
                                    "squirrel_midden_loading": 0.0,
                                    "efg_natural": 8,
                                    "filename": "FB_0009_FCCS.xml",
                                    "w_rotten_gt20_loading": 20.0,
                                    "w_stump_sound_loading": 0.0,
                                    "total_available_fuel_loading": 89.222305,
                                    "nw_secondary_loading": 0.0,
                                    "basal_accum_loading": 0.0,
                                    "litter_loading": 1.505,
                                    "pile_dirty_loading": 0.0,
                                    "shrubs_secondary_perc_live": 0.0,
                                    "midstory_loading": 0.0,
                                    "snags_c1wo_foliage_loading": 0.0,
                                    "overstory_loading": 8.193636,
                                    "snags_c1_wood_loading": 0.0,
                                    "w_rotten_3_9_loading": 4.7,
                                    "litter_depth": 0.5,
                                    "w_sound_9_20_loading": 3.7,
                                    "lichen_loading": 0.0015,
                                    "moss_depth": 0.5,
                                    "nw_primary_perc_live": 0.9,
                                    "nw_secondary_perc_live": 0.0,
                                    "shrubs_primary_loading": 1.7447560000000002,
                                    "shrubs_primary_perc_live": 0.85,
                                    "pile_clean_loading": 0.027473,
                                    "w_stump_lightered_loading": 0.0
                                }
                            }
                        ],
                        "start": "20150121"
                    }
                ],
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "type": "wildfire",
                "heat": {
                    "summary": {
                        "total": 1848147827041.6133,
                        "smoldering": 495568890902.2825,
                        "residual": 663626316677.9128,
                        "flaming": 688952619461.4178
                    }
                },
                "fuel_type": "natural",
                "id": "SF11C14225236095807750"
            }
        ],
        "today": "2016-09-15",
        "processing": [
            {
                "module_name": "ingestion",
                "parsed_input": [
                    {
                        "event_of": {
                            "id": "SF11E826544",
                            "name": "Natural Fire near Snoqualmie Pass, WA"
                        },
                        "fuel_type": "natural",
                        "growth": [
                            {
                                "end": "2015-01-21T17:00:00",
                                "start": "2015-01-20T17:00:00",
                                "location": {
                                    "geojson": {
                                        "type": "MultiPolygon",
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ]
                                    },
                                    "utc_offset": "-09:00",
                                    "ecoregion": "southern"
                                }
                            },
                            {
                                "end": "20150122",
                                "pct": 40,
                                "start": "20150121",
                                "location": {
                                    "geojson": {
                                        "type": "MultiPolygon",
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ]
                                    },
                                    "utc_offset": "-09:00",
                                    "ecoregion": "southern"
                                }
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "type": "wildfire"
                    }
                ],
                "module": "bluesky.modules.ingestion",
                "version": "0.1.0"
            },
            {
                "module_name": "fuelbeds",
                "fccsmap_version": "1.0.1",
                "module": "bluesky.modules.fuelbeds",
                "version": "0.1.0"
            },
            {
                "module_name": "consumption",
                "module": "bluesky.modules.consumption",
                "consume_version": "4.1.2",
                "version": "0.1.0"
            }
        ],
        "config": {},
        "runtime": {
            "modules": [
                {
                    "module_name": "ingestion",
                    "total": "0.0h 0.0m 0s",
                    "start": "2016-09-15T18:29:02Z",
                    "end": "2016-09-15T18:29:02Z"
                },
                {
                    "module_name": "fuelbeds",
                    "total": "0.0h 0.0m 0s",
                    "start": "2016-09-15T18:29:02Z",
                    "end": "2016-09-15T18:29:02Z"
                },
                {
                    "module_name": "consumption",
                    "total": "0.0h 0.0m 0s",
                    "start": "2016-09-15T18:29:02Z",
                    "end": "2016-09-15T18:29:02Z"
                }
            ],
            "total": "0.0h 0.0m 0s",
            "start": "2016-09-15T18:29:02Z",
            "end": "2016-09-15T18:29:02Z"
        }
    }


Finally, piping that through emissions

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption emissions
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption | bsp emissions

would give you:

    {
        "summary": {
            "heat": {
                "flaming": [
                    688952619461.4178
                ],
                "summary": {
                    "flaming": 688952619461.4178,
                    "smoldering": 495568890902.2825,
                    "residual": 663626316677.9128,
                    "total": 1848147827041.6128
                },
                "residual": [
                    663626316677.9128
                ],
                "smoldering": [
                    495568890902.2825
                ]
            },
            "emissions": {
                "flaming": {
                    "CO": [
                        3091.674879833111
                    ],
                    "NH3": [
                        51.94702750739089
                    ],
                    "PM25": [
                        313.4734418549451
                    ],
                    "PM10": [
                        369.8986613888351
                    ],
                    "CH4": [
                        164.48743789641338
                    ],
                    "VOC": [
                        746.7385204187441
                    ],
                    "CO2": [
                        71035.3210203438
                    ],
                    "NOx": [
                        104.20408369353949
                    ],
                    "SO2": [
                        42.198347942011836
                    ]
                },
                "summary": {
                    "VOC": 4298.71549560579,
                    "CO": 18314.805943380026,
                    "NH3": 299.0410779551853,
                    "PM25": 1518.4568601345582,
                    "total": 199348.95677666832,
                    "CH4": 879.4210821714989,
                    "PM10": 1791.7790949587784,
                    "CO2": 171963.54975633248,
                    "NOx": 169.9884117237156,
                    "SO2": 113.1990544062988
                },
                "residual": {
                    "CO": [
                        8715.07260377269
                    ],
                    "NH3": [
                        141.4585856630639
                    ],
                    "PM25": [
                        689.8395561866904
                    ],
                    "PM10": [
                        814.0106763002946
                    ],
                    "CH4": [
                        409.2915308111029
                    ],
                    "VOC": [
                        2033.4671689065442
                    ],
                    "CO2": [
                        57780.28432735418
                    ],
                    "NOx": [
                        37.66079347147156
                    ],
                    "SO2": [
                        40.64711189652216
                    ]
                },
                "smoldering": {
                    "CO": [
                        6508.0584597742245
                    ],
                    "NH3": [
                        105.63546478473053
                    ],
                    "PM25": [
                        515.1438620929226
                    ],
                    "PM10": [
                        607.8697572696485
                    ],
                    "CH4": [
                        305.6421134639828
                    ],
                    "VOC": [
                        1518.5098062805016
                    ],
                    "CO2": [
                        43147.94440863448
                    ],
                    "NOx": [
                        28.12353455870453
                    ],
                    "SO2": [
                        30.353594567764805
                    ]
                }
            },
            "fuelbeds": [
                {
                    "fccs_id": "9",
                    "pct": 100.0
                }
            ],
            "consumption": {
                "ground fuels": {
                    "duff upper": {
                        "flaming": [
                            742.6303962940011
                        ],
                        "residual": [
                            1485.2607925880022
                        ],
                        "smoldering": [
                            5198.412774058008
                        ]
                    },
                    "basal accumulations": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "duff lower": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "squirrel middens": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    }
                },
                "summary": {
                    "flaming": 43059.53871633861,
                    "smoldering": 30973.055681392656,
                    "residual": 41476.64479236955,
                    "total": 115509.23919010084
                },
                "litter-lichen-moss": {
                    "litter": {
                        "flaming": [
                            6498.741408473919
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            722.0823787193243
                        ]
                    },
                    "moss": {
                        "flaming": [
                            683.6992622425496
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            35.9841716969763
                        ]
                    },
                    "lichen": {
                        "flaming": [
                            6.836992622425496
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.359841716969763
                        ]
                    }
                },
                "canopy": {
                    "snags class 1 foliage": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "snags class 1 no foliage": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "understory": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "ladder fuels": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "snags class 1 wood": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "snags class 2": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "midstory": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "snags class 3": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "overstory": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    }
                },
                "nonwoody": {
                    "primary live": {
                        "flaming": [
                            570.6564262233663
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            30.034548748598233
                        ]
                    },
                    "primary dead": {
                        "flaming": [
                            63.40626958037403
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            3.3371720831775806
                        ]
                    },
                    "secondary live": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "secondary dead": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    }
                },
                "shrub": {
                    "primary live": {
                        "flaming": [
                            3168.0405196474476
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            166.7389747182867
                        ]
                    },
                    "primary dead": {
                        "flaming": [
                            529.6414491051462
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            58.8490499005718
                        ]
                    },
                    "secondary live": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "secondary dead": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    }
                },
                "woody fuels": {
                    "stumps lightered": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "stumps sound": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "stumps rotten": {
                        "flaming": [
                            355.64500297198356
                        ],
                        "residual": [
                            2133.870017831902
                        ],
                        "smoldering": [
                            1066.935008915951
                        ]
                    },
                    "10k+-hr fuels rotten": {
                        "flaming": [
                            3560.3233573900993
                        ],
                        "residual": [
                            21361.94014434059
                        ],
                        "smoldering": [
                            10680.970072170296
                        ]
                    },
                    "10000-hr fuels rotten": {
                        "flaming": [
                            1853.737964460779
                        ],
                        "residual": [
                            11122.427786764674
                        ],
                        "smoldering": [
                            5561.213893382337
                        ]
                    },
                    "10000-hr fuels sound": {
                        "flaming": [
                            1710.1488126630436
                        ],
                        "residual": [
                            855.0744063315218
                        ],
                        "smoldering": [
                            1710.1488126630436
                        ]
                    },
                    "10k+-hr fuels sound": {
                        "flaming": [
                            1177.032874541753
                        ],
                        "residual": [
                            2354.065749083506
                        ],
                        "smoldering": [
                            2354.065749083506
                        ]
                    },
                    "1000-hr fuels rotten": {
                        "flaming": [
                            717.6279390111373
                        ],
                        "residual": [
                            1794.069847527843
                        ],
                        "smoldering": [
                            1076.4419085167058
                        ]
                    },
                    "100-hr fuels": {
                        "flaming": [
                            4100.636259348429
                        ],
                        "residual": [
                            241.21389760873114
                        ],
                        "smoldering": [
                            482.4277952174623
                        ]
                    },
                    "10-hr fuels": {
                        "flaming": [
                            9711.408257579964
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            1079.0453619533293
                        ]
                    },
                    "1-hr fuels": {
                        "flaming": [
                            6836.992622425496
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            359.841716969763
                        ]
                    },
                    "piles": {
                        "flaming": [
                            0.0
                        ],
                        "residual": [
                            0.0
                        ],
                        "smoldering": [
                            0.0
                        ]
                    },
                    "1000-hr fuels sound": {
                        "flaming": [
                            772.3329017566977
                        ],
                        "residual": [
                            128.72215029278294
                        ],
                        "smoldering": [
                            386.1664508783488
                        ]
                    }
                }
            }
        },
        "fire_information": [
            {
                "growth": [
                    {
                        "location": {
                            "ecoregion": "southern",
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ]
                            },
                            "area": 2398.94477979842,
                            "utc_offset": "-09:00"
                        },
                        "emissions": {
                            "summary": {
                                "VOC": 2149.357747802895,
                                "CO": 9157.402971690013,
                                "NH3": 149.52053897759265,
                                "PM25": 759.2284300672791,
                                "total": 99674.47838833414,
                                "CH4": 439.7105410857495,
                                "PM10": 895.8895474793891,
                                "CO2": 85981.77487816624,
                                "NOx": 84.9942058618578,
                                "SO2": 56.5995272031494
                            }
                        },
                        "end": "2015-01-21T17:00:00",
                        "heat": {
                            "summary": {
                                "flaming": 344476309730.7089,
                                "smoldering": 247784445451.14124,
                                "residual": 331813158338.9564,
                                "total": 924073913520.8065
                            }
                        },
                        "start": "2015-01-20T17:00:00",
                        "fuelbeds": [
                            {
                                "fccs_id": "9",
                                "emissions": {
                                    "flaming": {
                                        "CH4": [
                                            82.24371894820669
                                        ],
                                        "CO": [
                                            1545.8374399165555
                                        ],
                                        "NH3": [
                                            25.973513753695446
                                        ],
                                        "PM25": [
                                            156.73672092747256
                                        ],
                                        "PM10": [
                                            184.94933069441754
                                        ],
                                        "CO2": [
                                            35517.6605101719
                                        ],
                                        "VOC": [
                                            373.36926020937204
                                        ],
                                        "NOx": [
                                            52.102041846769744
                                        ],
                                        "SO2": [
                                            21.099173971005918
                                        ]
                                    },
                                    "total": {
                                        "CH4": [
                                            439.71054108574947
                                        ],
                                        "CO": [
                                            9157.402971690011
                                        ],
                                        "NH3": [
                                            149.52053897759265
                                        ],
                                        "PM25": [
                                            759.2284300672793
                                        ],
                                        "PM10": [
                                            895.8895474793892
                                        ],
                                        "CO2": [
                                            85981.77487816622
                                        ],
                                        "VOC": [
                                            2149.357747802895
                                        ],
                                        "NOx": [
                                            84.9942058618578
                                        ],
                                        "SO2": [
                                            56.59952720314942
                                        ]
                                    },
                                    "residual": {
                                        "CH4": [
                                            204.64576540555146
                                        ],
                                        "CO": [
                                            4357.536301886345
                                        ],
                                        "NH3": [
                                            70.72929283153195
                                        ],
                                        "PM25": [
                                            344.9197780933452
                                        ],
                                        "PM10": [
                                            407.0053381501473
                                        ],
                                        "CO2": [
                                            28890.14216367709
                                        ],
                                        "VOC": [
                                            1016.7335844532721
                                        ],
                                        "NOx": [
                                            18.83039673573578
                                        ],
                                        "SO2": [
                                            20.32355594826108
                                        ]
                                    },
                                    "smoldering": {
                                        "CH4": [
                                            152.8210567319914
                                        ],
                                        "CO": [
                                            3254.0292298871123
                                        ],
                                        "NH3": [
                                            52.817732392365265
                                        ],
                                        "PM25": [
                                            257.5719310464613
                                        ],
                                        "PM10": [
                                            303.93487863482426
                                        ],
                                        "CO2": [
                                            21573.97220431724
                                        ],
                                        "VOC": [
                                            759.2549031402508
                                        ],
                                        "NOx": [
                                            14.061767279352265
                                        ],
                                        "SO2": [
                                            15.176797283882403
                                        ]
                                    }
                                },
                                "fuel_loadings": {
                                    "snags_c1_wood_loading": 0.0,
                                    "w_sound_gt20_loading": 7.0,
                                    "nw_secondary_perc_live": 0.0,
                                    "lichen_depth": 0.1,
                                    "moss_loading": 0.15,
                                    "w_sound_quarter_1_loading": 2.6,
                                    "snags_c3_loading": 3.445935,
                                    "total_available_fuel_loading": 89.222305,
                                    "w_rotten_3_9_loading": 4.7,
                                    "w_sound_0_quarter_loading": 1.5,
                                    "nw_primary_perc_live": 0.9,
                                    "cover_type": 135,
                                    "snags_c2_loading": 4.594579,
                                    "pile_dirty_loading": 0.0,
                                    "duff_lower_loading": 0.0,
                                    "w_rotten_9_20_loading": 8.0,
                                    "litter_depth": 0.5,
                                    "shrubs_primary_perc_live": 0.85,
                                    "filename": "FB_0009_FCCS.xml",
                                    "w_stump_lightered_loading": 0.0,
                                    "squirrel_midden_loading": 0.0,
                                    "ladderfuels_loading": 0.5,
                                    "moss_depth": 0.5,
                                    "duff_lower_depth": 0.0,
                                    "lichen_loading": 0.0015,
                                    "pile_vdirty_loading": 0.0,
                                    "basal_accum_loading": 0.0,
                                    "w_stump_sound_loading": 0.0,
                                    "snags_c1wo_foliage_loading": 0.0,
                                    "w_sound_1_3_loading": 2.5,
                                    "efg_natural": 8,
                                    "nw_primary_loading": 0.15,
                                    "litter_loading": 1.505,
                                    "w_sound_9_20_loading": 3.7,
                                    "ecoregion": 240.0,
                                    "shrubs_primary_loading": 1.7447560000000002,
                                    "shrubs_secondary_loading": 0.0,
                                    "efg_activity": 1,
                                    "duff_upper_loading": 11.52,
                                    "duff_upper_depth": 1.5,
                                    "w_sound_3_9_loading": 2.0,
                                    "w_rotten_gt20_loading": 20.0,
                                    "shrubs_secondary_perc_live": 0.0,
                                    "midstory_loading": 0.0,
                                    "pile_clean_loading": 0.027473,
                                    "understory_loading": 2.406917,
                                    "overstory_loading": 8.193636,
                                    "nw_secondary_loading": 0.0,
                                    "snags_c1_foliage_loading": 0.0,
                                    "w_stump_rotten_loading": 1.4825059999999999
                                },
                                "heat": {
                                    "flaming": [
                                        344476309730.7089
                                    ],
                                    "total": [
                                        924073913520.8066
                                    ],
                                    "residual": [
                                        331813158338.9564
                                    ],
                                    "smoldering": [
                                        247784445451.14124
                                    ]
                                },
                                "pct": 100.0,
                                "consumption": {
                                    "ground fuels": {
                                        "duff upper": {
                                            "flaming": [
                                                371.31519814700056
                                            ],
                                            "residual": [
                                                742.6303962940011
                                            ],
                                            "smoldering": [
                                                2599.206387029004
                                            ]
                                        },
                                        "squirrel middens": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "duff lower": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "basal accumulations": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "litter-lichen-moss": {
                                        "moss": {
                                            "flaming": [
                                                341.8496311212748
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                17.99208584848815
                                            ]
                                        },
                                        "litter": {
                                            "flaming": [
                                                3249.3707042369597
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                361.04118935966216
                                            ]
                                        },
                                        "lichen": {
                                            "flaming": [
                                                3.418496311212748
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.1799208584848815
                                            ]
                                        }
                                    },
                                    "woody fuels": {
                                        "stumps lightered": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "stumps sound": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "10k+-hr fuels rotten": {
                                            "flaming": [
                                                1780.1616786950497
                                            ],
                                            "residual": [
                                                10680.970072170296
                                            ],
                                            "smoldering": [
                                                5340.485036085148
                                            ]
                                        },
                                        "100-hr fuels": {
                                            "flaming": [
                                                2050.3181296742146
                                            ],
                                            "residual": [
                                                120.60694880436557
                                            ],
                                            "smoldering": [
                                                241.21389760873114
                                            ]
                                        },
                                        "1000-hr fuels sound": {
                                            "flaming": [
                                                386.1664508783488
                                            ],
                                            "residual": [
                                                64.36107514639147
                                            ],
                                            "smoldering": [
                                                193.0832254391744
                                            ]
                                        },
                                        "10000-hr fuels rotten": {
                                            "flaming": [
                                                926.8689822303895
                                            ],
                                            "residual": [
                                                5561.213893382337
                                            ],
                                            "smoldering": [
                                                2780.6069466911686
                                            ]
                                        },
                                        "10000-hr fuels sound": {
                                            "flaming": [
                                                855.0744063315218
                                            ],
                                            "residual": [
                                                427.5372031657609
                                            ],
                                            "smoldering": [
                                                855.0744063315218
                                            ]
                                        },
                                        "10k+-hr fuels sound": {
                                            "flaming": [
                                                588.5164372708765
                                            ],
                                            "residual": [
                                                1177.032874541753
                                            ],
                                            "smoldering": [
                                                1177.032874541753
                                            ]
                                        },
                                        "1000-hr fuels rotten": {
                                            "flaming": [
                                                358.81396950556865
                                            ],
                                            "residual": [
                                                897.0349237639215
                                            ],
                                            "smoldering": [
                                                538.2209542583529
                                            ]
                                        },
                                        "stumps rotten": {
                                            "flaming": [
                                                177.82250148599178
                                            ],
                                            "residual": [
                                                1066.935008915951
                                            ],
                                            "smoldering": [
                                                533.4675044579755
                                            ]
                                        },
                                        "10-hr fuels": {
                                            "flaming": [
                                                4855.704128789982
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                539.5226809766647
                                            ]
                                        },
                                        "1-hr fuels": {
                                            "flaming": [
                                                3418.496311212748
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                179.9208584848815
                                            ]
                                        },
                                        "piles": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "canopy": {
                                        "snags class 2": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 no foliage": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "understory": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "ladder fuels": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 wood": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 foliage": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "midstory": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 3": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "overstory": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "nonwoody": {
                                        "primary dead": {
                                            "flaming": [
                                                31.703134790187015
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                1.6685860415887903
                                            ]
                                        },
                                        "primary live": {
                                            "flaming": [
                                                285.32821311168317
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                15.017274374299117
                                            ]
                                        },
                                        "secondary dead": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "secondary live": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "shrub": {
                                        "primary dead": {
                                            "flaming": [
                                                264.8207245525731
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                29.4245249502859
                                            ]
                                        },
                                        "primary live": {
                                            "flaming": [
                                                1584.0202598237238
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                83.36948735914335
                                            ]
                                        },
                                        "secondary dead": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "secondary live": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    }
                                }
                            }
                        ],
                        "consumption": {
                            "summary": {
                                "flaming": 21529.769358169306,
                                "smoldering": 15486.52784069633,
                                "residual": 20738.32239618478,
                                "total": 57754.619595050426
                            }
                        }
                    },
                    {
                        "location": {
                            "ecoregion": "southern",
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ]
                            },
                            "area": 2398.94477979842,
                            "utc_offset": "-09:00"
                        },
                        "emissions": {
                            "summary": {
                                "VOC": 2149.357747802895,
                                "CO": 9157.402971690013,
                                "NH3": 149.52053897759265,
                                "PM25": 759.2284300672791,
                                "total": 99674.47838833414,
                                "CH4": 439.7105410857495,
                                "PM10": 895.8895474793891,
                                "CO2": 85981.77487816624,
                                "NOx": 84.9942058618578,
                                "SO2": 56.5995272031494
                            }
                        },
                        "end": "20150122",
                        "heat": {
                            "summary": {
                                "flaming": 344476309730.7089,
                                "smoldering": 247784445451.14124,
                                "residual": 331813158338.9564,
                                "total": 924073913520.8065
                            }
                        },
                        "start": "20150121",
                        "fuelbeds": [
                            {
                                "fccs_id": "9",
                                "emissions": {
                                    "flaming": {
                                        "CH4": [
                                            82.24371894820669
                                        ],
                                        "CO": [
                                            1545.8374399165555
                                        ],
                                        "NH3": [
                                            25.973513753695446
                                        ],
                                        "PM25": [
                                            156.73672092747256
                                        ],
                                        "PM10": [
                                            184.94933069441754
                                        ],
                                        "CO2": [
                                            35517.6605101719
                                        ],
                                        "VOC": [
                                            373.36926020937204
                                        ],
                                        "NOx": [
                                            52.102041846769744
                                        ],
                                        "SO2": [
                                            21.099173971005918
                                        ]
                                    },
                                    "total": {
                                        "CH4": [
                                            439.71054108574947
                                        ],
                                        "CO": [
                                            9157.402971690011
                                        ],
                                        "NH3": [
                                            149.52053897759265
                                        ],
                                        "PM25": [
                                            759.2284300672793
                                        ],
                                        "PM10": [
                                            895.8895474793892
                                        ],
                                        "CO2": [
                                            85981.77487816622
                                        ],
                                        "VOC": [
                                            2149.357747802895
                                        ],
                                        "NOx": [
                                            84.9942058618578
                                        ],
                                        "SO2": [
                                            56.59952720314942
                                        ]
                                    },
                                    "residual": {
                                        "CH4": [
                                            204.64576540555146
                                        ],
                                        "CO": [
                                            4357.536301886345
                                        ],
                                        "NH3": [
                                            70.72929283153195
                                        ],
                                        "PM25": [
                                            344.9197780933452
                                        ],
                                        "PM10": [
                                            407.0053381501473
                                        ],
                                        "CO2": [
                                            28890.14216367709
                                        ],
                                        "VOC": [
                                            1016.7335844532721
                                        ],
                                        "NOx": [
                                            18.83039673573578
                                        ],
                                        "SO2": [
                                            20.32355594826108
                                        ]
                                    },
                                    "smoldering": {
                                        "CH4": [
                                            152.8210567319914
                                        ],
                                        "CO": [
                                            3254.0292298871123
                                        ],
                                        "NH3": [
                                            52.817732392365265
                                        ],
                                        "PM25": [
                                            257.5719310464613
                                        ],
                                        "PM10": [
                                            303.93487863482426
                                        ],
                                        "CO2": [
                                            21573.97220431724
                                        ],
                                        "VOC": [
                                            759.2549031402508
                                        ],
                                        "NOx": [
                                            14.061767279352265
                                        ],
                                        "SO2": [
                                            15.176797283882403
                                        ]
                                    }
                                },
                                "fuel_loadings": {
                                    "snags_c1_wood_loading": 0.0,
                                    "w_sound_gt20_loading": 7.0,
                                    "nw_secondary_perc_live": 0.0,
                                    "lichen_depth": 0.1,
                                    "moss_loading": 0.15,
                                    "w_sound_quarter_1_loading": 2.6,
                                    "snags_c3_loading": 3.445935,
                                    "total_available_fuel_loading": 89.222305,
                                    "w_rotten_3_9_loading": 4.7,
                                    "w_sound_0_quarter_loading": 1.5,
                                    "nw_primary_perc_live": 0.9,
                                    "cover_type": 135,
                                    "snags_c2_loading": 4.594579,
                                    "pile_dirty_loading": 0.0,
                                    "duff_lower_loading": 0.0,
                                    "w_rotten_9_20_loading": 8.0,
                                    "litter_depth": 0.5,
                                    "shrubs_primary_perc_live": 0.85,
                                    "filename": "FB_0009_FCCS.xml",
                                    "w_stump_lightered_loading": 0.0,
                                    "squirrel_midden_loading": 0.0,
                                    "ladderfuels_loading": 0.5,
                                    "moss_depth": 0.5,
                                    "duff_lower_depth": 0.0,
                                    "lichen_loading": 0.0015,
                                    "pile_vdirty_loading": 0.0,
                                    "basal_accum_loading": 0.0,
                                    "w_stump_sound_loading": 0.0,
                                    "snags_c1wo_foliage_loading": 0.0,
                                    "w_sound_1_3_loading": 2.5,
                                    "efg_natural": 8,
                                    "nw_primary_loading": 0.15,
                                    "litter_loading": 1.505,
                                    "w_sound_9_20_loading": 3.7,
                                    "ecoregion": 240.0,
                                    "shrubs_primary_loading": 1.7447560000000002,
                                    "shrubs_secondary_loading": 0.0,
                                    "efg_activity": 1,
                                    "duff_upper_loading": 11.52,
                                    "duff_upper_depth": 1.5,
                                    "w_sound_3_9_loading": 2.0,
                                    "w_rotten_gt20_loading": 20.0,
                                    "shrubs_secondary_perc_live": 0.0,
                                    "midstory_loading": 0.0,
                                    "pile_clean_loading": 0.027473,
                                    "understory_loading": 2.406917,
                                    "overstory_loading": 8.193636,
                                    "nw_secondary_loading": 0.0,
                                    "snags_c1_foliage_loading": 0.0,
                                    "w_stump_rotten_loading": 1.4825059999999999
                                },
                                "heat": {
                                    "flaming": [
                                        344476309730.7089
                                    ],
                                    "total": [
                                        924073913520.8066
                                    ],
                                    "residual": [
                                        331813158338.9564
                                    ],
                                    "smoldering": [
                                        247784445451.14124
                                    ]
                                },
                                "pct": 100.0,
                                "consumption": {
                                    "ground fuels": {
                                        "duff upper": {
                                            "flaming": [
                                                371.31519814700056
                                            ],
                                            "residual": [
                                                742.6303962940011
                                            ],
                                            "smoldering": [
                                                2599.206387029004
                                            ]
                                        },
                                        "squirrel middens": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "duff lower": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "basal accumulations": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "litter-lichen-moss": {
                                        "moss": {
                                            "flaming": [
                                                341.8496311212748
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                17.99208584848815
                                            ]
                                        },
                                        "litter": {
                                            "flaming": [
                                                3249.3707042369597
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                361.04118935966216
                                            ]
                                        },
                                        "lichen": {
                                            "flaming": [
                                                3.418496311212748
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.1799208584848815
                                            ]
                                        }
                                    },
                                    "woody fuels": {
                                        "stumps lightered": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "stumps sound": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "10k+-hr fuels rotten": {
                                            "flaming": [
                                                1780.1616786950497
                                            ],
                                            "residual": [
                                                10680.970072170296
                                            ],
                                            "smoldering": [
                                                5340.485036085148
                                            ]
                                        },
                                        "100-hr fuels": {
                                            "flaming": [
                                                2050.3181296742146
                                            ],
                                            "residual": [
                                                120.60694880436557
                                            ],
                                            "smoldering": [
                                                241.21389760873114
                                            ]
                                        },
                                        "1000-hr fuels sound": {
                                            "flaming": [
                                                386.1664508783488
                                            ],
                                            "residual": [
                                                64.36107514639147
                                            ],
                                            "smoldering": [
                                                193.0832254391744
                                            ]
                                        },
                                        "10000-hr fuels rotten": {
                                            "flaming": [
                                                926.8689822303895
                                            ],
                                            "residual": [
                                                5561.213893382337
                                            ],
                                            "smoldering": [
                                                2780.6069466911686
                                            ]
                                        },
                                        "10000-hr fuels sound": {
                                            "flaming": [
                                                855.0744063315218
                                            ],
                                            "residual": [
                                                427.5372031657609
                                            ],
                                            "smoldering": [
                                                855.0744063315218
                                            ]
                                        },
                                        "10k+-hr fuels sound": {
                                            "flaming": [
                                                588.5164372708765
                                            ],
                                            "residual": [
                                                1177.032874541753
                                            ],
                                            "smoldering": [
                                                1177.032874541753
                                            ]
                                        },
                                        "1000-hr fuels rotten": {
                                            "flaming": [
                                                358.81396950556865
                                            ],
                                            "residual": [
                                                897.0349237639215
                                            ],
                                            "smoldering": [
                                                538.2209542583529
                                            ]
                                        },
                                        "stumps rotten": {
                                            "flaming": [
                                                177.82250148599178
                                            ],
                                            "residual": [
                                                1066.935008915951
                                            ],
                                            "smoldering": [
                                                533.4675044579755
                                            ]
                                        },
                                        "10-hr fuels": {
                                            "flaming": [
                                                4855.704128789982
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                539.5226809766647
                                            ]
                                        },
                                        "1-hr fuels": {
                                            "flaming": [
                                                3418.496311212748
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                179.9208584848815
                                            ]
                                        },
                                        "piles": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "canopy": {
                                        "snags class 2": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 no foliage": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "understory": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "ladder fuels": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 wood": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 1 foliage": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "midstory": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "snags class 3": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "overstory": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "nonwoody": {
                                        "primary dead": {
                                            "flaming": [
                                                31.703134790187015
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                1.6685860415887903
                                            ]
                                        },
                                        "primary live": {
                                            "flaming": [
                                                285.32821311168317
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                15.017274374299117
                                            ]
                                        },
                                        "secondary dead": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "secondary live": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    },
                                    "shrub": {
                                        "primary dead": {
                                            "flaming": [
                                                264.8207245525731
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                29.4245249502859
                                            ]
                                        },
                                        "primary live": {
                                            "flaming": [
                                                1584.0202598237238
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                83.36948735914335
                                            ]
                                        },
                                        "secondary dead": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        },
                                        "secondary live": {
                                            "flaming": [
                                                0.0
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                0.0
                                            ]
                                        }
                                    }
                                }
                            }
                        ],
                        "consumption": {
                            "summary": {
                                "flaming": 21529.769358169306,
                                "smoldering": 15486.52784069633,
                                "residual": 20738.32239618478,
                                "total": 57754.619595050426
                            }
                        }
                    }
                ],
                "fuel_type": "natural",
                "emissions": {
                    "summary": {
                        "VOC": 4298.71549560579,
                        "CO": 18314.805943380026,
                        "NH3": 299.0410779551853,
                        "PM25": 1518.4568601345582,
                        "total": 199348.95677666832,
                        "CH4": 879.4210821714989,
                        "PM10": 1791.7790949587784,
                        "CO2": 171963.54975633248,
                        "NOx": 169.9884117237156,
                        "SO2": 113.1990544062988
                    }
                },
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "type": "wildfire",
                "heat": {
                    "summary": {
                        "flaming": 688952619461.4178,
                        "smoldering": 495568890902.2825,
                        "residual": 663626316677.9128,
                        "total": 1848147827041.6128
                    }
                },
                "id": "SF11C14225236095807750",
                "consumption": {
                    "summary": {
                        "flaming": 43059.53871633861,
                        "smoldering": 30973.055681392656,
                        "residual": 41476.64479236955,
                        "total": 115509.23919010084
                    }
                }
            }
        ],
        "today": "2016-09-15",
        "runtime": {
            "modules": [
                {
                    "start": "2016-09-15T18:29:31Z",
                    "end": "2016-09-15T18:29:31Z",
                    "module_name": "ingestion",
                    "total": "0.0h 0.0m 0s"
                },
                {
                    "start": "2016-09-15T18:29:31Z",
                    "end": "2016-09-15T18:29:31Z",
                    "module_name": "fuelbeds",
                    "total": "0.0h 0.0m 0s"
                },
                {
                    "start": "2016-09-15T18:29:31Z",
                    "end": "2016-09-15T18:29:31Z",
                    "module_name": "consumption",
                    "total": "0.0h 0.0m 0s"
                },
                {
                    "start": "2016-09-15T18:29:31Z",
                    "end": "2016-09-15T18:29:31Z",
                    "module_name": "emissions",
                    "total": "0.0h 0.0m 0s"
                }
            ],
            "start": "2016-09-15T18:29:31Z",
            "end": "2016-09-15T18:29:31Z",
            "total": "0.0h 0.0m 0s"
        },
        "processing": [
            {
                "module": "bluesky.modules.ingestion",
                "version": "0.1.0",
                "parsed_input": [
                    {
                        "type": "wildfire",
                        "growth": [
                            {
                                "location": {
                                    "ecoregion": "southern",
                                    "geojson": {
                                        "type": "MultiPolygon",
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ]
                                    },
                                    "utc_offset": "-09:00"
                                },
                                "start": "2015-01-20T17:00:00",
                                "end": "2015-01-21T17:00:00"
                            },
                            {
                                "location": {
                                    "ecoregion": "southern",
                                    "geojson": {
                                        "type": "MultiPolygon",
                                        "coordinates": [
                                            [
                                                [
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4316976
                                                    ],
                                                    [
                                                        -121.3990506,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4099293
                                                    ],
                                                    [
                                                        -121.4522115,
                                                        47.4316976
                                                    ]
                                                ]
                                            ]
                                        ]
                                    },
                                    "utc_offset": "-09:00"
                                },
                                "start": "20150121",
                                "end": "20150122",
                                "pct": 40
                            }
                        ],
                        "fuel_type": "natural",
                        "id": "SF11C14225236095807750",
                        "event_of": {
                            "id": "SF11E826544",
                            "name": "Natural Fire near Snoqualmie Pass, WA"
                        }
                    }
                ],
                "module_name": "ingestion"
            },
            {
                "version": "0.1.0",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "fccsmap_version": "1.0.1"
            },
            {
                "module": "bluesky.modules.consumption",
                "version": "0.1.0",
                "consume_version": "4.1.2",
                "module_name": "consumption"
            },
            {
                "emitcalc_version": "1.0.1",
                "version": "0.1.0",
                "module_name": "emissions",
                "eflookup_version": "1.0.2",
                "module": "bluesky.modules.emissions",
                "ef_set": "feps"
            }
        ],
        "config": {}
    }
