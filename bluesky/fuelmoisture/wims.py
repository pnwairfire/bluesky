"""bluesky.fuelmoisture.wims

This is a rewrite of the WIMS fuel moisture module from BSF
"""

__version__ = '0.1.0'

import os
import urllib2
from math import radians, cos, sin, asin, sqrt
from fuel_moisture import DefaultFuelMoisture, MOISTURE_PROFILES

class WimsFuelMoisture(object):

    def __init__(self):
        self.url = Config('fuelmoisture', 'wims','url')
        self.data_dir = Config('fuelmoisture', 'wims','data_dir')
        self.wims_data = {}

    def set_fuel_moisture(self, start, location):
        """Extracts the closest WIMS data. Assigns default fuel moisture
         values if no WIMS data is found
        """
        self.download_data(start)

    def download_data(start):
        if start in self.wims_data:
            return self.wims_data

        wims_url = start.strftime(self.url)
        with osutils.create_working_dir(working_dir=self.data_dir) as data_dir:
            wims_file = os.path.join(data_dir,
                start.strftime("%Y-%m-%d_fdr_obs.dat"))
            if os.path.isfile(wims_file):
                # file was cached by another run
                with open(wims_file) as
            else:
                # TODO: download file
                # check for success, raise RuntimeError if failed
                pass

            # TODO: load data
            # TODO: save in self.wims_data[start]
            # TODO: return self.wims_data[start]









