import subprocess
import grass.script as gs

def lcp(costsurf, rcostpoint, startpoint, outpath):
    '''
    Generates LCPs using r.path.
    :param costsurf: List of costsurfaces, assumed to be the base name for the costdist and movdir raster created using r.cost
    :param rcostpoint: list of start points from which costdist were created using r.cost
    :param startpoint: list of points from which lcps are to be calculated using r.path
    :param outpath: directory path where the gpkg with your LCPs will be stored; e.g.: '/export/home/fkj22/rcostconvol/out'
    :return: A GPKG file (per costdist raster) with all lcps from several points back to a single start point.
    '''

    # for every file in your list of cost surfaces get the root of the cost surface raster

    for file in costsurf:
        # get the name without 'costsurf_'
        root = file.split("_", 1)[1]

        print(f'\n\n{root}')

        # for every point in your list of rcostpoints check if r.cost has been run from the rcostpoint
        for point in rcostpoint:
            # create the names of the movdir and costdist raster
            movdir = f'{point}_movdir_{root}'
            costdist = f'{point}_costdist_{root}'


            # create a list of raster against which to check if your movdir and costdist exist
            rasterdata = gs.list_strings(type='raster',
                                         mapset='PERMANENT')

            # for testing purposes here's a list of movdir and costdist raster:
            # rasterdata = ['167_movdir_convol227_00jan_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '167_costdist_convol227_00jan_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '167_movdir_convol227_01feb_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '167_costdist_convol227_01feb_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '167_movdir_convol227_02mar_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '1003_movdir_convol227_00jan_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '1003_costdist_convol227_00jan_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '1003_movdir_convol227_01feb_maxcost40_dsrt005_wat02_220121_3395@PERMANENT',
            #               '1003_costdist_convol227_01feb_maxcost40_dsrt005_wat02_220121_3395@PERMANENT']

            # here you do the actual checking if the movdir and costdist are in your list of GRASS raster
            if (movdir in rasterdata) and (costdist in rasterdata):
                print('\n')
                print(f'movdir: {movdir}')
                print(f'costdist: {costdist}')

                for x, y, sid in startpoint:
                    # # for test purposes
                    # list_vectors = []

                    if sid != point:
                        print(f'r.path from {sid} will be run on {point}_costdist')
                        # define your vector output name
                        namevect = f'lcp_{sid}_{point}_{root.split("@")[0]}'
                        print(f'output: {namevect}')

                        # run r.path
                        p = gs.start_command('r.path',
                                             input = movdir, # name of input direction raster
                                             format = 'degree',  # of input direction map; options: auto, degree, 45degree, bitmask
                                             values = costdist, # name of input raster map with cost values
                                             # raster_path=, #name for output raster path map
                                             vector_path = namevect,  # name for output vector path map
                                             start_coordinates = (x, y),  # coordinates of starting points(s) (E,N)
                                             overwrite = True,
                                             stderr=subprocess.PIPE,
                                             stdout=subprocess.PIPE
                                             # start_points=point #name of starting vector points map
                                             )
                        stdoutdata, stderrdata = p.communicate()
                        print(stdoutdata)
                        print(stderrdata)

                        # # for test purposes
                        # list_vectors.append(namevect)

                        # # get all your LCPs in a vector list
                        # vectordata = gs.list_strings(type='vector',
                        #                              pattern=f'lcp_*_{point}_*')
                        #
                        # # output all your LCPs according to the costdist raster on which they were created to a single GPKG
                        # for vect in vectordata:
                        #     print(f'Input layer for v.out.ogr is: {vect}')
                        #     out_path = outpath
                        #     out_file = f'{vect.split("@")[0].split("_", 2)[2]}.gpkg'
                        #     out_loc = f'{out_path}/{out_file}'
                        #     print(f'{vect} will be saved to GPKG named {out_file}')
                        #
                        #     gs.run_command('v.out.ogr',
                        #                    input=vect,
                        #                    type='line',
                        #                    output=out_loc,
                        #                    output_layer=vect,
                        #                    format='GPKG',
                        #                    flags='a'
                        #                    )

                    elif sid == point:
                        print(f'r.path will not be run from startpoint {sid} for costdist {point}')
                        pass

            else:
                print(f'WARNING: CANNOT CALCULATE LCP \n {movdir} or {costdist} are not in list of rasters.')
                pass