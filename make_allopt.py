#!/usr/bin/python

import subprocess
import json
import os,sys,string,time
import numpy as np

import make_inp


def readmesh(filename):
    """This will read the NETGEN neutral mesh 'filename' and return
    points, tetrahedra and triangles"""
    
    f = open(filename, 'r')

    #################################################################
    #
    # read the first line to get the number of points
    #
    #################################################################

    thisline         = f.readline()
    number_of_points = int(thisline)

    #################################################################
    #
    # read the points
    #
    #################################################################

    points = []

    for i in range(number_of_points):
        thisline  = f.readline()
        segments  = string.split(thisline[:-1])
        thispoint = list(map(lambda p: float(p), segments))
        points.append(thispoint)

    #################################################################
    #
    # now read all the volume elements
    # first, ascertain the number of volume elements
    #
    #################################################################

    thisline             = f.readline()
    number_of_tetrahedra = int(thisline)

    #################################################################
    #
    # then read and populate, keeping track
    # of the tetrahedra subdomain
    #
    #################################################################
    
    tetrahedra           = []
    tetrahedra_subdomain = []

    for i in range(number_of_tetrahedra):
        thisline = f.readline()
        segments = string.split(thisline[:-1])
        if len(segments) != 5:
            print "Found", len(segments), "elements, but expected 5"
            print segments
            raise "Oops", "File format error"

        tetrahedra_subdomain.append(int(segments[0])-1)

        # rpb, 17th March 2006 - updated to handle materials (note:
        # in netgen these are top-level objects [tlos])
        # original mapping was [a, b, c, d] (where a-d are points)
        # new mapping is [[a,b,c,d],m] (where m is a material ID)
        tetrahedron = [list(map(lambda t : int(t)-1, segments[1:5])), int(segments[0])]

        # netgen counts from 1 rather than from 0, hence int(t)-1

        tetrahedra.append(tetrahedron)

    #################################################################
    #
    # now for the surface elements
    # ascertain the number of surface elements
    #
    #################################################################

    thisline            = f.readline()
    number_of_triangles = int(thisline)
    triangles           = []
    triangles_subdomain = []
    for i in range(number_of_triangles):
        thisline = f.readline()
        segments = string.split(thisline[:-1])
        if len(segments) != 4:
            print "Found", len(segments), "elements, but expected 4"
            print segments
            raise "Oops", "File format error"

        triangles_subdomain.append(int(segments[0])-1)
        # similar adjustment for materials as with tetrahedra
        triangle = [list(map(lambda t : int(t)-1, segments[1:4])), int(segments[0])]
        triangles.append(triangle)

    #################################################################
    #
    # send back the read mesh
    #
    #################################################################
    
    return (points, tetrahedra, triangles, tetrahedra_subdomain, triangles_subdomain)



