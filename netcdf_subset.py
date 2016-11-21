import numpy as np
from netCDF4 import Dataset,num2date
from scipy.cluster.hierarchy import dendrogram, linkage, cut_tree
from datetime import timedelta

#Calculate precision,recall and F-scores for two clustering outcomes
def calculate_prf(clut_list1,clut_list2):
          if len(clut_list1)!=1 and len(clust_list2)!=1:
              raise ValueError('List of clusters must contain only a single variable or a single list for multiple variables')
          P = []
          R = []
          F = []
          for c in clut_list1[0]:
              C_precision = []
              C_recall = []
              C_f = []
              for cc in clut_list2[0]:
                  p = len(np.intersect1d(c,cc))/float(len(cc))
                  r = len(np.intersect1d(c,cc))/float(len(c))
                  if len(np.intersect1d(c,cc)) != 0:
                      C_precision.append(p)
                      C_recall.append(r)
                      C_f.append(2*p*r/(p+r))
                  else:
                      C_precision.append(0)
                      C_recall.append(0)
                      C_f.append(0)
              P.append(C_precision)
              R.append(C_recall)
              F.append(C_f)
          return P,R,F

#Calculate Cohesion(WSS) by Sum squared error and Separation measured by between cluster sum of squares
def calculate_clut_metrics(cluster_data,normalize=False):
    wss_c = []
    bss_c = []
    mag = []
    if normalize:
        for cluster in cluster_data:
            mag.append(np.linalg.norm(cluster))
        max_mag = max(mag)
        cluster_norm = []
        for cluster in cluster_data:
            cluster_norm.append(np.divide(cluster,max_mag))
    flatten_clust = np.array([0])
    if normalize:
        for c in cluster_norm:
            flatten_clust = np.append(flatten_clust,c)
    else:
        for c in cluster_data:
            flatten_clust = np.append(flatten_clust,c)
    flatten_clust = np.delete(flatten_clust,0)
    m = np.mean(flatten_clust,axis=0)
    if normalize:
       for cluster in cluster_norm:
            mi = np.mean(np.matrix(cluster),axis=0)
            wss = np.power((np.subtract(cluster,mi)),2)
            bss = np.multiply(len(cluster),np.power(np.subtract(m,mi),2))
            wss_c.append(np.divide(np.sum(wss),len(cluster)))
            bss_c.append(np.divide(np.sum(bss),len(cluster)))
    else:
        for cluster in cluster_data:
            mi = np.mean(np.matrix(cluster),axis=0)
            wss = np.power((np.subtract(cluster,mi)),2)
            bss = np.multiply(len(cluster),np.power(np.subtract(m,mi),2))
            wss_c.append(np.sum(wss))
            bss_c.append(np.sum(bss))
    WSS = np.sum(wss_c)
    BSS = np.sum(bss_c)
    TOTAL = WSS+BSS
    return WSS,BSS,TOTAL

