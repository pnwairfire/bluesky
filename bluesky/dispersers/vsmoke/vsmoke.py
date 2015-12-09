"""bluesky.dispersers.vsmoke

The code in this module was copied from BlueSky Framework, and modified
significantly.  It was originally written by Sonoma Technology, Inc.
"""

__author__      = "Joel Dubowy and Sonoma Technology, Inc."
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__version__ = "0.1.0"

# import math
# import os
# import tempfile
# import zipfile
# from datetime import datetime,timedelta
# from dispersion import Dispersion
# from emissions import Emissions
# from kernel.bs_datetime import BSDateTime
# from kernel.core import Process
# from kernel.log import OUTPUT
# from kernel.types import construct_type

from .. import DispersionBase, working_dir

__all__ = [
    'VSMOKEDispersion'
]

class VSMOKEDispersion(DispersionBase):

    # KML isopleth information (not user-configurable)
    ISOPLETHS = [38, 88, 138, 351, 526]
    ISONAMES = ['Moderate', 'UnhealthyforSensitiveGroups', 'Unhealthy', 'VeryUnhealthy', 'Hazardous']
    ISOCOLORS = ['ff00ffff', 'ff007eff', 'ff0000ff', 'ff4c0099', 'ff23007e']

    BINARIES = {
        'VSMOKE': 'vsmoke',
        'VSMOKEGIS': 'vsmkgs'
    }
    DEFAULTS = defaults

    def run(self, fires, start, num_hours, dest_dir, output_dir_name):
        """Runs hysplit

        args:
         - fires - list of fires to run through hysplit
         - start - model run start hour
         - num_hours - number of hours in model run
         - dest_dir - directory to contain output dir
         - output_dir_name - name of output dir
        """

        fireInfo = self.get_input("fires")

        with working_dir() as wdir:
            input_file = os.path.join(wdir, "VSMOKE.IPT")
            iso_input_file = os.path.join(wdir, "vsmkgs.ipt")

        # Define variables for making KML and KMZ files

        contour_names = VSMOKEDispersion.ISONAMES
        contour_colors = VSMOKEDispersion.ISOCOLORS

        overlay_title = self.config("OVERLAY_TITLE")
        legend_image = self.config("LEGEND_IMAGE")

        self.log.debug("PM Isopleths =%s" % self.ISOPLETHS)
        self.log.debug("PM Isopleths Names =%s" % contour_names)
        self.log.debug("PM Isopleths Colors =%s" % contour_colors)

        # Define variables to make KML and KMZ files
        temp_dir = tempfile.gettempdir()
        doc_kml = os.path.join(temp_dir, "doc.kml")
        self.log.debug("Fire kmz = %s" % doc_kml)
        kmz_files = [doc_kml]
        date = self.config("DATE", BSDateTime)
        kmz_filename = os.path.join(self.config("OUTPUT_DIR"), (self.config("KMZ_FILE")))
        kmz_filename = date.strftime(kmz_filename)
        self.log.debug("Creating KMZ file " + os.path.basename(kmz_filename))

        # Make KMZ object for fire
        my_kmz = KMZAnimation(doc_kml, overlay_title, legend_image)

        # Define variables to decide if a GeoJSON will be created
        create_json = self.config("CREATE_JSON").upper() == "TRUE"
        if create_json:
            json = GeoJSON()

        # For each fire run VSMOKE and VSMOKEGIS
        for fireLoc in fires:
            in_var = INPUTVariables(fireLoc)

            date_time_str = fireLoc['date_time'].bs_strftime()
            timezone = int(date_time_str[-6:-3]) # Get '-zz' from YYYYmmddHHMM-zz:zz

            # Get emissions for fire
            cons = fireLoc["consumption"]
            emis = fireLoc["emissions"]
            if not cons or not emis:
                continue
            npriod = len(emis.time)
            self.log.debug("%d hour run time for fireID %s" % (npriod, fireLoc["id"]))

            # Run VSMOKE GIS for each hour
            for hr in xrange(npriod):
                # Make input file to be used by VSMOKEGIS
                self._write_iso_input(emis, hr, in_var, iso_input_file)

                # Run VSMOKEGIS
                context.execute(BINARIES['VSMOKEGIS'])

                # Rename input and output files and archive
                iso_output = "VSMKGS_" + fireLoc["id"] + "_hour" + str(hr+1) + ".iso"
                gis_output = "VSMKGS_" + fireLoc["id"] + "_hour" + str(hr+1) + ".opt"
                iso_input = "VSMKGS_" + fireLoc["id"] + "_hour" + str(hr+1) + ".ipt"
                context.copy_file("vsmkgs.iso", iso_output)
                context.copy_file("vsmkgs.opt", gis_output)
                context.copy_file("vsmkgs.ipt", iso_input)
                context.archive_file(iso_input)
                context.archive_file(gis_output)
                context.archive_file(iso_output)
                iso_file = context.full_path("vsmkgs.iso")

                # Make KML file
                kml_name = in_var.fireID + "_" + str(hr+1) + ".kml"
                kml_path = os.path.join(temp_dir, kml_name)
                self._build_kml(kml_path, in_var, iso_file, contour_names, contour_colors)
                kmz_files.append(kml_path)
                my_kmz.add_kml(kml_name, fireLoc, hr)

                # Add data to GeoJSON file
                if create_json:
                    self._build_json(json, in_var, iso_file, contour_names, contour_colors, fireLoc['id'], timezone, hr)

            # Write input files
            self._write_input(emis, cons, npriod, in_var, input_file, timezone)
            # Run VSMOKE for fire
            context.execute(self.BINARIES['VSMOKE'])

            # Rename input and output files and archive
            fire_input = "VSMOKE_" + fireLoc["id"] + ".IPT"
            fire_output = "VSMOKE_" + fireLoc["id"] + ".OUT"
            context.copy_file("VSMOKE.IPT", fire_input)
            context.copy_file("VSMOKE.OUT", fire_output)
            context.archive_file(fire_input)
            context.archive_file(fire_output)

        # Make KMZ file
        my_kmz.write()
        z = zipfile.ZipFile(kmz_filename, 'w', zipfile.ZIP_DEFLATED)
        for kml in kmz_files:
            if os.path.exists(kml):
                z.write(kml, os.path.basename(kml))
            else:
                self.log.error('Failure while trying to write KMZ file -- KML file does not exist')
                self.log.debug('File "%s" does not exist', kml)
        z.write(os.path.join(self.config('PACKAGE_DIR'), legend_image), legend_image)
        z.close()

        # If necessary, create the GeoJSON output file
        if create_json:
            temp_json = context.full_path(self.config('JSON_FILE'))
            json.write(temp_json)
            final_json = os.path.join(self.config("OUTPUT_DIR"), self.config('JSON_FILE'))
            context.copy_file(temp_json, final_json)

        r = {
            "output": {
                "directory": ,
                "kmz_filename": kmz_filename
            }
        }
        if create_json:
            r['output']['json_file_name'] = final_json
        # TODO: anytheing else to include in response
        return r

    def _write_input(self, emissions, cons, npriod, in_var, input_file, tz):
        """
        This function will create the input file needed to run VSMOKE.
        These parameters are fixed or are not used since user should provide stability.
        """
        hrntvl = 1.0      # The BSF Only deals in 1-hour time steps.
        lstbdy = 'TRUE'   # stability class or daylight data are given
        lqread = 'TRUE'   # emissions are provided
        lsight = 'FALSE'  # we are not calculating crossplume site values
        cc0crt = self.config("CC0CRT", float)
        viscrt = self.config("VISCRT")
        efpm = self.config("EFPM", float)
        efco = self.config("EFCO", float)
        thot = self.config("THOT", float)
        tconst = self.config("TCONST", float)
        tdecay = self.config("TDECAY", float)
        grad_rise = self.config("GRAD_RISE")
        rfrc = self.config("RFRC", float)
        emtqr = self.config("EMTQR", float)

        tons = npriod * (cons["flaming"] + cons["smoldering"] + cons["residual"] + cons["duff"])

        warn = []
        if in_var.temp_fire is None:
            in_var.temp_fire = self.config("TEMP_FIRE", float)
            warn.append('surface temperature')
        if in_var.pres is None:
            in_var.pres = self.config("PRES", float)
            warn.append('surface pressure')
        if in_var.irha is None:
            in_var.irha = self.config("IRHA", int)
            warn.append('relative humidity')
        if in_var.ltofdy is None:
            in_var.ltofdy = self.config("LTOFDY")
            warn.append('sunrise')
        if in_var.stability is None:
            in_var.stability = self.config("STABILITY", int)
            warn.append('stability')
        if in_var.mix_ht is None:
            in_var.mix_ht = self.config("MIX_HT", float)
            warn.append('mixing height')
        if in_var.oyinta is None:
            in_var.oyinta = self.config("OYINTA", float)
            warn.append('horizontal crosswind dispersion')
        if in_var.ozinta is None:
            in_var.ozinta = self.config("OZINTA", float)
            warn.append('vertical crosswind dispersion')
        if in_var.bkgpma is None:
            in_var.bkgpma = self.config("BKGPMA", float)
            warn.append('background PM2.5')
        if in_var.bkgcoa is None:
            in_var.bkgcoa = self.config("BKGCOA", float)
            warn.append('background CO')
        if warn:
            self.log.warn("For fire " + in_var.fireID + ", used default values for the parameters: " + ', '.join(warn))

        with open(input_file, "w") as f:
            f.write("60\n")
            f.write("%s\n" % in_var.title)
            f.write("%f %f %f %d %d %d %d %f %f %s %s %s %f %s\n" % (in_var.alat, in_var.along, tz,
                                                                     in_var.iyear, in_var.imo, in_var.iday, npriod,
                                                                     in_var.hrstrt, hrntvl, lstbdy, lqread, lsight,
                                                                     cc0crt, viscrt))
            f.write("%f %f %f %f %f %f %f %f %s %f\n" % (in_var.acres, tons, efpm, efco, in_var.tfire, thot, tconst,
                                                         tdecay, grad_rise, rfrc))
            for hour in xrange(npriod):
                nhour = hour + 1
                f.write("%d %f %f %d %s %d %f %f %f %f %f %f\n" % (nhour, in_var.temp_fire, in_var.pres, in_var.irha,
                                                                   in_var.ltofdy, in_var.stability, in_var.mix_ht,
                                                                   in_var.ua, in_var.oyinta, in_var.ozinta,
                                                                   in_var.bkgpma, in_var.bkgcoa))

            for hour in xrange(npriod):
                nhour = hour + 1
                emtqh = (emissions["heat"][hour]) / 3414425.94972     # Btu to MW
                emtqpm = (emissions["pm25"][hour].sum()) * 251.99576  # tons/hr to g/s
                emtqco = (emissions["co"][hour].sum()) * 251.99576    # tons/hr to g/s
                f.write("%d %f %f %f %f\n" % (nhour, emtqpm, emtqco, emtqh, emtqr))

    def _write_iso_input(self, emissions, hour, in_var, input_file):
        """ Create the input file needed to run VSMOKEGIS. """
        # Plume rise characteristics
        grad_rise = self.config("GRAD_RISE")
        emtqr = self.config("EMTQR", float)

        # Starting and ending distance point for centerline concentrations
        xbgn = self.config("XBGN", float)
        xend = self.config("XEND", float)

        # self.ISOPLETHS between centerline receptors (0 default is 31 log points)
        xntvl = self.config("XNTVL", float)

        # Tolerance for isolines
        chitol = self.config("TOL", float)

        # Number of isolines
        niso = len(self.ISOPLETHS)

        # Displacement of dispersion output from fire start
        utm_e = self.config("DUTMFE", float)
        utm_n = self.config("DUTMFN", float)

        warn = []
        if in_var.ltofdy is None:
            in_var.ltofdy = self.config("LTOFDY")
            warn.append('sunrise')
        if in_var.stability is None:
            in_var.stability = self.config("STABILITY", int)
            warn.append('stability')
        if in_var.mix_ht is None:
            in_var.mix_ht = self.config("MIX_HT", float)
            warn.append('mixing height')
        if in_var.oyinta is None:
            in_var.oyinta = self.config("OYINTA", float)
            warn.append('horizontal crosswind dispersion')
        if in_var.ozinta is None:
            in_var.ozinta = self.config("OZINTA", float)
            warn.append('vertical crosswind dispersion')
        if in_var.bkgpma is None:
            in_var.bkgpma = self.config("BKGPMA", float)
            warn.append('background PM2.5')
        if warn and (hour == 0):
            self.log.warn("For fire " + in_var.fireID + ", used default values for these parameters: " + ', '.join(warn))

        with open(input_file, "w") as f:
            emtqh = (emissions["heat"][hour]) / 3414425.94972     # Btu to MW
            emtqpm = (emissions["pm25"][hour].sum()) * 251.99576  # tons/hr to g/s

            f.write("%s\n" % in_var.title)
            f.write("%s %f %f %f %f\n" % (grad_rise, in_var.acres, emtqpm, emtqh, emtqr))
            f.write("%s %d %f %f %f %f %f %f\n" % (in_var.ltofdy, in_var.stability, in_var.mix_ht, in_var.ua,
                                                   in_var.wdir, in_var.oyinta, in_var.ozinta, in_var.bkgpma))
            f.write("%f %f %f %f %f %d\n" % (utm_e, utm_n, xbgn, xend, xntvl, niso))
            for interval in self.ISOPLETHS:
                f.write("%d %f\n" % (interval, chitol))

    def _build_isopleths(self, in_var, iso_file):
        """ build isopleth data needed for output files """
        dlat = 1.0 / 111325.0
        dlon = 1.0 / (111325.0 * math.cos(in_var.alat * math.pi / 180.0))
        f = open(iso_file, 'r')
        ds = f.readlines()
        iso = []
        for d in ds:
            q = d.strip().split(' ')
            while q.__contains__(''):
                q.remove('')
            try:
                q.remove('*')
            except:
                pass
            if len(q) > 2:
                iso.append([(float(q[1]), float(q[2]))])
            elif len(q) == 2:
                iso[-1].append((float(q[0]), float(q[1])))
            else:
                iso[-1].append(iso[-1][0])
                pass
        isopleths = {}

        for i, l in zip(iso, self.ISOPLETHS):
            pts = []
            for pt in i:
                x = in_var.along + dlon * pt[0]
                y = in_var.alat + dlat * pt[1]
                pts.append((x, y))
            isopleths[str(int(l))] = pts[1:]

        return isopleths

    def _build_kml(self, kml_file, in_var, iso_file, contour_names, contour_colors):
        """
        Make a KML file.
        Based on runvsmoke.py code used to run VSMOKEGIS
        """
        smoke_color = '2caaaaaa'
        mykml = KMLFile(kml_file)
        for k, interval in enumerate(self.ISOPLETHS):
            mykml.add_style(name=contour_names[k], line_color=contour_colors[k], fill_color=smoke_color)

        isopleths = self._build_isopleths(in_var, iso_file)

        mykml.open_folder('Potential Health Impacts', Open=True)
        for c, interval in enumerate(self.ISOPLETHS):
            name = str(interval)
            mykml.add_placemarker(isopleths[name], name=contour_names[c], TurnOn=1)
        mykml.close_folder()
        mykml.close()
        mykml.write()

    def _build_json(self, json, in_var, iso_file, contour_names, contour_colors, fire_id, timezone, hr):
        isopleths = self._build_isopleths(in_var, iso_file)

        for c, interval in enumerate(self.ISOPLETHS):
            name = str(interval)
            json.add_linestring(fire_id, contour_names[c], contour_colors[c], hr, isopleths[name], timezone)


