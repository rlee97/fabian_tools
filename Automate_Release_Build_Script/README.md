# Automated Release Build Script/s

## Getting Started
These are the instructions to get the Automated Release Build Project up and running.

### Installing Packages
Built using Python 32 bit 3.7.2
Necessary Packages to Install: GitPython, pywinauto
```
python -m pip install GitPython
python -m pip install pywinauto
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

Necessary Directories: Release_Package
* Release_Package: This directory and all of it's contents are the base for the release package. Once this project has run please copy directory "Release_Package" into another location.

## Running Program
Once the automate.ini file has been configured with the correct version numbers then simply run the following in the command prompt window where the files exist. NOTE: the .ini file must follow the exact format used or it will not run through the program properly. The code only has a specific amount of variables so the string must be exact.
```
python main.py
```

The automate.ini file also contains a section called [HASH]. If you want to have the repository reference a specific commit sha then simply put in the commit sha hash for that specific repository in the following slot and the repository will reflect that hash.

### Steps
1: Deletes all directories with fabian in it's name
2: Clones all directories regarding fabian software
3: Updates the file versions if specified
4: Builds all fabian directories
5: Takes hex files and converts them to pj2, pm3, and .bin
6: Moves corresponding files to the appropriate place in the Release_Package directory

## Output
* Once the program has run to completion check the automate_build.log file to see if any warnings has arisen. If there are no WARNINGS then the program was able to run successfully.
* Copy the Release_Package to your desired location

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

## Notes:
* Currently the script needs all version numbers in the .ini to write the version number into the filename. If the .ini contains a version "None"/no version then the output of the filename will be blank
* Beware of git conflicts or backend processes running while running the script. This can cause the script to not run properly.
* Script typically takes around 16 minutes to completion
* PLEASE READ the automated_build.log to find any problems or warnings during the process