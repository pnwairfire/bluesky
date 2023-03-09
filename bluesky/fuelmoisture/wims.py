"""bluesky.fuelmoisture.wims

This is a rewrite of the WIMS fuel moisture module from BSF
"""

__version__ = '0.1.0'

import os
import urllib.request
from math import radians, cos, sin, asin, sqrt
#from fuel_moisture import DefaultFuelMoisture, MOISTURE_PROFILES

__all__ = [
    'WimsFuelMoisture'
]

class WimsFuelMoisture():

    def __init__(self):
        raise NotImplementedError("WIMS fuel moisture module is not yet implemented")

        self.url = Config('fuelmoisture', 'wims','url')
        self.data_dir = Config('fuelmoisture', 'wims','data_dir')
        self.wims_data = {}

    def set_fuel_moisture(self, aa, location):
        """Extracts the closest WIMS data. Assigns default fuel moisture
         values if no WIMS data is found
        """
        self.download_data(aa.start)

    def download_data(start):
        if start in self.wims_data:
            return self.wims_data

        wims_url = start.strftime(self.url)
        with osutils.create_working_dir(working_dir=self.data_dir) as data_dir:
            wims_file = os.path.join(data_dir,
                start.strftime("%Y-%m-%d_fdr_obs.dat"))
            if os.path.isfile(wims_file):
                # file was cached by another run
                with open(wims_file) as f:
                    pass
            else:
                # TODO: download file
                # check for success, raise RuntimeError if failed
                pass

            # TODO: load data
            # TODO: save in self.wims_data[start]
            # TODO: return self.wims_data[start]







##
## BSF code
##