class netCDF_subset(object):
      dataset = None #initial netcdf dataset path
      level_name = None
      time_name = None
      pressure_levels = None #pressure level of interest
      subset_variables = None #variables of interest

      #Constructor
      def __init__(self,dataset,levels,sub_vars,lvlname,timename):
          #Init original dataset
          self.dataset = dataset
          #Multiple levels
          self.pressure_levels = levels
          #Multiple vars
          self.subset_variables = sub_vars
          self.level_name = lvlname
          self.time_name = timename

      #Find pressure level position in dataset
      def lvl_pos(self):
          idx_list = []
          arr = np.array(self.dataset.variables[self.level_name]).tolist()
          for lvl in self.pressure_levels:
              idx_list.append(arr.index(lvl))
          return idx_list

      #Retrieve variables for a specific level (defined in Class attributes)
      def extract_data(self,sub_pos):
          var_list = []
          for v in self.subset_variables:
                var_list.append(self.dataset.variables[v][:,sub_pos,:,:])
          return var_list

      #Retrieve variables for a specific level and time (used in clusters to file)
      def extract_timedata(self,time_pos,sub_pos):
          var_list = []
          for v in self.subset_variables:
                var_list.append(self.dataset.variables[v][time_pos,sub_pos,:,:])
          return var_list

      #Perform clustering and retrieve dataset clustered in n_clusters (for multiple variables)
      def link_multivar(self,method,metrics,n_clusters):
          var_list = self.extract_data(self.lvl_pos())
          clut_list = []
          temp_v_list = []
          for pos,v in enumerate(var_list):
              temp_v_list.append(np.ndarray(shape=(v.shape[0],v[0][:].flatten().shape[0])))
              for i in range(0,v.shape[0]):
                  temp_v_list[pos][i] = v[i][:].flatten()
          gather_data = np.concatenate(temp_v_list)
          uv = np.ndarray(shape=(gather_data.shape[0]/len(var_list),gather_data.shape[1]*len(var_list)))
          for pos,idx in enumerate(uv):
              iters = []
              iters.append(pos)
              for it in range(1,len(var_list)):
                     iters.append(iters[it-1]+uv.shape[0])
              uv[pos] = gather_data[iters].flatten()
          print uv.shape
          del gather_data
          UV = linkage(uv,method,metrics)
          cutree = np.array(cut_tree(UV,n_clusters=n_clusters).flatten())
          clut_indices = []
          for nc in range(0,n_clusters):
              clut_indices.append(np.where(cutree == nc)[0])
          clut_list.append(clut_indices)
          print 'Cluster distirbution'
          print '---------------------'
          for pos,c in enumerate(clut_list):
              obv_dev = []
              for nc in range(0,n_clusters):
                  obv_dev.append((nc,len(c[nc])))
              print sorted(obv_dev,key=lambda x:x[1],reverse=True)
              #for nc in range(0,n_clusters):
              #    print 'Cluster ',nc
              #    print '--------------------------'
              #    unit = self.dataset.variables['time'].units
              #    cal = self.dataset.variables['time'].calendar
              #    times = self.dataset.variables['time'][c[nc]]
              #    print num2date(times,unit,cal)
          return clut_list,UV

      #Perform clustering and retrieve dataset clustered in n_clusters (every var individually)
      def link_var(self,method,metrics,n_clusters):
          var_list = self.extract_data(self.lvl_pos())
          clut_list = []
          for v in var_list:
              var_data = np.ndarray(shape=(v.shape[0],v[0][:].flatten().shape[0]))
              for i in range(0,v.shape[0]):
                  var_data[i] = v[i][:].flatten()
              print var_data.shape
              V = linkage(var_data,method,metrics)
              cutree = np.array(cut_tree(V, n_clusters=n_clusters).flatten())
              clut_indices = []
              for nc in range(0,n_clusters):
                  clut_indices.append(np.where(cutree == nc)[0])
              clut_list.append(clut_indices)
              print 'Cluster distirbution'
              print '---------------------'
              for pos,c in enumerate(clut_list):
                  print 'Variable ',self.subset_variables[pos]
                  obv_dev = []
                  for nc in range(0,n_clusters):
                      obv_dev.append((nc,len(c[nc])))
                  print sorted(obv_dev,key=lambda x:x[1],reverse=True)
                  #for nc in range(0,n_clusters):
                  #    print 'Cluster ',nc
                  #    print '--------------------------'
                  #    unit = self.dataset.variables['time'].units
                  #    cal = self.dataset.variables['time'].calendar
                  #    times = self.dataset.variables['time'][c[nc]]
                  #    print num2date(times,unit,cal)
          return clut_list,V

      def get_clusters_saved(self,V,n_clusters,saved_model='hierachical'):
          clut_list = []
          if saved_model == 'hierachical':
             cutree = np.array(cut_tree(V, n_clusters=n_clusters).flatten())
          clut_indices = []
          for nc in range(0,n_clusters):
              if saved_model == 'hierachical':
                 clut_indices.append(np.where(cutree == nc)[0])
              else:
                 clut_indices.append(np.where(V == nc)[0])
          clut_list.append(clut_indices)
          print 'Cluster distirbution'
          print '---------------------'
          for pos,c in enumerate(clut_list):
              #print 'Variable ',self.subset_variables[pos]
              obv_dev = []
              for nc in range(0,n_clusters):
                  obv_dev.append((nc,len(c[nc])))
              print sorted(obv_dev,key=lambda x:x[1],reverse=True)
              #for nc in range(0,n_clusters):
                  #print 'Cluster ',nc
                  #print '--------------------------'
                  #unit = self.dataset.variables['time'].units
                  #cal = self.dataset.variables['time'].calendar
                  #times = self.dataset.variables['time'][c[nc]]
                  #print num2date(times,unit,cal)
          return clut_list

      def prepare_c_list_for_metrics(self,clut_list):
         if (len(clut_list)!=1):
             raise ValueError('List of clusters must contain only a single variable or a single list for multiple variables')
         ret_list = []
         for c in clut_list[0]:
             print c.tolist()
             temp_arr = np.array(self.extract_timedata(c.tolist(),self.lvl_pos()))
             temp_arr = temp_arr.reshape(len(c),len(self.dataset.variables['longitude'])*len(self.dataset.variables['latitude']))
             ret_list.append(temp_arr)
         return ret_list


      #Write a single cluster to a file for a variable
      def single_cluster_tofile(self,out_path,cluster_label,clut_list):
          for pos,c in enumerate(clut_list):
              print 'Creating file for Variable ',self.subset_variables[pos]
              print 'Cluster label is ',cluster_label
              self.write_timetofile(out_path+'/var_'+self.subset_variables[pos]+'_cluster'+str(cluster_label)+'.nc',self.lvl_pos(),c[cluster_label])

      #Write a single cluster to file for mixed variable
      def multi_cluster_tofile(self,out_path,cluster_label,clut_list):
          for pos,c in enumerate(clut_list):
              print 'Creating file for mixed variables. Cluster label is ',cluster_label
              self.write_timetofile(out_path+'/var_mixed_cluster'+str(cluster_label)+'.nc',self.lvl_pos(),c[cluster_label])

      #Find the maximum continuous timeslot for every cluster
      def find_continuous_timeslots(self,clut_list,hourslot=6):
          times_list = []
          for pos,c in enumerate(clut_list):
              for nc in range(0,len(clut_list[0])):
                  unit = self.dataset.variables['time'].units
                  cal = self.dataset.variables['time'].calendar
                  times = self.dataset.variables['time'][c[nc]]
                  times_list.append(num2date(times,unit,cal))
          for c,time in enumerate(times_list):
              idx_difs = []
              idx_dif = []
              for idx,t in enumerate(time):
                  try:
                     dif = (time[idx+1]-time[idx])==timedelta(hourslot)
                     if dif:
                         idx_dif.append(idx)
                     else:
                         idx_difs.append(idx_dif)
                         idx_dif = []
                         continue
                  except:
                      continue
              len_list = []
              for idx in idx_difs:
                  len_list.append(len(idx))
              print 'Cluster ',c
              print '-------------------------'
              try:
                 max_idx = max(len_list)
              except:
                  print 'No continuous timeslots'
              else:
                  pos_max = len_list.index(max_idx)
                  start_idx = idx_difs[pos_max][0]
                  end_idx = idx_difs[pos_max][len(idx_difs[pos_max])-1]
                  print 'Maximum continuous timeslot'
                  print time[start_idx],time[end_idx]
                  print time[end_idx]-time[start_idx]
                  print start_idx,end_idx

      #Export results to file from attibute dataset
      def write_tofile(self,out_path):
          dsout = Dataset(out_path,'w')
          dim_vars = []
          var_list = self.extract_data(self.lvl_pos())
          for dname, dim in self.dataset.dimensions.iteritems():
              dim_vars.append(dname)
              if dname != self.level_name:
                 dsout.createDimension(dname, len(dim) if not dim.isunlimited() else None)
              else:
                 dsout.createDimension(dname, len(self.pressure_levels) if not dim.isunlimited() else None)
          for v_name, varin in self.dataset.variables.iteritems():
              if v_name in self.subset_variables:
                  for pos_v,v in enumerate(self.subset_variables):
                      if v_name == v:
                          outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
                          outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
                          outVar[:] = var_list[pos_v]
              elif v_name in dim_vars:
                  outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
                  outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
                  if v_name == self.level_name:
                     outVar[:] = self.pressure_levels
                  else:
                     outVar[:] = varin[:]
          dsout.close()

      #Export variables for specific lvl and time period
      def write_timetofile(self,out_path,lvl_pos,time_pos):
          dsout = Dataset(out_path,'w')
          dim_vars = []
          var_list = self.extract_timedata(time_pos,lvl_pos)
          for dname, dim in self.dataset.dimensions.iteritems():
              dim_vars.append(dname)
              if dname == self.level_name:
                 dsout.createDimension(dname, len(self.pressure_levels) if not dim.isunlimited() else None)
              elif dname == self.time_name:
                 dsout.createDimension(dname, len(time_pos) if not dim.isunlimited() else None)
              else:
                 dsout.createDimension(dname, len(dim) if not dim.isunlimited() else None)
          for v_name, varin in self.dataset.variables.iteritems():
              if v_name in self.subset_variables:
                  for pos_v,v in enumerate(self.subset_variables):
                      if v_name == v:
                          outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
                          outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
                          outVar[:] = var_list[pos_v]
              elif v_name in dim_vars:
                  outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
                  outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})
                  if v_name == self.level_name:
                     outVar[:] = self.pressure_levels
                  elif v_name == self.time_name:
                     outVar[:] = self.dataset.variables[self.time_name][time_pos]
                  else:
                     outVar[:] = varin[:]
          dsout.close()
