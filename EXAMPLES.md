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
                    "timezone": "-09:00"
                },
                "growth": [
                    {
                        "pct": 60,
                        "start": "20150120",
                        "end": "20150121"
                    },
                    {
                        "pct": 40,
                        "start": "20150121",
                        "end": "20150122"
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
        "fire_information": [
            {
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "growth": [
                    {
                        "end": "20150121",
                        "pct": 60,
                        "start": "20150120"
                    },
                    {
                        "end": "20150122",
                        "pct": 40,
                        "start": "20150121"
                    }
                ],
                "id": "SF11C14225236095807750",
                "location": {
                    "ecoregion": "southern",
                    "perimeter": {
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
                        ],
                        "type": "MultiPolygon"
                    },
                    "timezone": "-09:00"
                }
            }
        ],
        "processing": [
            {
                "module": "bluesky.modules.ingestion",
                "module_name": "ingestion",
                "parsed_input": [
                    {
                        "event_of": {
                            "id": "SF11E826544",
                            "name": "Natural Fire near Snoqualmie Pass, WA"
                        },
                        "growth": [
                            {
                                "end": "20150121",
                                "pct": 60,
                                "start": "20150120"
                            },
                            {
                                "end": "20150122",
                                "pct": 40,
                                "start": "20150121"
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "location": {
                            "ecoregion": "southern",
                            "perimeter": {
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
                                ],
                                "type": "MultiPolygon"
                            },
                            "timezone": "-09:00"
                        }
                    }
                ],
                "version": "0.1.0"
            }
        ]
    }


Piping that through fuelbeds

    cat ./tmp/locations.json | bsp ingestion fuelbeds
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds

would give you:

    {
        "fire_information": [
            {
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "fuelbeds": [
                    {
                        "fccs_id": "49",
                        "pct": 50.0
                    },
                    {
                        "fccs_id": "46",
                        "pct": 50.0
                    }
                ],
                "growth": [
                    {
                        "end": "20150121",
                        "pct": 60,
                        "start": "20150120"
                    },
                    {
                        "end": "20150122",
                        "pct": 40,
                        "start": "20150121"
                    }
                ],
                "id": "SF11C14225236095807750",
                "location": {
                    "area": 2398.94477979842,
                    "ecoregion": "southern",
                    "perimeter": {
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
                        ],
                        "type": "MultiPolygon"
                    },
                    "timezone": "-09:00"
                }
            }
        ],
        "processing": [
            {
                "module": "bluesky.modules.ingestion",
                "module_name": "ingestion",
                "parsed_input": [
                    {
                        "event_of": {
                            "id": "SF11E826544",
                            "name": "Natural Fire near Snoqualmie Pass, WA"
                        },
                        "growth": [
                            {
                                "end": "20150121",
                                "pct": 60,
                                "start": "20150120"
                            },
                            {
                                "end": "20150122",
                                "pct": 40,
                                "start": "20150121"
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "location": {
                            "ecoregion": "southern",
                            "perimeter": {
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
                                ],
                                "type": "MultiPolygon"
                            },
                            "timezone": "-09:00"
                        }
                    }
                ],
                "version": "0.1.0"
            },
            {
                "fccsmap_version": "0.1.7",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            }
        ],
        "summary": {
            "fuelbeds": [
                {
                    "fccs_id": "46",
                    "pct": 50.0
                },
                {
                    "fccs_id": "49",
                    "pct": 50.0
                }
            ]
        }
    }


Piping that through consumption

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption

would give you:

    {
        "fire_information": [
            {
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
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
                                ...
                            ...
                        },
                        "fccs_id": "49",
                        "fuel_loadings": {
                            "basal_accum_loading": 0.0,
                            "cover_type": 166,
                            ...
                        },
                        "pct": 50.0
                    },
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
                                ...
                            ...
                        },
                        "fccs_id": "46",
                        "fuel_loadings": {
                            "basal_accum_loading": 0.0,
                            "cover_type": 161,
                            "duff_lower_depth": 0.2,
                            ...
                        },
                        "pct": 50.0
                    }
                ],
                "growth": [
                    {
                        "end": "20150121",
                        "pct": 60,
                        "start": "20150120"
                    },
                    {
                        "end": "20150122",
                        "pct": 40,
                        "start": "20150121"
                    }
                ],
                "id": "SF11C14225236095807750",
                "location": {
                    "area": 2398.94477979842,
                    "ecoregion": "southern",
                    "perimeter": {
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
                        ],
                        "type": "MultiPolygon"
                    },
                    "timezone": "-09:00"
                }
            }
        ],
        "processing": [
            {
                "module": "bluesky.modules.ingestion",
                "module_name": "ingestion",
                "parsed_input": [
                    {
                        "event_of": {
                            "id": "SF11E826544",
                            "name": "Natural Fire near Snoqualmie Pass, WA"
                        },
                        "growth": [
                            {
                                "end": "20150121",
                                "pct": 60,
                                "start": "20150120"
                            },
                            {
                                "end": "20150122",
                                "pct": 40,
                                "start": "20150121"
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "location": {
                            "ecoregion": "southern",
                            "perimeter": {
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
                                ],
                                "type": "MultiPolygon"
                            },
                            "timezone": "-09:00"
                        }
                    }
                ],
                "version": "0.1.0"
            },
            {
                "fccsmap_version": "0.1.7",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            },
            {
                "consume_version": "4.1.2",
                "module": "bluesky.modules.consumption",
                "module_name": "consumption",
                "version": "0.1.0"
            }
        ],
        "summary": {
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
                    ...
                ...
            },
            "fuelbeds": [
                {
                    "fccs_id": "46",
                    "pct": 50.0
                },
                {
                    "fccs_id": "49",
                    "pct": 50.0
                }
            ]
        }
    }