# _bluesky_version_ = "3.5.1"
#
# import os
# import urllib2
# from kernel.types import construct_type
# from math import radians, cos, sin, asin, sqrt
# from fuel_moisture import DefaultFuelMoisture, MOISTURE_PROFILES
#
# class FUEL_MOISTURE_WIMS(DefaultFuelMoisture):
#     """  WIMS Fuel Moisture Module """
#
#     def run(self, context):
#
#         #Get url to WIMS data
#         url = self.config("URL")
#
#         #Get path to where WIMS data would be downloaded
#         path = self.config("DATA_PATH")
#
#         # Get the fire location object
#         fireInfo = self.get_input("fires")
#
#         # Run GetWIMSData() to download and append fuel moisture from closest weather station
#         # to each fire object
#         fires = self.GetWIMSData(url,path,fireInfo)
#
#         # Set fire object as output
#         self.set_output("fires", fires)
#
#     def GetWIMSData(self,url,path,fireInfo):
#
#         self.log.info("Running FUEL_MOISTURE_WIMS")
#
#         # Loop through each fire and extract the closest WIMS data
#         # Assign default fuel moisture values if no WIMS data is found
#         for fireLoc in fireInfo.locations():
#
#             # Get date of fire (Including Year, Month, Day)
#             date_time = str(fireLoc["date_time"])
#             Date = date_time.split(" ")[0]
#             Date = Date.split("-")
#             Year = Date[0]
#             Month = Date[1]
#             Day = Date[2]
#
#             # Get the exact URL to WIMS file for the given date
#             wims_url = url % (Year, Month, Day)
#
#             # Check if the url was recently opened (if yes, its data
#             # is still available, so no need opening the url again)
#             try:
#                 url_old
#             except:
#                 url_old=None
#             if (wims_url != url_old):
#
#                 # Check if the WIMS file exists in the input directory
#                 wims_file = r"/"+Year+Month+Day+"_fdr_obs.dat"
#                 if (os.path.isfile(r""+path+wims_file+"")):
#                     self.log.info("Reading WIMS fuel moisture data from file "+path+wims_file)
#                     data = open(r""+path+wims_file+"","rb")
#                 else:
#                     # Open the url containing WIMS data
#                     try:
#                         #self.log.info("Reading WIMS fuel moisture data from url "+wims_url) # Commented out because the message could fill log file
#                         try:
#                             data = urllib2.urlopen(wims_url,"rb")
#                         except: # The WIMS files for some days end with .dat, so the given file might be a .dat file, if not a .txt.
#                             wims_url = wims_url.replace(".txt",".dat")
#                             data = urllib2.urlopen(wims_url,"rb")
#
#                         # Download the data file to the input directory
#                         content = data.read()
#                         data_file = open(r""+path+wims_file+"","wb")
#                         data_file.write(content)
#                         data_file.close()
#                         data = urllib2.urlopen(wims_url,"rb") # Reopen the url (have to do this else it fails to read later)
#                     except:
#                         # Warn user (only once to avoid filling log file) that
#                         # the date in question does not have fuel moisture
#                         date_check = date_time[0:10]
#                         try:
#                             date_old
#                         except:
#                             date_old = None
#                         if(date_check!=date_old):
#                             self.log.info("WARNING: There is no WIMS data for day "+date_check+". Default fuel moisture values will be used.")
#                             date_old = date_check
#
#                         # Use default fuel moisture
#                         self.default_fuel_moisture(fireLoc)
#                         continue
#
#                 # Create variables to hold WIMS data
#                 StnID = [];     StnName = [];       HUN = []
#                 Lat = [];       Long = [];          THOU = []
#                 TEN = [];       #Elev = [];         Wind = []
#                 #Mdl = []       Tmp = [];           RH = []
#                 #PPT = [];      ERC = [];           BI = []
#                 #SC = [];       KBDI = []
#
#                 # Loop through each line of WIMS data and extract data needed
#                 for line in data:
#
#                     # Check if this is a data line
#                     if line[:6].strip().isdigit():
#                         #StnName.append(line[6:25].strip())
#                         #Elev.append(line[25:30].strip())
#                         # Validate longitude before storing data into array
#                         #Mdl.append(line[41:45].strip())
#                         #Tmp.append(line[45:50].strip())
#                         #RH.append(line[50:55].strip())
#                         #Wind.append(line[55:60].strip())
#                         #PPT.append(line[60:67].strip())
#                         #ERC.append(line[67:72].strip())
#                         #BI.append(line[72:77].strip())
#                         #SC.append(line[77:82].strip())
#                         #KBDI.append(line[82:87].strip())
#                         StnID.append(line[:6].strip())
#                         Lat.append(float(line[30:35].strip()))
#                         if float(line[35:41].strip()) > 0:
#                             Long.append(float('-'+line[35:41].strip()))
#                         else:
#                             Long.append(float(line[35:41].strip()))
#                         HUN.append(line[87:93].strip())
#                         THOU.append(line[93:99].strip())
#                         TEN.append(line[99:105].strip())
#
#                 # Close the data file/url
#                 data.close()
#                 url_old = wims_url
#
#             # Get coordinates of fire
#             latitude = fireLoc["latitude"]
#             longitude = fireLoc["longitude"]
#
#             # Compute the distance between fire object and all WIMS data.
#             # Get the index location of the shortest distance (Closest fire)
#             Num_elements_StnID = len(StnID) # This variable is 0 if the WIMS file
#                                             # exists online, but is empty.
#             distance = 0
#
#             # If there is no data for the given date fill in values for
#             # default fuel moisture
#             if Num_elements_StnID == 0:
#                 self.default_fuel_moisture(fireLoc)
#                 continue
#
#             for i in range(0,Num_elements_StnID):
#                 d = self.hav_distance(longitude, latitude, Long[i], Lat[i])
#                 if ((d<distance) | (i==0)):
#                     distance = d
#                     ind = i
#
#             # Create variable to hold data from the closest WIMS station in fire object
#             fireLoc["metadata"]["StnID"] = StnID[ind]
#             fireLoc["metadata"]["Distance_km"] = (distance)/1000.00
#
#             # Determine fuel moisture based on distance treshold and write to fire object
#             # First build the fuel moisture type
#             fmoisture = construct_type("FuelMoistureData")
#
#             # If distance is > 300 km, assign default fuel moisture values
#             if ((distance>300000.00) & (fireLoc['type'] == 'RX')):
#                 fmoisture.moisture_1khr = 25.00
#                 fmoisture.moisture_10hr = 12.00
#                 fmoisture.moisture_100hr = None
#                 fmoisture.moisture_1hr = None
#                 fmoisture.moisture_live = None
#                 fmoisture.moisture_duff = None
#             elif ((distance>300000.00) & (fireLoc['type'] == 'WF')):
#                 fmoisture.moisture_1khr = 12.00
#                 fmoisture.moisture_10hr = 9.00
#                 fmoisture.moisture_100hr = None
#                 fmoisture.moisture_1hr = None
#                 fmoisture.moisture_live = None
#                 fmoisture.moisture_duff = None
#             else:
#                 fmoisture.moisture_1khr = THOU[ind]
#                 fmoisture.moisture_10hr = TEN[ind]
#                 fmoisture.moisture_100hr = HUN[ind]
#                 fmoisture.moisture_1hr = None
#                 fmoisture.moisture_live = None
#                 fmoisture.moisture_duff = None
#
#             # Write the fuel moisture to the fireLoc object
#             fireLoc.fuel_moisture = fmoisture
#
#             # Fill the missing fuel moisture values with defaults
#             self.populateMissingFields(fireLoc)
#
#         return fireInfo
#
#     def hav_distance(self, lon1, lat1, lon2, lat2):
#         """
#         Calculate the great circle distance (in meters) between two
#         points on the earth (specified in decimal degrees) using the
#         haversine approach
#         """
#         # convert decimal degrees to radians
#         lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
#
#         # haversine formula
#         dlon = lon2 - lon1
#         dlat = lat2 - lat1
#         a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#         c = 2 * asin(sqrt(a))
#         m = 6367000 * c
#         return m
#
#     def default_fuel_moisture(self,fireLoc):
#         # Construct fuel moisture type
#         fmoisture = construct_type("FuelMoistureData")
#
#         # Initialize the fuel moisture variable
#         fmoisture.moisture_1khr = None
#         fmoisture.moisture_10hr = None
#         fmoisture.moisture_100hr = None
#         fmoisture.moisture_1hr = None
#         fmoisture.moisture_live = None
#         fmoisture.moisture_duff = None
#         fireLoc["metadata"]["StnID"] = -999
#         fireLoc["metadata"]["Distance_km"] = -999
#
#         # Assign the fuel moisture to the fireLoc object
#         fireLoc.fuel_moisture = fmoisture
#
#         # Fill the missing fuel moisture values with defaults
#         self.populateMissingFields(fireLoc)
#         return fireLoc