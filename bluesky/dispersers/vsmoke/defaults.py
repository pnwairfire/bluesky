import os

# Temperature of fire (F)
TEMP_FIRE = 59.0

# Atmospheric pressure at surface (mb)
PRES = 1013.25

# Period relative humidity
IRHA = 25

# Is fire before sunset?
LTOFDY = True

# Period instability class
# 1 = extremely unstable
# 2 = moderately unstable
# 3 = slightly unstable
# 4 = near neutral
# 5 = slightly stable
# 6 = moderately stable
# 7 = extremely stable
STABILITY = 4

# Period mixing height (m)
MIX_HT = 1500.0

# Period's initial horizontal crosswind dispersion at the source (m)
OYINTA = 0.0

# Period's initial vertical dispersion at the surface (m)
OZINTA = 0.0

# Period's background PM (ug/m3)
BKGPMA = 0.0

# Period's background CO (ppm)
BKGCOA = 0.0

# Duration of convective period of fire (decimal hours)
THOT = 4

# Duration of constant emissions period (decimal hours)
TCONST = 4

# Exponential decay constant for smoke emissions (decimal hours)
TDECAY = 2

# Emission factor for PM2.5 (lbs/ton)
EFPM = 30

# Emission factor for CO (lbs/ton)
EFCO = 250

# Period's cloud cover (tenths)
ICOVER = 0

# Period's cloud ceiling height (feet)
CEIL = 99999

# Critical contrast ratio for crossplume visibility estimates
CC0CRT = 0.02

# Visibility criterion for roadway safety
VISCRT = 0.125

#
# RUN SETTINGS
#

# Plume rise: TRUE = gradual to final ht, FALSE = immediately attain final ht
GRAD_RISE = True

# Proportion of emissions subject to plume rise
RFRC = -.75

# Proportion of emissions subject to plume rise for each period
EMTQR = -.75

#
# OUTPUT SETTINGS
#

# KMZ Output settings
KMZ_FILE = "smoke_dispersion.kmz"
OVERLAY_TITLE = "Peak Hourly PM2.5"
LEGEND_IMAGE = os.path.join(os.path.dirname(__file__), 'images', "aqi_legend.png")

# GeoJSON Output settings
JSON_FILE = "smoke_dispersion.json"
CREATE_JSON = True

# UTM displacement of fire east of reference point
DUTMFE = 0

# UTM displacement of fire north of reference point
DUTMFN = 100

# What downward distance to start calculations (km)
XBGN = 150

# What downward distance to end calculation (km) - 200km max
XEND = 200

# Downward distance interval (km) - 0 results in default 31 distances
XNTVL = 0.05

# Tolerance for isopleths
TOL = .1