class GeoJSON:
    """ Used to create GeoJSON outputs """

    def __init__(self):
        self.plume_rings = {}

    def add_linestring(self, fire_id, aqi, color, hr, pts, timezone):
        """ For a particular fire, at a particular time,
        add a new rint of points to the GeoJSON. """
        if fire_id not in self.plume_rings:
            self.plume_rings[fire_id] = {}
        if aqi not in self.plume_rings[fire_id]:
            self.plume_rings[fire_id][aqi] = {}
        if hr not in self.plume_rings[fire_id][aqi]:
            self.plume_rings[fire_id][aqi][hr] = []

        self.plume_rings[fire_id][aqi]['color'] = color
        self.plume_rings[fire_id][aqi]['timezone'] = timezone

        pts.append(pts[0])
        for p in pts:
            self.plume_rings[fire_id][aqi][hr].append(p)

    def write(self, filepath):
        """ Write the JSON to an output file. """
        f = open(filepath, 'w')
        f.write(self.__str__())
        f.close()

    def __str__(self):
        """ Build a string of a single GeoJSON object for each fire,
        inside a great JSON object. """
        # create a master JSON object
        json = '{"fires":['

        fires = []
        # for each fire, create a GeoJSON object
        for fire in self.plume_rings:
            s = '{"fire_id": "' + fire + '", "geo_json": '
            s += '{"type": "FeatureCollection","features":['
            for aqi in self.plume_rings[fire]:
                # add a plume ring for each hour of the fire
                for hr in sorted(self.plume_rings[fire][aqi].keys())[:-2]:
                    # we need at least 4 points to guarantee our inputs are valid rings
                    if len(self.plume_rings[fire][aqi][hr]) <= 3:
                        continue
                    new_feature = '{"type": "Feature","geometry":'
                    new_feature += '{"type": "LineString","coordinates": ['

                    coords = []
                    for pt in self.plume_rings[fire][aqi][hr]:
                        coords.append('[' + str(pt[0]) + ', ' + str(pt[1]) + ']')

                    new_feature += ','.join(coords)
                    new_feature += ']},"properties": {'
                    new_feature += '"AQI": "' + aqi + '",'
                    new_feature += '"color": "' + self.plume_rings[fire][aqi]['color'] + '",'
                    new_feature += '"timezone": ' + str(self.plume_rings[fire][aqi]['timezone']) + ','
                    new_feature += '"hour": ' + str(hr)
                    new_feature += '}},'
                    s += new_feature

            s = s[:-1] + ']}}'
            fires.append(s)

        json += ','.join(fires) + ']}'

        return json

    def __repr__(self):
        return self.__str__()


