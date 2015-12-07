"""bluesky.dispersers.hysplit

TODO: Move this package into it's own repo.  One thing that would need to be
done first is to remove the dependence on bluesky.models.fires.Fire.
This would be fairly easy, since Fire objects are for the most part dicts.
Attr access of top level keys would need to be replaced with direct key
access, and the logic in Fire.latitude and Fire.longitude would need to be
moved into hysplit.py.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

# Import dispersion class and version here to enable generic instantiation
# code in bluesky.modules.dispersion
from .hysplit import HYSPLITDispersion, __version__
