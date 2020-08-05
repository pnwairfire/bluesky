__author__      = "Tobias Schmidt"

import os
import subprocess
import logging
import csv

# required executables
FEPS_EMISSIONS_BINARY = 'feps_emissions'

class UbcBsfFEPSEmissions(object):
    """ FEPS Emissions Module used in Canadian system

    FEPSEmissions was copied from BlueSky Framework, and subsequently modified
    TODO: acknowledge original authors (STI?)
    """

    def __init__(self, **config):
        self._config = config

    def config(self, key):
        return self._config.get(key.lower, getattr(self, key))

    def run(self, fireLoc, working_dir):
        consumptionFile = os.path.join(working_dir, "cons.txt")
        self._write_consumption(fireLoc['consumption']['summary'],fireLoc,consumptionFile)
        totalEmissionsFile = os.path.join(working_dir, "total_emissions.txt")

        emissionsArgs = [FEPS_EMISSIONS_BINARY,
                        "-c", consumptionFile,
                        "-a", str(fireLoc["area"]),
                        "-o", totalEmissionsFile]

        #TODO: Log output?
        subprocess.check_output(emissionsArgs)

        emissions = self.readEmissions(totalEmissionsFile)

        return emissions
    
    # NOTE: Assumes that consumption is in the UBC team's units of tons/acre
    def _write_consumption(self, consumption, fire_location_info, filename):
        f = open(filename, 'w')
        f.write("cons_flm=%f\n" % (consumption["flaming"]))
        f.write("cons_sts=%f\n" % (consumption["smoldering"]))
        f.write("cons_lts=%f\n" % (consumption["residual"]))
        # TODO: what to do if duff consumption isn't defined? is 0.0 appropriate?
        f.write("cons_duff=%f\n" % (consumption.get("duff", 0.0)))
        f.write("moist_duff=%f\n" % fire_location_info['moisture_duff'])
        f.close()

    def readEmissions(self, filename):
        flaming = {}
        residual = {}
        smoldering = {}
        total = {}
        emissions = {"flaming": flaming,
                    "residual": residual,
                    "smoldering": smoldering,
                    "total": total}

        phases = {"Flame": "flaming",
                "Smold": "smoldering",
                "Resid": "residual",
                "Total": "total"}
        
        def loadArrays(v, p, x):
            v[phases[p]][x] = [float(row[x])]
            return v

        for row in csv.DictReader(open(filename, 'r'), skipinitialspace=True):
            p = row["Phase"]
            emissions = loadArrays(emissions,p,"PM25")
            emissions = loadArrays(emissions,p,"PM10")
            emissions = loadArrays(emissions,p,"CO")
            emissions = loadArrays(emissions,p,"CO2")
            emissions = loadArrays(emissions,p,"CH4")
            emissions = loadArrays(emissions,p,"NOx")
            emissions = loadArrays(emissions,p,"NH3")
            emissions = loadArrays(emissions,p,"SO2")
            emissions = loadArrays(emissions,p,"VOC")
    
        return emissions