class KMLFile:
    """ Used to create KML files """

    def __init__(self, filename='test.kml'):
        self.content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><kml xmlns="http://earth.google.com/kml/2.2"><Document>'''
        self.name = filename

    def write(self):
        """ Write the KML content string to a file. """
        output = open(self.name, 'w')
        output.write(self.content)
        output.close()

    def add_style(self, name, line_color='647800F0', fill_color='647800F0', width=2, outline=1, fill=1):
        self.content += '''<Style id="%s"><LineStyle><color>%s</color><width>%d</width></LineStyle><PolyStyle><color>%s</color><fill>%d</fill><outline>%d</outline></PolyStyle></Style>''' %(name, line_color, width, fill_color, fill, outline)

    def close(self):
        self.content += '''</Document></kml>'''

    def open_folder(self, name, Open=True):
        if Open:
            self.content += '''<Folder><name>%s</name>''' % name
        else:
            self.content += '''<Folder><name>%s</name><Style><ListStyle><listItemType>checkHideChildren</listItemType><bgColor>00ffffff</bgColor></ListStyle></Style>''' % name

    def close_folder(self):
        self.content += '''</Folder>'''

    def add_placemarker(self, pts, description = " ", name = " ", TurnOn=0):
        self.content += '''<Placemark><description>%s</description><name>%s</name><visibility>%d</visibility><styleUrl>#%s</styleUrl><Polygon><outerBoundaryIs><LinearRing><coordinates>''' % (description, name, TurnOn, name)
        pts.append(pts[0])
        for p in pts:
            self.content += ','.join([str(p[0]),str(p[1]),'0 '])
        self.content = self.content[:-1]  # Remove extra space
        self.content += '''</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>'''


