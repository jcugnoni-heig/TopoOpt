# -*- coding: utf-8 -*-
"""
Created on Thu Feb 28 08:16:17 2019

@author: utilisateur
"""

import os
from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog, QListWidgetItem, QPlainTextEdit, QPushButton, QLabel
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt,QRect, QTimer #,  pyqtSlot
#from PyQt5.QtGui import QStandardItem, QStandardItemModel
import pickle
import subprocess
import time
import re


class runDialog(QDialog):
	def __init__(self,p_topoOpt,parent=None):
		QDialog.__init__(self,parent)
		self.resize(620,450)
		self.lbl_iter = QLabel("Iteration 0/" + str(p_topoOpt.parametersDic['nIter']) + '\nRelative volume difference wrt. previous iteration : -\nValue required : ' + "{:.2E}".format(p_topoOpt.parametersDic['convCrit']) + '\nElapsed time : -', self)
		self.lbl_iter.setGeometry(QRect(10, 5, 620, 65))	   
		self.textbox = QPlainTextEdit("",self)
		self.textbox.setGeometry(QRect(10, 70, 600, 340))
		self.textbox.setReadOnly(True)
		self.textbox.setLineWrapMode(QPlainTextEdit.NoWrap)
		self.btn_run = QPushButton("RUN", self)
		self.btn_run.setGeometry(QRect(100, 420, 50, 20))
		self.btn_run.clicked.connect(self.button_run)
		self.btn_stop = QPushButton("STOP", self)
		self.btn_stop.setGeometry(QRect(300, 420, 50, 20))
		self.btn_stop.clicked.connect(self.button_stop)
		self.timer=QTimer()
		self.timer.setInterval(100)
		self.timer.timeout.connect(self.updateText)
		self.pipe=None
		self.subprocess=None
		self.running=False
		self.message=''
		self.TopoOptInstance=p_topoOpt
		self.startTime = 0.0
		self.currentIter = 0
		self.currentRelDiff = -1.0
		self.currentValue = -1.0
		self.volTarget = -1.0
		
		self.updateInfo()
	
	def button_run(self):
		self.currentIter = 0
		self.currentRelDiff = -1.0
		self.currentValue = -1.0
		self.startTime = time.time()
		self.updateInfo()
		
		self.TopoOptInstance.saveCurrentInputParams()
		if self.TopoOptInstance.writeExport() == 0:
			return
		if self.TopoOptInstance.writeCommandFile() == 0:
			return
		
		self.running=True
		
		# print(self.TopoOptInstance.filesDic['asRun'])
		# print(self.TopoOptInstance.filesDic['workingDir'])
		# print(self.TopoOptInstance.parametersDic['jobName']+'.export')
		
		self.subprocess=subprocess.Popen([self.TopoOptInstance.filesDic['asRun'],self.TopoOptInstance.filesDic['workingDir'] + self.TopoOptInstance.parametersDic['jobName']+'.export'], stdout=subprocess.PIPE)
		self.pipe=self.subprocess.stdout
		
		self.timer.start()
		
	
	def button_stop(self):
		self.timer.stop()
		if self.subprocess != None:
			self.subprocess.terminate()
		
		self.TopoOptInstance.getConvergenceData()
		
		txt_result = ''
		if self.sender() == self.timer: # "natural" end => .unv should be available => execute mesh smooth
			if self.subprocess.returncode == 0:
				txt_result = 'Optimization finished successfully.'
				
				[myErrorCode, result] = self.TopoOptInstance.execMeshSmooth('mat1')
				if myErrorCode != 0 or result != 0:
					txt_result += '\n\nTopoOpt.execMeshSmooth(''mat1'') crashed :\nMy error code =' + str(myErrorCode) + '\nExit code =' + str(result)
				
				if self.TopoOptInstance.parametersDic['bimat'] == True:
					[myErrorCode2, result2] = self.TopoOptInstance.execMeshSmooth('mat2')
					if myErrorCode2 != 0 or result2 != 0:
						txt_result += '\n\nTopoOpt.execMeshSmooth(''mat2'') crashed :\nMy error code =' + str(myErrorCode) + '\nExit code =' + str(result)
			else:
				txt_result = 'Optimization crashed.\nReturn code = ' + str(self.subprocess.returncode)
			QMessageBox.information(self.TopoOptInstance.interface,'Information', txt_result, QMessageBox.Ok,)
			
		self.running=False		 
			
	def updateText(self):
		self.updateInfo()
		if self.subprocess.poll()==None:
			for i in range(50):
				try:
					text=self.pipe.readline().decode()
					
					self.textbox.appendPlainText(text)
					self.message=self.message+text

					pattern1 = r"^iteration [1-9]([0-9])*"
					pattern2 = r"^Relative ... difference ([0-9])+"
					pattern3 = r"Current ... ([0-9])+"
					
					if re.match(pattern1, text):
						try:
							number = int(text.split(' ')[1])
							self.updateInfo(p_iter = number)
						except:
							pass
						
					if re.match(pattern2, text):
						try:
							number = float(text.split(' ')[3])
							self.updateInfo(p_relDiff = number)
						except:
							pass 
						
					if re.match(pattern3, text):
						try:
							number = float(text.split(' ')[2])
							if self.TopoOptInstance.parametersDic['boolVolTarget'] == True and text.split(' ')[1] == 'vol':
								if self.currentIter == 1:
									self.volTarget = number*self.TopoOptInstance.parametersDic['targetVF']
								number = number / self.volTarget * 100.0
								self.updateInfo(p_curVal = number)
							elif self.TopoOptInstance.parametersDic['boolVolTarget'] == False and text.split(' ')[1] == 'dpl':
								number = number / self.TopoOptInstance.parametersDic['targetDispl'] * 100.0
								self.updateInfo(p_curVal = number)
						except:
							pass   
				except:
					pass

		else: # optimization over
			self.button_stop()
	
	def updateInfo(self, p_iter=None, p_relDiff=None, p_curVal=None):
		if p_iter != None: self.currentIter = p_iter
		if p_relDiff != None: self.currentRelDiff = p_relDiff
		if p_curVal != None: self.currentValue = p_curVal
		
		boolVolTarget = self.TopoOptInstance.parametersDic['boolVolTarget']
		line1 = 'Iteration ' + str(self.currentIter) + '/' + str(self.TopoOptInstance.parametersDic['nIter'])
		line3 = 'Relative ' + boolVolTarget*'volume' + (not boolVolTarget)*'max displacement' + ' difference wrt. previous iteration : '
		line3 = line3 + (self.currentRelDiff == -1.0)*'-' + (self.currentRelDiff != -1.0)*"{:.2E}".format(self.currentRelDiff)
		line3 = line3 + '  (required : ' + "{:.2E}".format(self.TopoOptInstance.parametersDic['convCrit']) + ')'
		line2 = 'Current ' + boolVolTarget*'volume' + (not boolVolTarget)*'max displacement' + ' wrt. target : '
		line2 = line2 + (self.currentValue == -1.0)*'-' + (self.currentValue != -1.0)*("{0:5.2f}".format(self.currentValue) + '%') + '	(tolerated error : 1%)'
		line4 = 'Elapsed time : ' + (time.strftime("%H:%M:%S", time.gmtime(time.time() - self.startTime)))*(self.running) + ('-')*(not self.running)
		self.lbl_iter.setText(line1 + '\n' + line2 + '\n' + line3 + '\n' + line4)

		
			




