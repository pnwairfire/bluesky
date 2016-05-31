"""bluesky.modules

This subpackage contains BlueSky modules.  These modules can be implemented
either as python modules or subpackages. All that's required is that the
modules/packages have a run method that can be imported, and that the run
method have the signature:

    def run(fires_manager)

where 'fires_manager' is a bluesky.models.fires.FiresManager obejct

If implemented as a subpackage, the __init__.py just needs to define a run
method or import it from one of it's modules.)
"""

__author__ = "Joel Dubowy"

import pkgutil

# Note: pkgutil.walk_packages recursively walks modules and packages, while
# pkgutil.iter_modules iterates through only modules and packages that are
# one deep
AVAILABLE_MODULES = [
    #p[1].split('.')[-1] for p in pkgutil.iter_modules(modules.__path__, modules.__name__ + '.') #if p[2]
    p[1] for p in pkgutil.iter_modules(__path__)
]
