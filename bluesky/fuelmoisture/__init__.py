import datetime

from afdatetime.parsing import parse_datetime

# Default FM profiles from BSF
MOISTURE_PROFILES = {
    "very_dry": {
        '1_hr': 4, '10_hr': 6, '100_hr': 8, '1000_hr': 8,
        'live': 60, 'duff': 25
    },
    "dry": {
        '1_hr': 7, '10_hr': 8, '100_hr': 9, '1000_hr': 12,
        'live': 80, 'duff': 40
    },
    "moderate": {
        '1_hr': 8, '10_hr': 9, '100_hr': 11, '1000_hr': 15,
        'live': 100, 'duff': 70
    },
    "moist": {
        '1_hr': 10, '10_hr': 12, '100_hr': 12, '1000_hr': 22,
        'live': 130, 'duff': 150
    },
    "wet": {
        '1_hr': 18, '10_hr': 20, '100_hr': 22, '1000_hr': 31,
        'live': 180, 'duff': 250
    },
    "very_wet": {
        '1_hr': 28, '10_hr': 30, '100_hr': 32, '1000_hr': 75,
        'live': 300, 'duff': 400
    },
}

def get_defaults(fire, loc):
    # This logic is also from BSF
    if fire.is_wildfire:
        return MOISTURE_PROFILES['dry']
    # TODO: only reutrn moist if rx ???
    else:
        return MOISTURE_PROFILES['moist']

ONE_HOUR = datetime.timedelta(hours=1)

def fill_in_defaults(fire, aa, loc):
    defaults = get_defaults(fire, loc)
    loc['fuelmoisture'] = loc.get('fuelmoisture', {})

    hr = parse_datetime(aa['start'])
    while hr < parse_datetime(aa['end']):
        hr_str = hr.strftime('%Y-%m-%dT%H:%M:%S')
        if not loc['fuelmoisture'].get(hr_str):
            loc['fuelmoisture'][hr_str] = defaults

        else:
            for k, v in defaults.items():
                if loc['fuelmoisture'][hr_str].get(k) is None:
                    loc['fuelmoisture'][hr_str][k] = v
        hr += ONE_HOUR
