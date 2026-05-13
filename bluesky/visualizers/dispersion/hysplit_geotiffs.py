import logging
import os

import boto3
from botocore.exceptions import NoCredentialsError
from osgeo import gdal


__all__ = [
    'create_hysplit_geotiffs'
]

def create_hysplit_geotiffs(hysplit_output_nc_file, output_dir, filename_template):
    """Parses HYSPLIT NetCDF to extract time/layer info and
    exports each hour of the surface layer as a reprojected geotiff.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Open the specific PM25 subdataset (format: NETCDF:"filename":variable)
    sd_path = f'NETCDF:"{hysplit_output_nc_file}":PM25'
    ds = gdal.Open(sd_path)

    if not ds:
        logging.error(f"Could not read PM2.5 data from hysplit output {hysplit_output_nc_file}.")
        return

    # TODO: make sure this always extracts surface layer

    # In GDAL, the bands represent the product of Time x Layers
    total_bands = ds.RasterCount

    # Metadata extraction (parsed from NC_GLOBAL)
    metadata = ds.GetMetadata_Dict()
    nlays = int(metadata.get('NC_GLOBAL#NLAYS', 1))
    tsteps = total_bands // nlays

    logging.debug(f"Detected Dimensions: {tsteps} hours, {nlays} layer(s).")

    # Extract spatial parameters from metadata
    # Note: Metadata values are returned as strings, so we cast them to float/int
    left = float(metadata.get('NC_GLOBAL#XORIG'))
    bottom = float(metadata.get('NC_GLOBAL#YORIG'))
    x_cell = float(metadata.get('NC_GLOBAL#XCELL'))
    y_cell = float(metadata.get('NC_GLOBAL#YCELL'))
    ncols = int(metadata.get('NC_GLOBAL#NCOLS'))
    nrows = int(metadata.get('NC_GLOBAL#NROWS'))

    # Calculate the Right and Top boundaries
    right = left + (ncols * x_cell)
    top = bottom + (nrows * y_cell)

    # Define the output bounds for GDAL (format: [min_x, max_y, max_x, min_y])
    calc_bounds = [left, top, right, bottom]

    # Loop through each hour (surface layer is always the first set of bands)
    for hour in range(0, tsteps):
        output_name = os.path.join(output_dir, filename_template.format(hour=hour))
        full_dir = os.path.dirname(output_name)
        if not os.path.exists(full_dir):
            os.makedirs(full_dir)

        # 1. Translate: Extract specific band and assign spatial bounds
        # Note: In GDAL, Band 1 = Hour 1/Layer 1, Band 2 = Hour 2/Layer 1...
        tmp_ds = gdal.Translate(
            '', ds, format='VRT',
            bandList=[hour + 1], # 1-based indexing
            outputSRS='EPSG:4326',
            outputBounds=calc_bounds,
            noData=0
        )

        # 2. Warp: Ensure final projection alignment and add Alpha channel for MapLibre
        gdal.Warp(
            output_name, tmp_ds,
            dstSRS='EPSG:4326',
            dstAlpha=True,
            creationOptions=['COMPRESS=DEFLATE', 'TILED=YES']
        )

        if (hour+1) % 10 == 0:
            logging.debug(f"Finished generating {hour+1} hours of geotiffs")

    logging.debug(f"Done creating geotiffs. Files saved in: {output_dir}")
    return tsteps


def upload_to_s3(s3_info, num_hours, output_dir, filename_template):
    """
    Uploads a file to an S3 bucket.
    """
    s3 = boto3.client('s3')

    try:
        for hour in range(0, num_hours):
            try:
                f = filename_template.format(hour=hour)
                local_file = os.path.join(output_dir, f)
                s3_key = os.path.join(s3_info['key_prefix'], f)
                s3.upload_file(local_file, s3_info['bucket'], s3_key)
                logging.debug(f"Successfully uploaded {s3_key}")

            except FileNotFoundError as e:
                logging.debug(f"Failed to find geotiff file {local_file} to upload to s3")

    except NoCredentialsError as e:
        logging.debug("AWS credentials not available. Check your ~/.aws/credentials file.")
