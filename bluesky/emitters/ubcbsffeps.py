__author__      = "Tobias Schmidt"

import os
import subprocess
import logging
import csv



class UbcBsfFEPSEmissions(object):
    """ FEPS Emissions Module used in Canadian system

    FEPSEmissions was copied from BlueSky Framework, and subsequently modified
    TODO: acknowledge original authors (STI?)
    """

    # required executables
    FEPS_EMISSIONS_BINARY = 'feps_emissions'
    FEPS_OUTPUT_BINARY = 'feps_output'

    def __init__(self, **config):
        self._config = config

    def config(self, key):
        return self._config.get(key.lower, getattr(self, key))
    
    def loadHeat(self, plume_dir):
        plumeFile = os.path.join(plume_dir, "plume.txt")

        heat = {"flaming": [0],
                "residual": [0],
                "smoldering": [0],
                "total": [0]}

        #TODO: Investigate if this is the right kind of heat
        for row in csv.DictReader(open(plumeFile, 'r'), skipinitialspace=True):
            heat["total"][0] = heat["total"][0] + float(row["heat"])
            heat["residual"][0] = heat["residual"][0] + float(row["heat"])

        return heat

    def run(self, fireLoc, working_dir, plume_dir):
        consumptionFile = os.path.join(plume_dir, "cons.txt")
        totalEmissionsFile = os.path.join(working_dir, "total_emissions.txt")

        emissionsArgs = [self.config("FEPS_EMISSIONS_BINARY"),
                        "-c", consumptionFile,
                        "-a", str(fireLoc["area"]),
                        "-o", totalEmissionsFile]

        #TODO: Log output?
        subprocess.check_output(emissionsArgs)

        emissions = self.readEmissions(totalEmissionsFile)


        return emissions

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