class dialog_groupBC(QDialog):
	def __init__(self, p_topoOpt, p_fieldName):
		super(dialog_groupBC, self).__init__()
		filepath=os.path.dirname(os.path.realpath(__file__))
		uiFilePath=os.path.join(filepath,'dialog_group.ui')
		loadUi(uiFilePath,self)
		self.setWindowTitle('New ' + (p_fieldName == 'BC')*'boundary condition' + (p_fieldName == 'group')*'group')
		self.txt_field.setPlaceholderText('<New ' + (p_fieldName == 'BC')*'boundary condition' + (p_fieldName == 'group')*'group' + ' name')
		self.topoOpt = p_topoOpt
		self.fieldName = p_fieldName
		
		self.button_groupOK.clicked.connect(self.add)
		self.button_close.clicked.connect(self.close)
		
		self.entities = []
	def add(self):
		newField = self.txt_field.text()
		if newField == '' or newField == ' ':
			self.txt_field.setText('')
			return
		
		for entity in self.entities:
			if newField == entity:
				return
			
		self.entities.append(newField)
		self.txt_field.setText('')

class BoundaryCondition:
	def __init__(self, p_name):
		self.name = p_name
		self.groupNames = None
		self.BCtype = None
		self.DoF_x = None
		self.DoF_y = None
		self.DoF_z = None
		self.pressureValue = None
		
	def setType(self, BCtype):
		self.BCtype = BCtype
	
	def setGroup(self, p_groups):
		if p_groups == None or len(p_groups) == 0:
			return
		self.groupNames = []
		for item in p_groups:
			self.groupNames.append(item.text())
		
	def setPressure(self, pressVal):
		try:
			self.pressureValue = float(pressVal)
		except:
			self.pressureValue = None
		
	def setDoFs(self, DoF_x, DoF_y, DoF_z):
		try:
			self.DoF_x = float(DoF_x)
		except:
			self.DoF_x = None

		try:
			self.DoF_y = float(DoF_y)
		except:
			self.DoF_y = None
			
		try:
			self.DoF_z = float(DoF_z)
		except:
			self.DoF_z = None

class LoadCase:
	def __init__(self, p_number, p_BCs):
		self.number = p_number
		self.BCs = p_BCs




