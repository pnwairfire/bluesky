import argparse
import json
import logging
import sys
import zipfile

from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime

KML_HEADER = '''<?xml version="1.0" encoding="utf-8" ?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document id="root_doc">

	<Style id="dotStyle">
    <IconStyle>
      <scale>0.4</scale> <!-- Adjust icon size -->
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
      </Icon>
    </IconStyle>
    <LabelStyle>
      <scale>0</scale> <!-- Hide label if desired -->
    </LabelStyle>
  </Style>

  <Style id="redDotStyle">
    <IconStyle><color>ff0000ff</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ff0000ff</color><width>2</width></LineStyle>
  </Style>

  <Style id="oraDotStyle">
    <IconStyle><color>ff00a5ff</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ff00a5ff</color><width>2</width></LineStyle>
  </Style>

  <Style id="yelDotStyle">
    <IconStyle><color>ff00ffff</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ff00ffff</color><width>2</width></LineStyle>
  </Style>

  <Style id="greDotStyle">
    <IconStyle><color>ff00ff00</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ff00ff00</color><width>2</width></LineStyle>
  </Style>

  <Style id="bluDotStyle">
    <IconStyle><color>ffff8800</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ffff8800</color><width>2</width></LineStyle>
  </Style>

  <Style id="pinkDotStyle">
    <IconStyle><color>ffb469ff</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ffb469ff</color><width>2</width></LineStyle>
  </Style>

  <Style id="darkPurpleDotStyle">
    <IconStyle><color>ff820000</color><scale>0.6</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>ff820000</color><width>2</width></LineStyle>
  </Style>

<Schema name="hysplit_trajectories" id="hysplit_trajectories">
	<SimpleField type="string" name="Description"/>
	<SimpleField type="string" name="Name"/>
	<SimpleField name="fire_id" type="string"></SimpleField>
	<SimpleField name="location_lat" type="float"></SimpleField>
	<SimpleField name="location_lng" type="float"></SimpleField>
	<SimpleField name="start_hour" type="string"></SimpleField>
	<SimpleField name="hour" type="int"></SimpleField>
	<SimpleField name="point_lat" type="float"></SimpleField>
	<SimpleField name="point_lng" type="float"></SimpleField>
	<SimpleField name="point_height" type="float"></SimpleField>
	<SimpleArrayField name="heights" type="float"></SimpleArrayField>
</Schema>
'''

KML_FOOTER = '''
</Document></kml>'''

STYLE_MAP = {
    10: ('redDotStyle', 'ff0000ff'),      # Red (ff0000ff = alpha,blue,green,red)
    50: ('oraDotStyle', 'ff00a5ff'),      # Orange (ff00a5ff = alpha,blue,green,red)
    100: ('yelDotStyle', 'ff00ffff'),     # Yellow
    500: ('greDotStyle', 'ff00ff00'),     # Green (ff00ff00 = alpha,blue,green,red)
    1000: ('pinkDotStyle', 'ffb469ff'),   # Pink (ffb469ff = alpha,blue,green,red)
    2000: ('bluDotStyle', 'ffff0000'),    # Blue (ffff0000 = alpha,blue,green,red)
    5000: ('darkPurpleDotStyle', 'ff820000'),  # Dark Purple (ff820000 = alpha,blue,green,red)
}

