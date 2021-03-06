import datetime
import numpy as np
from scipy.cluster.hierarchy import fcluster, dendrogram
from netcdf_subset import netCDF_subset
from operator import attrgetter
from argparse import ArgumentParser
from netCDF4 import Dataset
from sklearn.decomposition import PCA as PCA
from sklearn.cluster import KMeans
import cPickle
from matplotlib.mlab import PCA as mlabPCA
from Kclustering import Kclustering
from Hclustering import Hclustering
from Meta_clustering import Meta_clustering

if __name__ == '__main__':
    parser = ArgumentParser(description='Extract variables from netcdf file')
    parser.add_argument('-i', '--input', required=True, type=str,
                        help='input file')
    parser.add_argument('-o', '--output', type=str,
                        help='output file')
    opts = parser.parse_args()
    getter = attrgetter('input', 'output')
    inp, outp = getter(opts)
    dsin = Dataset(inp, "r")
    data_dict = {'dataset': dsin, 'levels': [500,700,900],
                 'sub_vars': ['UU','VV'], 'lvlname': 'num_metgrid_levels',
                 'timename': 'Times', 'time_unit': 'hours since 1900-01-01 00:00:0.0',
                 'time_cal': 'gregorian', 'ncar_lvls': None}
    c_dict = {'n_clusters': 9, 'normalize': True, 'season': None,
      'therm_season': None, 'multilevel': True, 'size_desc': 13, 'size_div': 1}
    #print clut_list[0][0]
    kc = Kclustering(c_dict, data_dict)
    #clut_list,V,obd = kc.link_multivar()
    '''
    max_ret_list = kc._netcdf_subset.find_continuous_timeslots(clut_list)
    data_dict = {'dataset': Dataset('../../data/1986_1990.nc', 'r'), 'levels': [500,700,900],
                 'sub_vars': ['UU', 'VV'], 'lvlname': 'num_metgrid_levels',
                 'timename': 'Times', 'time_unit': 'hours since 1900-01-01 00:00:0.0',
                 'time_cal': 'gregorian', 'ncar_lvls': None}
    kc2 = Kclustering(c_dict, data_dict)
    print max_ret_list
    kc2.cluster_descriptor_middle(outp, max_ret_list)
    '''