#
#
#                else:
#                    # open the url containing wims data
#                    try:
#                        #self.log.info("reading wims fuel moisture data from url "+wims_url) # commented out because the message could fill log file
#                        try:
#                            data = urllib2.urlopen(wims_url,"rb")
#                        except: # the wims files for some days end with .dat, so the given file might be a .dat file, if not a .txt.
#                            wims_url = wims_url.replace(".txt",".dat")
#                            data = urllib2.urlopen(wims_url,"rb")
#
#                        # download the data file to the input directory
#                        content = data.read()
#                        data_file = open(r""+path+wims_file+"","wb")
#                        data_file.write(content)
#                        data_file.close()
#                        data = urllib2.urlopen(wims_url,"rb") # reopen the url (have to do this else it fails to read later)
#                    except:
#                        # warn user (only once to avoid filling log file) that
#                        # the date in question does not have fuel moisture
#                        date_check = date_time[0:10]
#                        try:
#                            date_old
#                        except:
#                            date_old = none
#                        if(date_check!=date_old):
#                            self.log.info("warning: there is no wims data for day "+date_check+". default fuel moisture values will be used.")
#                            date_old = date_check
#
#                        # use default fuel moisture
#                        self.default_fuel_moisture(fireloc)
#                        continue
#
#                # create variables to hold wims data
#                stnid = [];     stnname = [];       hun = []
#                lat = [];       long = [];          thou = []
#                ten = [];       #elev = [];         wind = []
#                #mdl = []       tmp = [];           rh = []
#                #ppt = [];      erc = [];           bi = []
#                #sc = [];       kbdi = []
#
#                # loop through each line of wims data and extract data needed
#                for line in data:
#
#                    # check if this is a data line
#                    if line[:6].strip().isdigit():
#                        #stnname.append(line[6:25].strip())
#                        #elev.append(line[25:30].strip())
#                        # validate longitude before storing data into array
#                        #mdl.append(line[41:45].strip())
#                        #tmp.append(line[45:50].strip())
#                        #rh.append(line[50:55].strip())
#                        #wind.append(line[55:60].strip())
#                        #ppt.append(line[60:67].strip())
#                        #erc.append(line[67:72].strip())
#                        #bi.append(line[72:77].strip())
#                        #sc.append(line[77:82].strip())
#                        #kbdi.append(line[82:87].strip())
#                        stnid.append(line[:6].strip())
#                        lat.append(float(line[30:35].strip()))
#                        if float(line[35:41].strip()) > 0:
#                            long.append(float('-'+line[35:41].strip()))
#                        else:
#                            long.append(float(line[35:41].strip()))
#                        hun.append(line[87:93].strip())
#                        thou.append(line[93:99].strip())
#                        ten.append(line[99:105].strip())
#
#                # close the data file/url
#                data.close()
#                url_old = wims_url
#
#            # get coordinates of fire
#            latitude = fireloc["latitude"]
#            longitude = fireloc["longitude"]
#
#            # compute the distance between fire object and all wims data.
#            # get the index location of the shortest distance (closest fire)
#            num_elements_stnid = len(stnid) # this variable is 0 if the wims file
#                                            # exists online, but is empty.
#            distance = 0
#
#            # if there is no data for the given date fill in values for
#            # default fuel moisture
#            if num_elements_stnid == 0:
#                self.default_fuel_moisture(fireloc)
#                continue
#
#            for i in range(0,num_elements_stnid):
#                d = self.hav_distance(longitude, latitude, long[i], lat[i])
#                if ((d<distance) | (i==0)):
#                    distance = d
#                    ind = i
#
#            # create variable to hold data from the closest wims station in fire object
#            fireloc["metadata"]["stnid"] = stnid[ind]
#            fireloc["metadata"]["distance_km"] = (distance)/1000.00
#
#            # determine fuel moisture based on distance treshold and write to fire object
#            # first build the fuel moisture type
#            fmoisture = construct_type("fuelmoisturedata")
#
#            # if distance is > 300 km, assign default fuel moisture values
#            if ((distance>300000.00) & (fireloc['type'] == 'rx')):
#                fmoisture.moisture_1khr = 25.00
#                fmoisture.moisture_10hr = 12.00
#                fmoisture.moisture_100hr = none
#                fmoisture.moisture_1hr = none
#                fmoisture.moisture_live = none
#                fmoisture.moisture_duff = none
#            elif ((distance>300000.00) & (fireloc['type'] == 'wf')):
#                fmoisture.moisture_1khr = 12.00
#                fmoisture.moisture_10hr = 9.00
#                fmoisture.moisture_100hr = none
#                fmoisture.moisture_1hr = none
#                fmoisture.moisture_live = none
#                fmoisture.moisture_duff = none
#            else:
#                fmoisture.moisture_1khr = thou[ind]
#                fmoisture.moisture_10hr = ten[ind]
#                fmoisture.moisture_100hr = hun[ind]
#                fmoisture.moisture_1hr = none
#                fmoisture.moisture_live = none
#                fmoisture.moisture_duff = none
#
#            # write the fuel moisture to the fireloc object
#            fireloc.fuel_moisture = fmoisture
#
#            # fill the missing fuel moisture values with defaults
#            self.populatemissingfields(fireloc)
#
#        return fireinfo
#
#    def hav_distance(self, lon1, lat1, lon2, lat2):
#        """
#        calculate the great circle distance (in meters) between two
#        points on the earth (specified in decimal degrees) using the
#        haversine approach
#        """
#        # convert decimal degrees to radians
#        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
#
#        # haversine formula
#        dlon = lon2 - lon1
#        dlat = lat2 - lat1
#        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#        c = 2 * asin(sqrt(a))
#        m = 6367000 * c
#        return m
#
#    def default_fuel_moisture(self,fireloc):
#        # construct fuel moisture type
#        fmoisture = construct_type("fuelmoisturedata")
#
#        # initialize the fuel moisture variable
#        fmoisture.moisture_1khr = none
#        fmoisture.moisture_10hr = none
#        fmoisture.moisture_100hr = none
#        fmoisture.moisture_1hr = none
#        fmoisture.moisture_live = none
#        fmoisture.moisture_duff = none
#        fireloc["metadata"]["stnid"] = -999
#        fireloc["metadata"]["distance_km"] = -999
#
#        # assign the fuel moisture to the fireloc object
#        fireloc.fuel_moisture = fmoisture
#
#        # fill the missing fuel moisture values with defaults
#        self.populatemissingfields(fireloc)
#        return fireloc