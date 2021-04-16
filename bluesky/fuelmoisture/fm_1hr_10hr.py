# Fuel moisture function set

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
