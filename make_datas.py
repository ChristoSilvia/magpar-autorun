#!/usr/bin/env python

import os, sys, json
import numpy as np

if __name__ == '__main__':
  permutations = [ (diameter,c_to_s_ratio) for diameter in np.linspace(10,100,num=10) for c_to_s_ratio in np.linspace(0.8,1.0,num=6) ]
  
  json_data_file = open(sys.argv[1])
  data = json.load(json_data_file)
  
  if not os.path.exists(sys.argv[1]+"-runchildren"):
    print "Creating runchildren directory"
    os.makedirs(sys.argv[1]+"-runchildren")
  
  for diameter, c_to_s_ratio in permutations:
    simname = "dia"+str(diameter)+"c2s"+str(c_to_s_ratio)
    data["name"] = simname
    data["mesh"]["diameter"] = diameter
    data["mesh"]["c_to_s_ratio"] = c_to_s_ratio
    data["mesh"]["partition"] = "lambda x: 1 if np.sqrt(x[0]**2 + x[1]**2) >={0} else 2".format(diameter * 0.5 * c_to_s_ratio)
    newfile = sys.argv[1]+"-runchildren/"+simname+sys.argv[1]
    print "Creating file: "+newfile
    new_data_file = open(newfile,"w+")
    json.dump(data,new_data_file)
    new_data_file.close()

  json_data_file.close()