def make_mesh(partition, outputfile,points,tetrahedra, triangles, tetrasub, trisub):
    print stamp() + "Points:     %d" % len(points)
    print stamp() + "Tetrahedra: %d [%d in subdomain]" % (len(tetrahedra), len(tetrasub))
    print stamp() + "Triangles:  %d [%d in subdomain]" % (len(triangles),  len(trisub))

    #################################################################
    #
    # the first line of a UCD file reads:
    # a b c d e
    #
    # where a is the number of nodes
    #       b is the number of cells
    #       c is the length of vector data associated with the nodes
    #       d is the length of vector data associated with the cells
    #       e is the length of vector data associated with the model
    #
    # example: 12 2 1 0 0
    #
    #################################################################

    # n.b. here the third integer indicates the number of placeholders
    
    print stamp() + "Creating descriptor [UCD]"
    writeln(str(len(points)) + " " + str(len(tetrahedra)) + " 3 0 0", outputfile)
    print stamp() + "UCD descriptor created"
    
    #################################################################
    #
    # then we have nodes in threespace, one line per node
    # n x y z
    # where n is the node ID -- integer (not necessarily sequential)
    #       x,y,z are the x, y and z coordinates
    #
    #################################################################

    print stamp() + "Now converting nodes"
    for i in range(len(points)):
        x, y, z = points[i][0], points[i][1], points[i][2]
        writeln(str(i+1) + " " + str(x) + " " + str(y) + " " + str(z), outputfile)
    print stamp() + "Nodes converted"

    #################################################################
    #
    # now the cells, one line/cell:
    #
    # c m t n1 n2 ... nn
    #
    # where c is the cell ID
    #       m is the material type (int, leave as 1 if we don't care)
    #       t is the cell type (prism|hex|pyr|tet|quad|tri|line|pt)
    #       n1...nn is a node ID list corresponding to cell vertices
    #
    #################################################################

    print stamp() + "Now assigning materials to tetrahedra"
  
    materials = {}

    for tetra in tetrahedra:
        tet = tetra[0]
        materials_family = tetra[1]
        tetra_points = map(lambda x:[points[x][0],
                                     points[x][1],
                                     points[x][2]],tet)
        tetra_center = map(np.mean,zip(*tetra_points))
        tetra[1] = partition(tetra_center)
        if tetra[1] in materials:
          materials[tetra[1]] += 1
        else:
          materials[tetra[1]] = 1

    print stamp() + "Materials assigned to tetrahedra " + str(materials)

    n_of_materials = len(materials)

    cellctr = 0

    print stamp() + "Converting tetrahedra"

    ### here we need to take extra care of the tetrahedra point write
    ### order to avoid "negative" volume issues

    for tetra in tetrahedra:
        tet = tetra[0] # just the tetrahedron; tetra[1] is the material
        tetorder  = [0, 2, 1, 3]
        tetstring =  " " + str(tet[tetorder[0]]+1)
        tetstring += " " + str(tet[tetorder[1]]+1)
        tetstring += " " + str(tet[tetorder[2]]+1)
        tetstring += " " + str(tet[tetorder[3]]+1)
        writeln(str(cellctr+1) + " " + str(tetra[1]) + " tet" + tetstring, outputfile)
        cellctr   += 1

    print stamp() + "Tetrahedra converted"

    #################################################################
    #
    # uncomment the following section to convert triangles as well
    # - since magpar will ignore these, leave away for the time being
    #
    # print stamp() + "Converting triangles"
    #
    # cellctr = 0
    # for triang in triangles:
    #     tri = triang[0] # just the triangle; triang[1] is the material
    #     tristring = ""
    #     for node in tri:
    #         tristring += " " + str(node+1)
    #     writeln(str(cellctr+1) + " " + str(triang[1]) + " tri" + ts, outputfile)
    #
    # print stamp() + "Triangles converted"
    #
    #################################################################

    #################################################################
    #
    # for the data vector associated with the nodes:
    #
    # first line tells us into which components the vector is divided
    #
    #   example: vector of 5 floats could be 3 3 1 1
    #            node scalar could be 1 1
    #
    # next lines, for each data component, use a cs label/unit pair
    #
    #   example: temperature, kelvin
    #
    # subsequent lines, for each node, the vector of associated data
    # in this order
    #
    #   example: 1 10\n2 15\n3 12.4\n4 9
    #
    #################################################################

    print stamp() + "Initialising placeholders"

    writeln("3 1 1 1", outputfile)
    writeln("M_x, none", outputfile)
    writeln("M_y, none", outputfile)
    writeln("M_z, none", outputfile)
    
    #################################################################
    #
    # create some initial scalar values; here, generally
    # +x=1.0 +y=+z=0.01*x (everything else)="\epsilon"
    #
    #################################################################

    scalarstring =  " 1.0 0.0 0.0"

    for i in range(len(points)):
        writeln(str(i+1) + scalarstring, outputfile)

    print stamp() + "Placeholders inserted"

    # all done

    print stamp() + "All finished"

    return n_of_materials

def bail(message="Sorry, I don't understand. Bailing out..."):
    """A 'get-out' clause"""
    print message
    sys.exit(1)

def initialise_file(file):
    """Attempt to remove the file first to avoid append issues"""
    try:
        os.remove(file)
    except:
        # no problem
        pass

def writeln(line, file):
    """One-shot file line append; this keeps the code terse"""
    f = open(file, 'a')
    f.write(line + '\n')
    f.close()

def stamp():
    """Format a time and a date for stdout feedback"""
    thistime = time.localtime()
    return "[%04d/%02d/%02d %02d:%02d:%02d] " % (thistime[0],
                                                 thistime[1],
                                                 thistime[2],
                                                 thistime[3],
                                                 thistime[4],
                                                 thistime[5])

    

def info():
    """Output GPL details"""
    print """ngtoucd, copyright (c) 2002-2005 Richard Boardman, Hans Fangohr
ngtoucd comes with ABSOLUTELY NO WARRANTY; for details see the file COPYING"""