class KMZAnimation:
    """For creating a KMZ file used for Google Earth"""

    def __init__(self, filename='doc.kml', overlay_title=" ", legend_image=" "):
        self.name = filename
        self.fires = {}
        self.overlay_title = overlay_title
        self.legend_image = legend_image
        self.min_time = ''
        self.max_time = ''
        self.content = ''

    def _add_header(self):
        self.content = '''<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://earth.google.com/kml/2.2">
            <Document>
                <name>%s</name>
                <open>0</open>
                <TimeSpan>
                    <begin>%s</begin>
                    <end>%s</end>
                </TimeSpan>
                <ScreenOverlay>
                    <name>Legend</name>
                    <overlayXY x="0" y="0" xunits="pixel" yunits="pixel"/>
                    <screenXY x="0" y="0" xunits="fraction" yunits="fraction"/>
                    <size x="-1" y="-1" xunits="pixels" yunits="pixels"/>
                    <color>e0ffffff</color>
                    <Icon>%s</Icon>
                </ScreenOverlay>
        ''' % (self.overlay_title, self.min_time.isoformat(), self.max_time.isoformat(), self.legend_image)

    def add_kml(self, kmlfile, fireLoc, hour):
        if fireLoc['id'] not in self.fires:
            self.fires[fireLoc['id']] = []

        fire_dt = fireLoc["date_time"]
        hour_delta = timedelta(hours=1)
        dt = fire_dt + hour_delta * hour
        content = '''
            <NetworkLink>
                <name>%s - %s</name>
                <visibility>1</visibility>
                <TimeSpan><begin>%s</begin><end>%s</end></TimeSpan>
                <Link><href>%s</href></Link>
                <Style>
                    <ListStyle>
                        <listItemType>checkHideChildren</listItemType>
                    </ListStyle>
                </Style>
            </NetworkLink>
            ''' % (fireLoc['id'], dt.strftime('Hour %HZ'), dt.isoformat(), (dt + hour_delta).isoformat(), kmlfile)

        self.fires[fireLoc['id']].append(content)

        if self.min_time == '' or dt < self.min_time:
            self.min_time = dt
        if self.max_time == '' or (dt + hour_delta) > self.max_time:
            self.max_time = dt

    def _add_footer(self):
        self.content += '''
            </Document>
        </kml>
        '''

    def _fill_content(self):
        self.content = ''
        self._add_header()

        for _id in self.fires:
            self.content += """
            <Folder>
                <name>%s</name>
            """ % _id

            self.content += '\n'.join(self.fires[_id])

            self.content += """
            </Folder>"""

        self._add_footer()

    def write(self):
        self._fill_content()
        output = open(self.name, 'w')
        output.write(self.content)
        output.close()


