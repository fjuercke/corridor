import grass.script as gs
from grass.script import core as gscore
import datetime
from itertools import combinations, product

# _________________THE BELOW FUNCTION IS NOT NEEDED AND SHOULD BE DELETED___________________
def pairs(*lists):
    '''
    Function taken from here: https://stackoverflow.com/a/35271220
    create a list of tuples with all unique combinations of input raster in the two lists filesW and E using the combinations function from the python itertools module
    for a good reference on various ways of calculating combinations in Python (incl the combinations function of the itertools module and for loops)
    see here: https://s3.amazonaws.com/assets.datacamp.com/production/course_13369/slides/chapter3.pdf
    you can calculate the amount of unordered samples without replacement by using formula three at the bottom of this website: https://www.probabilitycourse.com/chapter2/2_1_4_unordered_with_replacement.php
    for 6 elements in your list (i.e. six raster) this will lead to a combination of 15 pairs (tuples in new list)
    :param lists:
    :return:
    '''
    # combinations(lists, 2)

    for t in combinations(lists, 2):
        for pair in product(*t):
            # Don't output pairs containing duplicated elements
            if pair[0] != pair[1]:
                yield pair
# _________________THE ABOVE FUNCTION IS NOT NEEDED AND SHOULD BE DELETED___________________



def corridors(site1, site2):
    '''
    Function to create corridors using r.mapcalc. Takes two cost distance raster file names (str) as input.
    Can be used in a for loop, when looping through a list of tuples where each tuple is composed of two raster names.
    For further information on r.mapcalc including NULL handling, see: https://grass.osgeo.org/grass78/manuals/r.mapcalc.html
    :param site1: A cost distance raster from one site of pattern '[site]_[costdist]@[MAPSET]'.
    :param site2: A cost distance raster from one site of pattern '[site]_[costdist]@[MAPSET]'.
    :return: A raster representing the corridor between site1 and site2.
    '''

    # Get the root of the file names, to check both cost dist raster were created from the same cost surface.
    # Requires file name to be of pattern '[site]_[costdist]@[MAPSET]' where [costdist]@[MAPSET] will be the root to check.
    roota = site1.split("_", 1)[1]
    rootb = site2.split("_", 1)[1]

    # Check if both cost distance raster were created from the same cost surface.
    if roota == rootb:
        raster_a = site1
        raster_b = site2

        # Print which two raster will be combined to form the corridor.
        print(f'Proceeding to combine raster: \n'
              f' {raster_a} \n'
              f' {raster_b}')

        # Set region extent based on both input raster.
        gs.run_command('g.region',
                       raster=[site1, site2],
                       flags='p'
                       )

        # ________Create output string________
        # Get raster name to pass to output string.
        rast_root = site1.split("_", 1)
        rast = rast_root[1].split("@")[0]

        # Get string site number to pass to output string.
        a = raster_a.split("_")[0]
        b = raster_b.split("_")[0]

        # Create output string.
        corridor = f'corridor_{a}_{b}_{rast}'

        #________Check corridor does not already exist________
        # Get a list of all rasters in PERMANENT mapset.
        rasts = gs.list_strings(type='raster',
                                mapset='PERMANENT'
                                )
        # Create a list of rasters without mapset information. GRASS will print out the raster names of pattern [name]@[MAPSET].
        cleanrasts = []
        for rast in rasts:
            substring = rast.split("@")[0]
            cleanrasts.append(substring)

        # Check that the corridor does not already exist in the PERMANENT mapset.
        if corridor not in cleanrasts:
            # ________Run r.mapcalc to create corridors________
            begin_time = datetime.datetime.now()
            gs.mapcalc(f'{corridor} = ({raster_a} + {raster_b})/2')
            runtime_corr = (datetime.datetime.now() - begin_time).total_seconds()
            # Print when operation is finished.
            print(f'It took {runtime_corr} seconds to create: \n', corridor)

        else:
            # Don't do anything if the corridor already exists.
            print(f'!!! {corridor}\n  already exists and will not be created.')
            pass

    elif roota != rootb:
        # Don't do anything if the raster roots are not the same.
        print('Cost distance raster do not have the same root! Nothing happens.')
        pass



def tenperc(rasterlist):
    '''
    This function calculates the 10th percentile of a raster map and creates a new raster where all cells above
    the 10th percentile are promoted to NULL. It uses GRASS r.quantile to calculate the 10th percentile and
    then r.mapcalc to create a new raster containing only the lower 10th percentile.
    It takes a list of raster files as input, assumed to have been created using gs.list_strings(), but can be any other list input,
    where raster names are of pattern [name]@[MAPSET].
    This function was orignally designed to reduce the file size of corridors created using the corridor function,
    but can be used on any raster.
    For more info on r.quantile see:
        https://gis.stackexchange.com/questions/421954/which-quantile-calculation-methods-does-grass-gis-use (on quantile calculation algorithm using r.quantile)
    And examples can be found:
         https://gis.stackexchange.com/questions/229796/reclassify-a-raster-file-with-quantiles < uses numpy, not r.quantile
         https://gis.stackexchange.com/questions/266375/problem-with-r-quantile
    :type rasterlist: List
    :param rasterlist: List of raster files from which to calculate the 10th percentile.
    :return: A raster with only 10% of values.
    '''
    for rast in rasterlist:
        # Set the computational region to the current raster.
        gs.run_command('g.region', raster=rast)
        print(f'\n10 percent corridor will be created for: \n {rast}')

        # ________Run r.quantile________
        # Get the start time of the quantile calculation
        begin_time = datetime.datetime.now()
        # Calculate the 10th percentile of each raster using r.quantile
        p = gscore.pipe_command('r.quantile',
                                input=rast,
                                percentiles=10)
        # Feed the output of r.quantile into a list
        perc = []
        for line in p.stdout:
            result = line.decode('UTF-8')
            val1, val2, percs = result.split(':')
            # put the result of
            perc.append(float(percs))
        # Print some info about the variable.
        print(f'10th percentile: {perc[0]}')
        p.wait()
        # Tell me how long it took to calculate the 10th percentile using r.quantile.
        runtime_perc = (datetime.datetime.now() - begin_time).total_seconds()
        print(f'The runtime to calculate the 10th percentile is {runtime_perc} seconds.\n')

        # ________Create mapcalc output string________
        name = rast.split("@")[0]
        out = f'{name}_10perc'  #
        print('\nRunning r.mapcalc to create: \n', out)

        # ________Run r.mapcalc to create corridors________
        # Start time calculations for the mapcalc operation.
        begin_time_mapcalc = datetime.datetime.now()
        # Calculate the new raster only containing the upper 10% of values using r.mapcalc.
        gs.mapcalc(f'{out} = if({rast}>={perc[0]}, null(), {rast})')  # taken from here: https://gis.stackexchange.com/a/81730
        # Tell me how long it took to create the new raster.
        runtime_mapcalc = (datetime.datetime.now() - begin_time_mapcalc).total_seconds()
        print(f'The runtime to promote all cells above 10th percentile to NULL is {runtime_mapcalc} seconds.')