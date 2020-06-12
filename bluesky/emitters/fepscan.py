#******************************************************************************
#
#  BlueSky Framework - Controls the estimation of emissions, incorporation of
#                      meteorology, and the use of dispersion models to
#                      forecast smoke impacts from fires.
#  Copyright (C) 2003-2006  USDA Forest Service - Pacific Northwest Wildland
#                           Fire Sciences Laboratory
#  BlueSky Framework - Version 3.5.1
#  Copyright (C) 2007-2009  USDA Forest Service - Pacific Northwest Wildland Fire
#                      Sciences Laboratory and Sonoma Technology, Inc.
#                      All rights reserved.
#
# See LICENSE.TXT for the Software License Agreement governing the use of the
# BlueSky Framework - Version 3.5.1.
#
# Contributors to the BlueSky Framework are identified in ACKNOWLEDGEMENTS.TXT
#
#******************************************************************************

import os
import subprocess
import logging
import csv



class FEPSCanEmissions(object):
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

        # profileFile = os.path.join(plume_dir, "profile.txt")
        consumptionFile = os.path.join(plume_dir, "cons.txt")
        totalEmissionsFile = os.path.join(working_dir, "total_emissions.txt")
        # emissionsFile = os.path.join(working_dir, "emissions.txt")

        emissionsArgs = [self.config("FEPS_EMISSIONS_BINARY"),
                        "-c", consumptionFile,
                        "-a", str(fireLoc["area"]),
                        "-o", totalEmissionsFile]

        #TODO: Log output?
        subprocess.check_output(emissionsArgs)

        # if not len(fireLoc["timeprofile"]):
        #     logging.info("WARNING: Skipping a fire because it has an invalid time profile. See FEPSCan")
        #     emissions = None
        # else:
        #     outputArgs = [self.config("FEPS_OUTPUT_BINARY"),
        #                     "-e", totalEmissionsFile,
        #                     "-p", profileFile,
        #                     "-o", emissionsFile]
            
        #    #TODO: Log output?
        #    subprocess.check_output(outputArgs)

        emissions = self.readEmissions(totalEmissionsFile)


        return emissions

        # TODO: TOBIAS: Determine if this following block useful!!!

        # # If FEPS_EMIS_HAP set to be true, output HAPs emission
        # if self.config("FEPS_EMIS_HAP")== "true":
        #     ##AddHAP calculation
        #     # these emission factors are in lbs/ton consumed
        #     # consumption is in tons/acre burned
        #     total_consumption = ((fireLoc["consumption"]["flaming"] +
        #         fireLoc["consumption"]["smoldering"] +
        #         fireLoc["consumption"]["residual"]) *
        #         fireLoc["area"] / 2000.0)
        #     fireLoc["metadata"]["hap_106990"] = total_consumption * 0.405 # 1,3-butadiene
        #     fireLoc["metadata"]["hap_75070"] = total_consumption * 0.40825 # acetaldehyde
        #     fireLoc["metadata"]["hap_107028"] = total_consumption * 0.424 # acrolein
        #     fireLoc["metadata"]["hap_120127"] = total_consumption * 0.005 # anthracene
        #     fireLoc["metadata"]["hap_56553"] = total_consumption * 0.0062 # benz(a)anthracene
        #     fireLoc["metadata"]["hap_71432"] = total_consumption * 1.125 # benzene
        #     fireLoc["metadata"]["hap_203338"] = total_consumption * 0.0026 # benzo(a)fluoranthene
        #     fireLoc["metadata"]["hap_50328"] = total_consumption * 0.00148 # benzo(a)pyrene
        #     fireLoc["metadata"]["hap_195197"] = total_consumption * 0.0039 # benzo(c)phenanthrene
        #     fireLoc["metadata"]["hap_192972"] = total_consumption * 0.00266 # benzo(e)pyrene
        #     fireLoc["metadata"]["hap_191242"] = total_consumption * 0.00508 # benzo(ghi)perlyene
        #     fireLoc["metadata"]["hap_207089"] = total_consumption * 0.0026 # benzo(k)fluoranthene
        #     #remove benzofluoranthenes as it's the total of benzo(a)fluoranthene & benzo(k)fluoranthene
        #     #fireLoc["metadata"]["hap_56832736"] = total_consumption * 0.00514 # benzofluoranthenes
        #     fireLoc["metadata"]["hap_463581"] = total_consumption * 0.000534 # carbonyl sulfide
        #     fireLoc["metadata"]["hap_218019"] = total_consumption * 0.0062 # chrysene
        #     fireLoc["metadata"]["hap_206440"] = total_consumption * 0.00673 # fluoranthene
        #     fireLoc["metadata"]["hap_50000"] = total_consumption * 2.575 # formaldehyde
        #     fireLoc["metadata"]["hap_193395"] = total_consumption * 0.00341 # indeno(1,2,3-cd)pyrene
        #     fireLoc["metadata"]["hap_74873"] = total_consumption * 0.128325 # methyl chloride
        #     fireLoc["metadata"]["hap_26914181"] = total_consumption * 0.00823 # methylanthracene
        #     fireLoc["metadata"]["hap_247"] = total_consumption * 0.00296 # methylbenzopyrenes
        #     fireLoc["metadata"]["hap_248"] = total_consumption * 0.0079 # methylchrysene
        #     fireLoc["metadata"]["hap_2381217"] = total_consumption * 0.00905 # methylpyrene,-fluoranthene
        #     fireLoc["metadata"]["hap_110543"] = total_consumption * 0.0164025 # n-hexane
        #     # replace o,m,p-xylene total with individual isomers 
        #     #fireLoc["metadata"]["hap_1330207"] = total_consumption * 0.242 # o,m,p-xylene
        #     fireLoc["metadata"]["hap_108383"] = total_consumption * 0.242 * 0.5907 # m-xylene
        #     fireLoc["metadata"]["hap_106423"] = total_consumption * 0.242 * 0.1925 # p-xylene
        #     fireLoc["metadata"]["hap_95476"] = total_consumption * 0.242 * 0.2168 # o-xylene
        #     fireLoc["metadata"]["hap_198550"] = total_consumption * 0.000856 # perylene
        #     fireLoc["metadata"]["hap_85018"] = total_consumption * 0.005 # phenanthrene
        #     fireLoc["metadata"]["hap_129000"] = total_consumption * 0.00929 # pyrene
        #     fireLoc["metadata"]["hap_108883"] = total_consumption * 0.56825 # toluene            

        #     context.pop_dir()

    def readEmissionsTEMP(self, filename):
        flaming = {}
        residual = {}
        smoldering = {}
        total = {}
        emissions = {"flaming": flaming,
                    "residual": residual,
                    "smoldering": smoldering,
                    "total": total}

        def loadArrays(v, x):
            if x not in v["flaming"]:
                v["flaming"][x] = [0]
                v["smoldering"][x] = [0]
                v["residual"][x] = [0]
                v["total"][x] = [0]
            v["flaming"][x][0] = float(row["flame_" + x]) + v["flaming"][x][0]
            v["smoldering"][x][0] = float(row["smold_" + x]) + v["smoldering"][x][0]
            v["residual"][x][0] = float(row["resid_" + x]) + v["residual"][x][0]
            v["total"][x][0] = float(row[x]) + v["total"][x][0]
            return v

        
        for row in csv.DictReader(open(filename, 'r'), skipinitialspace=True):
            emissions = loadArrays(emissions,"PM25")
            emissions = loadArrays(emissions,"PM10")
            emissions = loadArrays(emissions,"CO")
            emissions = loadArrays(emissions,"CO2")
            emissions = loadArrays(emissions,"CH4")
            emissions = loadArrays(emissions,"NOx")
            emissions = loadArrays(emissions,"NH3")
            emissions = loadArrays(emissions,"SO2")
            emissions = loadArrays(emissions,"VOC")

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