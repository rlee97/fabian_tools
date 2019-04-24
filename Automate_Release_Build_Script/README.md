# Automated Release Build Script/s

## Getting Started
These are the instructions to get the Automated Release Build Project up and running.

### Installing Packages
Built using Python 32 bit 3.7.2
Necessary Packages to Install: GitPython, pywinauto, pywin32
```
python -m pip install GitPython
python -m pip install pywinauto==0.6.6
python -m pip install pywin32
```

Other Packages Used: os, sys, enum, fileinput, time, logging, shutil, configparser, ast, subprocess, 

### Overview
Script Files: main.py, icp-automate.py, mim_automate.py, mplabx_ipe_automate.py
* main.py: runs the complete application
* icp_automate.py: automates the ICP for Windows application 
* mim_automate.py: automates the alarm post processing using the application MIM
* mplabx_ipe_automate.py: runs the backend commands from the ipecmd documentation

Necessary Files: automate.ini, build_pm3.cmd, automated_build.log, README.md
* automate.ini: this has all the version numbers to be written into the code
* build_pm3.cmd: this is generated and runs the ipecmd backend commands for MPLABx/IPE
* automated_build.log: this is the logger for the applicaiton
* README.md:

## Running Program
Once the automate.ini file has been configured with the correct version numbers then simply run the following in the command prompt window where the files exist. NOTE: the .ini file must follow the exact format used or it will not run through the program properly. The code only has a specific amount of variables so the string must be exact.
```
python main.py
```

The automate.ini file also contains a section called [HASH]. If you want to have the repository reference a specific commit sha then simply put in the commit sha hash for that specific repository in the following slot and the repository will reflect that hash.

Another section in the automate.ini file is [RESPOSITORY]. If "True" then the repository will be cloned, if "False" then the repository will not be cloned. When you do not clone a specific repository, know that warnings will arise associated with that specific repository.

The last section is [GUI] which can determine if the HFO or EVO or both will be built during the process.

NOTE: in the automate.ini file where there are multiple versions it follows as such:
```
gui_version = [HFO, EVO] example: ["5.1.0.10", "5.1.0.9"]
pic_controller_bootloader_version = [controller, edition 4, evo edition 4] example: ["S.5", "S.6", "S.7"]
pic_alarm_version = ["4.2", latest alarm version] example: ["4.2", "5.2"]
```

If you do not want to change the versions then put None in the place of the version
```
gui_version = [None, None]
pic_controller_bootloader_version = [None, None, None]
pic_alarm_version = [None, None]
```

## Output
* Once the program has run to completion check the automate_build.log file to see if any warnings has arisen. If there are no WARNINGS then the program was able to run successfully. (NOTE: warnings will arise if not all repositories are cloned, in which case look at the warnings and make sure they correspond with the repositories you decided not to clone in the .ini file.)
* Copy/push the fabian-release-packages to your desired location
* Check the fabian-build-logs to see the build process for FabianHFO.exe, FabianEvo.exe, and SetupFabian.exe.

## Sub Script
The mplabx_ipe_automate.py script can be run on it's own to generate the .pm3 and .bin files from the corresponding hex file. The script input arguements are:
* Arguement 1: path to hex file
* Arguement 2: directory location
* Arguement 3: PIC type
* Arguement 4: file name
* Arguement 5: version 

To use it, follow the example:
```
python mplabx_ipe_automate.py C:\directory1\directory2\hex_file.hex C:\directory1\directory2\ PIC18F2520 new_hex_file_name 1.1.1
```

This script will output a build_pm3.cmd file that can now be run on the command line to generate the necessary files.

## Important Notes:
* The computer must not sleep during the execution of this program as it relies on the visual interface of the screen at certain points. Either install caffeine or lengthen the sleep time on your computer.
* Beware of git conflicts or backend processes running while running the script. This can cause the script to not run properly.
* Script typically takes around 16 minutes to completion
* PLEASE READ the automated_build.log to find any problems or warnings during the process
