# -*- coding: utf-8 -*-

###
### This file is generated automatically by SALOME v8.5.0 with dump python functionality
###

import sys
import salome

salome.salome_init()
theStudy = salome.myStudy

import salome_notebook
notebook = salome_notebook.NoteBook(theStudy)
#sys.path.insert( 0, r'/home/caelinux/tmp/topo/SIMPforum/m3')
# sys.path.insert( 0, 'C:\\Users\\raphael.nardin\\Documents\\Optimisation_topologique\\inputFiles')
# sys.path.insert( 0, 'C:\\Users\\raphael.nardin\\Documents\\sm-2018-w64-0-3\\WORK')

unvFile = sys.argv[1]
stlFile = unvFile[:-3] + 'stl'


###
### GEOM component
###

import GEOM
from salome.geom import geomBuilder
import math
import SALOMEDS


geompy = geomBuilder.New(theStudy)


###
### GENERICSOLVER component
###

###
### PYLIGHT component
###

###
### ADAO component
###

###
### YACS component
###

###
### SMESH component
###

import  SMESH, SALOMEDS
from salome.smesh import smeshBuilder

smesh = smeshBuilder.New(theStudy)
#~aFilterManager = smesh.CreateFilterManager()

print('Reading input mesh: ', unvFile)
meshopt_unv = smesh.CreateMeshesFromUNV(unvFile)
  
frozenGpList=[]
frozenGrps = False


print('Looking for "frozen" groups...')
try:
  gpnamelist = meshopt_unv.GetGroupNames()
  for gpname in gpnamelist:
    # find groups with "frozen" in their name
    if gpname.lower().find('frozen') > -1 :
      gp = meshopt_unv.GetGroupByName( gpname, elemType = SMESH.VOLUME )
      frozenGpList.extend(gp)
      print('found frozen group: ' , gpname)
  # combine frozen grps in one gp:
  if len(frozenGpList)>0:
    frzVol=meshopt_unv.UnionListOfGroups(frozenGpList,name='frzVol')
    #smesh.SetName(frzVol,'frzVol')
    frozenGrps = True
  else:
    frozenGrps = False
    print('No group names contain "frozen" => disable frozen nodes in mesh smoothing')
  
    
except Exception as exc:
  print('Error processing frozen groups; frozen groups ignored in the following')
  print(exc)
  frozenGrps = False


print('Surface mesh extraction in progress')
nbAdded, meshopt_unv, group = meshopt_unv.MakeBoundaryElements( SMESH.BND_2DFROM3D, 'group', '', 0, [])

#~fr = meshopt_unv.CreateDimGroup( [ gp1 ], SMESH.NODE, 'fr', SMESH.ALL_NODES, 0)

if frozenGrps:
  print('Frozen node list extraction')
  frznFr = meshopt_unv.CreateDimGroup( [ frzVol ], SMESH.FACE, 'frznFr', SMESH.ALL_NODES, 0)
  gpInter = meshopt_unv.IntersectGroups(frznFr, group, 'gpInter')
  frzNodes = meshopt_unv.CreateDimGroup( [ gpInter ], SMESH.NODE, 'frzNodes', SMESH.ALL_NODES, 0)
  ids = frzNodes.GetIDs()
else:
  ids = []
print('Number of frozen nodes: ', len(ids))

#~Mesh = smesh.CopyMesh( meshopt_unv, 'Mesh', 1, 0)
#~[ frozen, gp22, gp33, gp44, gp55, gp66 ] = Mesh.GetGroups()

print('Laplacian Mesh Smoothing in progress')
isDone = meshopt_unv.SmoothParametricObject( meshopt_unv, ids, 1, 1.1, SMESH.SMESH_MeshEditor.LAPLACIAN_SMOOTH )
try:
  meshopt_unv.ExportSTL( stlFile, 1, group)
  print('ExportPartToSTL done. Filename: ', stlFile)
  pass
except:
  print('ExportPartToSTL() failed. Invalid file name?')

smesh.SetName(meshopt_unv.GetMesh(), 'meshopt_unv')

#smesh.SetName(gp1,'gp1')
#smesh.SetName(gp2,'gp2')
#smesh.SetName(gp3,'gp3')

#~smesh.SetName(frznFr, 'frznFr')


if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()
else:
  sys.exit(0)