class TopoOpt:
	# Current dictionnaries keys :
	# filesDic : 'topoOptFileName', 'workingDir', 'meshFile', 'asRun', 'commTemplate', 'exportTemplate'
	# parametersDic : 'jobName', 'memoryLimit', 'nbCpu', 'solverIndex', 'timeLimit', 'version', 'saveInterval',
	#				  'optiGroups', 'frozenGroups', 'Eini', 'Smax', 'SEDtargetMax', 'useDefValSED', 'nIter', 
	#				  'targetVF', 'targetDispl', 'densityPenaltyExponent', 'precision', 'Emin',
	#				  'useDefValEmin', 'eta1', 'eta2', 'bimat', 'convCrit', 'boolVolTarget'

	def __init__(self, p_interface=None, p_filesDic={}, p_parametersDic={}, p_groups=[], p_BCs=[], p_loadCases=[]):
		self.interface = p_interface
		self.filesDic = p_filesDic
		self.parametersDic = p_parametersDic
		self.groups = p_groups
		self.BCs = p_BCs
		self.loadCases = p_loadCases
		progDir=os.path.dirname(os.path.realpath(__file__))
		
		#if 'topoOptFileName' not in self.filesDic: self.filesDic.update({'topoOptFileName' : ''})
		if 'workingDir' not in self.filesDic:
			self.filesDic.update({'workingDir' : progDir})
		else:
			wkDir = self.filesDic['workingDir'].replace('\\', os.sep)
			wkDir = wkDir.replace('/', os.sep)
			if (wkDir[-1] != os.sep):
				wkDir = wkDir + os.sep
				self.filesDic.update({'workingDir' : wkDir})

		if ('asRun' not in self.filesDic) or (os.path.exists(self.filesDic['asRun']) == False): 
			self.filesDic.update({'asRun' : 'as_run'})	

		if ('commTemplate' not in self.filesDic) or (os.path.exists(self.filesDic['commTemplate']) == False): 
			self.filesDic.update({'commTemplate' : os.path.join(progDir, 'template.comm')})	 

		if ('exportTemplate' not in self.filesDic) or (os.path.exists(self.filesDic['exportTemplate']) == False):
			self.filesDic.update({'exportTemplate' : os.path.join(progDir, 'template.export')}) 


	def saveAs(self, p_path):
		if (self.saveCurrentInputParams() == 0):
			return

		if p_path[-5:] != '.topo':
			p_path = p_path + '.topo'
			
		self.filesDic.update({'topoOptFileName' : p_path})
		
		pickle_out = open(p_path,"wb")
		
		try: pickle.dump(self.filesDic, pickle_out)
		except: pickle.dump(None, pickle_out)
		try: pickle.dump(self.parametersDic, pickle_out)
		except: pickle.dump(None, pickle_out)

		try: pickle.dump(self.BCs, pickle_out)
		except: pickle.dump(None, pickle_out)
		try: pickle.dump(self.groups, pickle_out)
		except: pickle.dump(None, pickle_out)
		try: pickle.dump(self.loadCases, pickle_out)
		except: pickle.dump(None, pickle_out)

		pickle_out.close()
		self.interface.setWindowTitle('Topological optimization - ' + p_path.split(os.sep)[-1])

		
	def setWorkingDir(self):
		# dlg = dialog_setWD(self)
		# dlg.show()
		# dlg.exec_()

		dir = QFileDialog.getExistingDirectory(self.interface, 'Choose directory', self.filesDic['workingDir'])
		if dir == '':
			return
		
		fullDirName = dir.replace('/', os.sep)
		fullDirName = fullDirName.replace('\\', os.sep)
		if fullDirName[-1] != os.sep:
			fullDirName = fullDirName + os.sep
		self.filesDic.update({'workingDir' : fullDirName})
		
		self.interface.label_wdir.setText(fullDirName)
		
	def newGroup(self):
		dlg = dialog_groupBC(self, 'group')
		dlg.show()
		dlg.exec_()
		
		for newEntity in dlg.entities:
			exists = False
			for i in range(self.interface.list_makeGroup.count()):
				if self.interface.list_makeGroup.item(i).text() == newEntity:
					exists = True
					break
			if exists == False:
				self.interface.list_makeGroup.addItem(newEntity)
				self.groups.append(newEntity)
		
	def newBC(self): # + button
		dlg = dialog_groupBC(self, 'BC')
		dlg.show()
		dlg.exec_()
		
		BCsToAdd = []

		for newEntity in dlg.entities:
			exists = False
			for i in range(self.interface.list_makeBC.count()):
				if self.interface.list_makeBC.item(i).text() == newEntity:
					exists = True
					break
			if exists == False:
				newBC = BoundaryCondition(newEntity)
				BCsToAdd.append(newBC)
				self.BCs.append(newBC)
		
		Utils.fillListView(BCsToAdd, self.interface.list_makeBC)
		
	def defineBC(self): # apply button
		if self.interface.list_makeBC.currentItem() == None or self.interface.list_makeBC.currentItem().text() == '':
			QMessageBox.information(self.interface, 'Information', 'Please choose a boundary condition.', QMessageBox.Ok,)
			return
		if self.interface.rb_force.isChecked() == False and self.interface.rb_displ.isChecked() == False and self.interface.rb_press.isChecked() == False:
			QMessageBox.information(self.interface, 'Information', 'Please choose a boundary condition type.', QMessageBox.Ok,)
			return
		if self.interface.list_makeGroup.selectedItems() == None or len(self.interface.list_makeGroup.selectedItems()) == 0:
			QMessageBox.information(self.interface, 'Information', 'Please choose a geometry group.', QMessageBox.Ok,)
			return
		
		newBC = None
		for BC in self.BCs:
			if BC.name == self.interface.list_makeBC.currentItem().text():
				newBC = BC		  
		
		groups = self.interface.list_makeGroup.selectedItems()
		
		newBC.setGroup(groups)
			
		if self.interface.rb_force.isChecked() == True:
			newBC.setType('force')
		if self.interface.rb_displ.isChecked() == True:
			newBC.setType('displacement')
		if self.interface.rb_press.isChecked() == True:
			newBC.setType('pressure')
			
		newBC.setDoFs(self.interface.txt_dofX.text(), self.interface.txt_dofY.text(), self.interface.txt_dofZ.text())
		newBC.setPressure(self.interface.txt_press.text())
			
		if newBC.BCtype == 'force' or newBC.BCtype == 'displacement':
			if newBC.DoF_x == None and newBC.DoF_y == None and newBC.DoF_z == None:
				QMessageBox.information(self.interface, 'Information', 'Please enter at least one DoF.', QMessageBox.Ok,)
				return
		elif newBC.BCtype == 'pressure' and newBC.pressureValue == None:
			QMessageBox.information(self.interface, 'Information', 'Please enter a pressure value.', QMessageBox.Ok,)
			return	  
			
	def displayBC(self):
		for i in range(self.interface.list_makeGroup.count()):
			item = self.interface.list_makeGroup.item(i)
			item.setSelected(False)
			
		if self.interface.list_makeBC.currentItem() == None:
			return
		
		BC = None
		for bc in self.BCs:
			if bc.name == self.interface.list_makeBC.currentItem().text():
				BC = bc
		if BC == None:
			return
		
		txtBoxes = [self.interface.txt_press, self.interface.txt_dofX, self.interface.txt_dofY, self.interface.txt_dofZ]
		for i in range(0,4):
			txtBoxes[i].setText('')
		
		if BC.BCtype == 'force':
			self.interface.rb_force.setChecked(True)
		elif BC.BCtype == 'displacement':
			self.interface.rb_displ.setChecked(True)
		elif BC.BCtype == 'pressure':
			self.interface.rb_press.setChecked(True)
		
		BCcontents = [BC.pressureValue, BC.DoF_x, BC.DoF_y, BC.DoF_z]
		for i in range(0,4):
			if BCcontents[i] != None:
				txtBoxes[i].setText(str(BCcontents[i]))
		
		if BC.groupNames == None:
			return
		
		for i in range(self.interface.list_makeGroup.count()):
			item = self.interface.list_makeGroup.item(i)
			for gp in BC.groupNames:
				if item.text() == gp:
					item.setSelected(True)
					break
	
	def openMesh(self):
		file = QFileDialog.getOpenFileName(self.interface, 'Open mesh', self.filesDic['workingDir'])
		if file[0] == '':
			return
		
		fullFileName = file[0].replace('/', os.sep)
		fullFileName = fullFileName.replace('\\', os.sep)
		self.filesDic.update({'meshFile' : fullFileName})
		
		self.interface.label_mesh.setText(fullFileName)
		
	def useCustomTemplate(self):
		file = QFileDialog.getOpenFileName(self.interface, 'Choose .comm file template', self.filesDic['workingDir'])
		if file[0] == '':
			return
		
		fullFileName = file[0].replace('/', os.sep)
		fullFileName = fullFileName.replace('\\', os.sep)
		self.filesDic.update({'commTemplate' : fullFileName})
		
		self.interface.label_commFile.setText(fullFileName)
		
	def defAsRunPath(self):			   
		file = QFileDialog.getOpenFileName(self.interface, "Browse 'as_run' file", self.filesDic['workingDir'])
		if file[0] == '':
			reply = QMessageBox.question(self.interface, 'Define "as_run" path', 'Set "as_run" path to "as_run" ?', QMessageBox.Yes, QMessageBox.No)
			if reply == QMessageBox.Yes:
				fullFileName = 'as_run'
			else:
				return
		else:
			fullFileName = file[0].replace('/',os.sep)
			fullFileName = fullFileName.replace('\\', os.sep)

		self.filesDic.update({'asRun' : fullFileName})
		self.interface.label_asRun.setText(fullFileName)
	
	def writeExport(self):
		try:
			if self.filesDic['meshFile'] == '':
				QMessageBox.information(self.interface, 'Information', 'No mesh loaded.', QMessageBox.Ok)
				return 0
		except:
			QMessageBox.information(self.interface, 'Information', 'No mesh loaded.', QMessageBox.Ok)
			return 0
		
		self.saveCurrentInputParams()
		
		try:
			filepath=os.path.join(self.filesDic['workingDir'] , self.parametersDic['jobName']+ '.export')
			print("Opening "+filepath)
			fileExport = open(filepath, 'w')
		except:
			QMessageBox.information(self.interface, 'Information', 'Unable to open one of the export files.', QMessageBox.Ok,)
			return 0
		try:
			substDic = {'#[memjob]': 'P memjob ' + str(self.parametersDic['memoryLimit']*1024), '#[tpsjob]': 'P tpsjob ' + str(self.parametersDic['timeLimit']), '#[tpmax]': 'P tpmax ' + str(self.parametersDic['timeLimit']), '#[commFile]': 'F comm ' + self.filesDic['workingDir'] + self.parametersDic['jobName'] + '.comm D 1'}	
			substDic.update({'#[meshFile]' : 'F mmed ' + self.filesDic['meshFile'] + ' D 20'})
			substDic.update({'#[messFile]' : 'F mess ' + self.filesDic['workingDir'] + self.parametersDic['jobName'] + '.mess R 6'})
			substDic.update({'#[resultFile]' : 'F rmed ' + self.filesDic['workingDir'] + self.parametersDic['jobName'] + '.res.med R 80'})
			myDir = self.filesDic['workingDir'] + self.parametersDic['jobName']
			substDic.update({'#[meshOptFile]' : 'F unv ' + myDir + '_mat1_meshOpt.unv R 30' + '\nF unv ' + myDir + '_mat2_meshOpt.unv R 31'})
			substDic.update({'#[memory_limit]' : 'P memory_limit ' + str(self.parametersDic['memoryLimit'])})
			substDic.update({'#[ncpus]' : 'P ncpus ' + str(self.parametersDic['nbCpu'])})
			substDic.update({'#[nomJob]' : 'P nomjob ' + self.parametersDic['jobName']})
			substDic.update({'#[time_limit]' : 'P time_limit ' + str(self.parametersDic['timeLimit'])})
			substDic.update({'#[version]' : 'P version ' + self.parametersDic['version']})
		except:
			QMessageBox.information(self.interface, 'Information', 'Some informations are missing to write the export file.', QMessageBox.Ok)
			return 0
		
		fileContent = Utils.substitute(self.filesDic['exportTemplate'], substDic, self.interface)
		
		fileExport.write(fileContent)
		fileExport.close()
