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

meshopt_unv = smesh.CreateMeshesFromUNV(unvFile)

frozenGrps = True
try:
  [ gp1, gp2, gp3, frzVol ] = meshopt_unv.GetGroups()
  smesh.SetName(frzVol,'frzVol')
except:
  [ gp1, gp2, gp3 ] = meshopt_unv.GetGroups()
  frozenGrps = False

nbAdded, meshopt_unv, group = meshopt_unv.MakeBoundaryElements( SMESH.BND_2DFROM3D, 'group', '', 0, [])

#~fr = meshopt_unv.CreateDimGroup( [ gp1 ], SMESH.NODE, 'fr', SMESH.ALL_NODES, 0)

if frozenGrps:
  frznFr = meshopt_unv.CreateDimGroup( [ frzVol ], SMESH.FACE, 'frznFr', SMESH.ALL_NODES, 0)
  gpInter = meshopt_unv.IntersectGroups(frznFr, group, 'gpInter')
  frzNodes = meshopt_unv.CreateDimGroup( [ gpInter ], SMESH.NODE, 'frzNodes', SMESH.ALL_NODES, 0)
  ids = frzNodes.GetIDs()
else:
  ids = []

#~Mesh = smesh.CopyMesh( meshopt_unv, 'Mesh', 1, 0)
#~[ frozen, gp22, gp33, gp44, gp55, gp66 ] = Mesh.GetGroups()

isDone = meshopt_unv.SmoothParametricObject( meshopt_unv, ids, 2, 1.1, SMESH.SMESH_MeshEditor.LAPLACIAN_SMOOTH )
try:
  meshopt_unv.ExportSTL( stlFile, 1, group)
  pass
except:
  print('ExportPartToSTL() failed. Invalid file name?')

smesh.SetName(meshopt_unv.GetMesh(), 'meshopt_unv')
smesh.SetName(gp1,'gp1')
smesh.SetName(gp2,'gp2')
smesh.SetName(gp3,'gp3')

#~smesh.SetName(frznFr, 'frznFr')


if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()
