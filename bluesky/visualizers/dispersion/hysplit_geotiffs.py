import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import boto3
import numpy as np
from botocore.exceptions import NoCredentialsError
from osgeo import gdal


__all__ = [
    'create_hysplit_geotiffs'
]


def create_hysplit_geotiffs(geotiffs_config, hysplit_output_file, vis_output_directory):
    if not geotiffs_config.get('enabled'):
        return

    def _replace_vis_dir(p):
        return p.replace('{vis_dir}', vis_output_directory)

    output_dir = _replace_vis_dir(geotiffs_config.get('output_dir'))

    filename_templates = {
        k: _replace_vis_dir(v)
        for k, v in geotiffs_config.get('filename_templates', {}).items()
    }

    daily_utc_offsets = geotiffs_config.get('daily_utc_offsets', [])

    result = _create_geotiffs(
        hysplit_output_file, output_dir,
        filename_templates, daily_utc_offsets
    )

    if not result:
        return

    info = {
        "output_dir": output_dir,
        "filename_templates": filename_templates,
        "num_hours": result['tsteps'],
    }

    s3_info = geotiffs_config.get('s3')
    if s3_info and s3_info.get('bucket') and s3_info.get('key_prefix'):
        upload_to_s3(
            s3_info, result['tsteps'], result['start_dt'],
            daily_utc_offsets, output_dir, filename_templates
        )
        info['s3'] = s3_info

    return info


def _get_start_datetime(metadata):
    """Extract the UTC start datetime from HYSPLIT NetCDF metadata (CMAQ format).

    Expects NC_GLOBAL#SDATE in YYYYDDD (Julian date) format and
    NC_GLOBAL#STIME in HHMMSS format.
    """
    sdate_str = metadata.get('NC_GLOBAL#SDATE')
    stime_str = metadata.get('NC_GLOBAL#STIME', '0')

    if not sdate_str:
        return None

    sdate = int(sdate_str)
    year = sdate // 1000
    day_of_year = sdate % 1000

    stime = int(stime_str)
    hour = stime // 10000
    minute = (stime % 10000) // 100
    second = stime % 100

    return (datetime(year, 1, 1, tzinfo=timezone.utc)
            + timedelta(days=day_of_year - 1, hours=hour, minutes=minute, seconds=second))


def _group_hours_by_day(tsteps, start_dt, utc_offset):
    """Group hour indices by their local calendar day for the given UTC offset.

    Returns a dict mapping timezone-aware midnight datetime to list of hour indices.
    """
    local_tz = timezone(timedelta(hours=utc_offset))
    days = defaultdict(list)
    for hour in range(tsteps):
        utc_time = start_dt + timedelta(hours=hour)
        local_time = utc_time.astimezone(local_tz)
        local_day = local_time.replace(hour=0, minute=0, second=0, microsecond=0)
        days[local_day].append(hour)
    return days


def _write_array_as_geotiff(arr, output_path, ref_ds):
    """Write a 2D numpy array as a warped geotiff using ref_ds for spatial info."""
    full_dir = os.path.dirname(output_path)
    if full_dir and not os.path.exists(full_dir):
        os.makedirs(full_dir)

    nrows, ncols = arr.shape
    mem_driver = gdal.GetDriverByName('MEM')
    mem_ds = mem_driver.Create('', ncols, nrows, 1, gdal.GDT_Float32)
    mem_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    mem_ds.SetProjection(ref_ds.GetProjection())

    band = mem_ds.GetRasterBand(1)
    band.WriteArray(arr.astype(np.float32))
    band.SetNoDataValue(0)

    gdal.Warp(
        output_path, mem_ds,
        dstSRS='EPSG:4326',
        dstAlpha=True,
        creationOptions=['COMPRESS=DEFLATE', 'TILED=YES']
    )
    mem_ds = None


