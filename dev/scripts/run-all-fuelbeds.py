#!/usr/bin/env python

import argparse
import datetime
import json
import os
import subprocess
import sys

FCCS_IDS = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 58, 59,
    60, 61, 62, 63, 65, 66, 67, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
    80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 97, 98,
    99, 100, 101, 102, 103, 104, 105, 106, 107, 109, 110, 114, 115, 120, 121,
    123, 124, 125, 129, 131, 133, 134, 135, 138, 140, 142, 143, 146, 147, 148,
    152, 154, 155, 156, 157, 158, 161, 162, 164, 165, 166, 168, 170, 173, 174,
    175, 176, 178, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191,
    196, 203, 208, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221,
    222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236,
    237, 238, 239, 240, 241, 242, 243, 260, 261, 262, 263, 264, 265, 266, 267,
    268, 269, 270, 272, 273, 274, 275, 276, 279, 280, 281, 282, 283, 284, 286,
    287, 288, 289, 291, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311,
    312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326,
    327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 401, 402,
    403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417,
    418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432,
    433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 445, 448, 449, 450,
    451, 453, 454, 455, 456, 457, 458, 1201, 1202, 1203, 1205, 1223, 1225,
    1241, 1242, 1243, 1244, 1245, 1247, 1252, 1260, 1261, 1262, 1271, 1273,
    1280, 1281, 1290, 1291, 1292, 1293, 1294, 1295, 1296, 1297, 1298, 1299,
]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--fccs-ids',
        help="comma-dilimited list of fccs ids to run")
    parser.add_argument('-t', '--fire-type', default="wf",
        help="'wf' or 'rx'; default 'wf'")
    parser.add_argument('-e', '--ecoregion', default="western",
        help="ecoregion; default 'western'")
    parser.add_argument('--indented-output', default=False,
        action="store_true", help="produce indented output")
    parser.add_argument('-l', '--local-code',
        default=False, action="store_true",
        help="Run with local code mounted in docker container")
    parser.add_argument('--produce-emissions-csv', action="store_true",
        help="Run with local code mounted in docker container")


    return parser.parse_args()

def main():
    args = parse_args()
    fccs_ids = ([i.strip() for i in args.fccs_ids.split(',')]
        if args.fccs_ids else FCCS_IDS)

    input_data = {
        "run_id": ("one-fire-per-fccsid-" +
            datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')),
        "config": {
            "extrafiles":{
                "dest_dir": "/data/",
                "sets": (["firescsvs", "emissionscsv"]
                    if args.produce_emissions_csv else ["firescsvs"]),
                "firescsvs": {
                    "fire_locations_filename": "fire_locations.csv",
                    "fire_events_filename": "fire_events.csv"
                },
                "emissionscsv": {
                    "filename": "fire_emissions.csv"
                }
            }
        },
        "fire_information": []
    }
    today = datetime.date.today()
    start = today.strftime('%Y-%m-%dT%H:%M:%SZ')
    end = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    for fccs_id in fccs_ids:
        input_data['fire_information'].append({
            "type": args.fire_type,
            "growth": [
                {
                    "location": {
                        "longitude": -120.5906549, #-119.7615805,
                        "ecoregion": args.ecoregion,
                        "utc_offset": "-07:00",
                        "latitude": 39.0704668, #37.909644,
                        "area": 1
                    },
                    "fuelbeds":[
                        {
                            "pct": 100.0,
                            "fccs_id": str(fccs_id)
                        }
                    ],
                    "start": start,
                    "end": end
                }
            ]
        })
    if not os.path.exists('tmp/run-all-fuelbeds/'):
        os.makedirs('tmp/run-all-fuelbeds/')
    with open('./tmp/run-all-fuelbeds/' + input_data['run_id'] + '-input.json', 'w') as f:
        f.write(json.dumps(input_data))


    cmd = "docker run -ti --rm -v $PWD/tmp/run-all-fuelbeds/:/data/"

    if args.local_code:
        cmd += (" -v $PWD/:/code/"
            " -e PYTHONPATH=/code/"
            " -e PATH=/code/bin/:$PATH")

    cmd += (" bluesky bsp --log-level=DEBUG"
        " -i /data/" + input_data['run_id'] + "-input.json"
        " -o /data/" + input_data['run_id'] + "-output.json"
        " consumption emissions")

    if args.produce_emissions_csv:
        cmd += " timeprofiling"

    cmd += " extrafiles"

    subprocess.run(cmd, shell=True, check=True)

    if args.indented_output:
        with open('./tmp/run-all-fuelbeds/' + input_data['run_id'] + '-output.json', 'r') as f_in:
            data = json.loads(f_in.read())
            with open('./tmp/run-all-fuelbeds/' + input_data['run_id'] + '-output-indented.json', 'w') as f_out:
                f_out.write(json.dumps(data, indent=4))
        os.remove('./tmp/run-all-fuelbeds/' + input_data['run_id'] + '-output.json')


if __name__ == "__main__":
    main()
