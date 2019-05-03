# Coverity Static Analysis Script/s

## Getting Started
These are the instructions to get the Coverity Static Analysis Script up and running.

### Installing Packages
Built using Python 32 bit 3.7.2
Necessary Packages to Install: GitPython
```
python -m pip install GitPython
```

Make sure that Coverity has been installed onto your computer correctly and has the environment variable path added to execute the coverity commands.

Other Packages Used: os, sys, enum, time, logging, configparser, subprocess, 

### Overview
Script Files: main.py
* main.py: runs the complete application

Necessary Files: coverity_script.ini, README.md
* coverity_script.ini: this has all the streams in them with what to push to coverity
* README.md:

## Running Program
Once the coverity_script.ini file has been configured then simply run the following in the command prompt window where the files exist. 

The coverity_script.ini has all the streams to do analysis on and you need to put your login information in the INFO section.

```
[INFO]
username = firstname.lastname
password = caretrees
```

Once the ini file has been configured simply run the following in a command line interface.

```
python main.py
```

## Output
* Once the program has run to completion check the coverity_analysis.log file to see if any warnings has arisen. If there are no WARNINGS then the program was able to run successfully. (NOTE: warnings will arise if not all repositories are cloned, in which case look at the warnings and make sure they correspond with the streams you decided not to clone in the .ini file.)
* Copy/push the fabian-release-packages to your desired location
* Check the fabian-build-logs to see the build process for FabianHFO.exe, FabianEvo.exe, and SetupFabian.exe.

## Important Notes:
* Beware of git conflicts or backend processes running while running the script. This can cause the script to not run properly.
* PLEASE READ the coverity_analysis.log to find any problems or warnings during the process
