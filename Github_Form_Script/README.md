# Pull Request Form Script

## Getting Started
These are the instructions to run the Pull Request Form script

### Installing Packages
Built using Python 32 bit 3.7.2
Necessary Packages to Install: Pandas
```
python -m pip install pandas
```

Other Packages Used: requests, sys, os, configparser, logging, enum, ast

### Overview
Script Files: pull_request_form.py
* pull_request_form.py: runs the complete application

Necessary Files: form.ini, pull_request_form.log, README.md
* form.ini: this has all the commit hashes to be written into the code as well as authentication
* pull_request_form.log: this is the logger for the applicaiton
* README.md:

## Running Program
Once the form.ini file has been configured with the correct commit hashes then simply run the following in the command prompt window where the files exist. NOTE: the .ini file must follow the exact format used or it will not run through the program properly. The code only has a specific amount of variables so the string must be exact. To run the script you need to run the script itself and input your username and password from github to run properly.
```
python pull_request_form.py -u github_username -p github_password
```

You can also bring up the help in the command line by typing any of the following:
```
python pull_request_form.py -h
python pull_request_form.py help
python pull_request_form.py ?
```

In the form.ini file there is a section named [COMMITS]. On the left side is the starting commit and the right side is the ending commit. The program will grab all commits after the starting commit and to the ending commit.

NOTE: here are the form.ini examples
```
fabian_gui = [first_commit, latest_commit] - example: fabian_monitor = ["872ae671e4b33849dc45c41596f485f9bf1bdcc1", "9dd23dad0db0e21ec30ab4e56fd640e66d0f26f0"]
```
To get the full commit click on the following place in the picture below:

![Commit place](/images/commit_place.PNG)

If you do not want the form to be generated simply put None is place of the value like so:
```
fabian_gui = [None, None]
```

## Output
* Once the program has run to completion check the pull_request_form.log and all .csv and .html files associated with the repository