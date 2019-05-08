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

If you want to push a specific commit sha into the coverity website simply put in the commit sha into the HASH section.

The coverity_script.ini has all the streams to do analysis on and you need to put your login information in the INFO section.

```
[DEFAULT]
fabian_gui_hfo_release = True
fabian_gui_evo_release = True
fabian_alarm_pic_v4 = True
fabian_alarm_pic_v5 = True
fabian_blender_pic = True
fabian_controller_pic_evo_2520 = True
fabian_controller_pic_hfo_2520 = True
fabian_controller_pic_evo_26k80 = True
fabian_controller_pic_hfo_46k80 = True
fabian_hfo_pic = True
fabian_monitor_pic = True
fabian_power_pic_hfo_hw1 = True
fabian_power_pic_hfo_hw2 = True
fabian_power_pic_hfo_hw3 = True
fabian_power_pic_evo_hw1 = True
fabian_power_pic_evo_hw2 = True
fabian_power_pic_evo_hw3 = True
fabian_alarm_pic_bootloader = True
fabian_controller_pic_bootloader_pre_ed4 = True
fabian_controller_pic_bootloader_hfo_ed4 = True
fabian_controller_pic_bootloader_evo_ed4 = True
fabian_monitor_pic_bootloader = True
fabian_hfo_pic_bootloader = True
```

```
[HASH]
fabian_gui = None
fabian_alarm = None
fabian_blender = None
fabian_controller = None
fabian_hfo = None
fabian_monitor = None
fabian_power_hfo = None
fabian_power_evo = None
fabian_alarm_bootloader = None
fabian_controller_bootloader = None
fabian_monitor_bootloader = None
fabian_hfo_bootloader = None
```

```
[INFO]
username = firstname.lastname
password = password
```

Once the ini file has been configured simply run the following in a command line interface.

```
python main.py
```

## Output
* Once the program has run to completion check the coverity_analysis.log file to see if any warnings has arisen. If there are no WARNINGS then the program was able to run successfully. (NOTE: warnings will arise if not all repositories are cloned, in which case look at the warnings and make sure they correspond with the streams you decided not to clone in the .ini file.)

## Important Notes:
* Beware of git conflicts or backend processes running while running the script. This can cause the script to not run properly.
* PLEASE READ the coverity_analysis.log to find any problems or warnings during the process