#		 fileExportTemplate.close()
		
		return 1
	
	def WriteBoundaryCondition(self, p_BC):
		if p_BC == None:
			QMessageBox.information(self.interface, 'Information', 'Error, no BC chosen.', QMessageBox.Ok,)
			return 0
		
		fileContent = p_BC.name + " = AFFE_CHAR_MECA(MODELE=MODE, "
		BCletter = (p_BC.BCtype == 'displacement')*'D' + (p_BC.BCtype == 'force')*'F'
		BCtype = (p_BC.BCtype == 'displacement')*'DDL_IMPO' + (p_BC.BCtype == 'force')*'FORCE_FACE'
		txtGroups = ''
		if p_BC.groupNames != None and len(p_BC.groupNames) != 0:
			for gp in p_BC.groupNames:
				txtGroups += "'" + gp + "', "
		
		if p_BC.BCtype == 'displacement' or p_BC.BCtype == 'force':
			fileContent += BCtype + "=_F(GROUP_MA=(" + txtGroups + "), "
			if p_BC.DoF_x != None:
				fileContent += BCletter + 'X=' + str(p_BC.DoF_x) + ', '
			if p_BC.DoF_y != None:
				fileContent += BCletter + 'Y=' + str(p_BC.DoF_y) + ', '
			if p_BC.DoF_z != None:
				fileContent += BCletter + 'Z=' + str(p_BC.DoF_z)
		elif p_BC.BCtype == 'pressure':
			if p_BC.pressureValue == None:
				QMessageBox.information(self.interface, 'Information', 'Error : cannot write a pressure BC without a pressure value.', QMessageBox.Ok,)
				return 0
			fileContent += "PRES_REP = _F(GROUP_MA=(" + txtGroups + "), PRES=" + str(p_BC.pressureValue)
		
		fileContent += '));\n'
				
		return fileContent
	
	def WriteFunctions(self, p_nLoadCases):
		txt = ''
		
		abcisse = '('
		for i in range(0, p_nLoadCases + 1):
			abcisse += str(i) + ', '
		abcisse += ')'
			
		for i in range(1, p_nLoadCases + 1):
			
			ordonnee = '('
			for j in range(0, p_nLoadCases + 1):
				if j == i:
					ordonnee += '1, '
				else:
					ordonnee += '0, '
			ordonnee += ')'
				
			txt += 'FM' + str(i) + " = DEFI_FONCTION ( NOM_PARA = 'INST', ABSCISSE = " + abcisse + ", ORDONNEE = " + ordonnee + ", PROL_DROITE = 'CONSTANT', PROL_GAUCHE = 'CONSTANT',)\n"
		return txt
	
	def writeCommandFile(self):	  
		if	len(self.BCs) == 0:
			QMessageBox.information(self.interface, 'Information', 'You must define boundary conditions first.', QMessageBox.Ok,)
			return 0
		
		self.saveCurrentInputParams()
		
		try:
