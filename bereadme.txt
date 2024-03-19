
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

