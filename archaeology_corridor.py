import os
import datetime
from itertools import combinations
import grass.script as gs
import grass.script.setup as gsetup
from def_rcost_checki import costdistcheck
from def_rcost_run import costdist
from def_corridors import corridors
from def_corridors import tenperc
from def_lcp import lcp
from def_ringdal import ringdal
from def_routgdal import routgdal


'''
This code is set up to create corridors from one or more input cost surfaces 
'''

# _____________START GRASS SESSION & INPUT DEFINITION_____________
# Start the GRASS session:
rcfile = gsetup.init('/usr/lib/grass78', '/export/home/fkj22/grassdata', 'sensitivity', 'PERMANENT')
# of pattern: rcfile = gsetup.init(gisbase, gisdb, location, mapset)

# Get the start time of the whole process.
begin_time_whole = datetime.datetime.now()
print(f'The whole process starts now: {begin_time_whole}')
# Get the start date as a string to feed to txt file name.
today = begin_time_whole.strftime('%Y-%m-%d')

# Set the string that you want to identify your files by.
envfact = 'seas_snow_surfw_dam_wat01_noconvol_dsrt005excl' # HERE USER INPUT TO ONLY TAKE THOSE FILES OF ONE ENVIRONMENTAL FACTOR/FILE PATTERN

# _____________READ IN SITES VECTOR_____________
# read in a csv with the start points including a column called 'name'
gs.run_command('v.in.ascii',
               input='sites_arch_corr.csv', #file name for csv, change as appropriate
               output='arch_points',
               format='point',
               separator='comma',
               x=2,
               y=3,
               cat=1,
               columns='cat int, x double precision, y double precision, sid int, name varchar(20), purpose varchar(10)',
               skip=1)

# _____________READ IN COSTSURFACES_____________
# Read in the cost surfaces over which the following steps should be executed

begin_time = datetime.datetime.now()
print(f'Reading in TIFFs starts now: {begin_time}')

folder = '/export/home/fkj22/rcostconvol/in'
ringdal(folder, envfact) # Read in files from a particular pattern using a r.in.gdal

# _____________GET INPUTS FOR R.COST_____________
# Step 1: get a list of costsurfaces to calculate costdist from
# list raster files according to a particular pattern [pattern='pattern']
filepattern = f'costsurf_slope_{envfact}*mean*' # HERE USER INPUT define the file pattern in the you look for
excludepattern = '' # HERE USER INPUT define the file pattern for files to exclude if any

costsurfs = gs.list_strings(type='raster',
                            mapset='PERMANENT',
                            pattern=filepattern,
                            exclude=excludepattern,
                            )
print(f'Cost distance raster will be created for: ', *costsurfs, sep='\n  ')

# Step 2: get a list of points to calculate costdist from
cststarts = gs.read_command('v.out.ascii',
                            input='arch_points',
                            columns='sid',
                            separator='comma').strip().splitlines()

cststarts = [p.split(",") for p in cststarts]

# remove the cat numbers which are read by the v.out.ascii command:
cststart_number = [row.pop(2) for row in cststarts]
print('from start points: ', *cststarts, sep='\n')


# _____________RUN COSTDIST_____________
# Step 3: check memory requirements for cost dist calculation
costdistcheck(costsurfs,cststarts)

# Step 4: calculate cost dist
begin_time = datetime.datetime.now()
print(f'Cost dist calculation starts now: {begin_time}')
costdist(costsurfs,cststarts)
runtime_costdist = (datetime.datetime.now() - begin_time).total_seconds()
print(f'The runtime to calculate all cost distance raster is {runtime_costdist} seconds.\n')


# _____________CALCULATE CORRIDORS_____________
# Step 1: get a list of cost dist to calculate corridors from
# list raster files according to a particular pattern [pattern='pattern']
filepattern = f'*costdist_slope_{envfact}*' # HERE USER INPUT define the file pattern you look for
excludepattern = '' # HERE USER INPUT define the file pattern for files to exclude if any

costdists = gs.list_strings(type='raster',
                           pattern=filepattern,
                           exclude=excludepattern
                           )


# Step 2: create a list of tuples from the list of cost dists, creating unique combinations across a single list
combosall = list(combinations(costdists, 2))

# Step 3: check that only those raster are connected that have the same root and put them into a new list
combos = []
for i, comb in enumerate(combosall):
    roota = comb[0].split("_", 1)[1]
    # print(roota)
    rootb = comb[1].split("_", 1)[1]
    if roota == rootb:
        combos.append(comb)
    elif roota == rootb:
        pass

print(f'{len(combos)} corridors will be created from: ', *combos, sep='\n  ')

# Step 4: run corridor analysis; corridors function also has inbuilt check for if the two raster roots are the same so no useless corridors are created
begin_time = datetime.datetime.now()
print(f'Corridor calculation starts now: {begin_time}')
for i, comb in enumerate(combos):
    corridors(comb[0], comb[1])
runtime_corr = (datetime.datetime.now() - begin_time).total_seconds()
print(f'The runtime to calculate all corridors is {runtime_corr} seconds.\n')

# _____________10% CORRIDORS_____________
# Create raster with only the first 10 percent of each corridor
# Step 1: get a list of corridors
# list raster files according to a particular pattern [pattern='pattern']
filepattern = f'corridor_*_slope_{envfact}*' # HERE USER INPUT define the file pattern you look for
excludepattern = '' # HERE USER INPUT define the file pattern for files to exclude if any

corridors = gs.list_strings(type='raster',
                           pattern=filepattern,
                           exclude=excludepattern
                           )

