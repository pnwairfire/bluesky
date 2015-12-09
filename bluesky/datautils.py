"""bluesky.datautils"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import numpy

__all__ = [
    'deepmerge',
    'summarize',
    'multiply_nested_data',
    'format_datetimes'
]

def deepmerge(a, b):
    """Merges b into a, retaining nested keys in a that aren't in b, replacing
    any common keys with b's value.

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

def _is_num(v):
    return isinstance(v, (int, float, long))

def _is_array(v):
    return isinstance(v, (list, numpy.ndarray))

def _is_dict(v):
    return isinstance(v, dict) # TODO: catch other dict types?

def multiply_nested_data(nested_data, multiplier):


    if _is_array(nested_data):
        for i in range(len(nested_data)):
            if _is_num(nested_data[i]):
                nested_data[i] = nested_data[i] * multiplier

    elif _is_dict(nested_data):
        for k in nested_data:
            if _is_dict(nested_data[k]) or _is_array(nested_data[k]):
                multiply_nested_data(nested_data[k], multiplier)

            elif _is_num(nested_data[k]):
                nested_data[k] = nested_data[k] * multiplier

    else:
        raise ValueError("Not nested data: {}".format(nested_data))

def sum_nested_data(nested_data):
    if not _is_dict(nested_data):
        raise ValueError("Nested data must be a dict")

    summed_data = {}
    def _sum(nested_data):
        for k, v in nested_data.items():
            if _is_num(v):
                summed_data[k] = summed_data.get(k, 0.0) + v
            elif _is_array(v):
                # we're assuming it's an array of number values
                summed_data[k] = summed_data.get(k, 0.0) + sum(v)
            elif _is_dict(v):
                _sum(v)
            else:
                raise ValueError("Nested data must contain number values")

    _sum(nested_data)
    return summed_data

def _is_datetime(v):
    return hasattr(v, 'isoformat')

def format_datetimes(data):
    """Formats all datetimes (keys and values) in ISO8601 format

    This function could also go in bluesky.datetimeutils
    """
    if _is_datetime(data):
        data = data.isoformat()

    elif _is_array(data):
        for i in range(len(data)):
            data[i] = format_datetimes(data[i])

    elif _is_dict(data):
        for k in data:
            # first, format key if it's a datetime
            if _is_datetime(k):
                v = data.pop(k)
                k = k.isoformat()
                data[k] = v

            data[k] = format_datetimes(data[k])

    return data