#			 fileCommTemplate = open(self.commTemplate, 'r')
			fileComm = open(os.path.join(self.filesDic['workingDir'] , self.parametersDic['jobName'] + '.comm'), 'w')
		except:
			QMessageBox.information(self.interface, 'Information', 'Unable to open command file.', QMessageBox.Ok,)
			return 0
		
		if len(self.loadCases) == 0:
			self.useDefaultLCs()
			
		self.updateListBC()			   
			
		txtModiMail = "MAIL=MODI_MAILLAGE(reuse =MAIL,MAILLAGE=MAIL,ORIE_PEAU_3D=_F(GROUP_MA=("
		writeModiMail = False
		for LC in self.loadCases:
			for BC in LC.BCs:
				if BC.BCtype == 'pressure':
					writeModiMail = True
					for gp in BC.groupNames:
						txtModiMail += "'" + gp + "', "
		
		if writeModiMail == True:
			txtModiMail += "),),);\n"
		else:
			txtModiMail = ''
		
		
		txtModele = "MODE=AFFE_MODELE(MAILLAGE=MAIL, AFFE=_F(TOUT='OUI', PHENOMENE='MECANIQUE', MODELISATION='3D',)," + (self.parametersDic['nbCpu'] > 1)*("DISTRIBUTION=_F(METHODE='SOUS_DOMAINE', PARTITIONNEUR='SCOTCH',NB_SOUS_DOMAINE=" + str(self.parametersDic['nbCpu']) + "),") + ");\n"
		
		txtBCs = ''
		for BC in self.BCs:
			temp = self.WriteBoundaryCondition(BC)
			if temp == 0:
				return 0
			txtBCs += temp
		
		txtTimes = 'times = DEFI_LIST_REEL( VALE = ('
		for i in range(1, len(self.loadCases) + 1):
			txtTimes += str(i) + ', '
		txtTimes += '));\n'

		txtFonctions = self.WriteFunctions(len(self.loadCases))
		
		txtBCNDS = txtLOADCASES = txtFMS = ''
		i = 1
		for BC in self.BCs:
			if BC.BCtype == 'displacement':
				txtBCNDS += BC.name + ', '
		for LC in self.loadCases:
			txtFMS += 'FM' + str(i) + ', '
			i += 1
			txtLOADCASES += '['
			for BC in LC.BCs:
				txtLOADCASES +=	 BC.name + ', '
			txtLOADCASES += '], '
		txtBCloadsArr = 'BCNDS = [' + txtBCNDS + ']\nLOADCASES = [' + txtLOADCASES + ']\nFMS = [' + txtFMS + ']\n'

		txtOptiGroups = "groupOpt=(" + self.parametersDic['optiGroups'] + ");\ngroupFrozen=(" + self.parametersDic['frozenGroups'] + ");";
		
		if self.parametersDic['solverIndex'] == 0:
			txtSolver = "SOLVOPT={'METHODE':'MUMPS','ELIM_LAGR':'NON'}\n"
		elif self.parametersDic['solverIndex'] == 1:
			txtSolver = "SOLVOPT={'METHODE':'GCPC', 'PRE_COND':'LDLT_INC','NIVE_REMPLISSAGE':1}\n"
		elif self.parametersDic['solverIndex'] == 2:
			txtSolver = "SOLVOPT={'ELIM_LAGR':'LAGR2','LOW_RANK_SEUIL':'1e-09','MATR_DISTRIBUEE':'OUI','METHODE':'MUMPS','RENUM':'SCOTCH'}\n"
		elif self.parametersDic['solverIndex'] == 3:
			txtSolver = "SOLVOPT={'METHODE':'PETSC','PRE_COND':'LDLT_SP', 'MATR_DISTRIBUEE':'OUI'}\n"
		elif self.parametersDic['solverIndex'] == 4:
			txtSolver = "SOLVOPT={'METHODE':'PETSC','PRE_COND':'BOOMER','MATR_DISTRIBUEE':'OUI'}\n"
			
		substDic = {'#[modimaillage]' : txtModiMail, '#[modele]' : txtModele , '#[BCs]' : txtBCs , '#[times]' : txtTimes, '#[fonctions]' : txtFonctions, '#[BCloadsArrays]' : txtBCloadsArr, '#[optimizationGroups]' : txtOptiGroups, '#[solver]' : txtSolver }
		paramsKeys = ['Eini', 'Smax', 'SEDtargetMax', 'nIter', 'targetVF', 'targetDispl', 'densityPenaltyExponent', 'precision', 'adaptRate', 'Emin', 'eta1', 'eta2', 'saveInterval','bimat', 'convCrit', 'boolVolTarget']

		for key in paramsKeys:
			try:
				lineEnd = '\n'
