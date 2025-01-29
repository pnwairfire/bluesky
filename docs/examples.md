## Examples

### Through Emissions

Assume that you have the following input data in ./tmp/fires.json

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "WF near Lake Chelan",
                    "id": "ABC123"
                },
                "activity": [
                    {
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
                                        "lat": 48.06,
                                        "lng": -120.22,
                                        "area": 120
                                    },
                                    {
                                        "lat": 48.07,
                                        "lng": -120.223,
                                        "area": 103,
                                        "ecoregion": "western"
                                    }
                                ],
                                "perimeter": {
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": [
                                            [
                                                [-120.22, 48.06],
                                                [-120.23, 48.06],
                                                [-120.23, 48.08],
                                                [-120.22, 48.08],
                                                [-120.22, 48.06]
                                            ]
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

(Note that ecoregion and other location input fields can be defined either per location or in the parent active area object)

You can run bluesky through fuelbeds on that input data by either piping it or
by specifying the input file with the '-i' option.

    cat ./tmp/fires.json | bsp --indent 4 fuelbeds
    bsp -i ./tmp/fires.json --indent 4 fuelbeds

Either way would give you the following:

    {
        "bluesky_version": "4.6.11",
        "counts": {
            "failed_fires": 0,
            "fires": 1,
            "locations": 2
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
                                    "geometry": {
                                        "coordinates": [
                                            [
                                                [-120.22,48.06],
                                                [-120.23,48.06],
                                                [-120.23,48.08],
                                                [-120.22,48.08],
                                                [-120.22,48.06]
                                            ]
                                        ],
                                        "type": "Polygon"
                                    }
                                },
                                "specified_points": [
                                    {
                                        "area": 120,
                                        "fuelbeds": [
                                            {
                                                "fccs_id": "52",
                                                "pct": 100.0
                                            }
                                        ],
                                        "lat": 48.06,
                                        "lng": -120.22,
                                        "name": "HMW-32434"
                                    },
                                    {
                                        "area": 103,
                                        "ecoregion": "western",
                                        "fuelbeds": [
                                            {
                                                "fccs_id": "52",
                                                "pct": 100.0
                                            }
                                        ],
                                        "lat": 48.07,
                                        "lng": -120.223
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
                "fccsmap_version": "5.0.2",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            }
        ],
        "run_config": {
            /* The configuration used for the run would be listed
               here.  It's cut here, for brevity */
        },
        "run_id": "c41164bc-7267-4760-975b-93e53c514b8f",
        "runtime": {
            "end": "2025-01-29T17:21:15.720657Z",
            "modules": [
                {
                    "end": "2025-01-29T17:21:15.720340Z",
                    "module_name": "fuelbeds",
                    "start": "2025-01-29T17:21:15.542702Z",
                    "total": "0h 0m 0.177638s"
                }
            ],
            "start": "2025-01-29T17:21:15.542697Z",
            "total": "0h 0m 0.17796s"
        },
        "summary": {
            "fuelbeds": [
                {
                    "fccs_id": "52",
                    "pct": 100.0
                }
            ]
        },
        "today": "2025-01-29T00:00:00"
    }


Running through consumption with the following command

    bsp -i ./tmp/fires.json --indent 4 fuelbeds consumption

or

    cat ./tmp/fires.json |bsp --indent 4 fuelbeds consumption

or

    cat ./tmp/fires.json |bsp fuelbeds | bsp consumption --indent 4


would give you give you the following

    {
        "bluesky_version": "4.6.11",
        "counts": {
            "failed_fires": 0,
            "fires": 1,
            "locations": 2
        },
        "fires": [
            {
                "activity": [
                    {
                        "active_areas": [
                            {
                                "consumption": {
                                    "summary": {
                                        "flaming": 773.0540904948921,
                                        "residual": 163.29028860443086,
                                        "smoldering": 210.9871561676324,
                                        "total": 1147.3315352669554
                                    }
                                },
                                "country": "USA",
                                "ecoregion": "western",
                                "end": "2015-08-05T17:00:00",
                                "heat": {
                                    "summary": {
                                        "flaming": 12368865447.918274,
                                        "residual": 2612644617.6708937,
                                        "smoldering": 3375794498.6821184,
                                        "total": 18357304564.271286
                                    }
                                },
                                "perimeter": {
                                    "geometry": {
                                        "coordinates": [
                                            [
                                                [-120.22,48.06],
                                                [-120.23,48.06],
                                                [-120.23,48.08],
                                                [-120.22,48.08],
                                                [-120.22,48.06]
                                            ]
                                        ],
                                        "type": "Polygon"
                                    }
                                },
                                "specified_points": [
                                    {
                                        "area": 120,
                                        "consumption": {
                                            "summary": {
                                                "flaming": 415.9932325533051,
                                                "residual": 87.86921359879688,
                                                "smoldering": 113.53568941756004,
                                                "total": 617.3981355696623
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
                                                        /* ... */
                                                    },
                                                    "woody fuels": {
                                                        /* ... */
                                                    }
                                                },
                                                "fccs_id": "52",
                                                "fuel_loadings": {
                                                    "FCCSID": "52",
                                                    "basal_accum_loading": 0.030600000000000002,
                                                    "cover_type": 118.0,
                                                    "duff_lower_depth": 0.0,
                                                    "duff_lower_loading": 0.0,
                                                    /* ... */
                                                },
                                                "heat": {
                                                    "flaming": [6655891720.852882],
                                                    "residual": [1405907417.58075],
                                                    "smoldering": [1816571030.6809607],
                                                    "total": [9878370169.114592]
                                                },
                                                "pct": 100.0
                                            }
                                        ],
                                        "heat": {
                                            "summary": {
                                                "flaming": 6655891720.852882,
                                                "residual": 1405907417.58075,
                                                "smoldering": 1816571030.6809607,
                                                "total": 9878370169.114594
                                            }
                                        },
                                        "lat": 48.06,
                                        "lng": -120.22,
                                        "name": "HMW-32434"
                                    },
                                    {
                                        "area": 103,
                                        "consumption": {
                                            "summary": {
                                                "flaming": 357.06085794158685,
                                                "residual": 75.42107500563398,
                                                "smoldering": 97.45146675007234,
                                                "total": 529.9333996972933
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
                                                "fccs_id": "52",
                                                "fuel_loadings": {
                                                    "FCCSID": "52",
                                                    "basal_accum_loading": 0.026265000000000004,
                                                    "cover_type": 118.0,
                                                    "duff_lower_depth": 0.0,
                                                    "duff_lower_loading": 0.0,
                                                    "duff_upper_depth": 1.1,
                                                    /* ... */
                                                },
                                                "heat": {
                                                    "flaming": [5712973727.065391],
                                                    "residual": [1206737200.0901437],
                                                    "smoldering": [1559223468.001158],
                                                    "total": [8478934395.156691]
                                                },
                                                "pct": 100.0
                                            }
                                        ],
                                        "heat": {
                                            "summary": {
                                                "flaming": 5712973727.065391,
                                                "residual": 1206737200.0901437,
                                                "smoldering": 1559223468.001158,
                                                "total": 8478934395.1566925
                                            }
                                        },
                                        "lat": 48.07,
                                        "lng": -120.223
                                    }
                                ],
                                "start": "2015-08-04T17:00:00",
                                "state": "WA",
                                "utc_offset": "-09:00"
                            }
                        ],
                        "consumption": {
                            "summary": {
                                "flaming": 773.0540904948921,
                                "residual": 163.29028860443086,
                                "smoldering": 210.9871561676324,
                                "total": 1147.3315352669554
                            }
                        },
                        "heat": {
                            "summary": {
                                "flaming": 12368865447.918274,
                                "residual": 2612644617.6708937,
                                "smoldering": 3375794498.6821184,
                                "total": 18357304564.271286
                            }
                        },
                        "name": "First day"
                    }
                ],
                "consumption": {
                    "summary": {
                        "flaming": 773.0540904948921,
                        "residual": 163.29028860443086,
                        "smoldering": 210.9871561676324,
                        "total": 1147.3315352669554
                    }
                },
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "fuel_type": "natural",
                "heat": {
                    "summary": {
                        "flaming": 12368865447.918274,
                        "residual": 2612644617.6708937,
                        "smoldering": 3375794498.6821184,
                        "total": 18357304564.271286
                    }
                },
                "id": "SF11C14225236095807750",
                "type": "wildfire"
            }
        ],
        "processing": [
            {
                "fccsmap_version": "5.0.2",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            },
            {
                "module": "bluesky.modules.ecoregion",
                "module_name": "ecoregion",
                "version": "0.1.0"
            },
            {
                "consume_version": "5.3.1",
                "module": "bluesky.modules.consumption",
                "module_name": "consumption",
                "version": "0.1.0"
            }
        ],
        "run_config": {
            /* The configuration used for the run would be listed
               here.  It's cut here, for brevity */
        },
        "run_id": "6f7ac90f-89a1-44d7-87b9-be9def906aa9",
        "runtime": {
            "end": "2025-01-29T17:24:50.986237Z",
            "modules": [
                {
                    "end": "2025-01-29T17:24:50.791119Z",
                    "module_name": "fuelbeds",
                    "start": "2025-01-29T17:24:50.617809Z",
                    "total": "0h 0m 0.17331s"
                },
                {
                    "end": "2025-01-29T17:24:50.791517Z",
                    "module_name": "ecoregion",
                    "start": "2025-01-29T17:24:50.791453Z",
                    "total": "0h 0m 6.4e-05s"
                },
                {
                    "end": "2025-01-29T17:24:50.986199Z",
                    "module_name": "consumption",
                    "start": "2025-01-29T17:24:50.791537Z",
                    "total": "0h 0m 0.194662s"
                }
            ],
            "start": "2025-01-29T17:24:50.617803Z",
            "total": "0h 0m 0.368434s"
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
                    "fccs_id": "52",
                    "pct": 100.0
                }
            ],
            "heat": {
                "flaming": [
                    12368865447.918274
                ],
                "residual": [
                    2612644617.6708937
                ],
                "smoldering": [
                    3375794498.6821184
                ],
                "summary": {
                    "flaming": 12368865447.918274,
                    "residual": 2612644617.6708937,
                    "smoldering": 3375794498.6821184,
                    "total": 18357304564.271286
                }
            }
        },
        "today": "2025-01-29T00:00:00"
    }

Finally, running through emissions

    bsp -i ./tmp/fires.json --indent 4 fuelbeds consumption emissions

would give you the above output, but with added emissions data - PM2.5, CO2, etc.
