import os
import grass.script as gs
import grass.script.setup as gsetup

# _____________START GRASS SESSION & INPUT DEFINITION_____________
# to start the GRASS session in PERMANENT mapset
# rcfile = gsetup.init('/usr/lib/grass78', '/export/home/fkj22/grassdata', 'sensitivity', 'PERMANENT')
# of pattern: rcfile = gsetup.init(gisbase, gisdb, location, mapset)

# specify folder where the input tifs can be found
# folder = '/export/home/fkj22/rcostconvol/in'


# _____________FUNCTION R.IN.GDAL WITH EXISTS CHECK_____________
def ringdal(folder, namestring):
    '''
    Function to read raster data (tif only!) into GRASS environment from a specified directory using r.in.gdal.
    :param folder: Directory in which tifs are stored.
    :param namestring: Substring if only specific files from directory should be read in.
    :return: Registered grass raster datasets. No output.
    '''
    # STEP 1: Check that dataset with same name does not already exist in GRASS.
    # Create a list of raster file names that are currently in GRASS.
    rasterdata = gs.list_strings(type='raster',
                                 mapset='PERMANENT',
                                 flag='r')
    # Create a new list from the above list that does not contain the mapset information.
    cleanraster = []
    for rast in rasterdata:
        substring = rast.split("@")[0]
        cleanraster.append(substring)

    # read in raster using r.in.gdal
    # this is the folder where your GEE exports are in
    for file in os.listdir(folder):
        filename = os.path.splitext(file)[0]
        # iterate through geotiffs in the folder
        if (file.endswith('.tif')) \
                and (os.path.splitext(file)[0] not in cleanraster) \
                and (namestring in filename):
            # -e flag extends region to extent of new dataset, updates default region if used in PERMANENT mapset
            gs.run_command('r.in.gdal',
                           input=os.path.join(folder, file),
                           output=filename,
                           flags='e',
                           memory=1000
                           )
        else:
            pass

