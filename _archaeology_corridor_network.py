#!/usr/bin/env python3

'''
Code to rescale and join corridors locally. With the right region settings and resolution should take c. 30-35 mins for 10-15 raster.

'''

import os
import datetime
import grass.script as gs
import grass.script.setup as gsetup
import re

# _____________START GRASS SESSION & INPUT DEFINITION_____________
# # Start the GRASS session:
# rcfile = gsetup.init('/usr/lib/grass78', '/export/home/fkj22/grassdata', 'sensitivity', 'PERMANENT')
# # of pattern: rcfile = gsetup.init(gisbase, gisdb, location, mapset)

# Get the start time of the whole process.
begin_time_whole = datetime.datetime.now()
print(f'The whole process starts now: {begin_time_whole}')
# Get the start date as a string to feed to txt file name.
today = begin_time_whole.strftime('%Y-%m-%d')

# Set the string that you want to identify your files by.
# envfact = 'seas_snow_surfw_dam_wat01_noconvol_dsrt005excl' # HERE USER INPUT TO ONLY TAKE THOSE FILES OF ONE ENVIRONMENTAL FACTOR

# get a list of raster maps
filepattern = f'corridor*1003*10perc*' # CHANGE AS APPROPRIATE
excludepattern = ''

folder = '' # folder location of corridors

for file in os.listdir(folder):
    filename = os.path.splitext(file)[0]
    # iterate through geotiffs in the folder
    if (file.endswith('.tif') and '1003' in file): # CHANGE AS APPROPRIATE
        # -e flag extends region to extent of new dataset, updates default region if used in PERMANENT mapset
        gs.run_command('r.in.gdal',
                       input=os.path.join(folder, file),
                       output=filename,
                       flags='e',
                       memory=1800
                       )
    else:
        pass

data = gs.list_strings(type='raster',
                       pattern=filepattern,
                       exclude=excludepattern,
                       mapset='PERMANENT'
                       )

gs.run_command('g.region', raster=data)


#_______________BYTE STRETCH 0-255_______________#
# via linear conversion
# formula for stretch from here: https://gis.stackexchange.com/a/28563
# smin=0; smax=255
# ( x - min(x) ) * (smax - smin) / ( max(x) - min(x) ) + smin
# NewRaster = ( OldRaster - -1 ) * 255 / ( 1 - -1 ) + 0
# another stack which provides the same answer in their case to stretch to 0-100: https://gis.stackexchange.com/a/50173
# ("raster" - min("raster")) * 100 / (max("raster") - min("raster")) + 0

# see also here: https://stackoverflow.com/a/929107

# translated into GRASS this will look like the following:

# define your min and max variables to which your raster will be stretched
stretch_min = 1
stretch_max = 255


# for each of the maps in your list do...
for map in data:
    begin_time = datetime.datetime.now()
    # ...set the computational region
    gs.run_command('g.region', raster=map)

    # ...get min and max values of the map
    # r.univar
    stats = gs.parse_command('r.univar',
                             map=map,
                             # output=, # Name for output file (if omitted or "-" output to stdout)
                             separator='comma',
                             flags='g'  # -t flag prints in tabular format; -g flag prints in shell script style
                             )

    print('Stats:\n', *stats, sep='\n')
    map_min = stats['min']
    map_max = stats['max']

    # ...stretch the map to 0-255 values using the above formula
    # r.mapcalc
    outraster = f'{map.split("@")[0]}_stretch_{stretch_min}{stretch_max}'  # name of output raster
    gs.mapcalc(f'{outraster} = ({map}-{map_min})*({stretch_max}-{stretch_min})/({map_max}-{map_min}) + {stretch_min}')

    runtime_stretch = (datetime.datetime.now() - begin_time).total_seconds()
    print(f'Stretching took {runtime_stretch/60} mins.')


# _____________JOIN STRETCHED RASTER_____________
# join raster using r.mapcalc
# minimum r.mapcalc nmin() excludes NULL values and therefore does not require NULL-value conversion!

# get all stretched maps
filepattern = '*stretch*'
excludepattern = ''
corridors = gs.list_strings(type='raster',
                           pattern=filepattern,
                           exclude=excludepattern,
                           mapset='PERMANENT'
                           )


rastbase = corridors[0].split("@")[0]
# get the part of the raster name to be replaced for renaming
rast_root = re.findall('corridor_[0-9]{3,4}_[0-9]{3,4}_costdist', rastbase)
out_min = f'{rastbase.replace(rast_root[0], "corridors_mid4th_wY")}_minjoined' #name of output raster

minmaps = ','.join(corridors) # creates a single string in which the rasters to be combined are separated by a comma and can be fed into r.mapcalc
gs.mapcalc(f'{out_min} = nmin({minmaps})') #joins the stretched raster based on selecting the minimum value across all rasters, excluding NULL cells

# Transform joined raster into Byte format (check here for details: https://grasswiki.osgeo.org/wiki/Large_raster_data_processing)
# set up the variables
out_mult100 = f'{out_min}_mult100'
out_byte = f'{out_mult100}_rounded'
# run gs.mapcalc 2x
gs.mapcalc(f'{out_mult100} = {out_min}@PERMANENT * 100') # multiply by 100
gs.mapcalc(f'{out_byte} = round({out_mult100}@PERMANENT)') # then round to integer

# run r.out.gdal to output the final result for check in QGIS
outloc = 'FOLDER' #folder location for export
out = f'{outloc}/{out_byte.split("@")[0]}_Int16.tif'
gs.run_command('r.out.gdal',
               input=f'{out_byte}@PERMANENT',
               output=out,
               format='GTiff',
               type='Int16',
               flags='f')  # Force the output to the chosen datatype.


# _____________CLEAN UP AFTER YOURSELF_____________
runtime_whole = (datetime.datetime.now() - begin_time_whole).total_seconds()
print(f'The whole process takes {runtime_whole/60} minutes.\n')
# gsetup.finish()