#				 eval("substDic.update({'#[" + key + "]' : '" + key + " = ' + self.interface.txt_" + key + ".text() + lineEnd})")
				eval("substDic.update({'#[" + key + "]' : '" + key + " = ' + str(self.parametersDic['" + key + "']) + lineEnd})")
			except:
				pass
		
 
		fileContent = Utils.substitute(self.filesDic['commTemplate'], substDic, self.interface)
		if fileContent == 0:
			return 0
		fileComm.write(fileContent)
		fileComm.close()
		
		return 1
			
	def delBC(self):		
		listItems = self.interface.list_makeBC.selectedItems()
		if not listItems: return		
		for item in listItems:
			self.interface.list_makeBC.takeItem(self.interface.list_makeBC.row(item))
			i = 0
			while i < len(self.BCs):
				bcToRemove = self.BCs[i]
				if bcToRemove.name == item.text():
					
					self.BCs.remove(bcToRemove)					   
					iLC = 0
					
					while iLC < len(self.loadCases):
						LC = self.loadCases[iLC]
						try:
							LC.BCs.remove(bcToRemove)
							if len(LC.BCs) == 0:
								self.loadCases.remove(LC)
								iLC -= 1
						except:
							pass
						iLC += 1
						
					break
				i += 1
		
	def delGroup(self):
		listItems = self.interface.list_makeGroup.selectedItems()		 
		if not listItems: return		
		for item in listItems:
			self.interface.list_makeGroup.takeItem(self.interface.list_makeGroup.row(item))
			self.groups.remove(item.text())
			for BC in self.BCs:
				if BC.groupNames == None:
					continue
				for gp in BC.groupNames:
					if gp == item.text():
						BC.groupNames.remove(gp)
	
	def BCtypeChanged(self):
		self.interface.txt_press.setDisabled(not self.interface.rb_press.isChecked())
		self.interface.txt_dofX.setDisabled(self.interface.rb_press.isChecked())
		self.interface.txt_dofY.setDisabled(self.interface.rb_press.isChecked())
		self.interface.txt_dofZ.setDisabled(self.interface.rb_press.isChecked())
		self.interface.txt_press.setText('')
		self.interface.txt_dofX.setText('')
		self.interface.txt_dofY.setText('')
		self.interface.txt_dofZ.setText('')
		
	def updateListBC(self):		   
		
		self.interface.list_BC.clear()
		
		for BC in self.BCs:
			item = QListWidgetItem(BC.name)
			if BC.BCtype == 'displacement':
				item.setFlags(Qt.NoItemFlags)
			self.interface.list_BC.addItem(item)
			
	def updateListLC(self):		   
		
		self.interface.list_LC.clear()
		
		Utils.fillListView(self.loadCases, self.interface.list_LC)
			
	def createLC(self):
		BCsToAdd = []
		
		if len(self.interface.list_BC.selectedItems()) == 0:
			return
		
		for itemBC in self.interface.list_BC.selectedItems():
			for BC in self.BCs:
				if itemBC.text() == BC.name:
					BCsToAdd.append(BC)
					break
		
		prevNo = 0
		if self.loadCases != None:
			for LC in self.loadCases:
				prevNo = max(prevNo, LC.number)
		
		loadCase = LoadCase(prevNo + 1, BCsToAdd)
		self.loadCases.append(loadCase)
#		 
#		 item = QListWidgetItem('Load case ' + str(loadCase.number))
#		 self.interface.list_LC.addItem(item)
#		 
		Utils.fillListView([loadCase], self.interface.list_LC)
	
	def highlightBCs(self):
		for i in range(self.interface.list_BC.count()):
			item = self.interface.list_BC.item(i)
			item.setSelected(False)
		
		item = self.interface.list_LC.currentItem()
		try:
			text = item.text()
		except:
			return
		LCnumber = int(text.split(' ')[2])

		for LC in self.loadCases:
			if LC.number == LCnumber:
				# the load case clicked is LC
				for BC in LC.BCs:
					# consider BC, one of our LC's BCs
					for i in range(self.interface.list_BC.count()):
						# loop on list_BC
						item = self.interface.list_BC.item(i)
						if item.text() == BC.name:
							item.setSelected(True)
							break					 
				return
	
	def deleteLCs(self):
		self.interface.list_LC.clear()
		self.loadCases = []
	
	def useDefaultLCs(self):
		self.deleteLCs()
		self.updateListBC()
		iItem = 0
		iLC = 0
		while iItem < self.interface.list_BC.count():
			item = self.interface.list_BC.item(iItem)
			
			for BC in self.BCs:
				if item.text() == BC.name:
					iItem += 1
					if BC.BCtype == 'displacement':
						continue
					LC = LoadCase(iLC+1, [BC])
					self.loadCases.append(LC)
					Utils.fillListView([LC], self.interface.list_LC)
					iLC += 1
					
					break

		
	def saveCurrentInputParams(self):
		