Finally, piping that through emissions

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption emissions
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption | bsp emissions

would give you:

    {
        "fire_information": [
            {
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "fuelbeds": [
                    {
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "flaming": [0.0],
                                    "residual": [0.0],
                                    "smoldering": [0.0]
                                },
                                "midstory": {
                                    "flaming": [0.0],
                                    "residual": [0.0],
                                    "smoldering": [0.0]
                                },
                                ...
                            ...
                        },
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "flaming": {
                                        "CH4": [0.0],
                                        "CO": [0.0],
                                        "CO2": [0.0],
                                        "NH3": [0.0],
                                        "NOx": [0.0],
                                        "PM10": [0.0],
                                        "PM25": [0.0],
                                        "SO2": [0.0],
                                        "VOC": [0.0]
                                    },
                                    "residual": {
                                        "CH4": [0.0],
                                        "CO": [0.0],
                                        "CO2": [0.0],
                                        "NH3": [0.0],
                                        "NOx": [0.0],
                                        "PM10": [0.0],
                                        "PM25": [0.0],
                                        "SO2": [0.0],
                                        "VOC": [0.0]
                                    },
                                    "smoldering": {
                                        "CH4": [0.0],
                                        "CO": [0.0],
                                        "CO2": [0.0],
                                        "NH3": [0.0],
                                        "NOx": [0.0],
                                        "PM10": [0.0],
                                        "PM25": [0.0],
                                        "SO2": [0.0],
                                        "VOC": [0.0]
                                    }
                                },
                                ...
                            ...
                        },
                        "fccs_id": "49",
                        "fuel_loadings": {
                            "basal_accum_loading": 0.0,
                            "cover_type": 166,
                            "duff_lower_depth": 0.0,
                            ...
                        },
                        "pct": 50.0
                    },
                    {
                        "consumption": {
                            "canopy": {
                                "ladder fuels": {
                                    "flaming": [0.0],
                                    "residual": [0.0],
                                    "smoldering": [0.0]
                                },
                                "midstory": {
                                    "flaming": [0.0],
                                    "residual": [0.0],
                                    "smoldering": [0.0]
                                },
                                "overstory": {
                                    "flaming": [0.0],
                                    "residual": [0.0],
                                    "smoldering": [0.0]
                                },
                                ...
                            ...
                        },
                        "emissions": {
                            "canopy": {
                                "ladder fuels": {
                                    "flaming": {
                                        "CH4": [0.0],
                                        "CO": [0.0],
                                        "CO2": [0.0],
                                        "NH3": [0.0],
                                        "NOx": [0.0],
                                        "PM10": [0.0],
                                        "PM25": [0.0],
                                        "SO2": [0.0],
                                        "VOC": [0.0]
                                    },
                                    "residual": {
                                        "CH4": [0.0],
                                        "CO": [0.0],
                                        "CO2": [0.0],
                                        "NH3": [0.0],
                                        "NOx": [0.0],
                                        "PM10": [0.0],
                                        "PM25": [0.0],
                                        "SO2": [0.0],
                                        "VOC": [0.0]
                                    },
                                    "smoldering": {
                                        "CH4": [0.0],
                                        "CO": [0.0],
                                        "CO2": [0.0],
                                        "NH3": [0.0],
                                        "NOx": [0.0],
                                        "PM10": [0.0],
                                        "PM25": [0.0],
                                        "SO2": [0.0],
                                        "VOC": [0.0]
                                    }
                                },
                                ...
                            ...
                        },
                        "fccs_id": "46",
                        "fuel_loadings": {
                            "basal_accum_loading": 0.0,
                            "cover_type": 161,
                            "duff_lower_depth": 0.2,
                            ...
                        },
                        "pct": 50.0
                    }
                ],
                "growth": [
                    {
                        "end": "20150121",
                        "pct": 60,
                        "start": "20150120"
                    },
                    {
                        "end": "20150122",
                        "pct": 40,
                        "start": "20150121"
                    }
                ],
                "id": "SF11C14225236095807750",
                "location": {
                    "area": 2398.94477979842,
                    "ecoregion": "southern",
                    "perimeter": {
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
                        ],
                        "type": "MultiPolygon"
                    },
                    "timezone": "-09:00"
                }
            }
        ],
        "processing": [
            {
                "module": "bluesky.modules.ingestion",
                "module_name": "ingestion",
                "parsed_input": [
                    {
                        "event_of": {
                            "id": "SF11E826544",
                            "name": "Natural Fire near Snoqualmie Pass, WA"
                        },
                        "growth": [
                            {
                                "end": "20150121",
                                "pct": 60,
                                "start": "20150120"
                            },
                            {
                                "end": "20150122",
                                "pct": 40,
                                "start": "20150121"
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "location": {
                            "ecoregion": "southern",
                            "perimeter": {
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
                                ],
                                "type": "MultiPolygon"
                            },
                            "timezone": "-09:00"
                        }
                    }
                ],
                "version": "0.1.0"
            },
            {
                "fccsmap_version": "0.1.7",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            },
            {
                "consume_version": "4.1.2",
                "module": "bluesky.modules.consumption",
                "module_name": "consumption",
                "version": "0.1.0"
            },
            {
                "ef_set": "feps",
                "emitcalc_version": "0.3.2",
                "module": "bluesky.modules.emissions",
                "module_name": "emissions",
                "version": "0.1.0"
            }
        ],
        "summary": {
            "consumption": {
                "canopy": {
                    "ladder fuels": {
                        "flaming": [0.0],
                        "residual": [0.0],
                        "smoldering": [0.0],
                        "total": [
                            0.0
                        ]
                    },
                    "midstory": {
                        "flaming": [0.0],
                        "residual": [0.0],
                        "smoldering": [0.0],
                        "total": [
                            0.0
                        ]
                    },
                    ...
                ...
            },
            "emissions": {
                "canopy": {
                    "ladder fuels": {
                        "flaming": {
                            "CH4": [0.0],
                            "CO": [0.0],
                            "CO2": [0.0],
                            "NH3": [0.0],
                            "NOx": [0.0],
                            "PM10": [0.0],
                            "PM25": [0.0],
                            "SO2": [0.0],
                            "VOC": [0.0]
                        },
                        "residual": {
                            "CH4": [0.0],
                            "CO": [0.0],
                            "CO2": [0.0],
                            "NH3": [0.0],
                            "NOx": [0.0],
                            "PM10": [0.0],
                            "PM25": [0.0],
                            "SO2": [0.0],
                            "VOC": [0.0]
                        },
                        "smoldering": {
                            "CH4": [0.0],
                            "CO": [0.0],
                            "CO2": [0.0],
                            "NH3": [0.0],
                            "NOx": [0.0],
                            "PM10": [0.0],
                            "PM25": [0.0],
                            "SO2": [0.0],
                            "VOC": [0.0]
                        }
                    },
                    ...
                ...
            },
            "fuelbeds": [
                {
                    "fccs_id": "46",
                    "pct": 50.0
                },
                {
                    "fccs_id": "49",
                    "pct": 50.0
                }
            ]
        }
    }
