#!/usr/bin/env python

import sys, json
from matplotlib import pyplot as plt
import numpy as np

def get_file_info(json_data_file):
  jd = json_data_file
  toplevel_name = jd["name"]
  sim_names = [ key for key in jd["simulations"] ]
  return toplevel_name, [ ( toplevel_name+"-"+sim_name, jd["simulations"][sim_name] ) for sim_name in sim_names ]

def make_plots(name,dirnames):
  labelled_data = [ ( dirname, np.loadtxt(dirname+"/"+name+".log"), option["plotting"] ) for dirname, option in dirnames ]
  for dirname, dat, options in labelled_data:
    x = options["xaxis"]
    y = options["yaxis"]
    dat = dat[dat[:,x].argsort()]
    plt.xlabel(options["xlabel"])
    plt.ylabel(options["ylabel"])
    plt.plot(dat.T[x],dat.T[y])
    plt.grid(True)
    plt.title(options["title"])
    plt.show()
    

if __name__ == '__main__':
  the_file = open(sys.argv[1])
  data_file = json.load(the_file)
  name, dirnames = get_file_info(data_file)
  make_plots(name,dirnames)
  


