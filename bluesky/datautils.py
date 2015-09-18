"""bluesky.datautils"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__all__ = [
    'deepmerge',
    'summarize'
]

def deepmerge(a, b):
    """Merges b into a, retaining nested keys in a that aren't in b, replacing
    and common keys with b's value.

    Updates a in place, but returns new value as well

    Note: adapted from http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge

    TODO: move to pyairfire?
    """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                deepmerge(a[key], b[key])
            # elif isinstance(a[key], list) and isinstance(b[key], list):
            #     a[key].extend(b[key])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

def summarize(fires, subdata_key):

    def _summarize(nested_data, summary):
        if isinstance(nested_data, dict):
            summary = summary or {}
            for k in nested_data:
                summary[k] = _summarize(nested_data[k], summary.get(k))
        else:
            num_values = len(nested_data)
            summary = summary or [0] * num_values
            for i in range(num_values):
                summary[i] += nested_data[i]
        return summary

    summary = {}
    for fire in fires:
        for fb in fire.fuelbeds:
            summary = _summarize(fb[subdata_key], summary)
    return summary