#		 try:
			self.parametersDic.update({'jobName' : self.interface.txt_nomjob.text()})
			self.parametersDic.update({'memoryLimit' : int(self.interface.txt_memory_limit.text())})
			self.parametersDic.update({'nbCpu' : int(self.interface.txt_mpi_nbcpu.text())})
			self.parametersDic.update({'solverIndex' : self.interface.cb_solver.currentIndex()})
			self.parametersDic.update({'timeLimit' : float(self.interface.txt_time_limit.text())})
			self.parametersDic.update({'version' : self.interface.txt_version.text()})
			self.parametersDic.update({'saveInterval' : int(self.interface.txt_saveInterval.text())})
			self.parametersDic.update({'optiGroups' : self.interface.txt_optiGroup.text()})

			txt = self.interface.txt_frozenGroup.text()
			if txt != '' and txt[-1] != ',':
				txt = txt + ','			   
			self.parametersDic.update({'frozenGroups' : txt})
			
			self.parametersDic.update({'Eini' : float(self.interface.txt_Eini.text())})
			self.parametersDic.update({'Smax' : float(self.interface.txt_Smax.text())})
			self.parametersDic.update({'SEDtargetMax' : float(self.interface.txt_SEDtargetMax.text())})
			self.parametersDic.update({'useDefValSED' : self.interface.checkBox_SED.isChecked()})
			self.parametersDic.update({'nIter' : int(self.interface.txt_nIter.text())})
			self.parametersDic.update({'targetVF' : float(self.interface.txt_targetVF.text())})
			self.parametersDic.update({'targetDispl' : float(self.interface.txt_targetDispl.text())})
			self.parametersDic.update({'densityPenaltyExponent' : float(self.interface.txt_p.text())})
			self.parametersDic.update({'precision' : float(self.interface.txt_precision.text())})
			self.parametersDic.update({'Emin' : float(self.interface.txt_Emin.text())})
			self.parametersDic.update({'useDefValEmin' : self.interface.checkBox_Emin.isChecked()})
			self.parametersDic.update({'eta1' : float(self.interface.txt_eta1.text())})
			self.parametersDic.update({'eta2' : float(self.interface.txt_eta2.text())})
			self.parametersDic.update({'bimat' : bool(self.interface.checkBox_bimat.isChecked())})
			self.parametersDic.update({'boolVolTarget' : bool(self.interface.rb_targetVF.isChecked())})
			self.parametersDic.update({'convCrit' : float(self.interface.txt_convCrit.text())})
#		 except:
#			 QMessageBox.information(self.interface, 'Error', 'Problem reading input parameters. Please verify variables types.', QMessageBox.Ok,)
#			 return 0	  
#	 
#		 return 1
	
	def displayCase(self):
		try: self.interface.label_wdir.setText(str(self.filesDic['workingDir']))
		except: self.interface.label_wdir.setText('')
		try: self.interface.label_mesh.setText(str(self.filesDic['meshFile']))
		except: self.interface.label_mesh.setText('No mesh loaded...')
		try: self.interface.label_commFile.setText(str(self.filesDic['commTemplate']))
		except: self.interface.label_commFile.setText('')
		try: self.interface.label_asRun.setText(str(self.filesDic['asRun']))
		except: self.interface.label_asRun.setText('')
		try: self.interface.setWindowTitle('Topological optimization - ' + self.filesDic['topoOptFileName'].split(os.sep)[-1])
		except: self.interface.setWindowTitle('Topological optimization - *unsaved')
		
		try: self.interface.txt_nomjob.setText(str(self.parametersDic['jobName']))
		except: pass
		try: self.interface.txt_memory_limit.setText(str(self.parametersDic['memoryLimit']))
		except: pass
		try: self.interface.txt_mpi_nbcpu.setText(str(self.parametersDic['nbCpu']))
		except: pass
		try: self.interface.cb_solver.setCurrentIndex(self.parametersDic['solverIndex'])
		except: pass
		try: self.interface.txt_time_limit.setText(str(self.parametersDic['timeLimit']))
		except: pass
		try: self.interface.txt_version.setText(str(self.parametersDic['version']))
		except: pass
		try: self.interface.txt_saveInterval.setText(str(self.parametersDic['saveInterval']))
		except: pass
		
		try: self.interface.txt_optiGroup.setText(str(self.parametersDic['optiGroups']))
		except: pass
		try: self.interface.txt_frozenGroup.setText(str(self.parametersDic['frozenGroups']))
		except: pass
		try: self.interface.txt_Eini.setText(str(self.parametersDic['Eini']))
		except: pass
		try: self.interface.txt_Smax.setText(str(self.parametersDic['Smax']))
		except: pass
		try: self.interface.checkBox_SED.setChecked(self.parametersDic['useDefValSED'])
		except: pass
		try: self.interface.txt_SEDtargetMax.setText(str(self.parametersDic['SEDtargetMax']))
		except: pass
		try: self.interface.txt_nIter.setText(str(self.parametersDic['nIter']))
		except: pass
		try: self.interface.txt_targetVF.setText(str(self.parametersDic['targetVF']))
		except: pass
		try: self.interface.txt_targetDispl.setText(str(self.parametersDic['targetDispl']))
		except: pass
		try: self.interface.txt_p.setText(str(self.parametersDic['densityPenaltyExponent']))
		except: pass
		try: self.interface.txt_precision.setText(str(self.parametersDic['precision']))
		except: pass
		try: self.interface.checkBox_Emin.setChecked(self.parametersDic['useDefValEmin'])
		except: pass
		try: self.interface.txt_Emin.setText(str(self.parametersDic['Emin']))
		except: pass
		try: self.interface.txt_eta1.setText(str(self.parametersDic['eta1']))
		except: pass
		try: self.interface.txt_eta2.setText(str(self.parametersDic['eta2']))
		except: pass
		try: self.interface.checkBox_bimat.setChecked(bool(self.parametersDic['bimat']))
		except: pass
		try: self.interface.rb_targetVF.setChecked(bool(self.parametersDic['boolVolTarget']))
		except: pass
		try: self.interface.rb_targetDispl.setChecked(not bool(self.parametersDic['boolVolTarget']))
		except: pass
		try: self.interface.txt_convCrit.setText(str(self.parametersDic['convCrit']))
		except: pass

		
		self.interface.list_makeBC.clear()
		self.interface.list_makeGroup.clear()
		self.interface.list_BC.clear()
		self.interface.list_LC.clear()

		Utils.fillListView(self.BCs, self.interface.list_makeBC)
		Utils.fillListView(self.groups, self.interface.list_makeGroup)
		Utils.fillListView(self.BCs, self.interface.list_BC)
		Utils.fillListView(self.loadCases, self.interface.list_LC)

	def getConvergenceData(self):
		try:
			messFile = open(self.filesDic['workingDir'] + self.parametersDic['jobName'] + '.mess', 'r')
		except:
			QMessageBox.information(self.interface, 'Information', 'Unable to open ' + self.filesDic['workingDir'] + self.parametersDic['jobName'] + '.mess' + ' to get convergence data.', QMessageBox.Ok,)
			return 0

		try:
			resFile = open(self.filesDic['workingDir'] + self.parametersDic['jobName'] + '_convData.txt', 'w')
		except:
			QMessageBox.information('Problem wrinting file with convergence data.', QMessageBox.Ok,)
			return 0

		
		resDict = {'SED' : [], 'vol' : [], 'dpl' : [], 'node' : []}
		pattern = r"Current ... "
		
		for line in messFile:
			if re.match(pattern, line):
				try:
					number = float(line.split(' ')[2])
				except:
					continue
				
				key = line.split(' ')[1]
				resDict[key].append(number)
				
				if key == 'dpl': resDict['node'].append(line.split(' ')[5])
				
		txt = 'Iter SED_target Volume Max_displacement Node_maxD\n'		   
		for i in range(len(resDict['SED'])):
			line = str(i+1) + ' '
			for key in resDict:
				line += str(resDict[key][i]) + ' '
			txt += line + '\n'
			

		resFile.write(txt)
		resFile.close()
		messFile.close()

		