def make_inp_file(mesh_params,name):
  """ Creats an inp file in the current directory
  and returns its filename"""
  
  def cylinder(p):
    return """algebraic3d

solid cyl = cylinder (0,0,-1;0,0,1;{0})
        and plane (0,0,{1};0,0,1)
        and plane (0,0,-{1};0,0,-1) -maxh={2};

tlo cyl;""".format(p["diameter"]/2.0,p["diameter"]*p["aspect_ratio"]*0.5,p["mesh_res"])

  def coreshell(p):
    return """algebraic3d
solid core = cylinder (0,0,-1;0,0,1;{0})
         and plane (0,0,{1};0,0,1)
         and plane (0,0,-{1};0,0,-1) -maxh={2};

solid shell = cylinder (0,0,-1;0,0,1;{3})
         and plane (0,0,{1};0,0,1)
         and plane (0,0,-{1};0,0,-1)
         and not core -maxh={2};

tlo core;
tlo shell;""".format(p["diameter"] * 0.5 * p["c_to_s_ratio"],
                     p["diameter"] * p["aspect_ratio"]*0.5,
                     p["mesh_res"],
                     p["diameter"] * 0.5)

  supported_geometries = {
    "cylinder":cylinder,
    "coreshell":coreshell
  }
  if "inpfile" in mesh_params and mesh_params["inpfile"] is not "":
    """Make a new .inp file with the same name as the project"""
    old_inpfile = open(mesh_params["inpfile"])
    new_inpfile = open(name+".inp","w+")
    new_inpfile.write(old_inpfile.read())
    new_inpfile.close()
    old_inpfile.close()
    return name+".inp"
  elif "mshfile" in mesh_params and mesh_params ["mshfile"] is not "":
    """ Try to read a partition function from the input parameters,
        and make everything the first material if it fails"""
    if "partition" in mesh_params:
      partition = eval(mesh_params["partition"])
    else:
      partition = lambda x:1
    """Read from the mesh file, and write to a mesh with the partition function and the name of the project"""
    print "Reading from mshfile"
    points, tetrahedra, triangles, tetrahedra_subdomain, triangles_subdomain = readmesh(mesh_params["mshfile"])
    print "Read mshfile, writing inp file"
    n_of_materials = make_mesh(partition,name+".inp",points,tetrahedra,triangles,tetrahedra_subdomain, triangles_subdomain)
    print "Number of materials used:"+str(n_of_materials)
    return name+".inp"
  elif "geofile" in mesh_params and mesh_params["geofile"] is not "":
    print "Making mshfile using netgen"
    command = "netgen "+mesh_params["geofile"]+" -meshfiletype=\"Neutral Format\" -meshfile="+name+".msh"
    print "Executing command: $"+command
    p = os.system(command)
    print "netgen finished with status:"+str(p)
    mesh_params["mshfile"] = name+".msh"
    print "Recurring using mshfile as input"
    return make_inp_file(mesh_params,name)
  elif "geometry" in mesh_params:
    if mesh_params["geometry"] in supported_geometries:
      print "Accepted geometry:" + mesh_params["geometry"]
      try:
        geofile = open(name+".geo","w+")
        geofile.write( supported_geometries[mesh_params["geometry"]](mesh_params) )
        geofile.close()
        mesh_params["geofile"] = name+".geo"
        print "Recurring using generated geofile as input"
        return make_inp_file(mesh_params,name)
      except KeyError:
        raise KeyError("The specified built-in geometry,{0},requires additional keys to proceed.  Please check this file.".format(mesh_params["geometry"]))
    else:
      raise ValueError("Desired geometry not supported")
  else:
    raise ValueError("No mesh format or data given")

def make_inp(inputfile):
  datafile = open(inputfile)
  data = json.load(datafile)
  inp_filename = make_inp_file(data["mesh"],data["name"])
  print(inp_filename)


def make_krn(inputfile):
  data_file = open(inputfile)
  data = json.load(data_file)
  name, materials = data["name"],data["materials"]
  materials_string = generate_material_properties(materials)
  print "Generated output:\n" + materials_string
  output = open(name+".krn","w+")
  print "Writing to file: "+str(output)
  output.write(materials_string)
  output.close()


def generate_material_properties(materials):
  material_properties = ["theta","phi","K1","K2","Js","A","alpha","psi"]
  material_units      = ["Rad","Rad","J/m^3","J/m^3","T","J/m","1","Rad"]
  material_file = ""
  for material in materials:
    for key in material_properties:
      material_file += material[key]+"  "
    material_file += "# "+material["name"] + "\n" 
  material_file += "#\n#  " + "  ".join(material_properties)+"   name\n"
  material_file += "#  " + "  ".join(material_units) +"\n#\n"
  return material_file

def get_simulation_params(filename):
  datafile = open(filename)
  data = json.load(datafile)
  return data["name"],data["simulations"]

def make_allopt(simulation):
  allopt = "# Magpar configuration file\n"
  for key,value in simulation.iteritems():
    allopt += "-"+key+" "+value+"\n"
  return allopt

def make_run_directories(name,simulations,linkables):
  """Create run directories and populate them with an allopt
  and symlinks to all of the things specified"""
  print "Making run directories"
  run_dirs = []
  for simName,sim in simulations.iteritems():
    print "Creating directory for simulation: "+simName
    
    sim_filepath = name+"-"+simName
    if not os.path.exists(sim_filepath):
      os.makedirs(sim_filepath)
    
    allopt_file = open(sim_filepath+"/allopt.txt","w+")
    allopt = make_allopt(sim)
    print "Generated allopt:\n"+allopt
    allopt_file.write(allopt)
    allopt_file.close()

    for link in linkables:
      command =  "cp "+link+" "+sim_filepath+"/"+link
      print command
      os.system(command)

    run_dirs.append(sim_filepath)

  return run_dirs

if __name__ == '__main__':
  inputfile = sys.argv[1]

  make_inp(inputfile)
  make_krn(inputfile)

  name,sims = get_simulation_params(inputfile)
  print(sims)
  
  linkables = [name+".krn",name+".inp","magpar.exe","mkinp.sh","inp2vtu.pl"]

  for link in linkables:
    print link
  run_dirs = make_run_directories(name,sims,linkables)

  for run in run_dirs:
    run_command = "mpirun -n 6 {0}/magpar.exe > {0}/{1}.runlog && {0}/mkinp.sh {0}/{1}.0001.femsh {0}/*.gz && {0}/inp2vtu.pl {1} &".format(run,name)
    print run_command
    os.system(run_command)
  
