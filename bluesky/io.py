"""bluesky.io"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import csv
import json
import sys

class Stream(object):

    def __init__(self, file_name, flag):
        self._file_name = file_name
        self._flag = flag

    def _open_file(self):
        """Opens the imput file.

        This method exists soley for the purpose of monkeypatching the opening
        of the file (since you can't monkeypatch 'open' directly with py.test)
        """
        return open(self._file_name, self._flag)

    def __enter__(self):
        if self._file_name:
            self._file = self._open_file()
            return self._file
        else:
            if self._flag == 'r':
                return sys.stdin
            else:
                return sys.stdout

    def __exit__(self, type, value, tb):
        if type is not None:
            pass # Exception occurred

        if self._file_name and self._file:
            self._file.close()
        # else, nothing to do for stdin/stdout


class CSV2JSON(object):
    """Converts CVS-formatted data to JSON format.

    CSV2JSON is written primarily for converting fire data, but is written
    generally enought to be used on any CSV formatted data.
    """

    def __init__(self, input_file=None, output_file=None, merge_by_key=None,
            nest_under_key=None):
        """Constructor

        Optional Args:
         - input_file
         - output_file
         - merge_by_key
         - nest_under_key
        """
        self._input_file = input_file
        self._output_file = output_file
        self._merge_by_key = merge_by_key
        self._nest_under_key = nest_under_key

    def convert(self):
        data = self._load()
        data = self._merge(data)
        self._write(data)

    def _load(self):
        data = []
        with Stream(self._input_file, 'r') as s:
            headers = []
            for row in csv.reader(s):
                if not headers:
                    # record headers for this csv data
                    #headers = dict([(i, row[i].strip(' ')) for i in xrange(len(row))])
                    headers = [e.strip(' ') for e in row]
                else:
                    d = dict(zip(headers, [e.strip(' ') for e in row]))
                    self._cast_numeric_values(d)
                    data.append(d)
        return data

    def _write(self, data):
        if self._nest_under_key:
            data = {
                self._nest_under_key: data
            }

        with Stream(self._output_file, 'w') as s:
            s.write(json.dumps(data))

    def _merge(self, data):
        if not self._merge_by_key:
            return data
        raise NotImplementedError("Merging not yet supported")

    def _cast_numeric_values(self, obj):
        # TODO: better way to automatically parse numerical values
        for k in obj.keys():
            try:
                # try to parse int
                obj[k] = int(obj[k])
            except ValueError:
                try:
                    # try to parse float
                    obj[k] = float(obj[k])
                except:
                    # leave it as a string
                    pass