def _create_geotiffs(hysplit_output_nc_file, output_dir, filename_templates, daily_utc_offsets):
    """Parses HYSPLIT NetCDF to extract time/layer info and exports geotiffs for:
    - each hour of the surface layer (hourly)
    - running 3-hour averages
    - daily averages and maximums per UTC offset
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Open the specific PM25 subdataset (format: NETCDF:"filename":variable)
    sd_path = f'NETCDF:"{hysplit_output_nc_file}":PM25'
    ds = gdal.Open(sd_path)

    if not ds:
        logging.error(f"Could not read PM2.5 data from hysplit output {hysplit_output_nc_file}.")
        return None

    # TODO: make sure this always extracts surface layer

    bounds, start_dt, tsteps = _get_metadata(ds)

    filename_template_hourly = filename_templates.get('hourly')
    filename_template_3hr = filename_templates.get('3hr')
    filename_template_daily_avg = filename_templates.get('daily_avg')
    filename_template_daily_max = filename_templates.get('daily_max')

    _create_hourly_geotiffs(ds, bounds, output_dir, filename_template_hourly, tsteps)

    if (filename_template_daily_avg or filename_template_daily_max) and not start_dt:
        logging.warning(
            "Cannot generate daily geotiffs: unable to extract start datetime "
            "from NetCDF metadata (missing NC_GLOBAL#SDATE)."
        )
        filename_template_daily_avg = None
        filename_template_daily_max = None


    if filename_template_3hr or filename_template_daily_avg or filename_template_daily_max:
        band_arrays = np.array([
            ds.GetRasterBand(h + 1).ReadAsArray().astype(np.float64)
            for h in range(tsteps)
        ])
        # Reference VRT provides the correct geotransform and projection for
        # averaged products written via _write_array_as_geotiff
        ref_vrt = gdal.Translate(
            '', ds, format='VRT',
            bandList=[1],
            outputSRS='EPSG:4326',
            outputBounds=bounds,
            noData=0
        )

        _create_3hr_geotiffs(band_arrays, ref_vrt, output_dir, filename_template_3hr, tsteps)
        _create_daily_geotiffs(band_arrays, ref_vrt, output_dir,
            filename_template_daily_avg, filename_template_daily_max,
            tsteps, start_dt, daily_utc_offsets)

    logging.debug(f"All geotiffs saved in: {output_dir}")
    return {'tsteps': tsteps, 'start_dt': start_dt, "bounds": bounds}

def _get_metadata(ds):
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
    bounds = [left, top, right, bottom]

    start_dt = _get_start_datetime(metadata)

    return bounds, start_dt, tsteps

def _create_hourly_geotiffs(ds, bounds, output_dir, filename_template_hourly, tsteps):
    if filename_template_hourly:
        for hour in range(tsteps):
            output_name = os.path.join(output_dir, filename_template_hourly.format(hour=hour))
            full_dir = os.path.dirname(output_name)
            if full_dir and not os.path.exists(full_dir):
                os.makedirs(full_dir)

            # 1. Translate: Extract specific band and assign spatial bounds
            # Note: In GDAL, Band 1 = Hour 1/Layer 1, Band 2 = Hour 2/Layer 1...
            tmp_ds = gdal.Translate(
                '', ds, format='VRT',
                bandList=[hour + 1],  # 1-based indexing
                outputSRS='EPSG:4326',
                outputBounds=bounds,
                noData=0
            )

            # 2. Warp: Ensure final projection alignment and add Alpha channel for MapLibre
            gdal.Warp(
                output_name, tmp_ds,
                dstSRS='EPSG:4326',
                dstAlpha=True,
                creationOptions=['COMPRESS=DEFLATE', 'TILED=YES']
            )

            if (hour + 1) % 10 == 0:
                logging.debug(f"Finished generating {hour + 1} hours of geotiffs")

        logging.debug("Done creating hourly geotiffs.")


def _create_3hr_geotiffs(band_arrays, ref_vrt, output_dir, filename_template_3hr, tsteps):
    # --- 3-hour average geotiffs (centered rolling window, clipped at boundaries) ---
    if filename_template_3hr and band_arrays is not None:
        for hour in range(tsteps):
            window_start = max(0, hour - 1)
            window_end = min(tsteps, hour + 2)
            avg_arr = band_arrays[window_start:window_end].mean(axis=0)
            output_name = os.path.join(output_dir, filename_template_3hr.format(hour=hour))
            _write_array_as_geotiff(avg_arr, output_name, ref_vrt)

        logging.debug("Done creating 3hr average geotiffs.")

def _create_daily_geotiffs(band_arrays, ref_vrt, output_dir, filename_template_daily_avg,
        filename_template_daily_max, tsteps, start_dt, daily_utc_offsets):
    # --- Daily average and maximum geotiffs ---
    if (filename_template_daily_avg or filename_template_daily_max) and band_arrays is not None:
        for utc_offset in daily_utc_offsets:
            day_groups = _group_hours_by_day(tsteps, start_dt, utc_offset)
            for local_day, hours in sorted(day_groups.items()):
                day_arr = band_arrays[np.array(hours)]
                if filename_template_daily_avg:
                    avg_arr = day_arr.mean(axis=0)
                    output_name = os.path.join(output_dir, filename_template_daily_avg.format(day=local_day))
                    _write_array_as_geotiff(avg_arr, output_name, ref_vrt)
                if filename_template_daily_max:
                    max_arr = day_arr.max(axis=0)
                    output_name = os.path.join(output_dir, filename_template_daily_max.format(day=local_day))
                    _write_array_as_geotiff(max_arr, output_name, ref_vrt)

        logging.debug("Done creating daily average and maximum geotiffs.")

def upload_to_s3(s3_info, tsteps, start_dt, daily_utc_offsets, output_dir, filename_templates):
    """Upload all generated geotiff files to an S3 bucket."""
    s3 = boto3.client('s3')

    files_to_upload = []

    if 'hourly' in filename_templates:
        for hour in range(tsteps):
            files_to_upload.append(filename_templates['hourly'].format(hour=hour))

    if '3hr' in filename_templates:
        for hour in range(tsteps):
            files_to_upload.append(filename_templates['3hr'].format(hour=hour))

    if start_dt:
        for utc_offset in daily_utc_offsets:
            day_groups = _group_hours_by_day(tsteps, start_dt, utc_offset)
            for local_day in sorted(day_groups.keys()):
                if 'daily_avg' in filename_templates:
                    files_to_upload.append(filename_templates['daily_avg'].format(day=local_day))
                if 'daily_max' in filename_templates:
                    files_to_upload.append(filename_templates['daily_max'].format(day=local_day))

    try:
        for f in files_to_upload:
            try:
                local_file = os.path.join(output_dir, f)
                s3_key = os.path.join(s3_info['key_prefix'], f)
                s3.upload_file(local_file, s3_info['bucket'], s3_key)
                logging.debug(f"Successfully uploaded {s3_key}")

            except FileNotFoundError:
                logging.debug(f"Failed to find geotiff file {local_file} to upload to s3")

    except NoCredentialsError:
        logging.debug("AWS credentials not available. Check your ~/.aws/credentials file.")