class INPUTVariables:
    """ Defines input variables from Fire Location """
    MIN_STAB = 1
    MAX_STAB = 7
    MAX_MIXHT = 10000
    MIN_WS = 0
    MIN_DIR = 0
    MAX_DIR = 360

    def __init__(self, fireLoc):
        # Basic fire info
        self.fireID = fireLoc['id']
        self.alat = float(fireLoc['latitude'])
        self.along = float(fireLoc['longitude'])
        self.acres = fireLoc['area']

        # Fire Date and time information
        fire_dt = fireLoc['date_time']
        self.iyear = fire_dt.year
        self.imo = fire_dt.month
        self.iday = fire_dt.day
        self.hrstrt = fire_dt.hour
        self.tfire = fire_dt.hour
        self.firestart = fire_dt.strftime('%H%M')

        # Title for input files
        self.title = ("'VSMOKE input for fire ID %s'" % fireLoc['id'])

        # Stability
        self.stability = fireLoc["metadata"].get("vsmoke_stability", None)
        if self.stability:
            self.stability = int(self.stability)
            if self.stability < INPUTVariables.MIN_STAB:
                self.stability = INPUTVariables.MIN_STAB
            elif self.stability > INPUTVariables.MAX_STAB:
                self.stability = INPUTVariables.MAX_STAB

        # Mixing Height
        self.mix_ht = fireLoc['metadata'].get('vsmoke_mixht', None)
        if self.mix_ht:
            self.mix_ht = float(self.mix_ht)
            if self.mix_ht > INPUTVariables.MAX_MIXHT:
                self.mix_ht = INPUTVariables.MAX_MIXHT

        # Wind speed
        self.ua = fireLoc['metadata'].get('vsmoke_ws', None)
        if self.ua:
            self.ua = float(self.ua)
            if self.ua <= INPUTVariables.MIN_WS:
                self.ua = INPUTVariables.MIN_WS + 0.001

        # Wind direction
        self.wdir = fireLoc["metadata"].get("vsmoke_wd", None)
        if self.wdir:
            self.wdir = float(self.wdir)
            if self.wdir <= INPUTVariables.MIN_DIR:
                self.wdir = INPUTVariables.MIN_DIR + 0.001
            elif self.wdir > INPUTVariables.MAX_DIR:
                self.wdir = INPUTVariables.MAX_DIR

        # Surface temperature
        self.temp_fire = fireLoc["metadata"].get("vsmoke_temp", None)
        if self.temp_fire:
            self.temp_fire = float(self.temp_fire)

        # Surface pressure
        self.pres = fireLoc["metadata"].get("vsmoke_pressure", None)
        if self.pres:
            self.pres = float(self.pres)

        # Surface relative humidity
        self.irha = fireLoc["metadata"].get("vsmoke_rh", None)
        if self.irha:
            self.irha = int(self.irha)

        # Is fire during daylight hours or nighttime
        self.ltofdy = fireLoc["metadata"].get("vsmoke_sun", None)
        if self.ltofdy:
            self.ltofdy = str(self.ltofdy)

        # Initial horizontal dispersion
        self.oyinta = fireLoc["metadata"].get("vsmoke_oyinta", None)
        if self.oyinta:
            self.oyinta = float(self.oyinta)

        # Initial vertical dispersion
        self.ozinta = fireLoc["metadata"].get("vsmoke_ozinta", None)
        if self.ozinta:
            self.ozinta = float(self.ozinta)

        # Background PM 2.5
        self.bkgpma = fireLoc["metadata"].get("vsmoke_bkgpm", None)
        if self.bkgpma:
            self.bkgpma = float(self.bkgpma)

        # Background CO
        self.bkgcoa = fireLoc["metadata"].get("vsmoke_bkgco", None)
        if self.bkgcoa:
            self.bkgcoa = float(self.bkgcoa)
