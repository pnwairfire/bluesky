### Bluesky SMOKEREADY test 04-05-2021

```
mkdir -p ./tmp/smokeready-run/
​
echo '{
    "config": {
        "skip_failed_fires": true,
        "plumerise": {
            "model":"feps",
            "feps": {
                 "working_dir": "tmp/smokeready-run/plumerise"
            }
        },
        "extrafiles":{
            "dest_dir": "tmp/smokeready-run/output",
            "sets": ["firescsvs", "emissionscsv", "smokeready"],
            "firescsvs": {
                "fire_locations_filename": "fire_locations_smokereadytest.csv",
                "fire_events_filename": "fire_events_smokereadytest.csv"
            },
            "emissionscsv": {
                "filename": "fire_emissions_smokereadytest.csv"
            },
            "smokeready": {
                "ptinv_filename": "ptinv.ida",
                "ptday_filename": "ptday.ems95",
                "pthour_filename": "pthour.ems95",
                "separate_smolder": true,
                "write_ptinv_totals": true,
                "write_ptday_file": true
            }
        }
    }
}' > tmp/smokeready-run/config.json
​
docker run --rm -ti \
    -v $PWD/:/bluesky/ \
    -w /bluesky/ \
    -e PYTHONPATH=/bluesky/ \
    -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    bluesky \
    ./bin/bsp --log-level=DEBUG --indent 4 \
    -o ./tmp/smokeready-run/output_rehash.json \
    --run-id smokeready-run \
    -i ./tmp/smokeready-run/output.json \
    -c ./tmp/smokeready-run/config.json \
    filter fuelbeds ecoregion consumption emissions timeprofile plumerise extrafiles
    ```

### Dispersion test 09-2019
```
docker run -it --rm      -v $HOME/airfire/bluesky/:/bluesky/     -v $HOME/airfire/Met/PNW/4km/ARL/:/data/Met/PNW/4km/ARL/     -e PYTHONPATH=/bluesky/     -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin     -w /bluesky/ bluesky bsp --log-level=DEBUG --today 2019-07-28 --run-id PNW4km-dispersion-test{today}00Z -i ./dev/data/json/1-fire-24hr-20190728-OR.json -c ./dev/config/smokeready/PNW4km-dispersion-test.json -o ./output/{run_id}.json  filter fuelbeds ecoregion consumption emissions timeprofile findmetdata plumerise dispersion extrafiles
```
