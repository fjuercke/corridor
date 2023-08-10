import grass.script as gs


# _____________START GRASS SESSION_____________ /// NOT NECESSARY AS ONLY FUNCTION DEFINED HERE
# # to start the GRASS session
# rcfile = gsetup.init('/usr/lib/grass78', '/export/home/fkj22/grassdata', 'sensitivity', 'PERMANENT')
# # of pattern: rcfile = gsetup.init(gisbase, gisdb, location, mapset)

# _____________GET LIST OF RASTER_____________ /// NOT NECESSARY AS ONLY FUNCTION DEFINED HERE
# ###### Step 1: create a list of raster through which to iterate:
# raster_list = gs.list_strings(type='raster',
#                               pattern='costsurf_*mean*', #specify which months you want to run this on
#                               mapset='PERMANENT')

# _____________GET LIST OF START POINTS_____________ /// NOT NECESSARY AS ONLY FUNCTION DEFINED HERE
# # Step 2: create a nested list of start points you want to calculate distance raster from
# cststart = gs.read_command('v.out.ascii',
#                            input='start_points',
#                            columns='sid',
#                            where='"sid" IN ("167", "1005", "1003")',
#                            separator='comma').strip().splitlines()
#
# cststart = [p.split(",") for p in cststart]
#
# # remove the cat numbers which are read by the v.out.ascii command:
# cststart_number = [row.pop(2) for row in cststart]
# print('start points: ', *cststart, sep='\n')

# _____________R.COST: CHECK DISK SPACE AND MEMORY REQUIREMENTS_____________
# Step 3: r.cost using -i flag - check info on disk space and memory requirements of r.cost run
def costdistcheck(costsurfaces, cststart):
    '''
    Prints info about disk space and memory requirements of r.cost for several cost surfaces and start points given as input
    :param costsurfaces: list of strings containing names of costsurfaces
    :param cststart: list of points of pattern ... TODO
    :return: cost distance raster from each point for each costsurface given as input
    '''
    for raster in costsurfaces:
        # Create output strings
        namedist = f'{raster.replace("costsurf", "costdist")}'
        namedir = f'{raster.replace("costsurf", "movdir")}'

        # set region
        gs.run_command('g.region', raster=raster)

        for x, y, sid in cststart:

            # Create output strings
            outdist = f'{sid}_{namedist}'
            movdir = f'{sid}_{namedir}'

            # Check file does not already exist, create list of raster
            rasts = gs.list_strings(type='raster',
                                    mapset='PERMANENT'
                                    )
            # Create a list of rasters without mapset information. GRASS will print out the raster names of pattern [name]@[MAPSET].
            cleanrasts = []
            for rast in rasts:
                substring = rast.split("@")[0]
                cleanrasts.append(substring)

            # Check that the corridor does not already exist in the PERMANENT mapset.
            if outdist or movdir not in cleanrasts:
                # Run!
                print(f'\nCalculating r.cost over\n {raster}')
                print(f' from {sid}\n creating: ')
                print(f' - {outdist}')
                print(f' - {movdir}')
                gs.run_command('r.cost',
                               input = raster,
                               output = outdist,
                               start_coordinates = (x, y),
                               outdir = movdir,
                               memory=3000,
                               flags = 'kni'
                               )

            else:
                print('File already exists.')
                pass