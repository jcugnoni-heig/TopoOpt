# TopoOpt
A Code-Aster based tool / Salome-Meca plugin for multi-load case topology optimization

# Installation
To install the code,  place the files in your Salome-Meca plugin directory, which is typically located the /home/yourusername/.config/salome/Plugins. If the Plugins folder does not exist, just create it. For Windows, the same rule applies , put these files for example in c:\users\yourusername\.config\salome\Plugins.

Then edit or create the file "salome_plugins.py" to include the following line of codes:
```
import salome_pluginsmanager
import sys
import os


## topology optimization plugin, HEIG-VD 2019-2021

def topoOptGUI(context): 
    import interface
    widget = interface.topoOptApp()
    widget.show()
    
salome_pluginsmanager.AddFunction('topoOptGUI','topology optimization app',topoOptGUI)


# -----------------------------------------------------------------------------------
#  run a shell session in windows to get a SALOME python console, optional addition
def runSalomeShellSessionWindows(context):
    import os,subprocess
    import salome_version
    version = salome_version.getVersion(full=True)
    kernel_appli_dir = os.environ['KERNEL_ROOT_DIR']
    command = ""
    if os.path.exists("/usr/bin/gnome-terminal"):
      command = 'gnome-terminal -t "SALOME %s - Shell session" -e "%s/salome shell" &'%(version,kernel_appli_dir)
    elif os.path.exists("/usr/bin/konsole"):
      command = 'PATH="/usr/bin:/sbin:/bin" LD_LIBRARY_PATH="" konsole -e "%s/salome shell" &'%(kernel_appli_dir)
    elif os.path.exists("/usr/bin/xterm"):
      command = 'xterm -T "SALOME %s - Shell session" -e "%s/salome shell" &'%(version,kernel_appli_dir)
    else:
      print("Neither xterm nor gnome-terminal nor konsole is installed. Trying Windows cmd.exe...")
      command="start cmd.exe"

    if command is not "":
      try:
        subprocess.check_call(command, shell = True)
      except Exception as e:
        print("Error: ",e)


salome_pluginsmanager.AddFunction('SALOME shell session Windows',
                                  'Execute a SALOME shell session in an external xterm',
                                  runSalomeShellSessionWindows)

```