# Step 2: get all 10% value corridors to reduce file size
begin_time = datetime.datetime.now()
print(f'10%-corridor calculation starts now: {begin_time}')
tenperc(corridors)
runtime_tenperc = (datetime.datetime.now() - begin_time).total_seconds()
print(f'The runtime to calculate all ten percentile corridors is {runtime_tenperc} seconds.\n')


# _____________10% CORRIDORS - QUANTRECODE_____________
# For validation check; not actually needed for the archaeology corridors, I think. (230107)
# Recode all 10% corridors
# get a list of raster files to recode
corrpattern = 'corridor*10perc'
excludepattern = ''
files = gs.list_strings(type='raster', # Only list raster files
                        pattern=corrpattern, # Specify the pattern of raster names to be listed. Here all corridors.
                        exclude=excludepattern,
                        mapset='PERMANENT') # Specify the mapset in which to search for the files to be listed.

percs = list(range(0,99))
filepath = '/export/home/fkj22/rcostconvol/out'

# This is where the action happens
for rast in files:
    quantrecode(rast,percs,filepath)

# Export all recoded corridors
exportpattern = 'corridor*recoded*'
excludepattern = ''

# List raster files to be exported according to a particular pattern [pattern='pattern']
data = gs.list_strings(type='raster', # Only list raster files
                       pattern=exportpattern, # Specify the pattern of raster names to be listed. Here all corridors.
                       exclude=excludepattern,
                       mapset='PERMANENT') # Specify the mapset in which to search for the files to be listed.

outtype = 'Byte'
# choose from: Byte, Int16, UInt16, Int32, UInt32, Float32, Float64, CInt16, CInt32, CFloat32, CFloat64

# output location
outloc = '/export/home/fkj22/rcostconvol/out'

begin_time = datetime.datetime.now()
routgdal(data, outtype, outloc)
runtime_outgdal = (datetime.datetime.now() - begin_time).total_seconds()
print(f'It took {runtime_outgdal} seconds to export all files of pattern {filepattern}.\n')


# Check all files are actually exported
# Create a new list from the above list that does not contain the mapset information.
cleanraster = []
for rast in data:
    substring = rast.split("@")[0]
    cleanraster.append(substring)

# If they are exported then remove them from GRASS.
for raster in cleanraster:
    if any(raster in file for file in os.listdir(outloc)):
        print(f'YEY, {raster} exits and will be removed from GRASS')
        gs.run_command('g.remove',
                       type='raster',
                       pattern=raster,
                       exclude='',
                       flags='f'
                       )
    else:
        print(f'NEY, {raster} does not exist. Check what happened.')
        pass


# _____________10% CORRIDORS - EXPORT + CLEAN_____________
# Export all 10% corridors to
exportpattern = 'corridor*10perc'
excludepattern = ''

# List raster files to be exported according to a particular pattern [pattern='pattern']
data = gs.list_strings(type='raster', # Only list raster files
                       pattern=exportpattern, # Specify the pattern of raster names to be listed. Here all corridors.
                       exclude=excludepattern,
                       mapset='PERMANENT') # Specify the mapset in which to search for the files to be listed.

outtype = 'Float32'
# choose from: Byte, Int16, UInt16, Int32, UInt32, Float32, Float64, CInt16, CInt32, CFloat32, CFloat64

# output location
outloc = '/export/home/fkj22/rcostconvol/out'

begin_time = datetime.datetime.now()
routgdal(data, outtype, outloc)
runtime_outgdal = (datetime.datetime.now() - begin_time).total_seconds()
print(f'It took {runtime_outgdal} seconds to export all files of pattern {filepattern}.\n')


# Check all files are actually exported
# Create a new list from the above list that does not contain the mapset information.
cleanraster = []
for rast in data:
    substring = rast.split("@")[0]
    cleanraster.append(substring)

# If they are exported then remove them from GRASS.
for raster in cleanraster:
    if any(raster in file for file in os.listdir(outloc)):
        print(f'YEY, {raster} exits and will be removed from GRASS')
        gs.run_command('g.remove',
                       type='raster',
                       pattern=raster,
                       exclude='',
                       flags='' # Flag needs to be set to 'f' if cleaning is to take place
                       )
    else:
        print(f'NEY, {raster} does not exist. Check what happened.')
        pass

# _____________RUN LCP_____________
# get a list of costsurfaces from your grass mapset
list_costsurf = gs.list_strings(type = 'raster',
                                pattern = f'costsurf_slope_{envfact}*mean*',
                                mapset='PERMANENT')

# # read your list of startpoints for rpath with pattern x,y,sid
cststart = gs.read_command('v.out.ascii',
                           input='arch_points2',
                           columns='sid',
                           separator='comma').strip().splitlines()

cststart = [p.split(",") for p in cststart]

# remove the cat numbers which are read by the v.out.ascii command:
cststart_number = [row.pop(2) for row in cststart]
print('start points: ', *cststart, sep='\n')

# specify a list of rcostpoints (for costdist and movdir)
rcostpoint = [point[2] for point in cststart]
print(rcostpoint)

# specify your output directory:
outdirectory = '/export/home/fkj22/rcostconvol/out'

# run your lcp function
lcp(list_costsurf, rcostpoint, cststart, outdirectory)




# _____________CLEAN UP AFTER YOURSELF_____________
runtime_whole = (datetime.datetime.now() - begin_time_whole).total_seconds()
print(f'The whole process for {len(costsurfs)} cost surfaces takes {runtime_whole} seconds.\n')
gsetup.finish()