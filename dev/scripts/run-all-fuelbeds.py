#!/usr/bin/env python

import argparse
import datetime
import json
import logging
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

# TODO: Get default coordinates from Susan
DEFAULT_COORDINATES = [
    (45.0,-119.0),(44.0,-118.0),
]

DEFAULT_AREA = 1000

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', required=True,
        help="'coordinates' or 'fccs-ids'")
    parser.add_argument('-i', '--fccs-ids',
        help="comma-dilimited list of fccs ids to run")
    parser.add_argument('--coordinates',
        help="semi-colon-dilimited list of coordinages; e.g. '45,-123;33,-119'")
    parser.add_argument('-t', '--fire-type', default="wf",
        help="'wf' or 'rx'; default 'wf'")
    parser.add_argument('-a', '--area', default=DEFAULT_AREA,
        help="Are per fire; default {}".format(DEFAULT_AREA))
    parser.add_argument('-e', '--ecoregion', default="western",
        help="ecoregion; default 'western'")
    parser.add_argument('--indented-output', default=False,
        action="store_true", help="produce indented output")
    parser.add_argument('-l', '--local-code',
        default=False, action="store_true",
        help="Run with local code mounted in docker container")
    parser.add_argument('--produce-emissions-csv', action="store_true",
        help="run extrafiles to produce the emisisons csv")
    parser.add_argument('--run-through-plumerise', action="store_true")
    parser.add_argument('--log-level', default="INFO", help="Log level")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level),
        format='%(asctime)s %(levelname)s: %(message)s')

    logging.info(" Args:")
    for k,v in args.__dict__.items():
        if k in ('fccs_ids', 'coordinates'):
            logging.info("   %s: %s", k, v and v[:50])
        else:
            logging.info("   %s: %s", k, v)

    return args

def get_fccs_ids_fire_information(args, times):
    fccs_ids = ([i.strip() for i in args.fccs_ids.split(',')]
        if args.fccs_ids else FCCS_IDS)
    fires = []
    for fccs_id in fccs_ids:
        fires.append({
            "type": args.fire_type,
            "growth": [
                {
                    "location": {
                        "longitude": -120.5906549, #-119.7615805,
                        "ecoregion": args.ecoregion,
                        "utc_offset": "-07:00",
                        "latitude": 39.0704668, #37.909644,
                        "area": args.area
                    },
                    "fuelbeds":[
                        {
                            "pct": 100.0,
                            "fccs_id": str(fccs_id)
                        }
                    ],
                    "start": times['start'],
                    "end": times['end']
                }
            ]
        })
    return fires

def get_coordinates_fire_information(args):
    coordinates = ([[float(y.strip()) for y in x.split(',')] for x in args.coordinates.split(';')]
        if args.coordinates else DEFAULT_COORDINATES)
    fires = []
    for lat, lng in coordinates:
        fires.append({
            "type": args.fire_type,
            "growth": [
                {
                    "location": {
                        "latitude": lat,
                        "longitude": lng,
                        "ecoregion": args.ecoregion,
                        "utc_offset": "-07:00",
                        "area": args.area
                    },
                    "start": times['start'],
                    "end": times['end']
                }
            ]
        })
    return fires

MODES = {
    'fccs-ids': get_fccs_ids_fire_information,
    'coordinates': get_coordinates_fire_information
}

def get_times():
    today = datetime.date.today()
    return {
        "start": today.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end": (today + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    }

def main():
    args = parse_args()
    if args.mode not in MODES:
        print("\n*** ERROR: -m/--mode must be one of '{}'\n".format(
            "', '".join(MODES.keys())))
        sys.exit(1)

    times = get_times()

    run_id = (("by-fccsids" if args.mode == 'fccs-ids' else 'by-coordinates')
        + '/' + datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'))

    input_data = {
        "run_id": run_id,
        "fire_information": MODES[args.mode](args, times)
    }
    config = {
        "config": {
            "fuelbeds": {
                "no_sampling": True
            },
            "emissions": {
                "model": "prichard-oneill"
            },
            "extrafiles":{
                "dest_dir": "/data/" + run_id,
                "sets": (["firescsvs", "emissionscsv"]
                    if args.produce_emissions_csv else ["firescsvs"]),
                "firescsvs": {
                    "fire_locations_filename": "fire_locations.csv",
                    "fire_events_filename": "fire_events.csv"
                },
                "emissionscsv": {
                    "filename": "fire_emissions.csv"
                }
            },
            "plumerising": {
                "model":"feps",
                "feps": {
                    "working_dir": "/data/" + run_id
                }
            }
        }
    }

    host_output_dir = './tmp/run-all-fuelbeds/' + run_id
    if not os.path.exists(host_output_dir):
        os.makedirs(host_output_dir)
    with open(host_output_dir + '/input.json', 'w') as f:
        f.write(json.dumps(input_data))
    with open(host_output_dir + '/config.json', 'w') as f:
        f.write(json.dumps(config))

    cmd = "docker run -ti --rm -v $PWD/tmp/run-all-fuelbeds/:/data/"

    if args.local_code:
        cmd += (" -v $PWD/:/code/"
            " -e PYTHONPATH=/code/"
            " -e PATH=/code/bin/:$PATH")

    cmd += (" bluesky bsp --log-level=" + args.log_level
        + " --log-file " + '/data/' + run_id + "/output.log"
        + " -c /data/" + run_id + "/config.json"
        + " -i /data/" + run_id + "/input.json"
        + " -o /data/" + run_id + "/output.json")

    if args.mode == 'coordinates':
        cmd += fuelbeds

    cmd += " consumption emissions"

    if args.produce_emissions_csv or args.run_through_plumerise:
        cmd += " timeprofiling"
    if args.run_through_plumerise:
        cmd += " plumerising"

    cmd += " extrafiles"

    logging.info("Running command: " + cmd)
    logging.info("Output files:")
    logging.info("   Log: %s", host_output_dir + "/output.log")
    logging.info("   config: %s", host_output_dir + "/config.json")
    logging.info("   input: %s", host_output_dir + "/input.json")
    logging.info("   output: %s", host_output_dir + "/output.json")


    subprocess.run(cmd, shell=True, check=True)

    if args.indented_output:
        with open(host_output_dir + '-output.json', 'r') as f_in:
            data = json.loads(f_in.read())
            with open(host_output_dir + '-output-indented.json', 'w') as f_out:
                f_out.write(json.dumps(data, indent=4))
        os.remove(host_output_dir + '-output.json')


if __name__ == "__main__":
    main()
