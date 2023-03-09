"""bluesky.fuelmoisture.nfdrs

fm_1_10 written by asbova17
"""

__version__ = '0.1.0'

__all__ = [
    'NfdrsFuelMoisture'
]


class NfdrsFuelMoisture():

    def _set_first_value(self, met, met_key, key, fm_1_10_args,
            process_func=lambda a: a):
        vals = met.get(met_key)
        if vals:
            # Sometimes vals is a list and sometimes it's numerical value
            if hasattr(vals, 'append'):
                fm_1_10_args[key] = process_func(vals[0])
            else:
                fm_1_10_args[key] = vals
        # else, don't set it, so that `fm_1_10`s kward defualt is used

    def _convert_tcld_to_sow(self, tcld):
        """Convert's cloud cover to SOW

        0 - Clear, less than 1/10 cloud cover
        1 - Scattered clouds, 1/10 - 5/10 cloud cover
        2 - Broken clouds, 6/10 - 9/10 cloud cover
        3 - Overcast, 10/10 cloud cover
        """
        # tcld is a percentage in the met data
        if tcld <= 10:
            return 0
        elif tcld <= 50:
            return 1
        elif tcld <= 90:
            return 2
        else:
            return 3

    def _set_rain(self, met, fm_1_10_args):
            # For rain/precip, we want 24-hr total up to current time.  Take the
            # largest of the TPP<N>fields and multiply it to get 24-hr total
            # Potential fields, in order of preference
            #  - TPPD - 24 hour total
            #  - TPPT - 12 hour total
            #  - TPP6 - 6 hour total (multiple by 4 to get 24hr)
            #  - TPP3 - 3 hour total
            #  - TPP1 - 1 hr total
            #  - TPPA/TPPS - total over forecat window
            # Additionally, the value is in meters, and so needs to be
            # converted to mm
            self._set_first_value(met, 'TPPD', 'rain', fm_1_10_args,
                process_func=lambda a: a / 1000)
            if fm_1_10_args.get('rain') is None:
                self._set_first_value(met, 'TPPT', 'rain', fm_1_10_args,
                    process_func=lambda a: (a * 2) / 1000)
            if fm_1_10_args.get('rain') is None:
                self._set_first_value(met, 'TPP6', 'rain', fm_1_10_args,
                    process_func=lambda a: (a * 4) / 1000)
            if fm_1_10_args.get('rain') is None:
                self._set_first_value(met, 'TPP3', 'rain', fm_1_10_args,
                    process_func=lambda a: (a * 8) / 1000)
            if fm_1_10_args.get('rain') is None:
                self._set_first_value(met, 'TPP1', 'rain', fm_1_10_args,
                    process_func=lambda a: (a * 24) / 1000)
            # TODO: use TPPA/TPPS, but we need to make sure we have the
            #   correct total number of hours it represents

    def set_fuel_moisture(self, aa, location):
        """Extracts the closest WIMS data. Assigns default fuel moisture
         values if no WIMS data is found
        """
        for hr, met in location.get('localmet', {}).items():
            fm_1_10_args = {}
            # The profiler code says that TEMP is in Kelvin, but
            # the data appear to be in Celsius
            self._set_first_value(met, 'TEMP', 'temp', fm_1_10_args)
            self._set_first_value(met, 'RELH', 'rh', fm_1_10_args)
            # cloud cover is 'TCLD', we need it to compute 'sow', but
            self._set_first_value(met, 'TCLD', 'sow', fm_1_10_args,
                process_func=self._convert_tcld_to_sow)
            self._set_rain(met, fm_1_10_args)

            fm_1hr, fm_10hr = fm_1_10(**fm_1_10_args)
            location['fuelmoisture'][hr] = location['fuelmoisture'].get(hr, {})
            location['fuelmoisture'][hr]['1_hr'] = fm_1hr
            location['fuelmoisture'][hr]['10_hr'] = fm_10hr



def fm_1_10(temp=20, rh=30, rain=0, sow=0, units='SI'):

    """1 and 10 hour fuel moistures based on NFDRS:
    https://www.fs.fed.us/psw/publications/documents/psw_gtr082/psw_gtr082.pdf
    temp = temperature in C (SI) or F
    rh = relative humidity in percent
    rain = mm (SI) or inches
    sow = state of weather based on cloud cover:
    https://famit.nwcg.gov/sites/default/files/Appx_B_Field_Glossary.pdf
    0 - Clear, less than 1/10 cloud cover
    1 - Scattered clouds, 1/10 - 5/10 cloud cover
    2 - Broken clouds, 6/10 - 9/10 cloud cover
    3 - Overcast, 10/10 cloud cover
    units = data units, either 'SI' (default) or any dummy string
    (will assume US customary units if other than SI)"""

    if rh < 1:
        rh = rh * 100.  # convert rh if fraction instead of percent (assumes no rh < 1 %)

    # if data are in SI units, convert to US customary (deg F & inches of rain)
    if units == 'SI':
        temp = 1.8 * temp + 32.   # convert C to F
        rain = 0.039370 * rain  # convert mm to in

    # if rain > 0.1 in., set fm to 35% and exit
    if rain >= 0.1:
        fm_10hr = 0.35
        fm_1hr = 0.35
    else:
        sow = min([sow, 3])  # state of weather cannot be greater than 3

        # formulas below give same values for corrections based on sow as in NFDRS
        t_cor = round(-6.7 * sow + 25.3, 0)
        rh_cor = round(100*(0.084 * sow + 0.749))/100  # round to second decimal

        temp = temp + t_cor  # temperature correction (F) is added
        rh = rh * rh_cor  # rh correction is multiplied

        # equilibrium moisture content
        if rh > 50.:
            emc = 21.0606 + 0.005565 * (rh**2) - 0.00035 * rh * temp - 0.483199 * rh
        elif rh <= 10.:
            emc = 0.03229 + 0.281073 * rh - 0.000578 * rh * temp
        else:
            emc = 2.22749 + 0.160107 * rh - 0.014784 * temp

        fm_10hr = 1.28 * emc
        fm_1hr = 1.03 * emc

    return fm_1hr, fm_10hr