# /opt/SalomeMeca/appli_V2019_univ/salome -t /home/cae/.config/salome/Plugins/meshsmooth.py args:/home/cae/Documents/Nardin/topoOpt/Oberalp/boot_bimat/smooth_meshOpt.unv
	def execMeshSmooth(self, p_mat):
		runSalome = '/opt/SalomeMeca/appli_V2019_univ/salome'
		progDir=os.path.dirname(os.path.realpath(__file__))
		if progDir[-1] != os.sep: progDir = progDir + os.sep
		cmd=' -t ' + progDir + 'meshsmooth.py args:' + self.filesDic['workingDir'] + self.parametersDic['jobName'] + '_' + p_mat + '_meshOpt.unv'
		
		try:
			#QMessageBox.information(self.interface,'information','Going to execute\n\n' + runSalome + cmd,QMessageBox.Ok)
			result = os.system(runSalome + cmd) # premier essai
			if result != 0: # A. ca ne plante pas mais le code d'erreur est != 0
				file = QFileDialog.getOpenFileName(self.interface, "Please browse 'run_salome' file to execute the mesh smoothing operation" + self.parametersDic['bimat']*('for ' + p_mat) + "...", self.fileDic['workingDir']) # l'utilisateur recherche le bon fichier run_salome
				if file[0] == '':
					return [1, result] # l'utilisateur n'a pas choisi de fichier, on sort.
				runSalome = file[0].replace('/',os.sep)
				runSalome = runSalome.replace('\\', os.sep)
				try:
					result = os.system(runSalome + cmd) # l'utilisateur a choisi un fichier. On relance avec celui-là.
				except:
					return [2, result] # si ca ne marche toujours pas, on sort.

		except: # B. ca plante
			file = QFileDialog.getOpenFileName(self.interface, "Please browse 'run_salome' file to execute the mesh smoothing operation" + self.parametersDic['bimat']*('for ' + p_mat) + "...", self.filesDic['workingDir']) # l'utilisateur recherche le bon fichier run_salome
			if file[0] == '':
				return [3, result] # l'utilisateur n'a pas choisi de fichier, on sort.
			runSalome = file[0].replace('/',os.sep)
			runSalome = runSalome.replace('\\', os.sep)
			try:
				result = os.system(runSalome + cmd) # l'utilisateur a choisi un fichier. On relance avec celui-là.
			except:
				return [4, result] # si ca ne marche toujours pas, on sort.

		return [0, result]
	
class Utils:
	@staticmethod
	def substitute(p_templateFilePath, p_dic, p_interface):
		
		try:
			fileTemplate = open(p_templateFilePath, 'r')
		except:
			QMessageBox.information(p_interface, 'Information', 'Unable to open ' + p_templateFilePath, QMessageBox.Ok,)
			return 0
		
		fileContent = ''
		for line in fileTemplate:
			keyFound = False
			for key in p_dic.keys():
				if key == line.split('\n')[0]:
					keyFound = True
					fileContent += p_dic[key] + '\n'
					break
			if keyFound == False:
				fileContent += line
		fileTemplate.close()
		
		return fileContent

	@staticmethod
	def fillListView(p_list, p_listView):
		for element in p_list:
			myItem = QListWidgetItem('noObject')
			if isinstance(element, str):
				myItem = QListWidgetItem(element)
			elif isinstance(element, BoundaryCondition):
				myItem = QListWidgetItem(element.name)
			elif isinstance(element, LoadCase):
				myItem = QListWidgetItem('Load case ' + str(element.number)) 
			p_listView.addItem(myItem)




# 2 sortes d'equivalences aux "tags" du C#

#comboModel=self.interface.cb_BCs.model()
#
#BC1 = BoundaryCondition('bc1')
#myItem1 = QStandardItem(BC1.name)
#comboModel.appendRow(myItem1)
#self.interface.cb_BCs.setItemData(0,BC1)
#myBC1 = self.interface.cb_BCs.itemData(0)
#
#BC2 = BoundaryCondition('bc2')
#myItem2 = QStandardItem(BC2.name)
#comboModel.appendRow(myItem2)
#self.interface.cb_BCs.setItemData(1,BC2)
#myBC2 = self.interface.cb_BCs.itemData(1)

#		 marche mais n'affiche pas le texte dans la listview ...
#		 item = QListWidgetItem()
#		 item.setText( 'description') # set description
#		 item.setData( 0, BC )
#		 self.interface.list_BC.addItem(item)
