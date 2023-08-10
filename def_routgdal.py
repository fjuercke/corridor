"""
This script creates an output of raster files in a specified GRASS Mapset without starting GRASS explicitly.
The process consists of three steps:

1) Import the required packages and start the GRASS session.

2) Create a list of raster files to be exported according to a particular pattern.

3) Export the raster files specified in the list using GRASS module r.out.gdal.

In this study raster data was exported in FLOAT32 file type to reduce file size and facilitate further use of the data (in particular for visualisation).
The cost distance and consequently corridor raster created in GRASS are stored as DCELL data (see https://grasswiki.osgeo.org/wiki/GRASS_raster_semantics).
However, this high precision is not needed for further analysis and files are therefore stored using Float32.
Float32 file type reduces the final file size from 4.8 to 1.5 GB and makes data more manageable without loosing vital information.

Three create options were chosen based on the recommended settings for large raster files as specified in the GDAL documentation.
GDAL documentation is available on the GDAL website. The GeoTIFF File Format docs are here: https://gdal.org/drivers/raster/gtiff.html#raster-gtiff
The following create options were specified:

COMPRESS=LZW
PREDICTOR=3
BIGTIFF=YES

"""

import os
import grass.script as gs

def routgdal(rasterlist, datatype, loc_out):
    '''

    Here is some explanation as to datatypes and the type of data they store:
    https://gsp.humboldt.edu/olm/Lessons/GIS/08%20Rasters/RasterDataModels3.html
    :param rasterlist: a list of rasters to be exported
    :param datatype: (string) specify the data type;
    choose from: Byte, Int16, UInt16, Int32, UInt32, Float32, Float64, CInt16, CInt32, CFloat32, CFloat64
    :param loc_out: output location as string; e.g. '/export/home/fkj22/rcostconvol/out'
    :return: Creates a GeoTIFF of each file in the above list 'files' using GRASS module 'r.out.gdal'.
    see https://grass.osgeo.org/grass78/manuals/r.out.gdal.html for more details
    '''
    large_datatypes = ['Float32', 'Float64', 'CInt16', 'CInt32', 'CFloat32', 'CFloat64']

    for rast in rasterlist:

        # Set the computational region so as not to loose any data. This should not change, but is good practice to specify for each raster individually.
        gs.run_command('g.region', raster=rast)

        # Specify output location and name of resulting raster.
        name = rast.split("@")[0] # Use the name of the Grass dataset. As it will have the mapset information appended to it after '@', only take the string before '@'.
        file = f'{name}_{datatype}.tif'
        out = f'{loc_out}/{name}_{datatype}.tif' # Add 'datatype' at the end of the file name to indicate that the exported data type is Float32.

        # Set the createoptions to handle large files if the datatype is of a large type
        # Otherwise the compression and predictor will mess with the smaller data and the output is useless
        # If the datatype is not one of the large ones, then createopt will be empty. No harm done.
        options = 'COMPRESS=LZW,PREDICTOR=3,BIGTIFF=YES' if datatype in large_datatypes else ''

        if file not in os.listdir(loc_out):
        # Run GRASS module 'r.out.gdal'
            gs.run_command('r.out.gdal',
                           input=rast,
                           output=out,
                           createopt=options, # Create options separated by a comma of pattern NAME=OPTION based on the GTiff File Format documentation on the GDAL website.
                           format='GTiff',
                           type=datatype,
                           nodata=0,
                           flags='f') # Force the output to the chosen datatype.
            print(f'{rast} saved in {datatype} \n as {file} \n to {loc_out}')

        else:
            print('File already exists and will not be created.')
            pass


