
# Go here
    /Library/Frameworks/Python.framework/Versions/3.11/bin

# Use pyinstaller
# Need to add the other directories to 'paths'
pyinstaller -F --paths=/Users/brianetheridge/Code/power_ranger/power_ranger_plugin/modules  /Users/brianetheridge/Code/power_ranger/power_ranger_plugin/py-power_ranger.pyp


# compileall just looks for the .py modules and compiles them to .pyc in a cache folder
    https://docs.python.org/3/library/compileall.html

    python3 -m compileall /Users/brianetheridge/Code/power_ranger/power_ranger_plugin



Put into front of PATH:		/Library/Frameworks/Python.framework/Versions/3.11/bin

pyinstaller --onefile -F --paths=/Users/brianetheridge/Code/power_ranger/power_ranger_plugin/config:/Users/brianetheridge/Code/power_ranger/power_ranger_plugin/modules:/Users/brianetheridge/Code/power_ranger/power_ranger_plugin/res  /Users/brianetheridge/Code/power_ranger/power_ranger_plugin/py-power_ranger.pyp

The most common tokens:
    $prj: Project file name
    $camera: Current camera name
    $take: Current take name
    $pass: Multi-Pass or object channel name (the defined multi-pass names). Primarily to be used as the directory name.
    $userpass: Multi-Pass or object channel name (the multi-passes renamed via double-click in the Render Settings (opened Multi-Pass tree view). Primarily to be used as a directory name.
    $frame: Current animation frame
    $rs: Current Render Setting name
    $res: Image resolution (e.g., 800*600: 800X600)
    $range: Animation range (e.g., from frame 23 to 76; 23_76)
    $fps: Frame rate