def format_datetime(dt_str):
    """Convert ISO datetime to readable format"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    except:
        return dt_str

def add_extended_data(parent, **fields):
    """Helper to add extended data to a placemark"""
    ext_data = SubElement(parent, 'ExtendedData')
    schema_data = SubElement(ext_data, 'SchemaData', schemaUrl='#hysplit_trajectories')
    for name, value in fields.items():
        field = SubElement(schema_data, 'SimpleData', name=name)
        field.text = str(value)
    return schema_data

def create_trajectory_points(parent, points, fire_id, formatted_time, style_name):
    """Create placemarks for each point in the trajectory"""
    trajectory_points = []
    for hour, point in enumerate(points):
        lat, lng, alt = point if len(point) >= 3 else (point[0], point[1], 0)
        trajectory_points.append((lng, lat, alt))
        
        # Create point placemark
        placemark = SubElement(parent, 'Placemark')
        add_extended_data(placemark,
            fire_id=fire_id,
            start_hour=formatted_time,
            hour=hour,
            point_lat=lat,
            point_lng=lng,
            point_height=alt
        )
        
        # Add style and coordinates
        SubElement(placemark, 'styleUrl').text = f'#{style_name}'
        coords = SubElement(SubElement(placemark, 'Point'), 'coordinates')
        coords.text = f'{lng},{lat},0'
    
    return trajectory_points

def create_trajectory_line(parent, points, fire_id, location, formatted_time, height, color):
    """Create a line connecting all points in the trajectory"""
    placemark = SubElement(parent, 'Placemark')
    SubElement(placemark, 'name').text = f'{height} m'
    
    # Add line style
    line_style = SubElement(SubElement(placemark, 'Style'), 'LineStyle')
    SubElement(line_style, 'color').text = color
    
    # Add extended data
    add_extended_data(placemark,
        fire_id=fire_id,
        location_lat=location['lat'],
        location_lng=location['lng'],
        start_hour=formatted_time,
        heights=f"({len(points)}:{height},{','.join(str(p[2]) for p in points)})"
    )
    
    # Add line geometry
    coords = SubElement(SubElement(placemark, 'LineString'), 'coordinates')
    coords.text = ' '.join(f'{p[0]},{p[1]}' for p in points)

def create_point_placemark(parent, fire_id, start_time, hour, lat, lng, alt, style_name):
    """Create a point placemark with all necessary data"""
    placemark = SubElement(parent, 'Placemark')
    
    # Add extended data
    schema_data = SubElement(SubElement(placemark, 'ExtendedData'), 'SchemaData', schemaUrl='#hysplit_trajectories')
    
    # Add all metadata
    SubElement(schema_data, 'SimpleData', name='fire_id').text = fire_id
    SubElement(schema_data, 'SimpleData', name='start_hour').text = start_time
    SubElement(schema_data, 'SimpleData', name='hour').text = str(hour)
    SubElement(schema_data, 'SimpleData', name='point_lat').text = str(lat)
    SubElement(schema_data, 'SimpleData', name='point_lng').text = str(lng)
    SubElement(schema_data, 'SimpleData', name='point_height').text = str(alt)
    
    # Add style and coordinates
    SubElement(placemark, 'styleUrl').text = f'#{style_name}'
    SubElement(SubElement(placemark, 'Point'), 'coordinates').text = f'{lng},{lat},0'

def create_line_placemark(parent, fire_id, location, formatted_time, height, color, points):
    """Create a line placemark with all necessary data"""
    placemark = SubElement(parent, 'Placemark')
    SubElement(placemark, 'name').text = f'{height} m'
    
    # Add style
    line_style = SubElement(SubElement(placemark, 'Style'), 'LineStyle')
    SubElement(line_style, 'color').text = color
    
    # Add extended data
    schema_data = SubElement(SubElement(placemark, 'ExtendedData'), 'SchemaData', schemaUrl='#hysplit_trajectories')
    
    SubElement(schema_data, 'SimpleData', name='fire_id').text = fire_id
    SubElement(schema_data, 'SimpleData', name='location_lat').text = str(location['lat'])
    SubElement(schema_data, 'SimpleData', name='location_lng').text = str(location['lng'])
    SubElement(schema_data, 'SimpleData', name='start_hour').text = formatted_time
    
    # Create heights data
    heights = [str(p[2]) for p in points]
    SubElement(schema_data, 'SimpleData', name='heights').text = f"({len(heights)}:{height},{','.join(heights)})"
    
    # Add line geometry
    coords = [f'{p[0]},{p[1]}' for p in points]
    SubElement(SubElement(placemark, 'LineString'), 'coordinates').text = ' '.join(coords)

def json_to_kml(data):
    """Convert JSON data to KML format"""
    kml_parts = [KML_HEADER]
    
    # Create main folder
    folder = Element('Folder')
    SubElement(folder, 'name').text = 'hysplit_trajectories'
    
    # Process each fire
    for fire in data.get('fires', []):
        fire_id = fire.get('id', 'unknown')
        
        # Create fire folder
        fire_folder = SubElement(folder, 'Folder')
        SubElement(fire_folder, 'name').text = f'Fire: {fire_id}'
        
        # Create locations folder
        locations_folder = SubElement(fire_folder, 'Folder')
        SubElement(locations_folder, 'name').text = 'Locations'

        # Process each location with its trajectories
        if fire.get('locations'):
            for idx, location in enumerate(fire['locations']):
                # Create location folder
                location_folder = SubElement(locations_folder, 'Folder')
                SubElement(location_folder, 'name').text = f'Location {idx + 1}'

                # Add location placemark
                origin = SubElement(location_folder, 'Placemark')
                SubElement(origin, 'name').text = 'Origin'
                
                # Add origin extended data
                schema_data = SubElement(SubElement(origin, 'ExtendedData'), 'SchemaData', schemaUrl='#hysplit_trajectories')
                SubElement(schema_data, 'SimpleData', name='fire_id').text = fire_id                # Add location-specific data and style
                SubElement(schema_data, 'SimpleData', name='location_lat').text = str(location['lat'])
                SubElement(schema_data, 'SimpleData', name='location_lng').text = str(location['lng'])
                SubElement(origin, 'styleUrl').text = '#dotStyle'
                SubElement(SubElement(origin, 'Point'), 'coordinates').text = f"{location['lng']},{location['lat']}"

                # Create Times folder
                times_folder = SubElement(location_folder, 'Folder')
                SubElement(times_folder, 'name').text = 'Times'

                # Group trajectories by time first
                time_groups = {}
                for line in location.get('lines', []):
                    start_time = line.get('start', 'unknown')
                    formatted_time = format_datetime(start_time)
                    height = line.get('height', 0)
                    if formatted_time not in time_groups:
                        time_groups[formatted_time] = []
                    time_groups[formatted_time].append(line)
                
                # Process each time group
                for formatted_time, lines in time_groups.items():
                    # Create time folder
                    time_folder = SubElement(times_folder, 'Folder')
                    time_name = SubElement(time_folder, 'name')
                    date_part = formatted_time.split()[0].replace('/', '')  # YYYYMMDD
                    time_part = formatted_time.split()[1][:5].replace(':', '')  # HHMM
                    time_name.text = f'hour: {date_part}_{time_part}'
                    
                        # Process each height within this time
                    for line in lines:
                        height = line.get('height', 0)
                        points = line.get('points', [])
                        all_points = []
                        point_hour = 0
                        # Get style and color based on height
                        style_name, color = STYLE_MAP.get(height, ('dotStyle', 'ff000000'))
                        
                        # Create height folder
                        height_folder = SubElement(time_folder, 'Folder')
                        height_name = SubElement(height_folder, 'name')
                        height_name.text = f'{height} m'
                        
                        # Create points folder
                        points_folder = SubElement(height_folder, 'Folder')
                        SubElement(points_folder, 'name').text = 'points'

                        # First collect all points
                        for point in points:
                            lat, lng, alt = point if len(point) >= 3 else (point[0], point[1], 0)
                            all_points.append((lng, lat, alt))
                        
                        # Create line placemark first (so it appears under the points)
                        if all_points:
                            line_placemark = SubElement(height_folder, 'Placemark')
                            line_name = SubElement(line_placemark, 'name')
                            line_name.text = f'{height} m'
                            # Use the same style for line
                            SubElement(line_placemark, 'styleUrl').text = f'#{style_name}'
                            # Add line coordinates in sequence
                            line_geom = SubElement(line_placemark, 'LineString')
                            line_coords = SubElement(line_geom, 'coordinates')
                            line_coords.text = ' '.join(f'{lng},{lat},{alt}' for lng, lat, alt in all_points)

                        # Then create points
                        point_hour = 0
                        for lng, lat, alt in all_points:
                            # Create point placemark
                            placemark = SubElement(points_folder, 'Placemark')
                            schema_data = SubElement(SubElement(placemark, 'ExtendedData'), 'SchemaData', schemaUrl='#hysplit_trajectories')
                            
                            SubElement(schema_data, 'SimpleData', name='fire_id').text = fire_id
                            SubElement(schema_data, 'SimpleData', name='start_hour').text = formatted_time
                            SubElement(schema_data, 'SimpleData', name='hour').text = str(point_hour)
                            SubElement(schema_data, 'SimpleData', name='point_lat').text = str(lat)
                            SubElement(schema_data, 'SimpleData', name='point_lng').text = str(lng)
                            SubElement(schema_data, 'SimpleData', name='point_height').text = str(alt)
                            
                            # Use the predefined style from STYLE_MAP
                            SubElement(placemark, 'styleUrl').text = f'#{style_name}'
                            SubElement(SubElement(placemark, 'Point'), 'coordinates').text = f'{lng},{lat},{alt}'
                            
                            point_hour += 1
                        
                        # Use the same style as points for consistency
                        SubElement(line_placemark, 'styleUrl').text = f'#{style_name}'
                        
                        # Add extended data
                        extended_data = SubElement(line_placemark, 'ExtendedData')
                        schema_data = SubElement(extended_data, 'SchemaData', schemaUrl='#hysplit_trajectories')
                        
                        fire_id_data = SubElement(schema_data, 'SimpleData', name='fire_id')
                        fire_id_data.text = fire_id
                        
                        lat_data = SubElement(schema_data, 'SimpleData', name='location_lat')
                        lat_data.text = str(location['lat'])
                        lng_data = SubElement(schema_data, 'SimpleData', name='location_lng')
                        lng_data.text = str(location['lng'])
                        
                        start_data = SubElement(schema_data, 'SimpleData', name='start_hour')
                        start_data.text = formatted_time
                        
                        # Create heights data
                        heights_list = [str(point[2]) for point in all_points]
                        heights_data = SubElement(schema_data, 'SimpleData', name='heights')
                        heights_data.text = f"({len(heights_list)}:{height},{','.join(heights_list)})"
                        
                        # Add line geometry
                        line_geom = SubElement(line_placemark, 'LineString')
                        line_coords = SubElement(line_geom, 'coordinates')
                        coord_strings = [f'{lng},{lat}' for lng, lat, _ in all_points]
                        line_coords.text = ' '.join(coord_strings)



    
    # Convert folder to string with proper formatting (avoid duplicate XML declarations)
    formatted_xml = tostring(folder, encoding='unicode')
    
    kml_parts.append(formatted_xml)
    kml_parts.append(KML_FOOTER)
    
    return '\n'.join(kml_parts)

def transform_json_to_kml(json_file_name,output_file_name):
    
    try:
        with open(json_file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        kml_str = json_to_kml(data)
        
        with zipfile.ZipFile(output_file_name, 'w', zipfile.ZIP_DEFLATED) as kmz:
            kmz.writestr('doc.kml', kml_str)
        
        logging.info(f"KML file written to {output_file_name}")
    except Exception as e:
        logging.error(f"Error: {e}", file=sys.stderr)
