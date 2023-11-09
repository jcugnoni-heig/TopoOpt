import salome_pluginsmanager


def topoOptGUI(context): 
    import interface
    widget = interface.topoOptApp()
    widget.show()

salome_pluginsmanager.AddFunction('topoOptGUI','topology optimization app',topoOptGUI)
