# Examples

The examples listed here are based on **proposed** changes to the code base.  They
do not represent the current behavior.

## Through Emissions

Assume you have the following input data:

    {
        "locations": [
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
                    "ecoregion": "southern"
                }
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
                    },
                ],
            }
        ]
    }

Lets say that's in a file called locations.json. piping that into bsp
and running it through ingestion

    cat ./tmp/locations.json | bsp ingestion

would give you:


    {
        "locations": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
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
                    }
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
                    },
                ],
            }
        ],
        "processing": [
            {
                "module": "INGESTION 0.17,
                "parsed_input":
                    "id": "SF11C14225236095807750",
                    "event_of": {
                        "id": "SF11E826544",
                        "name": "Natural Fire near Snoqualmie Pass, WA"
                    },
                    "location": {
                        "type": "MultiPolygon",
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
                        },
                        "ecoregion": "southern",
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
                        },
                    ],
                }
            }
        ]
    }

Piping that through fuelbeds

    cat ./tmp/locations.json | bsp ingestion fuelbeds
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds

would give you:

    {
        "locations": [
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
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
                    }
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
                    },
                ],
            }
        ],
        "fuelbeds": [
            {
                "fccs_id": "49",
                "pct": 50.0
                "fuel_loadings": {
                    "canopy": 1232,
                    /* ... */
                },
            },
            {
                "fccs_id": "46",
                "pct": 50.0
                "fuel_loadings": {
                    "canopy": 143,
                    /* ... */
                },
            }
        ],
        "summary": {
            "area": {
                "total":234234,
                "burned": 234
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
            ]
        },
        "processing": [
            {
                "module": "INGESTION 0.17,
                "parsed_input":
                    "event_of": {
                        "id": "SF11E826544",
                        "name": "Natural Fire near Snoqualmie Pass, WA"
                    },
                    "id": "SF11C14225236095807750",
                    "location": {
                        "type": "MultiPolygon",
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
                        },
                        "ecoregion": "southern",
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
                        },
                    ],
                }
            },
            "looked up fuelbeds"
        ]
    }

Piping that through consumption

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption

would give you:

    {
        "locations": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
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
                    }
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
                    },
                ],
            }
        ],
        "fuelbeds": [
            {
                "fccs_id": "49",
                "pct": 50.0
                "fuel_loadings": {
                    "canopy": 143,
                    /* ... */
                },
                "consumption": {
                    "canopy": {
                        "ladder fuels": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        },
                        /* ... */
                        "understory": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        }
                        /* ... */
                    }
                    /* ... */
                 }
             },
            {
                "fccs_id": "46",
                "pct": 50.0
                "fuel_loadings": {
                    "canopy": 143,
                    /* ... */
                },
                "consumption": {
                    "canopy": {
                        "ladder fuels": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        },
                        /* ... */
                        "understory": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        }
                    },
                    "ground fuels": {
                        "basal accumulations": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        },
                        /* ... */
                    }
                    /* ... */
                 }
            }
        ],
        "summary": {
            "area": {
                "total":234234,
                "burned": 234
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
                    /* ... */
                }
                /* ... */
             }
        },
        "processing": [
            {
                "module": "INGESTION 0.17,
                "parsed_input":
                    "event_of": {
                        "id": "SF11E826544",
                        "name": "Natural Fire near Snoqualmie Pass, WA"
                    },
                    "id": "SF11C14225236095807750",
                    "location": {
                        "type": "MultiPolygon",
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
                        },
                        "ecoregion": "southern",
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
                        },
                    ],
                }
            },
            "fuelbeds",
            "CONSUMPTION: consume"
        ]
    }

Finally, piping that through emissions

    cat ./tmp/locations.json | bsp ingestion fuelbeds consumption emissions
    # or
    cat ./tmp/locations.json | bsp ingestion | bsp fuelbeds |bsp consumption | bsp emissions

would give you:



    {
        "locations": [
            {
                "id": "SF11C14225236095807750",
                "event_of" :{
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
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
                    }
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
                    },
                ],
            }
        ],
        "fuelbeds": [
            {
                "fccs_id": "49",
                "pct": 50.0
                "fuel_loadings": {
                    "canopy": 143,
                    /* ... */
                },
                "consumption": {
                    "canopy": {
                        "ladder fuels": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        },
                        /* ... */
                        "understory": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        }
                        /* ... */
                    }
                    /* ... */
                },
                "emissions": {
                    "canopy": {
                        "ladder fuels": {
                            "flaming": {
                                "CH4": [0.0],
                                /* ... */
                            },
                            "residual": {
                                "CH4": [0.0],
                                /* ... */
                            },
                            "smoldering": {
                                "CH4": [0.0],
                                /* ... */
                            }
                        },
                        /* ... */
                    }
                    /* ... */
                }
             },
            {
                "fccs_id": "46",
                "pct": 50.0
                "fuel_loadings": {
                    "canopy": 143,
                    /* ... */
                },
                "consumption": {
                    "canopy": {
                        "ladder fuels": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        },
                        /* ... */
                        "understory": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        }
                    },
                    "ground fuels": {
                        "basal accumulations": {
                            "flaming": [0.0],
                            "residual": [0.0],
                            "smoldering": [0.0],
                            "total": [0.0]
                        },
                        /* ... */
                    }
                    /* ... */
                }
                "emissions": {
                    "canopy": {
                        "ladder fuels": {
                            "flaming": {
                                "CH4": [0.0],
                                /* ... */
                            },
                            "residual": {
                                "CH4": [0.0],
                                /* ... */
                            },
                            "smoldering": {
                                "CH4": [0.0],
                                /* ... */
                            }
                        },
                        /* ... */
                    }
                    /* ... */
                }
            }
        ],
        "summary": {
            "area": {
                "total":234234,
                "burned": 234
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
                    /* ... */
                }
                /* ... */
            },
            "emissions": {
                "canopy": {
                    "ladder fuels": {
                        "flaming": {
                            "CH4": [0.0],
                            /* ... */
                        },
                        "residual": {
                            "CH4": [0.0],
                            /* ... */
                        },
                        "smoldering": {
                            "CH4": [0.0],
                            /* ... */
                        }
                    },
                    /* ... */
                }
                /* ... */
            }
        },
        "processing": [
            {
                "module": "INGESTION 0.17,
                "parsed_input":
                    "event_of": {
                        "id": "SF11E826544",
                        "name": "Natural Fire near Snoqualmie Pass, WA"
                    },
                    "id": "SF11C14225236095807750",
                    "location": {
                        "type": "MultiPolygon",
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
                        },
                        "ecoregion": "southern",
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
                        },
                    ],
                }
            },
            "fuelbeds",
            "CONSUMPTION: consume",
            "emissions"
        ]
    }












