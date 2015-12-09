"""bluesky.dispersers.vsmoke

The code in this module was copied from BlueSky Framework, and modified
significantly (mostly in VSMOKEDispersion).  It was originally written
by Sonoma Technology, Inc.
"""

__author__      = "Joel Dubowy and Sonoma Technology, Inc."
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__version__ = "0.1.0"

import logging
import math
import os
import zipfile
import shutil
from datetime import timedelta

from pyairfire.datetime import parsing as datetime_parsing

from bluesky.datetimeutils import parse_utc_offset

from .. import DispersionBase

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

    def __init__(self, met_info, **config):
        super(VSMOKEDispersion, self).__init__(met_info, **config)
        self._create_json = self.config("CREATE_JSON")
        self._set_input_file_vars()
        self._set_kml_vars()
        self.log.debug("PM Isopleths =%s" % self.ISOPLETHS)
        self.log.debug("PM Isopleths Names =%s" % self.ISONAMES)
        self.log.debug("PM Isopleths Colors =%s" % self.ISOCOLORS)

    def _set_input_file_vars(self):
        self._input_file = os.path.join(wdir, "VSMOKE.IPT")
        self._iso_input_file = os.path.join(wdir, "vsmkgs.ipt")

    def _set_kml_vars(self):
        # Define variables to make KML and KMZ files
        doc_kml = os.path.join(wdir, "doc.kml")
        self.log.debug("Fire kmz = %s" % doc_kml)
        self._kmz_files = [doc_kml]

        self._kmz_filename = os.path.join(self._run_output_dir, self.config("KMZ_FILE"))
        # The following will fill start date time into kmz file name if the
        # filename has an embedded datetime pattern
        self._kmz_filename = self._model_start.strftime(self._kmz_filename)
        self.log.debug("Creating KMZ file " + os.path.basename(self._kmz_filename))

        # Make KMZ object for fire
        self._legend_image = self.config("LEGEND_IMAGE")
        my_kmz = KMZAnimation(doc_kml, self.config("OVERLAY_TITLE"), legend_image)

    def _run(self, fires, wdir):
        """Runs hysplit

        args:
         - fires -- list of fires to run through VSMOKE
         - wdir -- working directory
        """
        # For each fire run VSMOKE and VSMOKEGIS
        for fire in fires:
            # TODO: check to make sure start+num_hours is within fire's
            #   growth windows
            in_var = INPUTVariables(fireLoc)

            utc_offset = fire.get('location', {}).get('utc_offset')
            utc_offset = parse_utc_offset(utc_offset) if utc_offset else 0.0
            # TODO: remove following line nad just rename 'timezone' to
            #  'utc_offset' in all subsequent code
            timezone = utc_offset

            # Get emissions for fire
            cons = datautils.sum_nested_data(
                [fb["consumption"] for fb in fire['fuelbeds']], 'summary', 'total')
            emis = datautils.sum_nested_data(
                [fb["emissions"] for fb in fire['fuelbeds']], 'summary', 'total')
            if not cons or not emis:
                continue
            npriod = len(emis.time)
            self.log.debug("%d hour run time for fireID %s" % (npriod, fireLoc["id"]))

            # Run VSMOKE GIS for each hour
            for hr in xrange(npriod):
                # Make input file to be used by VSMOKEGIS
                self._write_iso_input(emis, hr, in_var)

                # Run VSMOKEGIS
                context.execute(BINARIES['VSMOKEGIS'])

                # Rename input and output files and archive
                iso_output = "VSMKGS_" + fireLoc["id"] + "_hour" + str(hr+1) + ".iso"
                gis_output = "VSMKGS_" + fireLoc["id"] + "_hour" + str(hr+1) + ".opt"
                iso_input = "VSMKGS_" + fireLoc["id"] + "_hour" + str(hr+1) + ".ipt"
                context.copy_file("vsmkgs.iso", iso_output)
                context.copy_file("vsmkgs.opt", gis_output)
                context.copy_file("vsmkgs.ipt", iso_input)
                self._save_file(iso_input)
                self._save_file(gis_output)
                self._save_file(iso_output)
                iso_file = context.full_path("vsmkgs.iso")

                # Make KML file
                kml_name = in_var.fireID + "_" + str(hr+1) + ".kml"
                kml_path = os.path.join(temp_dir, kml_name)
                self._build_kml(kml_path, in_var, iso_file)
                self._kmz_files.append(kml_path)
                my_kmz.add_kml(kml_name, fireLoc, hr)

                self._add_geo_json(in_var, iso_file, fireLoc['id'], timezone, hr)

            # Write input files
            self._write_input(emis, cons, npriod, in_var, timezone)
            # Run VSMOKE for fire
            context.execute(self.BINARIES['VSMOKE'])

            # Rename input and output files and archive
            fire_input = "VSMOKE_" + fireLoc["id"] + ".IPT"
            fire_output = "VSMOKE_" + fireLoc["id"] + ".OUT"
            context.copy_file("VSMOKE.IPT", fire_input)
            context.copy_file("VSMOKE.OUT", fire_output)
            self._save_file(fire_input)
            self._save_file(fire_output)

        # Make KMZ file
        my_kmz.write()
        z = zipfile.ZipFile(self._kmz_filename, 'w', zipfile.ZIP_DEFLATED)
        for kml in self._kmz_files:
            if os.path.exists(kml):
                z.write(kml, os.path.basename(kml))
            else:
                self.log.error('Failure while trying to write KMZ file -- KML file does not exist')
                self.log.debug('File "%s" does not exist', kml)
        z.write(os.path.join(self.config('PACKAGE_DIR'), self._legend_image), self._legend_image)
        z.close()

        r = {
            "output": {
                "kmz_filename": self._kmz_filename
            }
        }

        json_file_name = self._create_geo_json()
        if json_file_name:
            r['output']['json_file_name'] = json_file_name
        # TODO: anytheing else to include in response
        return r

    def _write_input(self, emissions, cons, npriod, in_var, tz):
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

        with open(self._input_file, "w") as f:
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

    def _write_iso_input(self, emissions, hour, in_var):
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

        with open(self._iso_input_file, "w") as f:
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

    def _build_kml(self, kml_file, in_var, iso_file):
        """
        Make a KML file.
        Based on runvsmoke.py code used to run VSMOKEGIS
        """
        smoke_color = '2caaaaaa'
        mykml = KMLFile(kml_file)
        for k, interval in enumerate(self.ISOPLETHS):
            mykml.add_style(name=self.ISONAMES[k], line_color=self.ISOCOLORS[k], fill_color=smoke_color)

        isopleths = self._build_isopleths(in_var, iso_file)

        mykml.open_folder('Potential Health Impacts', Open=True)
        for c, interval in enumerate(self.ISOPLETHS):
            name = str(interval)
            mykml.add_placemarker(isopleths[name], name=self.ISONAMES[c], TurnOn=1)
        mykml.close_folder()
        mykml.close()
        mykml.write()

    def _add_geo_json(self, json, in_var, iso_file, fire_id, timezone, hr):
        if not self._create_json:
            return

        if not self._geo_json:
            self._geo_json = GeoJSON()

        isopleths = self._build_isopleths(in_var, iso_file)

        for c, interval in enumerate(self.ISOPLETHS):
            name = str(interval)
            self._geo_json.add_linestring(fire_id, self.ISONAMES[c], self.ISOCOLORS[c], hr, isopleths[name], timezone)

    def _create_geo_json(self, wdir):
        if self._create_json and self._geo_json:
            temp_json = os.path.join(wdir, self.config('JSON_FILE'))
            self._geo_json.write(temp_json)
            final_json = os.path.join(self._run_output_dir,
                self.config('JSON_FILE'))
            context.copy_file(temp_json, final_json)
            return final_json

class GeoJSON(object):
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


class KMLFile(object):
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


class KMZAnimation(object):
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


class INPUTVariables(object):
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
        self.alat = float(fireLoc['location']['latitude'])
        self.along = float(fireLoc['location']['longitude'])
        self.acres = fireLoc['location']['area']

        # Fire Date and time information
        fire_dt = datetime_parsing.parse(fireLoc['growth'][0]['start'])
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
