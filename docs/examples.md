## Examples

### Through Emissions

Assume you have the following input data:

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "activity": [
                    {
                        "name": "First day",
                        "active_areas": [
                            {
                                "start": "2015-08-04T17:00:00",
                                "end": "2015-08-05T17:00:00",
                                "utc_offset": "-09:00",
                                "country": "USA",
                                "state": "WA",
                                "ecoregion": "western",
                                "specified_points": [
                                    {
                                        "name": "HMW-32434",
                                        "lat": 47.41,
                                        "lng": -121.41,
                                        "area": 120
                                    },
                                    {
                                        "lat": 47.42,
                                        "lng": -121.43,
                                        "area": 103,
                                        "ecoregion": "western"
                                    }
                                ],
                                "perimeter": {
                                    "polygon": [
                                        [-121.45, 47.43],
                                        [-121.39, 47.43],
                                        [-121.39, 47.40],
                                        [-121.45, 47.40],
                                        [-121.45, 47.43]
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

(Note that ecoregion and other location input fields can be defined either per location or in the parent active area object)

Lets say that's in a file called fires.json. piping that into bsp
and running it through fuelbeds

    cat ./tmp/fires.json | bsp --indent 4 fuelbeds

would give you:

    {
        "bluesky_version": "4.1.2",
        "counts": {
            "fires": 1
        },
        "fires": [
            {
                "activity": [
                    {
                        "active_areas": [
                            {
                                "country": "USA",
                                "ecoregion": "western",
                                "end": "2015-08-05T17:00:00",
                                "perimeter": {
                                    "polygon": [
                                        [-121.45,47.43],
                                        [-121.39,47.43],
                                        [-121.39,47.4],
                                        [-121.45,47.4],
                                        [-121.45,47.43]
                                    ]
                                },
                                "specified_points": [
                                    {
                                        "area": 120.0,
                                        "fuelbeds": [
                                            {
                                                "fccs_id": "9",
                                                "pct": 100.0
                                            }
                                        ],
                                        "fuelbeds_total_accounted_for_pct": 100.0,
                                        "lat": 47.41,
                                        "lng": -121.41,
                                        "name": "HMW-32434"
                                    },
                                    {
                                        "area": 103.0,
                                        "ecoregion": "western",
                                        "fuelbeds": [
                                            {
                                                "fccs_id": "9",
                                                "pct": 100.0
                                            }
                                        ],
                                        "fuelbeds_total_accounted_for_pct": 100.0,
                                        "lat": 47.42,
                                        "lng": -121.43
                                    }
                                ],
                                "start": "2015-08-04T17:00:00",
                                "state": "WA",
                                "utc_offset": "-09:00"
                            }
                        ],
                        "name": "First day"
                    }
                ],
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "fuel_type": "natural",
                "id": "SF11C14225236095807750",
                "type": "wildfire"
            }
        ],
        "processing": [
            {
                "fccsmap_version": "2.1.0",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            }
        ],
        "run_config": {
            /* The configuration used for the run would be listed
               here.  It's cut here, for brevity */
        },
        "run_id": "154eb63c-adc5-4d4a-8a44-a806869dd672",
        "runtime": {
            "end": "2019-05-28T17:32:28.760890Z",
            "modules": [
                {
                    "end": "2019-05-28T17:32:28.760839Z",
                    "module_name": "fuelbeds",
                    "start": "2019-05-28T17:32:28.755644Z",
                    "total": "0h 0m 0.005195s"
                }
            ],
            "start": "2019-05-28T17:32:28.755635Z",
            "total": "0h 0m 0.005255s"
        },
        "summary": {
            "fuelbeds": [
                {
                    "fccs_id": "9",
                    "pct": 100.0
                }
            ]
        },
        "today": "2019-05-28"
    }

Piping that through consumption

    cat ./tmp/fires.json | bsp fuelbeds ecoregion consumption
    # or
    cat ./tmp/fires.json | bsp fuelbeds |bsp consumption

would give you give you the

    {
        "bluesky_version": "4.1.2",
        "counts": {
            "fires": 1
        },
        "fires": [
            {
                "activity": [
                    {
                        "active_areas": [
                            {
                                "consumption": {
                                    "summary": {
                                        "flaming": 2436.660009706181,
                                        "residual": 2693.4613796987646,
                                        "smoldering": 2354.6406474615565,
                                        "total": 7484.7620368665
                                    }
                                },
                                "country": "USA",
                                "ecoregion": "western",
                                "end": "2015-08-05T17:00:00",
                                "heat": {
                                    "summary": {
                                        "flaming": 38986560155.29889,
                                        "residual": 43095382075.18023,
                                        "smoldering": 37674250359.3849,
                                        "total": 119756192589.86403
                                    }
                                },
                                "perimeter": {
                                    "polygon": [
                                        [-121.45,47.43],
                                        [-121.39,47.43],
                                        [-121.39,47.4],
                                        [-121.45,47.4],
                                        [-121.45,47.43]
                                    ]
                                },
                                "specified_points": [
                                    {
                                        "area": 120.0,
                                        "consumption": {
                                            "summary": {
                                                "flaming": 1311.2071801109494,
                                                "residual": 1449.3962581338644,
                                                "smoldering": 1267.0712004277434,
                                                "total": 4027.6746386725563
                                            }
                                        },
                                        "fuelbeds": [
                                            {
                                                "consumption": {
                                                    "canopy": {
                                                        "ladder fuels": {
                                                            "flaming": [0.0],
                                                            "residual": [0.0],
                                                            "smoldering": [0.0],
                                                            "total": [0.0]
                                                        },
                                                        "midstory": {
                                                            "flaming": [0.0],
                                                            "residual": [0.0],
                                                            "smoldering": [0.0],
                                                            "total": [0.0]
                                                        },
                                                        "overstory": {
                                                            "flaming": [0.0],
                                                            "residual": [0.0],
                                                            "smoldering": [0.0],
                                                            "total": [0.0]
                                                        },
                                                        /* More canopy sub categories
                                                           would be listed here.*/
                                                    },
                                                    "ground fuels": {
                                                        /* ... */
                                                    },
                                                    "litter-lichen-moss": {
                                                        /* ... */
                                                    },
                                                    "nonwoody": {
                                                        /* ... */
                                                    },
                                                    "shrub": {
                                                        /* ... */
                                                    },
                                                    "summary": {
                                                        "canopy": {
                                                            "flaming": [0.0],
                                                            "residual": [0.0],
                                                            "smoldering": [0.0],
                                                            "total": [0.0]
                                                        },
                                                        /* ... */
                                                    },
                                                    "woody fuels": {
                                                        /* ... */
                                                    }
                                                },
                                                "fccs_id": "9",
                                                "fuel_loadings": {
                                                    "basal_accum_loading": 0.0,
                                                    "cover_type": 135,
                                                    "duff_lower_depth": 0.0,
                                                    "duff_lower_loading": 0.0,
                                                    /* ... */
                                                },
                                                "heat": {
                                                    "flaming": [20979314881.77519],
                                                    "residual": [23190340130.141827],
                                                    "smoldering": [20273139206.843895],
                                                    "total": [64442794218.7609]
                                                },
                                                "pct": 100.0
                                            }
                                        ],
                                        "fuelbeds_total_accounted_for_pct": 100.0,
                                        "heat": {
                                            "summary": {
                                                "flaming": 20979314881.77519,
                                                "residual": 23190340130.141827,
                                                "smoldering": 20273139206.843895,
                                                "total": 64442794218.76091
                                            }
                                        },
                                        "lat": 47.41,
                                        "lng": -121.41,
                                        "name": "HMW-32434"
                                    },
                                    {
                                        "area": 103.0,
                                        "consumption": {
                                            "summary": {
                                                "flaming": 1125.4528295952316,
                                                "residual": 1244.0651215649002,
                                                "smoldering": 1087.569447033813,
                                                "total": 3457.087398193945
                                            }
                                        },
                                        "ecoregion": "western",
                                        "fuelbeds": [
                                            {
                                                "consumption": {
                                                    "canopy": {
                                                        /* ... */
                                                    },
                                                    "ground fuels": {
                                                        /* ... */
                                                    },
                                                    "litter-lichen-moss": {
                                                        /* ... */
                                                    },
                                                    "nonwoody": {
                                                        /* ... */
                                                    },
                                                    "shrub": {
                                                        /* ... */
                                                    },
                                                    "summary": {
                                                        /* ... */
                                                    },
                                                    "woody fuels": {
                                                        /* ... */
                                                    }
                                                },
                                                "fccs_id": "9",
                                                "fuel_loadings": {
                                                    "basal_accum_loading": 0.0,
                                                    "cover_type": 135,
                                                    "duff_lower_depth": 0.0,
                                                    "duff_lower_loading": 0.0,
                                                    /* ... */
                                                },
                                                "heat": {
                                                    "flaming": [18007245273.523705],
                                                    "residual": [19905041945.038403],
                                                    "smoldering": [17401111152.541008],
                                                    "total": [55313398371.1031]
                                                },
                                                "pct": 100.0
                                            }
                                        ],
                                        "fuelbeds_total_accounted_for_pct": 100.0,
                                        "heat": {
                                            "summary": {
                                                "flaming": 18007245273.523705,
                                                "residual": 19905041945.038403,
                                                "smoldering": 17401111152.541008,
                                                "total": 55313398371.10312
                                            }
                                        },
                                        "lat": 47.42,
                                        "lng": -121.43
                                    }
                                ],
                                "start": "2015-08-04T17:00:00",
                                "state": "WA",
                                "utc_offset": "-09:00"
                            }
                        ],
                        "consumption": {
                            "summary": {
                                "flaming": 2436.660009706181,
                                "residual": 2693.4613796987646,
                                "smoldering": 2354.6406474615565,
                                "total": 7484.7620368665
                            }
                        },
                        "heat": {
                            "summary": {
                                "flaming": 38986560155.29889,
                                "residual": 43095382075.18023,
                                "smoldering": 37674250359.3849,
                                "total": 119756192589.86403
                            }
                        },
                        "name": "First day"
                    }
                ],
                "consumption": {
                    "summary": {
                        "flaming": 2436.660009706181,
                        "residual": 2693.4613796987646,
                        "smoldering": 2354.6406474615565,
                        "total": 7484.7620368665
                    }
                },
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "fuel_type": "natural",
                "heat": {
                    "summary": {
                        "flaming": 38986560155.29889,
                        "residual": 43095382075.18023,
                        "smoldering": 37674250359.3849,
                        "total": 119756192589.86403
                    }
                },
                "id": "SF11C14225236095807750",
                "type": "wildfire"
            }
        ],
        "processing": [
            {
                "fccsmap_version": "2.1.0",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            },
            {
                "consume_version": "5.0.2",
                "module": "bluesky.modules.consumption",
                "module_name": "consumption",
                "version": "0.1.0"
            }
        ],
        "run_config": {
            /* The configuration used for the run would be listed
               here.  It's cut here, for brevity */
        },
        "run_id": "ff9a9d80-e572-40d0-8ae4-22fb389b7b31",
        "runtime": {
            "end": "2019-05-28T17:37:49.009256Z",
            "modules": [
                {
                    "end": "2019-05-28T17:37:48.965167Z",
                    "module_name": "fuelbeds",
                    "start": "2019-05-28T17:37:48.959961Z",
                    "total": "0h 0m 0.005206s"
                },
                {
                    "end": "2019-05-28T17:37:49.009213Z",
                    "module_name": "consumption",
                    "start": "2019-05-28T17:37:48.965215Z",
                    "total": "0h 0m 0.043998s"
                }
            ],
            "start": "2019-05-28T17:37:48.959952Z",
            "total": "0h 0m 0.049304s"
        },
        "summary": {
            "consumption": {
                "canopy": {
                    "ladder fuels": {
                        "flaming": [0.0],
                        "residual": [0.0],
                        "smoldering": [0.0]
                    },
                    "midstory": {
                        /* ... */
                    },
                    "overstory": {
                        /* ... */
                    },
                    "snags class 1 foliage": {
                        /* ... */
                    },
                    "snags class 1 no foliage": {
                        /* ... */
                    },
                    "snags class 1 wood": {
                        /* ... */
                    },
                    "snags class 2": {
                        /* ... */
                    },
                    "snags class 3": {
                        /* ... */
                    },
                    "understory": {
                        /* ... */
                    }
                },
                "ground fuels": {
                    /* ... */
                },
                "litter-lichen-moss": {
                    /* ... */
                },
                "nonwoody": {
                    /* ... */
                },
                "shrub": {
                    /* ... */
                },
                "summary": {
                    /* ... */
                },
                "woody fuels": {
                    /* ... */
                }
            },
            "fuelbeds": [
                {
                    "fccs_id": "9",
                    "pct": 100.0
                }
            ],
            "heat": {
                "flaming": [38986560155.29889],
                "residual": [43095382075.18023],
                "smoldering": [37674250359.3849],
                "summary": {
                    "flaming": 38986560155.29889,
                    "residual": 43095382075.18023,
                    "smoldering": 37674250359.3849,
                    "total": 119756192589.86403
                }
            }
        },
        "today": "2019-05-28"
    }

Finally, piping that through emissions

    cat ./tmp/fires.json fuelbeds ecoregion consumption emissions
    # or
    cat ./tmp/fires.json | bsp fuelbeds |bsp consumption | bsp emissions

would give you the above output, but with added emissions output - PM2.5, CO2, etc.
