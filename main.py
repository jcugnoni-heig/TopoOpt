# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 17:04:08 2019

@author: utilisateur
"""

#import MEDLoader as ml
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog #, QWidget, QVBoxLayout, QPushButton, QDialog
from PyQt5.uic import loadUi
import topoOptModule as mod
import pickle
#import subprocess
#import time

class topoOptApp(QMainWindow):
    def __init__(self):
        super(topoOptApp, self).__init__()
        filepath=os.path.dirname(os.path.realpath(__file__))
        uiFilePath=os.path.join(filepath,'GUI.ui')
        loadUi(uiFilePath,self)
        self.setWindowTitle('Topological optimization - *unsaved')       
        
        
        ## Signals / slots
        # Main window / menu
        self.actionOpen.triggered.connect(self.openCase)
        self.actionSave.triggered.connect(self.save)
        self.actionSave_as.triggered.connect(self.saveAs)
        self.actionSet_working_directory.triggered.connect(self.setWorkingDir)
        self.actionOpen_mesh.triggered.connect(self.openMesh)
        self.actionRun.triggered.connect(self.runCase)
        self.actionQuit.triggered.connect(self.close)
        self.action_commTemplate.triggered.connect(self.useCustomTemplate)
        self.actionAsRun.triggered.connect(self.defAsRunPath)
        self.actionWrite_export.triggered.connect(self.writeExport)
        self.actionWrite_comm.triggered.connect(self.writeCommandFile)
        self.tabWidget.currentChanged.connect(self.updateLists)
        
        # tab1
        
        # tab2
        self.checkBox_SED.stateChanged.connect(self.updateSED)
        self.txt_Eini.textChanged.connect(self.updateSED)
        self.txt_Smax.textChanged.connect(self.updateSED)
        self.checkBox_Emin.stateChanged.connect(self.updateEmin)
        self.txt_Eini.textChanged.connect(self.updateEmin)
        self.txt_precision.textChanged.connect(self.updateEmin)
        self.rb_targetVF.toggled.connect(self.targetTypeChanged)
        self.rb_targetDispl.toggled.connect(self.targetTypeChanged)
        
        # tab3
        self.button_newGroup.clicked.connect(self.newGroup)
        self.button_delGroup.clicked.connect(self.delGroup)
        self.button_newBC.clicked.connect(self.newBC)
        self.button_delBC.clicked.connect(self.delBC)
        self.button_apply.clicked.connect(self.defineBC)
        self.list_makeBC.currentItemChanged.connect(self.displayBC)
        self.rb_force.toggled.connect(self.BCtypeChanged)
        self.rb_displ.toggled.connect(self.BCtypeChanged)
        self.rb_press.toggled.connect(self.BCtypeChanged)
        
        # tab4
        self.button_createLC.clicked.connect(self.createLC)
        self.list_LC.currentItemChanged.connect(self.highlightBCs)
        self.button_deleteLCs.clicked.connect(self.deleteLCs)
        self.button_useDefault.clicked.connect(self.useDefaultLCs)

        self.TopoOptInstance = mod.TopoOpt(self)
        self.TopoOptInstance.displayCase()

    def updateSED(self):
        self.txt_SEDtargetMax.setDisabled(self.checkBox_SED.isChecked())
        self.txt_Smax.setDisabled(not self.checkBox_SED.isChecked())
        if self.checkBox_SED.isChecked() == True:
            try:
                stress = float(self.txt_Smax.text())
                Eini = float(self.txt_Eini.text())
                SED = stress**2/(2*Eini)
                self.txt_SEDtargetMax.setText("{0:5.5f}".format(SED))
            except:
                pass
        else:
            if self.sender() == self.checkBox_SED:
                self.txt_SEDtargetMax.setText('')
    
    def targetTypeChanged(self):
        self.txt_targetVF.setDisabled(not self.rb_targetVF.isChecked())
        self.txt_targetDispl.setDisabled(not self.rb_targetDispl.isChecked())

    def updateEmin(self):
        self.txt_Emin.setDisabled(self.checkBox_Emin.isChecked())
        if self.checkBox_Emin.isChecked() == True:
            try:
                precision = float(self.txt_precision.text())
                Eini = float(self.txt_Eini.text())
                Emin = Eini*precision
                self.txt_Emin.setText("{0:5.2f}".format(Emin))
            except:
                pass
        else:
            if self.sender() == self.checkBox_Emin:
                self.txt_Emin.setText('')
                
    def openCase(self):
        
        wkDir = os.getcwd()
        if 'workingDir' in self.TopoOptInstance.filesDic:
            wkDir = self.TopoOptInstance.filesDic['workingDir']

        file = QFileDialog.getOpenFileName(self, 'Open', wkDir, "Topological optimization files (*.topo)")
        if file[0] == '':
            return
        
        fullFileName = file[0].replace('/', os.sep)
        fullFileName = fullFileName.replace('\\', os.sep)
        pickle_in = open(fullFileName,"rb")
        
        try:
            filesDic = pickle.load(pickle_in)
            parametersDic = pickle.load(pickle_in)
            
            BCs = pickle.load(pickle_in)
            groups = pickle.load(pickle_in)
            loadCases = pickle.load(pickle_in)
        except:
            QMessageBox.information(self, 'Error', 'Problem while loading selected case.', QMessageBox.Ok,)
            return
        
        ### ligne retiree de la version precedente.. 
        filesDic.update({'topoOptFileName' : fullFileName}) # le nom/emplacement de fichier peut avoir changé 
        
        # On remplace le membre initial par une nouvelle instance de TopoOpt
        self.TopoOptInstance = mod.TopoOpt(self, filesDic, parametersDic, groups, BCs, loadCases)
        
        # A revoir si on décide d'avoir un membre "liste de TopoOpt" et que displayCase afficherait une instance choisie...
        self.TopoOptInstance.displayCase()        
        
    def saveAs(self):
        wkDir = os.getcwd()
        if 'workingDir' in self.TopoOptInstance.filesDic:
            wkDir = self.TopoOptInstance.filesDic['workingDir']

        file = QFileDialog.getSaveFileName(self, 'Save TopoOpt file', wkDir, "Topological optimization files (*.topo)")
        if file[0] == '':
            return
        fullFileName = file[0].replace('/', os.sep)
        fullFileName = fullFileName.replace('\\', os.sep)

        self.TopoOptInstance.saveAs(fullFileName)
        
    def save(self):
        if 'topoOptFileName' not in self.TopoOptInstance.filesDic or self.TopoOptInstance.filesDic['topoOptFileName'] == '':
            self.saveAs()
            return
        
        self.TopoOptInstance.saveAs(self.TopoOptInstance.filesDic['topoOptFileName'])
 
    def setWorkingDir(self):        
        self.TopoOptInstance.setWorkingDir()
        
    def useCustomTemplate(self):
        self.TopoOptInstance.useCustomTemplate()
        
    def defAsRunPath(self):
        self.TopoOptInstance.defAsRunPath()
        
    def writeExport(self):
        self.TopoOptInstance.writeExport()        

    def writeCommandFile(self):
        self.TopoOptInstance.writeCommandFile()
    
    def newGroup(self):
        self.TopoOptInstance.newGroup()
        
    def delGroup(self):
        self.TopoOptInstance.delGroup()
        
    def newBC(self):
        self.TopoOptInstance.newBC()
        
    def delBC(self):
        self.TopoOptInstance.delBC()
        
    def defineBC(self):
        self.TopoOptInstance.defineBC()
        
    def displayBC(self):
        self.TopoOptInstance.displayBC()
        
    def BCtypeChanged(self):
        self.TopoOptInstance.BCtypeChanged()
        
    def openMesh(self):
        self.TopoOptInstance.openMesh()        
    
    def runCase(self):
        try:
            dialog=mod.runDialog(self.TopoOptInstance,parent=self)
        except:
            return
        dialog.setModal(False)
        dialog.show()
        
        #os.system(self.TopoOptInstance.filesDic['asRun'] + ' ' + self.TopoOptInstance.filesDic['workingDir'] + self.TopoOptInstance.parametersDic['jobName'] + '.export')
        # run solver without waiting for completion. Setup PIPES to read output during execution.
        #p=subprocess.Popen([self.TopoOptInstance.filesDic['asRun'],self.TopoOptInstance.filesDic['workingDir'] + self.TopoOptInstance.parametersDic['jobName']+'.export'],
        #                 stdout=subprocess.PIPE)
        #while p.poll()==None:
            # TODO: run this in a separate window and thread to implement job progress monitoring 
        #    print(p.stdout.readline())
        return
    
    def updateLists(self):
        self.TopoOptInstance.updateListBC()
        self.TopoOptInstance.updateListLC()
    
    def createLC(self):
        self.TopoOptInstance.createLC()
    
    def highlightBCs(self):
        self.TopoOptInstance.highlightBCs()
    
    def deleteLCs(self):
        self.TopoOptInstance.deleteLCs()
        
    def useDefaultLCs(self):
        self.TopoOptInstance.useDefaultLCs()

if __name__ == '__main__':
    app = QApplication([]) #sys.argv
    widget = topoOptApp()
    widget.show()
    sys.exit(app.exec_())
