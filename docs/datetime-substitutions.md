## Datetime Substitutions

Configuration settings, run id, and log file name (set with the
'--log-file' option) all support embedding timestamps, either
based on the current time or the run's "today" date.  For the
following examples, assume the current datetime is
2016-10-02T13:00:00Z and the run's "today" is set to 2016-10-01:

    "foo{today}" -> "foo20161001"
    "{today:%Y-%m-%d}" -> "2016-10-01"
    "{today-3:%Y-%m-%d}" -> "2016-09-28"
    "{yesterday}-bar" -> "20160930-bar"
    "{timestamp}" -> "20161002130000"
    "baz-{timestamp:%Y-%m-%dT%H:%M:%S}" -> "baz-2016-10-02T13:00:00"

Note that the default formatting ('%Y%m%d' for 'today' and
'yesterday', '%Y%m%d%H%M%S' for 'timestamp') can be overidden
by adding ':<FORMATSTRING>' after 'today'|'yesterday'|'timestamp'.
Also note that you can specify an offset, in days, such as in
'today-3'.

For configuration settings, after these substitutions are made,
values that are pure datetime string are then converted to
datetime objects.  For example:

    '20161002130000' -> datetime.datetime(2016,10,2,13,0,0)
    '2016-10-02' -> datetime.datetime(2016,10,2)

If you'd like a config setting to not be parsed into a datetime
object, use '{datetime-parse-buster}', which simply gets replaced
by an empty string:

    '{datetime-parse-buster}2016-10-02T13:00:00' -> '2016-10-02T13:00:00'
    '{datetime-parse-buster}{today}' -> '20161002'

