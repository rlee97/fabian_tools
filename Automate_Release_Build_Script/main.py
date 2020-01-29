import os
import git
import sys
from enum import Enum
import fileinput
from time import time
import logging
from shutil import copyfile
import configparser
import ast
from subprocess import check_output, CalledProcessError
from time import sleep
from datetime import datetime

from mplabx_ipe_automate import MPLABxIPE_Automation
from icp_automate import ICP_Automation
from mim_automate import MIM_Automation


# gui_version = ["5.1.0.8", "5.1.0.9"]
# pic_monitor_bootloader_version = "7"
# pic_monitor_version = "5.1.23"
# pic_power_version = "6.1"
# pic_power_evo_version = "6.1"
# pic_controller_bootloader_version = ["S.5", "S.6"]  # Does this have two different versions?
# pic_controller_version = "4.2.09"
# pic_alarm_bootloader_version = "1"
# pic_alarm_version = ["4.2", "5.2"]
# pic_blender_version = "5.6"
# pic_hfo_version = "3.0.2"
# pic_hfo_bootloader_version = "B.4"

# This is a global variable to hold the gui version
# The first place holds the HFO version and the second place holds the EVO version
HFO_INDEX = 0
EVO_INDEX = 1
gui_version = [None, None]
gui_builds = [True, True]

# Configuring the logger this will be used as a global over the whole program
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="automated_build.log", level=logging.DEBUG, format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()


def time_it(func):
    """
    Decorator function to time the input function
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        start = time()
        function_return = func(*args, **kwargs)
        end = time()
        hours, rem = divmod(end-start, 3600)
        minutes, seconds = divmod(rem, 60)
        print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
        return function_return
    return wrapper


# Class needs to contain a different variable or it will garbage collect it and then the variables will not enumerate
class CheckoutHash(Enum):
    fabian_gui_hash = ["temp_holder_1"]
    fabian_monitor_bootloader_hash = ["temp_holder_2"]
    fabian_monitor_hash = ["temp_holder_3"]
    fabian_power_hash = ["temp_holder_4"]
    fabian_power_evo_hash = ["temp_holder_5"]
    fabian_controller_bootloader_hash = ["temp_holder_6"]
    fabian_controller_hash = ["temp_holder_7"]
    fabian_alarm_bootloader_hash = ["temp_holder_8"]
    fabian_alarm_hash = ["temp_holder_9"]
    fabian_blender_hash = ["temp_holder_10"]
    fabian_HFO_hash = ["temp_holder_11"]
    fabian_HFO_bootloader_hash = ["temp_holder_12"]

class NonBuildableCheckoutHash(Enum):
    fabian_release_package_hash = ["temp_holder_1"]


class Repositories(Enum):
    fabian_gui = ["https://github.com/vyaire/fabian-gui.git", "NETDCUA9", None]
    fabian_monitor_bootloader = ["https://github.com/vyaire/fabian-monitor_bootloader.git", "dsPIC33FJ128GP706", "mon-bootloader_"]
    fabian_monitor = ["https://github.com/vyaire/fabian-monitor.git", "dsPIC33FJ128GP706", "mon-pic_"]  # Does not need name but I am naming it mon-pic
    fabian_power = ["https://github.com/vyaire/fabian-power.git", "PIC18F4423", "accu-pic_hfo_"]  # HW1, HW2, HW3
    fabian_power_evo = ["https://github.com/vyaire/fabian-power-evo.git", "PIC18F4423", "accu-pic_evo_"]  # HW1, HW2, HW3
    fabian_controller_bootloader = ["https://github.com/vyaire/fabian-controller_bootloader.git", "PIC18F2520", "PIC18F46K80", "PIC18F26K80", "ctrl-bootloader_"]  # (two projects)
    fabian_controller = ["https://github.com/vyaire/fabian-controller.git", "PIC18F2520", "PIC18F46K80", "PIC18F26K80", "ctrl-pic_"]  # (two projects) Does not need name but I am naming it ctrl-pic
    fabian_alarm_bootloader = ["https://github.com/vyaire/fabian-alarm_bootloader.git", "PIC16F1826", "alarm-bootloader_"]
    fabian_alarm = ["https://github.com/vyaire/fabian-alarm.git", "PIC16F1826", "PIC16F627A", "alarm-pic_"]
    fabian_blender = ["https://github.com/vyaire/fabian-blender.git", "dsPIC33FJ128GP706A", "blender-pic_"]
    fabian_HFO = ["https://github.com/vyaire/fabian-hfo.git", "PIC18F2420", "hfo-pic_"]  # Does not need anme but I am naming it hfo-pic
    fabian_HFO_bootloader = ["https://github.com/vyaire/fabian-hfo_bootloader.git", "PIC18F2420", "hfo-bootloader_"]


class NonBuildableRepositories(Enum):
    fabian_release_package = ["https://github.com/vyaire/fabian-release-packages.git"]


# This is the area where we update the EVO and HFO gui
class FabianGUIFiles(Enum):
    fabianHFOrc = "\\fabian-gui\\FabianHFO\\FabianHFO.rc"
    fabianHFO_MVModel = "\\fabian-gui\\FabianHFO\\MVModel.cpp"
    fabianEVOrc = "\\fabian-gui\\FabianEvo\\Fabian.rc"
    fabianEVO_MVModel = "\\fabian-gui\\FabianEvo\\MVModel.cpp"

# Keep here if no .ini file is to be used
# class FabianPICFiles(Enum):
#     fabian_monitor_bootloader = ["\\fabian-monitor_bootloader\\Neo_mon Bootloader UART.X\\main_debug.c", pic_monitor_bootloader_version]
#     fabian_monitor = ["\\fabian-monitor\\SRC\\common.h", pic_monitor_version]
#     fabian_power = ["\\fabian-power\\Akku_4.C", pic_power_version]
#     fabian_power_evo = ["\\fabian-power-evo\\src\\Akku_5.C", pic_power_evo_version]
#     fabian_controller_bootloader = ["\\fabian-controller_bootloader\\Ctrl_Bootloader.X\\bootldr_neo.c", pic_controller_bootloader_version[0],
#                                     "\\fabian-controller_bootloader\\Ctrl_Bootloader_ed4.X\\bootldr_neo.c", pic_controller_bootloader_version[1]]
#     fabian_controller = ["\\fabian-controller\\src\\Define.h", pic_controller_version]  # Both versions use same file
#     fabian_alarm_bootloader = ["\\fabian-alarm_bootloader\\AlarmPIC_Fabian_UART_loader.X\\common.h", pic_alarm_bootloader_version]
#     fabian_alarm = ["\\fabian-alarm\\AlarmPIC_Fabian_V4.X\\src\\application\\common.h", pic_alarm_version[0],
#                     "\\fabian-alarm\\AlarmPIC_Fabian_V5.X\\src\\application\\common.h", pic_alarm_version[1]]
#     fabian_blender = ["\\fabian-blender\\Blender.X\\Src\\common.h", pic_blender_version]
#     fabian_HFO = ["\\fabian-hfo\\src\\Define.h", pic_hfo_version]
#     fabian_HFO_bootloader = ["\\fabian-hfo_bootloader\\bootldr_HF_Mod.c", pic_hfo_bootloader_version]]


class FabianPICFiles(Enum):
    fabian_monitor_bootloader = ["\\fabian-monitor_bootloader\\Neo_mon Bootloader UART.X\\main_debug.c", None]
    fabian_monitor = ["\\fabian-monitor\\SRC\\common.h", None]
    fabian_power = ["\\fabian-power\\Akku_4.C", None]
    fabian_power_evo = ["\\fabian-power-evo\\src\\Akku_5.C", None]
    fabian_controller_bootloader = ["\\fabian-controller_bootloader\\Ctrl_Bootloader.X\\bootldr_neo.c", None,
                                    "\\fabian-controller_bootloader\\Ctrl_Bootloader_ed4.X\\bootldr_neo.c", None,
                                    "\\fabian-controller_bootloader\\Ctrl_Bootloader_EVO_ed4.X\\bootldr_neo.c", None]
    fabian_controller = ["\\fabian-controller\\src\\Define.h", None]  # Both versions use same file
    fabian_alarm_bootloader = ["\\fabian-alarm_bootloader\\AlarmPIC_Fabian_UART_loader.X\\common.h", None]
    fabian_alarm = ["\\fabian-alarm\\AlarmPIC_Fabian_V4.X\\src\\application\\common.h", None,
                    "\\fabian-alarm\\AlarmPIC_Fabian_V5.X\\src\\application\\common.h", None]
    fabian_blender = ["\\fabian-blender\\Blender.X\\Src\\common.h", None]
    fabian_HFO = ["\\fabian-hfo\\src\\Define.h", None]
    fabian_HFO_bootloader = ["\\fabian-hfo_bootloader\\bootldr_HF_Mod.c", None]


class VersionType(Enum):
    FILEVERSION = "FILEVERSION"
    PRODUCTVERSION = "PRODUCTVERSION"
    ProductVersion = "ProductVersion"
    FileVersion = "FileVersion"
    m_szVersion = "m_szVersion"
    m_szBuildVersion = "m_szBuildVersion"

class ReleaseType(Enum):
    HFO_USB_Package = "\\fabian-release-packages\\113001 fabian HFO\\03 USB package\\SETUP\\"
    HFO_ICP2 = "\\fabian-release-packages\\113001 fabian HFO\\02 PIC package for programmers\\2.1 ICP2\\"
    HFO_PICKit3 = "\\fabian-release-packages\\113001 fabian HFO\\02 PIC package for programmers\\2.2 PICKit3\\"
    HFO_PM3 = "\\fabian-release-packages\\113001 fabian HFO\\02 PIC package for programmers\\2.3 PM3\\"
    HFO_HEX = "\\fabian-release-packages\\113001 fabian HFO\\HEX\\"
    EVO_USB_Package = "\\fabian-release-packages\\122001 fabian EVO\\03 USB package\\SETUP\\"
    EVO_ICP2 = "\\fabian-release-packages\\122001 fabian EVO\\02 PIC package for programmers\\2.1 ICP2\\"
    EVO_PICKit3 = "\\fabian-release-packages\\122001 fabian EVO\\02 PIC package for programmers\\2.2 PICKit3\\"
    EVO_PM3 = "\\fabian-release-packages\\122001 fabian EVO\\02 PIC package for programmers\\2.3 PM3\\"
    EVO_HEX = "\\fabian-release-packages\\122001 fabian EVO\\HEX\\"


class USBPackageHFO(Enum):
    hfo_ffs_disk = ["FFSDISK\\", ""]
    hfo_pic_alarm = ["PIC_ALARM\\", ".alr"]
    hfo_pic_controller = ["PIC_CONTROLLER\\", ".ctl", ".ct5"]
    hfo_pic_hfo = ["PIC_HFO\\", ".hfo"]
    hfo_pic_monitor = ["PIC_MONITOR\\", ".mon"]


class USBPackageEVO(Enum):
    evo_ffs_disk = ["FFSDISK\\", ""]
    evo_pic_alarm = ["PIC_ALARM\\", ".alr"]
    evo_pic_controller = ["PIC_CONTROLLER\\", ".fct", ".fc3"]
    evo_pic_monitor = ["PIC_MONITOR\\", ".fmo"]


class FileEndings(Enum):
    END_HEX_FILE = ".hex"
# We know that the alarm and all the bootloaders do not have a checksum hexmate function run after it so we need to make
# this work for those builds in specific
    END_HEX_FILE_CHECKSUM = "2.hex"


class AutomateBuild:

    def __init__(self):
        self.build_files_path = [[], []]

    @time_it
    def automate(self):
        """
        This will automate the whole process using all the functions from the AutomateBuild class. It will do this by
        iterating through the Repositories class, updating the gui files, and then building the correct repositories
        using the build commands already in the directories
        :return:
        """

        # This will delete all the old repositories and logger file
        logger.info("Deleting Unnecessary Files/Directories")
        self.delete()

        # This will clone all the repositories associated in the Repositories class
        # print("Cloning")
        logger.info("Cloning Repositories")
        for repository, repository_hash in zip(Repositories, CheckoutHash):
            self.clone_repositories(None, repository, repository_hash.value[0])

        logger.info("Cloning Release Package")
        self.clone_repositories(None, NonBuildableRepositories.fabian_release_package, NonBuildableCheckoutHash.fabian_release_package_hash.value[0])

        # print("Updating Files for GUI")
        logger.info("Updating Files for GUI")
        # This will update the gui files with the corresponding version number if it exists
        if((gui_version[HFO_INDEX] != None) or (gui_version[EVO_INDEX] != None)):
            for file in FabianGUIFiles:
                if((file == FabianGUIFiles.fabianHFOrc) or (file == FabianGUIFiles.fabianHFO_MVModel)):  # HFO Updating
                    if(gui_version[HFO_INDEX] != None):
                        if(gui_builds[HFO_INDEX] == True):
                            self.update_file_versions_gui(file.value, gui_version[HFO_INDEX])
                    else:
                        self.check_file_versions_gui(FabianGUIFiles.fabianHFO_MVModel.value)
                else:  # Updating for the EVO
                    if(gui_version[EVO_INDEX] != None):
                        if(gui_builds[EVO_INDEX] == True):
                            self.update_file_versions_gui(file.value, gui_version[EVO_INDEX])
                    else:
                        self.check_file_versions_gui(FabianGUIFiles.fabianEVO_MVModel.value)
        else:
            self.check_file_versions_gui(FabianGUIFiles.fabianHFO_MVModel.value)
            self.check_file_versions_gui(FabianGUIFiles.fabianEVO_MVModel.value)

        # print("Updating Files for PIC")
        logger.info("Updating Files for PIC")
        for file in FabianPICFiles:
            if(file == FabianPICFiles.fabian_controller_bootloader):
                if(file.value[1] != None):
                    self.update_file_versions_pic(file.value[0], file, file.value[1])
                else:
                    self.check_file_versions_pic(file.value[0], file)
                if(file.value[3] != None):
                    self.update_file_versions_pic(file.value[2], file, file.value[3])
                else:
                    self.check_file_versions_pic(file.value[2], file)
                if(file.value[5] != None):
                    self.update_file_versions_pic(file.value[4], file, file.value[5])
                else:
                    self.check_file_versions_pic(file.value[4], file)
            if(file == FabianPICFiles.fabian_alarm):
                if(file.value[1] != None):
                    self.update_file_versions_pic(file.value[0], file, file.value[1])
                else:
                    self.check_file_versions_pic(file.value[0], file)
                if(file.value[3] != None):
                    self.update_file_versions_pic(file.value[2], file, file.value[3])
                else:
                    self.check_file_versions_pic(file.value[2], file)
            else:
                if(file.value[1] != None):
                    self.update_file_versions_pic(file.value[0], file, file.value[1])
                else:
                    self.check_file_versions_pic(file.value[0], file)

        # print("Building Repositories")
        logger.info("Building Repositories")
        for repository in Repositories:
            if(self.build_repositories(repository)):
                logger.info("Built: " + str(repository))
            else:
                logger.warning("Did not build: " + str(repository))

        # This is setting up the alarm post processing
        self.alarm_checksum = None
        self.alarm_filepath = None
        self.alarm_mim_version = None

        # This checks to see if only gui has been enabled
        gui_only_flag = self.check_gui_only()

        if(gui_only_flag == False):
            # print("Converting Files to .pj2 and pm3")
            logger.info("Converting Files to .pj2 and pm3")
            icp = ICP_Automation()
            mplabxipe = MPLABxIPE_Automation()
            for repository in Repositories:
                self.convert_files_pj2_pm3(repository, icp, mplabxipe)
            icp.close_app()
            mplabxipe.close_app()

            if((self.alarm_filepath != None) and (self.alarm_checksum != None) and (self.alarm_mim_version != None)):
                logger.info("Special Alarm post processing")
                mim = MIM_Automation(self.alarm_filepath)
                mim_return_path = mim.convert_files(self.alarm_filepath, self.alarm_checksum, self.alarm_mim_version, logger)
            else:
                mim_return_path = None

            # This appends to the buffer that is used int he convert files function
            if(mim_return_path != None):
                self._convert_files_pj2_pm3_repository([mim_return_path], Repositories.fabian_alarm)
                mim.close_app()
        else:
            find_dir_temp = [os.getcwd() + "\\fabian-gui\\FabianHFO\\NetDCU9 (ARMV4I)\\Release\\FabianHFO.exe"]
            find_dir_temp.append(os.getcwd() + "\\fabian-gui\\FabianEvo\\NetDCU9 (ARMV4I)\\Release\\Fabian.exe")
            find_dir_temp.append(os.getcwd() + "\\fabian-gui\\SetupFabian\\NetDCU9 (ARMV4I)\\Release\\SetupFabian.exe")
            self._convert_files_pj2_pm3_repository(find_dir_temp, Repositories.fabian_gui)

        # print("Moving files into the release package")
        logger.info("Moving files into release package")
        self.release_package_update()

        # print("Complete")
        logger.info("Complete")

    def delete(self):
        """
        This function will try to delete all the repositories in the current working directory where the script has been
        executed from.
        :return:
        """
        all_files = os.listdir()
        for file in all_files:
            if(file.find("fabian") != -1):
                logger.info("Deleting: " + str(file))
                delete_string = "rd " + str(file) + " /s /q"
                del_flag = False
                counter = 0
                while(del_flag == False):
                    counter += 1
                    if(counter >= 10):
                        logger.warning("Could not delete the necessary files/directories")
                        sys.exit()
                    try:
                        check_output(delete_string, shell=True)
                        if(os.path.exists(file)):
                            del_flag = False
                            sleep(1)
                        else:
                            del_flag = True
                    except CalledProcessError as err:
                        if(err.returncode == 32):
                            logger.warning("Cannot access the directories that are being deleted")
                            sys.exit()
                        else:
                            print("Return Code: ", err.returncode)
                            logger.warning("Unknown error")
                            sys.exit()

    def check_gui_only(self):
        output = True
        repos = [repo.value[0] for repo in Repositories]

        for repository in Repositories:
            if(repository == Repositories.fabian_gui):
                if(repository.value[0] == None):
                    output = False
            elif(repository != Repositories.fabian_gui and repository.value[0] in repos):
                if(repository.value[0] != None):
                    output = False
            else:
                logger.warning("This repository has not been accounted for! " + str(repository))

        return output

    def clone_repositories(self, input_your_directory, input_dir, input_hash):
        """
        This function will clone the repositories using the input_cloning_directory
        :param input_your_directory:
        :param input_cloning_directory:
        :return:
        """
        input_cloning_directory = input_dir.value[0]

        cur_dir = None
        if(input_your_directory == None):  # Use current working directory if no directory is specified
            cur_dir = os.getcwd()
        else:
            cur_dir = input_your_directory

        if(os.path.exists(cur_dir)):
            try:
                if(input_cloning_directory != None):
                    git.Git(cur_dir).clone(input_cloning_directory)
                else:
                    logger.info("We are not cloning this directory " + str(input_dir))
            except git.GitCommandError:
                # print("Repository does not exist! Directory: ", input_cloning_directory)
                logger.warning("Repository does not exist! Directory: " + str(input_cloning_directory))

            if(input_hash != None):
                counter = -1
                while(input_cloning_directory[counter] != "/"):
                    counter -= 1
                    if(counter < -100):
                        logger.warning("Could not find the directory correctly for " + str(input_cloning_directory))
                        sys.exit()

                repo_path = cur_dir + "\\" + input_cloning_directory[counter:-4]
                try:
                    repo = git.Repo(repo_path)
                    repo.git.checkout(input_hash)
                    logger.info("Using commit sha " + str(input_hash) + " for " + str(input_cloning_directory))
                except git.GitCommandError:
                    logger.warning("Commit sha does not exist in " + str(input_cloning_directory) + " " + str(input_hash))
        else:
            # print("Input directory path does not exist! Directory: ", cur_dir)
            logger.warning("Input directory path does not exist! Directory: " + str(cur_dir))

    def update_file_versions_gui(self, input_file_path, input_file_version_string):
        """
        This function will update the versions in the gui code.
        :param input_file_path:
        :param input_file_version_string:
        :return:
        """
        cur_dir = os.getcwd()
        cur_dir += input_file_path

        if(os.path.exists(cur_dir)):
            if(cur_dir[-3:] == ".rc"):  # RC files need the input string to be used with commas instead of periods
                version_string = input_file_version_string.replace(".", ",")
            else:
                version_string = input_file_version_string

            skip = 0
            for line in fileinput.input(cur_dir, inplace=True):
                if(skip == 0):
                    if(line.find("MEDKOM_VERSION") != -1):
                        skip = 3

                    index = line.find("FILEVERSION")
                    addition = 12
                    file_type = VersionType.FILEVERSION
                    if(index == -1):
                        index = line.find("PRODUCTVERSION")
                        addition = 15
                        file_type = VersionType.PRODUCTVERSION
                    if(index == -1):
                        index = line.find("ProductVersion")
                        addition = 17
                        file_type = VersionType.ProductVersion
                    if(index == -1):
                        index = line.find("FileVersion")
                        addition = 14
                        file_type = VersionType.FileVersion
                    if(index == -1):
                        index = line.find("m_szVersion = _T(")
                        addition = 17
                        file_type = VersionType.m_szVersion
                    if(index == -1):
                        index = line.find("m_szBuildVersion = _T(")
                        addition = 22
                        file_type = VersionType.m_szBuildVersion
                    if(index != -1):
                        new_line = self._update_file_versions_gui(index, addition, file_type, version_string, line)
                        print("%s" % new_line, end="")
                    else:
                        print("%s" % line, end="")
                else:
                    skip -= 1
                    print("%s" % line, end="")

        else:  # File does not exist
            # print("File does not exist! ", cur_dir)
            logger.warning("File does not exist! " + str(cur_dir))

    def _update_file_versions_gui(self, index, addition, file_type, version_string, line):
        """
        This is the helper function for the update file versions gui function
        :param index:
        :param addition:
        :param file_type:
        :param version_string:
        :param line:
        :return: output_line
        """
        output_line = ""
        if((file_type == VersionType.FILEVERSION) or (file_type == VersionType.PRODUCTVERSION)):
            output_line = line[:index+addition] + version_string + "\n"
        elif((file_type == VersionType.ProductVersion) or (file_type == VersionType.FileVersion)):
            new_version_string = '"' + version_string + '"'
            output_line = line[:index+addition] + new_version_string + "\n"
        elif((file_type == VersionType.m_szVersion)):
            new_version_string = '"' + version_string[:-2] + '"' + ");"
            output_line = line[:index+addition] + new_version_string + "\n"
        elif((file_type == VersionType.m_szBuildVersion)):
            new_version_string = '"' + version_string + '"' + ");"
            output_line = line[:index+addition] + new_version_string + "\n"
        else:
            # print("Type does not exist! ", file_type)
            logger.warning("Type does not exist! " + str(file_type))

        return output_line

    def update_file_versions_pic(self, input_file_path, input_file, input_file_version_string):
        """
        This function will update the file versions on every pic
        :param input_file_path:
        :param input_file:
        :param input_file_version_string:
        :return:
        """
        cur_dir = os.getcwd()
        cur_dir += input_file_path

        if(os.path.exists(cur_dir)):
            # Write to the correct version line
            if(input_file == FabianPICFiles.fabian_monitor_bootloader):
                string_search = ["#define VERSION"]
                cur_versions = ["'" + input_file_version_string + "'"]
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_monitor):
                string_search = ["#define", "Vers_hi", "Vers_mid", "Vers_lo"]
                cur_versions = input_file_version_string.split(".")
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_power):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                cur_versions = input_file_version_string.split(".")
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_power_evo):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                cur_versions = input_file_version_string.split(".")
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_controller_bootloader):
                string_search = ["#define", "Vers_hi", "Vers_lo"]
                cur_versions = input_file_version_string.split(".")
                for i in range(0, len(cur_versions)):
                    cur_versions[i] = "'" + cur_versions[i] + "'"
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_controller):
                string_search = ["#define",  "VERS_0", "VERS_1", "VERS_2", "VERS_3", "VERS_4", "VERS_5"]
                cur_versions = []
                for i in range(0, len(input_file_version_string)):
                    cur_versions.append("'" + input_file_version_string[i] + "'")
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_alarm):
                if("4.X" in cur_dir):
                    string_search = ["#define VERSION_HI", "#define VERSION_HI"]
                    cur_versions = input_file_version_string.split(".")
                    for i in range(0, len(cur_versions)):
                        cur_versions[i] = "'" + cur_versions[i] + "'"
                    self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
                else:
                    string_search = ["#define VERSION"]
                    cur_versions = ['"' + input_file_version_string + '"']
                    self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_alarm_bootloader):
                string_search = ["#define VERSION"]
                cur_versions = ["'" + input_file_version_string + "'"]
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_blender):
                string_search = ["#define VERSION_HI", "#define VERSION_LO"]
                cur_versions = input_file_version_string.split(".")
                for i in range(0, len(cur_versions)):
                    cur_versions[i] = "'" + cur_versions[i] + "'"
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_HFO):
                string_search = ["#define", "Vers_0", "Vers_1", "Vers_2", "Vers_3", "Vers_4"]
                cur_versions = []
                for i in range(0, len(input_file_version_string)):
                    cur_versions.append("'" + input_file_version_string[i] + "'")
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            elif(input_file == FabianPICFiles.fabian_HFO_bootloader):
                string_search = ["#define Vers_hi", "#define Vers_lo"]
                cur_versions = input_file_version_string.split(".")
                for i in range(0, len(cur_versions)):
                    cur_versions[i] = "'" + cur_versions[i] + "'"
                self._update_file_versions_pic(cur_dir, string_search, cur_versions, input_file)
            else:
                # print("Input file does not exists in the PIC repositories! ", input_file)
                logger.warning("Update Version :: Input file does not exists in the PIC repositories! " + str(input_file))
        else:
            # print("File does not exist! ", cur_dir)
            logger.warning("Update Version :: File does not exist! " + str(cur_dir))

    def _update_file_versions_pic(self, input_file_path, input_string_search, input_cur_versions, input_file):
        """
        This is the helper function for the file versions pic function
        :param input_file_path:
        :param input_string_search:
        :param input_cur_versions:
        :return:
        """
        # This assumes that it goes in descending order ex: high->med->low or high->low
        if((input_file == FabianPICFiles.fabian_monitor) or (input_file == FabianPICFiles.fabian_controller_bootloader)
                or (input_file == FabianPICFiles.fabian_controller) or (input_file == FabianPICFiles.fabian_HFO)):
            for line in fileinput.input(input_file_path, inplace=True):
                for i in range(1, len(input_string_search)):
                    found_string, string_search_index = input_string_search[i], i-1
                    index_define = line.find(input_string_search[0])
                    index = line.find(input_string_search[i])

                    if((index_define != -1) and (index != -1)):
                        break

                if((index_define != -1) and (index != -1)):
                    new_line = line[:(index + len(found_string))] + " " + input_cur_versions[string_search_index] + "\n"
                    print("%s" % new_line, end="")
                else:
                    print("%s" % line, end="")
        else:
            for line in fileinput.input(input_file_path, inplace=True):
                for i in range(0, len(input_string_search)):
                    found_string, string_search_index = input_string_search[i], i
                    index = line.find(input_string_search[i])
                    if(index != -1):
                        break

                if(index != -1):
                    new_line = line[:len(found_string)] + " " + input_cur_versions[string_search_index] + "\n"
                    print("%s" % new_line, end="")
                else:
                    print("%s" % line, end="")

    def check_file_versions_gui(self, input_file_path):
        """
        This function will grab the current gui version number for hfo and evo
        :param input_file_path:
        :return:
        """
        global gui_version

        cf_cwd = os.getcwd()

        skip = 0
        if(os.path.exists(cf_cwd + input_file_path)):
            file = open(cf_cwd + input_file_path, "r")

            find_string = "m_szBuildVersion = _T("

            for line in file:
                if(skip == 0):
                    if(line.find("MEDKOM_VERSION") != -1):
                        skip = 3
                    index = line.find(find_string)
                    if(index != -1):
                        new_index = line.find(")")
                        if("HFO" in input_file_path):
                            gui_version[HFO_INDEX] = line[index+len(find_string):new_index]
                        else:
                            gui_version[EVO_INDEX] = line[index+len(find_string):new_index]
                if(skip > 0):
                    skip -= 1
        else:
            logger.warning("Check Version GUI :: Path does not exist! " + str(cf_cwd + input_file_path))

    def check_file_versions_pic(self, input_file_path, input_file):

        cur_dir = os.getcwd()
        cur_dir += input_file_path

        if(os.path.exists(cur_dir)):
            # Write to the correct version line
            if(input_file == FabianPICFiles.fabian_monitor_bootloader):
                string_search = ["#define VERSION"]
                FabianPICFiles.fabian_monitor_bootloader.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_monitor):
                string_search = ["#define", "Vers_hi", "Vers_mid", "Vers_lo"]
                FabianPICFiles.fabian_monitor.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_power):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                FabianPICFiles.fabian_power.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_power_evo):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                FabianPICFiles.fabian_power_evo.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_controller_bootloader):
                string_search = ["#define", "Vers_hi", "Vers_lo"]
                if("EVO_ed4" in cur_dir):
                    FabianPICFiles.fabian_controller_bootloader.value[5] = self._check_file_versions_pic(cur_dir, string_search, input_file)
                elif("ed4" in cur_dir):
                    FabianPICFiles.fabian_controller_bootloader.value[3] = self._check_file_versions_pic(cur_dir, string_search, input_file)
                else:
                    FabianPICFiles.fabian_controller_bootloader.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_controller):
                string_search = ["#define", "VERS_0", "VERS_1", "VERS_2", "VERS_3", "VERS_4", "VERS_5"]
                FabianPICFiles.fabian_controller.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_alarm):
                if("4.X" in cur_dir):
                    string_search = ["#define VERSION_HI", "#define VERSION_LO"]
                    FabianPICFiles.fabian_alarm.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
                else:
                    string_search = ["#define VERSION"]
                    FabianPICFiles.fabian_alarm.value[3] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_alarm_bootloader):
                string_search = ["#define VERSION"]
                FabianPICFiles.fabian_alarm_bootloader.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_blender):
                string_search = ["#define VERSION_HI", "#define VERSION_LO"]
                FabianPICFiles.fabian_blender.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_HFO):
                string_search = ["#define", "Vers_0", "Vers_1", "Vers_2", "Vers_3", "Vers_4"]
                FabianPICFiles.fabian_HFO.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif(input_file == FabianPICFiles.fabian_HFO_bootloader):
                string_search = ["#define Vers_hi", "#define Vers_lo"]
                FabianPICFiles.fabian_HFO_bootloader.value[1] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            else:
                # print("Input file does not exists in the PIC repositories! ", input_file)
                logger.warning("Check Version PIC :: Input file does not exists in the PIC repositories! " + str(input_file))
        else:
            # print("File does not exist! ", cur_dir)
            logger.warning("Check Version PIC :: File does not exist! " + str(cur_dir))

    def _check_file_versions_pic(self, input_file_path, input_string_search, input_file):

        if((input_file == FabianPICFiles.fabian_monitor) or (input_file == FabianPICFiles.fabian_controller_bootloader)
                or (input_file == FabianPICFiles.fabian_controller) or (input_file == FabianPICFiles.fabian_HFO)):

            length = len(input_string_search)

            version_number = [""]*(length-1)

            file = open(input_file_path, "r")

            for line in file:
                for i in range(1, len(input_string_search)):
                    found_string, string_search_index = input_string_search[i], i-1
                    index_define = line.find(input_string_search[0])
                    index = line.find(input_string_search[i])

                    if((index_define != -1) and (index != -1)):
                        break

                if((index_define != -1) and (index != -1)):
                    if(string_search_index != length-2):
                        version_number[string_search_index] = str(line[index+len(input_string_search[i]):])
                    else:
                        version_number[string_search_index] = str(line[index+len(input_string_search[i]):])

            file.close()
            new_version_number = self._check_file_versions_pic_helper(version_number, input_file, input_file_path)
            return "".join(new_version_number)

        else:
            length = len(input_string_search)

            version_number = [""]*length

            file = open(input_file_path, "r")

            for line in file:
                for i in range(0, len(input_string_search)):
                    found_string, string_search_index = input_string_search[i], i
                    index = line.find(input_string_search[i])
                    if(index != -1):
                        break

                if(index != -1):
                    if(string_search_index != length-1):
                        version_number[string_search_index] = str(line[index+len(input_string_search[i]):]) + "."
                    else:
                        version_number[string_search_index] = str(line[index+len(input_string_search[i]):])

            file.close()
            new_version_number = self._check_file_versions_pic_helper(version_number, input_file, input_file_path)
            return "".join(new_version_number)

    def _check_file_versions_pic_helper(self, input_version_number, input_file, input_path):
        replace_list = ["\t", "\n", " ", "/", ".", "'", '"']
        for i in range(0, len(input_version_number)):
            for ch in replace_list:
                input_version_number[i] = input_version_number[i].replace(ch, "")

            if(input_version_number[i] == ''):
                input_version_number[i] = "."

            index = input_version_number[i].find("*")
            if(index != -1):
                input_version_number[i] = input_version_number[i][:index]

            if((input_file == FabianPICFiles.fabian_monitor)):
                    if(i == 0):
                        input_version_number[i] = input_version_number[i][:1]

            if(input_file == FabianPICFiles.fabian_alarm):
                if("4.X" in input_path):
                    pass
                else:
                    input_version_number[i] = input_version_number[i][0] + "." + input_version_number[i][1:]

            if((input_file != FabianPICFiles.fabian_controller) and (input_file != FabianPICFiles.fabian_HFO)):
                if(i != len(input_version_number)-1):
                    input_version_number[i] = input_version_number[i] + "."

        return input_version_number

    def build_repositories(self, input_repositories):
        """
        Clone repositories must be run before this function is run otherwise it will not find the directory
        :param input_repositories:
        :return: {True, False} Depending on whether the repository existed
        """
        cur_dir = os.getcwd()

        if(input_repositories == Repositories.fabian_gui):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-gui'):
                    os.chdir(dir)
                    if((gui_builds[0] == True) and (gui_builds[1] == True)):
                        if(os.path.isfile('build_release.cmd')):
                            os.system('build_release.cmd')
                            os.chdir("..")
                            return True
                        else:
                            logger.warning("Could not find the fabian gui build_release.cmd file!")
                            os.chdir("..")
                            return False
                    elif((gui_builds[0] == True) and (gui_builds[1] == False)):
                        if(os.path.isfile('build-hfo_release.cmd')):
                            os.system('build-hfo_release.cmd')
                            os.chdir("..")
                            return True
                        else:
                            logger.warning("Could not find the fabian gui build-hfo_release.cmd file!")
                            os.chdir("..")
                            return False
                    elif((gui_builds[0] == False) and (gui_builds[1] == True)):
                        if(os.path.isfile('build-evo_release.cmd')):
                            os.system('build-evo_release.cmd')
                            os.chdir("..")
                            return True
                        else:
                            logger.warning("Could not find the fabian gui build-evo_release.cmd file!")
                            os.chdir("..")
                            return False
                    else:
                        logger.warning("No GUI is being built when repository was specified to be built!")

        elif(input_repositories == Repositories.fabian_monitor_bootloader):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-monitor_bootloader'):
                    os.chdir(dir)
                    if(os.path.isfile('build.cmd')):
                        os.system('build.cmd')
                        os.chdir("..")
                        return True
                    else:
                        # print("Could not find the fabian monitor bootloader build file!")
                        logger.warning("Could not find the fabian monitor bootloader build file!")
                        os.chdir("..")
                        return False
        elif(input_repositories == Repositories.fabian_monitor):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-monitor'):
                    os.chdir(dir)
                    if(os.path.isfile('build.cmd')):
                        os.system('build.cmd')
                        os.chdir("..")
                        return True
                    else:
                        # print("Could not find the fabian monitor build file!")
                        logger.warning("Could not find the fabian monitor build file!")
                        os.chdir("..")
                        return False
        elif(input_repositories == Repositories.fabian_power):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-power'):
                    os.chdir(dir)
                    flag = [False, False, False]
                    if(os.path.isfile('buildHW1.cmd')):
                        os.system('buildHW1.cmd')
                        flag[0] = True
                    if(os.path.isfile('buildHW2.cmd')):
                        os.system('buildHW2.cmd')
                        flag[1] = True
                    if(os.path.isfile('buildHW3.cmd')):
                        os.system('buildHW3.cmd')
                        flag[2] = True
                    os.chdir("..")
                    if((flag[0] == True) and (flag[1] == True) and (flag[2] == True)):
                        return True
                    else:
                        # print("Could not find the some of the fabian power build files!")
                        logger.warning("Could not find the some of the fabian power build files!")
                        return False
        elif(input_repositories == Repositories.fabian_power_evo):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-power-evo'):
                    os.chdir(dir)
                    flag = [False, False, False]
                    if(os.path.isfile('buildHW1.cmd')):
                        os.system('buildHW1.cmd')
                        flag[0] = True
                    if(os.path.isfile('buildHW2.cmd')):
                        os.system('buildHW2.cmd')
                        flag[1] = True
                    if(os.path.isfile('buildHW3.cmd')):
                        os.system('buildHW3.cmd')
                        flag[2] = True
                    os.chdir("..")
                    if((flag[0] == True) and (flag[1] == True) and (flag[2] == True)):
                        return True
                    else:
                        # print("Could not find the some of the fabian power evo build files!")
                        logger.warning("Could not find the some of the fabian power evo build files!")
                        return False
        elif(input_repositories == Repositories.fabian_controller_bootloader):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-controller_bootloader'):
                    os.chdir(dir)
                    flag = [False, False, False]
                    if(os.path.isfile('build_pre_ed4.cmd')):
                        os.system('build_pre_ed4.cmd')
                        flag[0] = True
                    if(os.path.isfile('build_ed4.cmd')):
                        os.system('build_ed4.cmd')
                        flag[1] = True
                    if(os.path.isfile('build_ed4-EVO.cmd')):
                        os.system('build_ed4-EVO.cmd')
                        flag[2] = True
                    os.chdir("..")
                    if((flag[0] == True) and (flag[1] == True) and (flag[2] == True)):
                        return True
                    else:
                        # print("Could not find the some of the fabian controller bootloader build files!")
                        logger.warning("Could not find the some of the fabian controller bootloader build files!")
                        return False
        elif(input_repositories == Repositories.fabian_controller):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-controller'):
                    os.chdir(dir)
                    flag = [False, False, False, False]
                    if(os.path.isfile('buildHFO_46K80.cmd')):
                        os.system('buildHFO_46K80.cmd')
                        flag[1] = True
                    if(os.path.isfile('buildHFO_2520.cmd')):
                        os.system('buildHFO_2520.cmd')
                        flag[2] = True
                    if(os.path.isfile('buildEvo_26K80.cmd')):
                        os.system('buildEVO_26K80.cmd')
                        flag[0] = True
                    if(os.path.isfile('buildEvo_2520.cmd')):
                        os.system('buildEVO_2520.cmd')
                        flag[3] = True
                    os.chdir("..")
                    if((flag[0] == True) and (flag[1] == True) and (flag[2] == True) and (flag[3] == True)):
                        return True
                    else:
                        # print("Could not find some of the fabian control build files")
                        logger.warning("Could not find some of the fabian controller build files")
                        return False
        elif(input_repositories == Repositories.fabian_alarm_bootloader):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-alarm_bootloader'):
                    os.chdir(dir)
                    if(os.path.isfile('build.cmd')):
                        os.system('build.cmd')
                        os.chdir("..")
                        return True
                    else:
                        # print("Could not find the fabian alarm bootloader build file")
                        logger.warning("Could not find the fabian alarm bootloader build file")
                        os.chdir("..")
                        return False
        elif(input_repositories == Repositories.fabian_alarm):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-alarm'):
                    os.chdir(dir)
                    flag = [False, False]
                    if(os.path.isfile('build_v4.cmd')):
                        os.system('build_v4.cmd')
                        flag[0] = True
                    if(os.path.isfile('build_v5.cmd')):
                        os.system('build_v5.cmd')
                        flag[1] = True
                    os.chdir("..")
                    if((flag[0] == True) and (flag[1] == True)):
                        return True
                    else:
                        # print("Could not find the fabian alarm build file!")
                        logger.warning("Could not find some of the fabian alarm build files!")
                        return False
        elif(input_repositories == Repositories.fabian_blender):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-blender'):
                    os.chdir(dir)
                    if(os.path.isfile('build.cmd')):
                        os.system('build.cmd')
                        os.chdir("..")
                        return True
                    else:
                        # print("Could not find the fabian blender build file!")
                        logger.warning("Could not find the fabian blender build file!")
                        os.chdir("..")
                        return False
        elif(input_repositories == Repositories.fabian_HFO):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-hfo'):
                    os.chdir(dir)
                    if(os.path.isfile('build.cmd')):
                        os.system('build.cmd')
                        os.chdir("..")
                        return True
                    else:
                        # print("Could not find the fabian HFO build file")
                        logger.warning("Could not find the fabian HFO build file")
                        os.chdir("..")
                        return False
        elif(input_repositories == Repositories.fabian_HFO_bootloader):
            list_dir = os.listdir(cur_dir)
            for dir in list_dir:
                if(dir == 'fabian-hfo_bootloader'):
                    os.chdir(dir)
                    if(os.path.isfile('build.cmd')):
                        os.system('build.cmd')
                        os.chdir("..")
                        return True
                    else:
                        # print("Could not find the fabian HFO bootloader build file")
                        logger.warning("Could not find the fabian HFO bootloader build file")
                        os.chdir("..")
                        return False
        else:
            # print("Repository does not exist! ", input_repositories)
            logger.warning("Repository does not exist! " + str(input_repositories))

        # print("Repository directory could not be found!")
        logger.warning("Repository directory could not be found!")
        return False

    def convert_files_pj2_pm3(self, input_repository, input_icp, input_mplabxipe):
        """
        This portion of the file conversion should find the corresponding hex file and convert them using the ICP
        Windows program and the MPLABX IPE program as well
        :param input_repository:
        :param input_icp:
        :return:
        """
        cf_cwd = os.getcwd()

        find_dir = None
        if(input_repository == Repositories.fabian_gui):
             # This will be the only one with the full file path in the directory buffer. This is because the gui does
             # not have multiple files to move over other than the executables
            find_dir = [cf_cwd + "\\fabian-gui\\FabianHFO\\NetDCU9 (ARMV4I)\\Release\\FabianHFO.exe"]
            find_dir.append(cf_cwd + "\\fabian-gui\\FabianEvo\\NetDCU9 (ARMV4I)\\Release\\Fabian.exe")
            find_dir.append(cf_cwd + "\\fabian-gui\\SetupFabian\\NetDCU9 (ARMV4I)\\Release\\SetupFabian.exe")
            # Use this function for gui anyway since it is a buffer to set up the release package
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)

            # We do not convert any files here so we set the find_dir to None for only fabian gui
            find_dir = None
        elif(input_repository == Repositories.fabian_monitor_bootloader):
            find_dir = [cf_cwd + "\\fabian-monitor_bootloader\\Neo_mon Bootloader UART.X\\dist\\default\\production\\"]
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_monitor):
            find_dir = [cf_cwd + "\\fabian-monitor\\Mon.X\\dist\\default\\production\\"]
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_power):
            find_dir = [cf_cwd + "\\fabian-power\\Akku_HFO_HW1.X\\dist\\default\\production\\"]
            find_dir.append(cf_cwd + "\\fabian-power\\Akku_HFO_HW2.X\\dist\\default\\production\\")
            find_dir.append(cf_cwd + "\\fabian-power\\Akku_HFO_HW3.X\\dist\\default\\production\\")
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_power_evo):
            find_dir = [cf_cwd + "\\fabian-power-evo\\Akku_EVO_HW1.X\\dist\\default\\production\\"]
            find_dir.append(cf_cwd + "\\fabian-power-evo\\Akku_EVO_HW2.X\\dist\\default\\production\\")
            find_dir.append(cf_cwd + "\\fabian-power-evo\\Akku_EVO_HW3.X\\dist\\default\\production\\")
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_controller_bootloader):
            find_dir = [cf_cwd + "\\fabian-controller_bootloader\\Ctrl_Bootloader.X\\dist\\default\\production\\"]
            find_dir.append(cf_cwd + "\\fabian-controller_bootloader\\Ctrl_Bootloader_ed4.X\\dist\\default\\production\\")
            find_dir.append(cf_cwd + "\\fabian-controller_bootloader\\Ctrl_Bootloader_EVO_ed4.X\\dist\\default\\production\\")
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_controller):
            find_dir = [cf_cwd + "\\fabian-controller\\Ctl_2520_hfo.X\\dist\\default\\production\\"]
            find_dir.append(cf_cwd + "\\fabian-controller\\Ctl_46K80_hfo.X\\dist\\default\\production\\")
            find_dir.append(cf_cwd + "\\fabian-controller\\Ctl_2520_evo.X\\dist\\default\\production\\")
            find_dir.append(cf_cwd + "\\fabian-controller\\Ctl_26K80_evo.X\\dist\\default\\production\\")

            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_alarm_bootloader):
            find_dir = [cf_cwd + "\\fabian-alarm_bootloader\\AlarmPIC_Fabian_UART_loader.X\\dist\\default\\production\\"]
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_alarm):
            find_dir = [cf_cwd + "\\fabian-alarm\\AlarmPIC_Fabian_V5.X\\dist\\default\\production\\"]
            find_dir.append(cf_cwd + "\\fabian-alarm\\AlarmPIC_Fabian_V4.X\\dist\\default\\production\\")
            # Setting up the alarm conversion for mim later
            self.alarm_filepath = cf_cwd + "\\fabian-alarm\\"
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_blender):
            find_dir = [cf_cwd + "\\fabian-blender\\Blender.X\\dist\\default\\production\\"]
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_HFO):
            find_dir = [cf_cwd + "\\fabian-hfo\\fabian-HFO.X\\dist\\default\\production\\"]
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        elif(input_repository == Repositories.fabian_HFO_bootloader):
            find_dir = [cf_cwd + "\\fabian-hfo_bootloader\\fabian-HFO-bootloader.X\\dist\\default\\production\\"]
            self._convert_files_pj2_pm3_repository(find_dir, input_repository)
        else:
            # print("Repository does not exist! ", input_repository)
            logger.warning("Repository does not exist! " + str(input_repository))

        self._convert_files_pj2_pm3(find_dir, input_repository, input_icp, input_mplabxipe)

    def _convert_files_pj2_pm3(self, input_file_path, repository_type, input_icp, input_mplabxipe):
        """
        This is a helper function for the convert files process
        :param input_file_path:
        :param repository_type:
        :param input_icp:
        :param input_mplabxipe:
        :return:
        """
        # print("INPUT FILE PATH:")
        logger.info("Converting " + str(repository_type) + " to .pj2, .pm3, .bin files")
        # print(input_file_path)
        if(input_file_path == None):
            # print("No file path given for this repository! ", repository_type)
            if(repository_type != Repositories.fabian_gui):
                logger.warning("No file path given for this repository! " + str(repository_type))
            return
        if(input_icp == None):
            # print("ICP was not found!")
            logger.critical("ICP was not found!")
            return

        for path in input_file_path:
            if(os.path.exists(path)):
                checksum_file = [file_string for file_string in os.listdir(path) if file_string.endswith(FileEndings.END_HEX_FILE_CHECKSUM.value)]
                non_checksum_file = [file_string for file_string in os.listdir(path) if (not file_string.endswith(FileEndings.END_HEX_FILE_CHECKSUM.value)) and (file_string.endswith(FileEndings.END_HEX_FILE.value))]

                if(checksum_file):
                    file = checksum_file[0]
                    file_ending = FileEndings.END_HEX_FILE.value
                else:
                    if(non_checksum_file):
                        file = non_checksum_file[0]
                        file_ending = FileEndings.END_HEX_FILE.value
                    else:
                        file = None
                        file_ending = FileEndings.END_HEX_FILE.value

                if(file != None):
                    if((repository_type == Repositories.fabian_monitor_bootloader)):
                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_monitor_bootloader.value[1])
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_monitor_bootloader.value[1])
                        os.rename(path+file, path + FabianPICFiles.fabian_monitor_bootloader.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_controller_bootloader)):
                        if("EVO_ed4" in path):
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[3], repository_type.value[-1] + "evo_", FabianPICFiles.fabian_controller_bootloader.value[5].replace(".", ""))
                            input_icp.convert_files(path+file, repository_type.value[3], return_checksum, repository_type.value[-1] + "evo_", FabianPICFiles.fabian_controller_bootloader.value[5].replace(".", ""))
                            os.rename(path+file, path + FabianPICFiles.fabian_controller_bootloader.value[5] + file_ending)
                        elif("ed4" in path):
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[2], repository_type.value[-1] + "hfo_", FabianPICFiles.fabian_controller_bootloader.value[3].replace(".", ""))
                            input_icp.convert_files(path+file, repository_type.value[2], return_checksum, repository_type.value[-1] + "hfo_", FabianPICFiles.fabian_controller_bootloader.value[3].replace(".", ""))
                            os.rename(path+file, path + FabianPICFiles.fabian_controller_bootloader.value[3] + file_ending)
                        else:
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_controller_bootloader.value[1].replace(".", ""))
                            input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_controller_bootloader.value[1].replace(".", ""))
                            os.rename(path+file, path + FabianPICFiles.fabian_controller_bootloader.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_alarm_bootloader)):
                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_alarm_bootloader.value[1])
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_alarm_bootloader.value[1])
                        os.rename(path+file, path + FabianPICFiles.fabian_alarm_bootloader.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_alarm)):
                        if("4.X" in path):
                            # This is the version 4.2 in the alarm file which is an outdated file
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[2], repository_type.value[-1], FabianPICFiles.fabian_alarm.value[1])
                            input_icp.convert_files(path+file, repository_type.value[2], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_alarm.value[1])
                            os.rename(path+file, path + FabianPICFiles.fabian_alarm.value[1] + file_ending)
                        else:
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_alarm.value[3])
                            input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_alarm.value[3])
                            # This is a special case for alarm pic
                            copyfile(path+file, path + FabianPICFiles.fabian_alarm.value[3] + file_ending)

                            # Setting up the alarm checksum for post processing later for mim
                            self.alarm_checksum = return_checksum
                            self.alarm_mim_version = FabianPICFiles.fabian_alarm.value[3]
                    elif((repository_type == Repositories.fabian_HFO)):
                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_HFO.value[1])
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_HFO.value[1])
                        os.rename(path+file, path + FabianPICFiles.fabian_HFO.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_HFO_bootloader)):
                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_HFO_bootloader.value[1])
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_HFO_bootloader.value[1])
                        os.rename(path+file, path + FabianPICFiles.fabian_HFO_bootloader.value[1] + file_ending)
                    # CHECKSUM FILES
                    elif((repository_type == Repositories.fabian_monitor)):
                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_monitor.value[1])
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_monitor.value[1])
                        os.rename(path+file, path + FabianPICFiles.fabian_monitor.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_power)):
                        if("HW1" in path):
                            version = FabianPICFiles.fabian_power.value[1]
                        elif("HW2" in path):
                            version = str(round(float(FabianPICFiles.fabian_power.value[1]) + 0.1, 2))
                        elif("HW3" in path):
                            version = str(round(float(FabianPICFiles.fabian_power.value[1]) + 0.2, 2))

                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], version)
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], version)
                        os.rename(path+file, path + FabianPICFiles.fabian_power.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_power_evo)):
                        if("HW1" in path):
                            version = FabianPICFiles.fabian_power_evo.value[1]
                        elif("HW2" in path):
                            version = str(round(float(FabianPICFiles.fabian_power_evo.value[1]) + 0.1, 2))
                        elif("HW3" in path):
                            version = str(round(float(FabianPICFiles.fabian_power_evo.value[1]) + 0.2, 2))

                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], version)
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], version)
                        os.rename(path+file, path + FabianPICFiles.fabian_power_evo.value[1] + file_ending)
                    elif((repository_type == Repositories.fabian_controller)):
                        if("2520" in path):
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_controller.value[1])
                            input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_controller.value[1])
                            os.rename(path+file, path + FabianPICFiles.fabian_controller.value[1] + file_ending)
                        elif("46K80" in path):
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[2], repository_type.value[-1], FabianPICFiles.fabian_controller.value[1])
                            input_icp.convert_files(path+file, repository_type.value[2], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_controller.value[1])
                            os.rename(path+file, path + FabianPICFiles.fabian_controller.value[1] + file_ending)
                        elif("26K80" in path):
                            return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[3], repository_type.value[-1], FabianPICFiles.fabian_controller.value[1])
                            input_icp.convert_files(path+file, repository_type.value[3], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_controller.value[1])
                            os.rename(path+file, path + FabianPICFiles.fabian_controller.value[1] + file_ending)
                        else:
                            # print("This hex file is not in either fabian controller repository")
                            logger.warning("This hex file is not in either fabian controller repository" + str(file))
                    elif((repository_type == Repositories.fabian_blender)):
                        return_checksum = input_mplabxipe.convert_files(path+file, path, repository_type.value[1], repository_type.value[-1], FabianPICFiles.fabian_blender.value[1])
                        input_icp.convert_files(path+file, repository_type.value[1], return_checksum, repository_type.value[-1], FabianPICFiles.fabian_blender.value[1])
                        os.rename(path+file, path + FabianPICFiles.fabian_blender.value[1] + file_ending)
                    else:
                        logger.warning("In converting files repository not found! " + str(repository_type))
                else:
                    logger.warning("No hex file exists in " + str(repository_type))
            else:
                logger.warning("A build process went incorrectly! " + str(path))

    def _convert_files_pj2_pm3_repository(self, input_find_dir, input_repository):
        """
        This function sets up the release package function to be able to fun through all the necessary files and then
        move then into the correct release package. It does this by saving the file path to the hex, pm3, .bin files
        and then putting the correct repository in the adjacent array index
        :param input_find_dir:
        :param input_repository:
        :return:
        """
        if(input_repository.value[0] != None):
            self.build_files_path[0].extend(input_find_dir)
            for i in range(0, len(input_find_dir)):
                self.build_files_path[1].extend([input_repository])
        else:
            logger.info("Not converting this repository to pm3 or bin files " + str())

    def release_package_update(self):
        """
        This function will update the release package with the necessary files
        :return:
        """
        # We want to delete all the unnecessary files in the release package
        logger.info("Deleting files in the release package")
        self._release_package_update_delete()

        for path, repo in zip(self.build_files_path[0], self.build_files_path[1]):

            logger.info("Moving files for the " + str(repo))

            # For fabian gui in the SETUP package we need to move in PIC Alarm, Controller, HFO, and Monitor
            if(repo == Repositories.fabian_gui):
                # This is sent to only USB Package
                # This needs to be put in the hfo and evo
                self._release_package_update_gui(path)
            elif(repo == Repositories.fabian_alarm):
                # Hex files need to go to the USB package and the .pj2, .pm3, .bin go to the PIC Package
                # The fabian alarm .alr file is ready and the path and repo are already set up to do normal move
                self._release_package_update_all(path, repo)
            elif(repo == Repositories.fabian_controller):
                # Hex files need to go to the USB package and the .pj2, .pm3, .bin go to the PIC Package
                self._release_package_update_all(path, repo)
            elif(repo == Repositories.fabian_HFO):
                # Hex files need to go to the USB package and the .pj2, .pm3, .bin go to the PIC Package for only HFO
                self._release_package_update_all(path, repo)
            elif(repo == Repositories.fabian_monitor):
                # Hex files need to go to the USB package and the .pj2, .pm3, .bin go to the PIC Package
                self._release_package_update_all(path, repo)
            else:
                # Hex files ARE NOT USED but .pj2, .pm3, .bin go to the PIC Package
                self._release_package_update_pics(path, repo)

        # Move the language files from the gui repo to the release package
        self._release_package_update_languages()

        # Create the build files log mover here
        self._release_package_update_build_logs()

    def _release_package_update_build_logs(self):
        """
        This function will save all the build logs
        :return:
        """
        logger.info("Creating fabian-build-logs directory")
        cur_dir = os.getcwd()
        log_dir = cur_dir + "\\fabian-build-logs"
        os.mkdir(log_dir)

        # Saves the log here
        if(os.path.exists(cur_dir + "\\fabian-gui\\FabianHFO\\NetDCU9 (ARMV4I)\\Release\\BuildLog.htm")):
            version_hfo = gui_version[HFO_INDEX].replace('"', '')
            with open(cur_dir + "\\fabian-gui\\FabianHFO\\NetDCU9 (ARMV4I)\\Release\\BuildLog.htm", encoding='utf-16') as f:
                with open(log_dir + "\\CompilerWarningsReport_" + version_hfo + "-hfo.htm", mode='w+') as f1:
                    for line in f:
                        f1.write(line)
            self.parse_build_logs(log_dir + "\\CompilerWarningsReport_" + version_hfo + "-hfo.htm", version_hfo)
            try:
                output_command = "wkhtmltopdf.exe " + log_dir + "\\CompilerWarningsReport_" + version_hfo + "-hfo.htm " + log_dir + "\\CompilerWarningsReport_" + version_hfo + "-hfo.pdf"
                os.system(output_command)
            except:
                logger.warning("Could not convert the hfo htm build log to pdf")
        if(os.path.exists(cur_dir + "\\fabian-gui\\FabianEvo\\NetDCU9 (ARMV4I)\\Release\\BuildLog.htm")):
            version_evo = gui_version[EVO_INDEX].replace('"', '')
            with open(cur_dir + "\\fabian-gui\\FabianEvo\\NetDCU9 (ARMV4I)\\Release\\BuildLog.htm", encoding='utf-16') as f:
                with open(log_dir + "\\CompilerWarningsReport_" + version_evo + "-evo.htm", mode='w+') as f1:
                    for line in f:
                        f1.write(line)
            self.parse_build_logs(log_dir + "\\CompilerWarningsReport_" + version_evo + "-evo.htm", version_evo)
            try:
                output_command = "wkhtmltopdf.exe " + log_dir + "\\CompilerWarningsReport_" + version_evo + "-evo.htm " + log_dir + "\\CompilerWarningsReport_" + version_evo + "-evo.pdf"
                os.system(output_command)
            except:
                logger.warning("Could not convert the evo htm build log to pdf")
        if(os.path.exists(cur_dir + "\\fabian-gui\\SetupFabian\\NetDCU9 (ARMV4I)\\Release\\BuildLog.htm")):
            copyfile(cur_dir + "\\fabian-gui\\SetupFabian\\NetDCU9 (ARMV4I)\\Release\\BuildLog.htm", log_dir + "\\CompilerWarningsReport_SetupFabian.htm")

    def parse_build_logs(self, input_file, input_version):
        find_time = "Rebuild started: "
        find_end = "</h3>"
        for line in fileinput.input(input_file, inplace=True):
            if line.startswith('<h3>'):
                index = line.find(find_time)
                first_part = line[:index + len(find_time)] + str(datetime.now()) + " "
                index_end = line.find(find_end)
                second_part = line[index + len(find_time):index_end]
                third_part = " Version: " + input_version + " " + "</h3>"
                new_line = first_part + second_part + third_part + "\n"
                print(new_line, end="")
            else:
                print(line, end="")

    def _release_package_update_delete(self):
        """
        This will delete all the unnecessary items in the release package
        :return:
        """

        cur_dir = os.getcwd()

        for release in ReleaseType:
            if(release == ReleaseType.HFO_USB_Package):
                # Delete the SetupFabian file
                if(os.path.exists(cur_dir + release.value)):
                    for file in os.listdir(cur_dir + release.value):
                        if(file == "SetupFabian.exe"):
                            if(Repositories.fabian_gui.value[0] != None):
                                if(gui_builds[0] == True):
                                    os.remove(cur_dir + release.value + file)
                else:
                    logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value))
                # Delete all the files necessary in the HFO package
                for package in USBPackageHFO:
                    if(package == USBPackageHFO.hfo_ffs_disk):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(file == "FabianHFO.exe"):
                                    if(Repositories.fabian_gui.value[0] != None):
                                        if(gui_builds[0] == True):
                                            os.remove(cur_dir + release.value + package.value[0] + "FabianHFO.exe")
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageHFO.hfo_pic_alarm):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_alarm.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageHFO.hfo_pic_controller):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_controller.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageHFO.hfo_pic_hfo):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_HFO.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageHFO.hfo_pic_monitor):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_monitor.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    else:
                        logger.warning("This package is not in the USBPackageHFO! " + str(package))

            elif(release == ReleaseType.HFO_ICP2):
                for file in os.listdir(cur_dir+release.value):
                    self._release_package_update_delete_helper(cur_dir, release, file)
            elif(release == ReleaseType.HFO_PICKit3):
                for file in os.listdir(cur_dir+release.value):
                    self._release_package_update_delete_helper(cur_dir, release, file)
            elif(release == ReleaseType.HFO_PM3):
                for file in os.listdir(cur_dir+release.value):
                    self._release_package_update_delete_helper(cur_dir, release, file)
            elif(release == ReleaseType.HFO_HEX):
                if(os.path.exists(cur_dir+release.value)):
                    for file in os.listdir(cur_dir+release.value):
                        self._release_package_update_delete_helper(cur_dir, release, file)
                else:
                    os.mkdir(cur_dir+release.value)

            elif(release == ReleaseType.EVO_USB_Package):
                # Delete the SetupFabian file
                if(os.path.exists(cur_dir + release.value)):
                    for file in os.listdir(cur_dir + release.value):
                        if(file == "SetupFabian.exe"):
                            if(Repositories.fabian_gui.value[0] != None):
                                if(gui_builds[1] == True):
                                    os.remove(cur_dir + release.value + file)
                else:
                    logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value))

                # Delete all the files necessary in the EVO package
                for package in USBPackageEVO:
                    if(package == USBPackageEVO.evo_ffs_disk):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(file == "Fabian.exe"):
                                    if(Repositories.fabian_gui.value[0] != None):
                                        if(gui_builds[1] == True):
                                            os.remove(cur_dir + release.value + package.value[0] + "Fabian.exe")
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageEVO.evo_pic_alarm):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_alarm.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageEVO.evo_pic_controller):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_controller.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    elif(package == USBPackageEVO.evo_pic_monitor):
                        if(os.path.exists(cur_dir + release.value + package.value[0])):
                            for file in os.listdir(cur_dir + release.value + package.value[0]):
                                if(Repositories.fabian_monitor.value[0] != None):
                                    os.remove(cur_dir + release.value + package.value[0] + file)
                        else:
                            logger.warning("Release package update delete path does not exist! " + str(cur_dir + release.value + package.value[0]))
                    else:
                        logger.warning("This package is not in the USBPackageEVO! " + str(package))

            elif(release == ReleaseType.EVO_ICP2):
                for file in os.listdir(cur_dir+release.value):
                    self._release_package_update_delete_helper(cur_dir, release, file)
            elif(release == ReleaseType.EVO_PICKit3):
                for file in os.listdir(cur_dir+release.value):
                    self._release_package_update_delete_helper(cur_dir, release, file)
            elif(release == ReleaseType.EVO_PM3):
                for file in os.listdir(cur_dir+release.value):
                    self._release_package_update_delete_helper(cur_dir, release, file)
            elif(release == ReleaseType.EVO_HEX):
                if(os.path.exists(cur_dir+release.value)):
                    for file in os.listdir(cur_dir+release.value):
                        self._release_package_update_delete_helper(cur_dir, release, file)
                else:
                    os.mkdir(cur_dir+release.value)
            else:
                logger.warning("This release type is not used in ReleaseType class! " + str(release))

    def _release_package_update_delete_helper(self, input_cur_dir, input_release, input_file):
        """
        This function helps determine if the file is something we want to delete out of the package
        :param input_cur_dir:
        :param input_release:
        :param input_file:
        :return:
        """

        if((Repositories.fabian_power.value[-1] in input_file) and (Repositories.fabian_power.value[0] == None)):
            pass
        elif((Repositories.fabian_power_evo.value[-1] in input_file) and (Repositories.fabian_power_evo.value[0] == None)):
            pass
        elif((Repositories.fabian_alarm_bootloader.value[-1] in input_file) and (Repositories.fabian_alarm_bootloader.value[0] == None)):
            pass
        elif((Repositories.fabian_alarm.value[-1] in input_file) and (Repositories.fabian_alarm.value[0] == None)):
            pass
        elif((Repositories.fabian_blender.value[-1] in input_file) and (Repositories.fabian_blender.value[0] == None)):
            pass
        elif((Repositories.fabian_controller_bootloader.value[-1] in input_file) and (Repositories.fabian_controller_bootloader.value[0] == None)):
            pass
        elif((Repositories.fabian_HFO_bootloader.value[-1] in input_file) and (Repositories.fabian_HFO_bootloader.value[0] == None)):
            pass
        elif((Repositories.fabian_HFO.value[-1] in input_file) and (Repositories.fabian_HFO.value[0] == None)):
            pass
        elif((Repositories.fabian_monitor_bootloader.value[-1] in input_file) and (Repositories.fabian_monitor_bootloader.value[0] == None)):
            pass
        elif(input_file == "auto01.res"):
            pass
        else:
            os.remove(input_cur_dir + input_release.value + input_file)

    def _release_package_update_gui(self, input_path):
        """
        This function goes through the GUI specific files that will be moved into the release package
        :param input_path:
        :return:
        """

        cur_dir = os.getcwd()

        if(os.path.exists(input_path)):
            if("FabianHFO" in input_path):
                # We move the FabianHFO.exe into the corresponding directory
                if(gui_builds[0] == True):
                    copyfile(input_path, cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_ffs_disk.value[0] + "FabianHFO.exe")
            elif("FabianEvo" in input_path):
                # We move the Fabian.exe into the corresponding directory
                if(gui_builds[1] == True):
                    copyfile(input_path, cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_ffs_disk.value[0] + "Fabian.exe")
            elif("SetupFabian" in input_path):
                # We move the SetupFabian.exe into the EVO and HFO corresponding directories
                if(gui_builds[0] == True):
                    copyfile(input_path, cur_dir + ReleaseType.HFO_USB_Package.value + "SetupFabian.exe")
                if(gui_builds[1] == True):
                    copyfile(input_path, cur_dir + ReleaseType.EVO_USB_Package.value + "SetupFabian.exe")
            else:
                logger.warning("Release gui package unknown path: " + str(input_path))
        else:
            logger.warning("This release path does not exist: " + str(input_path))

    def _release_package_update_pics(self, input_path, input_repo):
        """
        This function goes through the PIC specific files that will be moved into the release package
        :param input_path:
        :param input_repo:
        :return:
        """

        cur_dir = os.getcwd()

        if(os.path.exists(input_path)):
            checksum_file = [file_string for file_string in os.listdir(input_path) if file_string.endswith(FileEndings.END_HEX_FILE_CHECKSUM.value)]
            non_checksum_file = [file_string for file_string in os.listdir(input_path) if (not file_string.endswith(FileEndings.END_HEX_FILE_CHECKSUM.value)) and (file_string.endswith(FileEndings.END_HEX_FILE.value))]
            pj2_files = [file_string for file_string in os.listdir(input_path) if file_string.endswith(".pj2")]
            if(len(pj2_files) > 0):
                pj2_file = pj2_files[0]
            else:
                pj2_file = None

            if(checksum_file):
                file = checksum_file[0]
            else:
                if(non_checksum_file):
                    file = non_checksum_file[0]
                else:
                    file = None

            if(input_repo == Repositories.fabian_monitor_bootloader):
                if(file):
                    if(file[-5].isdigit()):
                        copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + file).lower())
                        copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + file).lower())
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.EVO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_power):
                # This only does to the HFO
                if(file):
                    if(file[-5].isdigit()):
                        if("HW1" in input_path):
                            copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "hw1_" + file).lower())
                        elif("HW2" in input_path):
                            try:
                                num = str(round(float(file[:3]) + 0.1, 2))
                                num += file[3:]
                                copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "hw2_" + num).lower())
                            except:
                                copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "hw2_" + file).lower())
                        elif("HW3" in input_path):
                            try:
                                num = str(round(float(file[:3]) + 0.2, 2))
                                num += file[3:]
                                copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "hw3_" + num).lower())
                            except:
                                copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "hw3_" + file).lower())
                        else:
                            logger.warning("Do not know this input path type for release package fabian_power: " + str(input_path))
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_power_evo):
                # This only goes to the EVO
                # First get the .pj2 files
                if(file):
                    if(file[-5].isdigit()):
                        if("HW1" in input_path):
                            copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "hw1_" + file).lower())
                        elif("HW2" in input_path):
                            try:
                                num = str(round(float(file[:3]) + 0.1, 2))
                                num += file[3:]
                                copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "hw2_" + num).lower())
                            except:
                                copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "hw2_" + file).lower())
                        elif("HW3" in input_path):
                            try:
                                num = str(round(float(file[:3]) + 0.2, 2))
                                num += file[3:]
                                copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "hw3_" + num).lower())
                            except:
                                copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "hw3_" + file).lower())
                        else:
                            logger.warning("Do not know this input path type for release package fabian_power_evo: " + str(input_path))
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.EVO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_controller_bootloader):
                # First get the .pj2 files
                if(file):
                    if(file[-5].isdigit()):
                        if("EVO_ed4" in input_path):
                            # copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "EVO_ed4_" + file).lower())
                            copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "EVO_ed4_" + file).lower())
                        elif("ed4" in input_path):
                            copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + "ed4_" + file).lower())
                            # copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + "ed4_" + file).lower())
                        else:
                            copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + file).lower())
                            copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + file).lower())
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    if("EVO_ed4" in input_path):
                        copyfile(input_path + pj2_file, (cur_dir + ReleaseType.EVO_ICP2.value + pj2_file).lower())
                    elif("ed4" in input_path):
                        copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                    else:
                        copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                        copyfile(input_path + pj2_file, (cur_dir + ReleaseType.EVO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            if("EVO_ed4" in input_path):
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                            elif("ed4" in input_path):
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            else:
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            if("EVO_ed4" in input_path):
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                            elif("ed4" in input_path):
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            else:
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                                copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_alarm_bootloader):
                # First get the .pj2 files
                if(file):
                    if(file[-5].isdigit()):
                        copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + file).lower())
                        copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + file).lower())
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.EVO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_blender):
                # First get the .pj2 files
                if(file):
                    if(file[-5].isdigit()):
                        copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + file).lower())
                        copyfile(input_path + file, (cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + file).lower())
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.EVO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))


                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.EVO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_HFO_bootloader):
                # This one only goes to the HFO
                # First get the .pj2 files
                if(file):
                    if(file[-5].isdigit()):
                        copyfile(input_path + file, (cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + file).lower())
                else:
                    logger.warning("No hex file for " + str(input_repo))

                if(pj2_file):
                    copyfile(input_path + pj2_file, (cur_dir + ReleaseType.HFO_ICP2.value + pj2_file).lower())
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                        elif(dir_file.endswith(".bin")):
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PICKit3.value + dir_file).lower())
                            copyfile(ev1_path + dir_file, (cur_dir + ReleaseType.HFO_PM3.value + dir_file).lower())
                else:
                    logger.warning("Path does not exist " + str(ev1_path))
            else:
                logger.warning("This repository should not be entering here! " + str(input_repo))
        else:
            logger.warning("Input path does not exist! " + str(input_path))

    def _release_package_update_all(self, input_path, input_repo):
        """
        This function will go through the files that need to go to the PIC and USB packages
        :param input_path:
        :param input_repo:
        :return:
        """

        cur_dir = os.getcwd()

        if(os.path.exists(input_path)):
            if(os.path.isfile(input_path)):
                pass
            else:
                checksum_file = [file_string for file_string in os.listdir(input_path) if file_string.endswith(FileEndings.END_HEX_FILE_CHECKSUM.value)]
                non_checksum_file = [file_string for file_string in os.listdir(input_path) if (not file_string.endswith(FileEndings.END_HEX_FILE_CHECKSUM.value)) and (file_string.endswith(FileEndings.END_HEX_FILE.value))]
                pj2_files = [file_string for file_string in os.listdir(input_path) if file_string.endswith(".pj2")]
                if(len(pj2_files) > 0):
                    pj2_file = pj2_files[0]
                else:
                    pj2_file = None

                if(checksum_file):
                    file = checksum_file[0]
                else:
                    if(non_checksum_file):
                        file = non_checksum_file[0]
                    else:
                        file = None


            if(input_repo == Repositories.fabian_alarm):
                if("MIM" in input_path):

                    counter = -1
                    while(input_path[counter] != "\\"):
                        counter -= 1

                    if(os.path.exists(cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_alarm.value[0])):
                        copyfile(input_path, cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_alarm.value[0] + input_path[counter:])
                    else:
                        logger.warning("Path does not exist: " + str(cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_alarm.value[0]))
                    if(os.path.exists(cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_pic_alarm.value[0])):
                        copyfile(input_path, cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_pic_alarm.value[0] + input_path[counter:])
                    else:
                        logger.warning("Path does not exist: " + str(cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_pic_alarm.value[0]))
                else:
                    if(file):
                        if(file[-5].isdigit()):
                            copyfile(input_path + file, cur_dir + ReleaseType.HFO_HEX.value + input_repo.value[-1] + file)
                            copyfile(input_path + file, cur_dir + ReleaseType.EVO_HEX.value + input_repo.value[-1] + file)
                    else:
                        logger.warning("No hex file for " + str(input_repo))

                    if(pj2_file):
                        pass
                        # Keep here in case we want to move over the files
                        # copyfile(input_path + pj2_file, cur_dir + ReleaseType.HFO_ICP2.value + pj2_file)
                        # copyfile(input_path + pj2_file, cur_dir + ReleaseType.EVO_ICP2.value + pj2_file)
                    else:
                        logger.warning("No pj2 for for " + str(input_repo))

                    # Then get the .pm3 and .bin files
                    ev1_path = input_path + "ev1\\"
                    if(os.path.exists(ev1_path)):
                        for dir_file in os.listdir(ev1_path):
                            if(dir_file.endswith(".pm3")):
                                pass
                                # Keep here if we want the alarm files there
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PICKit3.value + dir_file)
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PM3.value + dir_file)
                            elif(dir_file.endswith(".bin")):
                                pass
                                # Keep here if we want the alarm files there
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PICKit3.value + dir_file)
                                # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PM3.value + dir_file)
                    else:
                        logger.warning("Path does not exist " + str(ev1_path))
            elif(input_repo == Repositories.fabian_controller):
                if(pj2_file):
                    pass
                    # copyfile(input_path + file, cur_dir + ReleaseType.HFO_ICP2.value + file)
                    # copyfile(input_path + file, cur_dir + ReleaseType.EVO_ICP2.value + file)
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                if(file):
                    if("46K80_hfo" in input_path):
                        copyfile(input_path + file, cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_controller.value[0] + file[:-4] + USBPackageHFO.hfo_pic_controller.value[2])
                    elif("26K80_evo" in input_path):
                        copyfile(input_path + file, cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_pic_controller.value[0] + file[:-4] + USBPackageEVO.evo_pic_controller.value[2])
                    elif("2520_hfo" in input_path):
                        copyfile(input_path + file, cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_controller.value[0] + file[:-4] + USBPackageHFO.hfo_pic_controller.value[1])
                    elif("2520_evo" in input_path):
                        copyfile(input_path + file, cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_pic_controller.value[0] + file[:-4] + USBPackageEVO.evo_pic_controller.value[1])
                else:
                    logger.warning("No hex file for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):
                            pass  # if we want controller files in the directories
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PM3.value + dir_file)
                        elif(dir_file.endswith(".bin")):
                            pass  # if we want controller files in the directories
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PM3.value + dir_file)
                else:
                    logger.warning("Path does not exist " + str(ev1_path))
            elif(input_repo == Repositories.fabian_HFO):
                if(pj2_file):
                    pass
                    # copyfile(input_path + file, cur_dir + ReleaseType.HFO_ICP2.value + file)
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                if(file):
                    copyfile(input_path + file, cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_hfo.value[0] + file[:-4] + USBPackageHFO.hfo_pic_hfo.value[1])
                else:
                    logger.warning("No hex file for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):  # if we want the HFO files in the directories
                            pass
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                        elif(dir_file.endswith(".bin")):
                            pass
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                else:
                    logger.warning("Path does not exist " + str(ev1_path))

            elif(input_repo == Repositories.fabian_monitor):
                if(pj2_file):
                    pass
                    # copyfile(input_path + file, cur_dir + ReleaseType.HFO_ICP2.value + file)
                    # copyfile(input_path + file, cur_dir + ReleaseType.EVO_ICP2.value + file)
                else:
                    logger.warning("No pj2 for for " + str(input_repo))

                if(file):
                    copyfile(input_path + file, cur_dir + ReleaseType.HFO_USB_Package.value + USBPackageHFO.hfo_pic_monitor.value[0] + file[:-4] + USBPackageHFO.hfo_pic_monitor.value[1])
                    copyfile(input_path + file, cur_dir + ReleaseType.EVO_USB_Package.value + USBPackageEVO.evo_pic_monitor.value[0] + file[:-4] + USBPackageEVO.evo_pic_monitor.value[1])
                else:
                    logger.warning("No hex file for " + str(input_repo))

                # Then get the .pm3 and .bin files
                ev1_path = input_path + "ev1\\"
                if(os.path.exists(ev1_path)):
                    for dir_file in os.listdir(ev1_path):
                        if(dir_file.endswith(".pm3")):  # if we want monitor files in the directories
                            pass
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PM3.value + dir_file)
                        elif(dir_file.endswith(".bin")):
                            pass
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.HFO_PM3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PICKit3.value + dir_file)
                            # copyfile(ev1_path + dir_file, cur_dir + ReleaseType.EVO_PM3.value + dir_file)
                else:
                    logger.warning("Path does not exist " + str(ev1_path))
            else:
                logger.warning("This repository should not be enetring here! " + str(input_repo))
        else:
            logger.warning("This input path does not exist! " + str(input_path))

    def _release_package_update_languages(self):
        """
        NOTE: this will move the language files from the gui directory and put them into the release package LANGUAGES
        directory and save them there.
        :param:
        :return:
        """
        cur_dir = os.getcwd()

        package_lang_dir = cur_dir + "\\fabian-gui\\LanguagesFabian\\"

        hfo_release_lang_dir = cur_dir + ReleaseType.HFO_USB_Package.value + "LANGUAGE//"
        evo_release_lang_dir = cur_dir + ReleaseType.EVO_USB_Package.value + "LANGUAGE//"

        if(os.path.exists(hfo_release_lang_dir)):  # If the language folder exists in the release package HFO
            if(os.path.exists(package_lang_dir) and (gui_version[HFO_INDEX] != None)):  # Check that the path exists and that we want to move it over
                # First we need to delete all the current files in the release package directory
                for file_lang_release in os.listdir(hfo_release_lang_dir):
                    os.remove(hfo_release_lang_dir + file_lang_release)
                # Second we need to move all the .bmp and .lang files from the fabian-gui//LanguagesFabian// to release
                for file_lang_package in os.listdir(package_lang_dir):
                    if(file_lang_package.endswith(".bmp") or file_lang_package.endswith(".lang")):
                        copyfile(package_lang_dir + file_lang_package, hfo_release_lang_dir + file_lang_package)
            else:
                logger.warning("Path does not exist " + str(package_lang_dir))
        else:
            logger.warning("Path does not exist " + str(hfo_lang_dir))

        if(os.path.exists(evo_release_lang_dir)):  # If the language folder exists in the release package EVO
            if(os.path.exists(package_lang_dir) and (gui_version[EVO_INDEX] != None)):  # Check that the path exists and that we want to move it over
                # First we need to delete all the current files in the release package directory
                for file_lang_release in os.listdir(evo_release_lang_dir):
                    os.remove(evo_release_lang_dir + file_lang_release)
                # Second we need to move all the .bmp and .lang files from the fabian-gui//LanguagesFabian// to release
                for file_lang_package in os.listdir(package_lang_dir):
                    if(file_lang_package.endswith(".bmp") or file_lang_package.endswith(".lang")):
                        copyfile(package_lang_dir + file_lang_package, evo_release_lang_dir + file_lang_package)
            else:
                logger.warning("Path does not exist " + str(package_lang_dir))
        else:
            logger.warning("Path does not exist " + str(evo_lang_dir))

    def git_commit_push(self):  # This may not be implemented
        pass


# This is the configuration file functions for reading in the .ini file
def config_parser_ini(input_ini):
    """
    NOTE: the config parser functions are reliant on changing the class above as well as the gui_version global variable
    This takes in the input .ini file and then parses it for the correct versions numbers and checks them as well
    :param input_ini:
    :return:
    """
    dir_list = os.listdir(os.getcwd())
    if(input_ini in dir_list):
        config = configparser.ConfigParser()
        config.read(input_ini)

        try:
            gui_version_check = ast.literal_eval(config['DEFAULT']['gui_version'])
        except SyntaxError as err:
            logger.warning("Invalid Syntax Error: " + str(config['DEFAULT']['gui_version']))
            sys.exit()
        pic_monitor_bootloader_version_check = config['DEFAULT']['pic_monitor_bootloader_version'] if config['DEFAULT']['pic_monitor_bootloader_version'] != "None" else None
        pic_monitor_version_check = config['DEFAULT']['pic_monitor_version'] if config['DEFAULT']['pic_monitor_version'] != "None" else None
        pic_power_version_check = config['DEFAULT']['pic_power_version'] if config['DEFAULT']['pic_power_version'] != "None" else None
        pic_power_evo_version_check = config['DEFAULT']['pic_power_evo_version'] if config['DEFAULT']['pic_power_evo_version'] != "None" else None
        try:
            pic_controller_bootloader_version_check = ast.literal_eval(config['DEFAULT']['pic_controller_bootloader_version'])
        except SyntaxError as err:
            logger.warning("Invalid Syntax Error: " + str(config['DEFAULT']['gui_version']))
            sys.exit()
        pic_controller_version_check = config['DEFAULT']['pic_controller_version'] if config['DEFAULT']['pic_controller_version'] != "None" else None
        pic_alarm_bootloader_version_check = config['DEFAULT']['pic_alarm_bootloader_version'] if config['DEFAULT']['pic_alarm_bootloader_version'] != "None" else None
        try:
            pic_alarm_version_check = ast.literal_eval(config['DEFAULT']['pic_alarm_version'])
        except SyntaxError as err:
            logger.warning("Invalid Syntax Error: " + str(config['DEFAULT']['gui_version']))
            sys.exit()
        pic_blender_version_check = config['DEFAULT']['pic_blender_version'] if config['DEFAULT']['pic_blender_version'] != "None" else None
        pic_hfo_version_check = config['DEFAULT']['pic_hfo_version'] if config['DEFAULT']['pic_hfo_version'] != "None" else None
        pic_hfo_bootloader_version_check = config['DEFAULT']['pic_hfo_bootloader_version'] if config['DEFAULT']['pic_hfo_bootloader_version'] != "None" else None

        # This will update the version for the gui
        global gui_version
        if((gui_version_check[0] != None) or (gui_version_check[1] != None)):
            gui_version = check_version(gui_version_check, Repositories.fabian_gui)
        if(pic_monitor_bootloader_version_check  != None):
            FabianPICFiles.fabian_monitor_bootloader.value[1] = check_version(pic_monitor_bootloader_version_check, Repositories.fabian_monitor_bootloader)
        if(pic_monitor_version_check  != None):
            FabianPICFiles.fabian_monitor.value[1] = check_version(pic_monitor_version_check, Repositories.fabian_monitor)
        if(pic_power_version_check  != None):
            FabianPICFiles.fabian_power.value[1] = check_version(pic_power_version_check, Repositories.fabian_power)
        if(pic_power_evo_version_check  != None):
            FabianPICFiles.fabian_power_evo.value[1] = check_version(pic_power_evo_version_check, Repositories.fabian_power_evo)

        if((pic_controller_bootloader_version_check[0] != None) or (pic_controller_bootloader_version_check[1] != None) or (pic_controller_bootloader_version_check[2] != None)):
            ctrl_bl_v = check_version(pic_controller_bootloader_version_check, Repositories.fabian_controller_bootloader)
            FabianPICFiles.fabian_controller_bootloader.value[1] = ctrl_bl_v[0]
            FabianPICFiles.fabian_controller_bootloader.value[3] = ctrl_bl_v[1]
            FabianPICFiles.fabian_controller_bootloader.value[5] = ctrl_bl_v[2]

        if(pic_controller_version_check  != None):
            FabianPICFiles.fabian_controller.value[1] = check_version(pic_controller_version_check, Repositories.fabian_controller)
        if(pic_alarm_bootloader_version_check  != None):
            FabianPICFiles.fabian_alarm_bootloader.value[1] = check_version(pic_alarm_bootloader_version_check, Repositories.fabian_alarm_bootloader)

        if((pic_alarm_version_check[0] != None) or (pic_alarm_version_check[1] != None)):
            alarm_pic_v = check_version(pic_alarm_version_check, Repositories.fabian_alarm)
            FabianPICFiles.fabian_alarm.value[1] = alarm_pic_v[0]
            FabianPICFiles.fabian_alarm.value[3] = alarm_pic_v[1]

        if(pic_blender_version_check  != None):
            FabianPICFiles.fabian_blender.value[1] = check_version(pic_blender_version_check, Repositories.fabian_blender)
        if(pic_hfo_version_check  != None):
            FabianPICFiles.fabian_HFO.value[1] = check_version(pic_hfo_version_check, Repositories.fabian_HFO)
        if(pic_hfo_bootloader_version_check  != None):
            FabianPICFiles.fabian_HFO_bootloader.value[1] = check_version(pic_hfo_bootloader_version_check, Repositories.fabian_HFO_bootloader)

        # This will go through and check the hash for buildable repositories
        gui_hash = config['HASH']['gui_hash'] if config['HASH']['gui_hash'] != "None" else None
        pic_monitor_bootloader_hash = config['HASH']['pic_monitor_bootloader_hash'] if config['HASH']['pic_monitor_bootloader_hash'] != "None" else None
        pic_monitor_hash = config['HASH']['pic_monitor_hash'] if config['HASH']['pic_monitor_hash'] != "None" else None
        pic_power_hash = config['HASH']['pic_power_hash'] if config['HASH']['pic_power_hash'] != "None" else None
        pic_power_evo_hash = config['HASH']['pic_power_evo_hash'] if config['HASH']['pic_power_evo_hash'] != "None" else None
        pic_controller_bootloader_hash = config['HASH']['pic_controller_bootloader_hash'] if config['HASH']['pic_controller_bootloader_hash'] != "None" else None
        pic_controller_hash = config['HASH']['pic_controller_hash'] if config['HASH']['pic_controller_hash'] != "None" else None
        pic_alarm_bootloader_hash = config['HASH']['pic_alarm_bootloader_hash'] if config['HASH']['pic_alarm_bootloader_hash'] != "None" else None
        pic_alarm_hash = config['HASH']['pic_alarm_hash'] if config['HASH']['pic_alarm_hash'] != "None" else None
        pic_blender_hash = config['HASH']['pic_blender_hash'] if config['HASH']['pic_blender_hash'] != "None" else None
        pic_hfo_hash = config['HASH']['pic_hfo_hash'] if config['HASH']['pic_hfo_hash'] != "None" else None
        pic_hfo_bootloader_hash = config['HASH']['pic_hfo_bootloader_hash'] if config['HASH']['pic_hfo_bootloader_hash'] != "None" else None

        CheckoutHash.fabian_gui_hash.value[0] = gui_hash
        CheckoutHash.fabian_monitor_bootloader_hash.value[0] = pic_monitor_bootloader_hash
        CheckoutHash.fabian_monitor_hash.value[0] = pic_monitor_hash
        CheckoutHash.fabian_power_hash.value[0] = pic_power_hash
        CheckoutHash.fabian_power_evo_hash.value[0] = pic_power_evo_hash
        CheckoutHash.fabian_controller_bootloader_hash.value[0] = pic_controller_bootloader_hash
        CheckoutHash.fabian_controller_hash.value[0] = pic_controller_hash
        CheckoutHash.fabian_alarm_bootloader_hash.value[0] = pic_alarm_bootloader_hash
        CheckoutHash.fabian_alarm_hash.value[0] = pic_alarm_hash
        CheckoutHash.fabian_blender_hash.value[0] = pic_blender_hash
        CheckoutHash.fabian_HFO_hash.value[0] = pic_hfo_hash
        CheckoutHash.fabian_HFO_bootloader_hash.value[0] = pic_hfo_bootloader_hash

        # This will go through and check the hash for non-buildable repositories
        release_package_hash = config['NONBUILDABLE_HASH']['release_package_hash'] if config['NONBUILDABLE_HASH']['release_package_hash'] != "None" else None

        NonBuildableCheckoutHash.fabian_release_package_hash.value[0] = release_package_hash

        # If the gui_hash is using another release package, specify the release package

        # This will go through and check if the repository is wanted from the INI
        gui_repo = True if config['REPOSITORY']['gui_repo'] == "True" else False
        pic_monitor_bootloader_repo = True if config['REPOSITORY']['pic_monitor_bootloader_repo'] == "True" else False
        pic_monitor_repo = True if config['REPOSITORY']['pic_monitor_repo'] == "True" else False
        pic_power_repo = True if config['REPOSITORY']['pic_power_repo'] == "True" else False
        pic_power_evo_repo = True if config['REPOSITORY']['pic_power_evo_repo'] == "True" else False
        pic_controller_bootloader_repo = True if config['REPOSITORY']['pic_controller_bootloader_repo'] == "True" else False
        pic_controller_repo = True if config['REPOSITORY']['pic_controller_repo'] == "True" else False
        pic_alarm_bootloader_repo = True if config['REPOSITORY']['pic_alarm_bootloader_repo'] == "True" else False
        pic_alarm_repo = True if config['REPOSITORY']['pic_alarm_repo'] == "True" else False
        pic_blender_repo = True if config['REPOSITORY']['pic_blender_repo'] == "True" else False
        pic_hfo_repo = True if config['REPOSITORY']['pic_hfo_repo'] == "True" else False
        pic_hfo_bootloader_repo = True if config['REPOSITORY']['pic_hfo_bootloader_repo'] == "True" else False

        Repositories.fabian_gui.value[0] = Repositories.fabian_gui.value[0] if gui_repo is True else None
        Repositories.fabian_monitor_bootloader.value[0] = Repositories.fabian_monitor_bootloader.value[0] if pic_monitor_bootloader_repo is True else None
        Repositories.fabian_monitor.value[0] = Repositories.fabian_monitor.value[0] if pic_monitor_repo is True else None
        Repositories.fabian_power.value[0] = Repositories.fabian_power.value[0] if pic_power_repo is True else None
        Repositories.fabian_power_evo.value[0] = Repositories.fabian_power_evo.value[0] if pic_power_evo_repo is True else None
        Repositories.fabian_controller_bootloader.value[0] = Repositories.fabian_controller_bootloader.value[0] if pic_controller_bootloader_repo is True else None
        Repositories.fabian_controller.value[0] = Repositories.fabian_controller.value[0] if pic_controller_repo is True else None
        Repositories.fabian_alarm_bootloader.value[0] = Repositories.fabian_alarm_bootloader.value[0] if pic_alarm_bootloader_repo is True else None
        Repositories.fabian_alarm.value[0] = Repositories.fabian_alarm.value[0] if pic_alarm_repo is True else None
        Repositories.fabian_blender.value[0] = Repositories.fabian_blender.value[0] if pic_blender_repo is True else None
        Repositories.fabian_HFO.value[0] = Repositories.fabian_HFO.value[0] if pic_hfo_repo is True else None
        Repositories.fabian_HFO_bootloader.value[0] = Repositories.fabian_HFO_bootloader.value[0] if pic_hfo_bootloader_repo is True else None


        global gui_builds
        gui_builds[0] = True if config['GUI']['hfo'] == "True" else False
        gui_builds[1] = True if config['GUI']['evo'] == "True" else False
    else:
        logger.warning("INI file does not exists in current working directory! " + str(input_ini))
        # print("INI file does not exist!")


# This is the version checker for the config parser ini function
def check_version(input_version, input_repository):
    """
    This checks that the versions match up with the corresponding PIC code starting at 2/27/2019
    :param input_version:
    :param input_repository:
    :return:
    """
    if(input_repository == Repositories.fabian_gui):
        return_vals = True
        for version in input_version:
            if(version != None):
                if((version[1] != ".") or (version[3] != ".") or (version[5] != ".")):
                    logger.warning("Incorrect version: " + str(input_repository) + " " + version)
                    return_vals = False
                if((version[0].isalpha()) or (version[2].isalpha()) or (version[4].isalpha()) or (version[6:].isalpha())):
                    logger.warning("Incorrect version: " + str(input_repository) + " " + version)
                    return_vals = False
        if(return_vals == False):
            return [None, None]
    elif(input_repository == Repositories.fabian_monitor_bootloader):
        if(input_version.isalpha()):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_monitor):
        if((input_version[1] != ".") or (input_version[3] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isalpha()) or (input_version[2].isalpha()) or (input_version[4].isalpha()) ):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_power):
        if((input_version[1] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isalpha()) or (input_version[2].isalpha())):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_power_evo):
        if((input_version[1] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isalpha()) or (input_version[2].isalpha())):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_controller_bootloader):
        return_vals = True
        for version in input_version:
            if(version != None):
                if((version[0].isdigit()) or (version[1] != ".") or (version[2:].isalpha())):
                    return_vals = False
        if(return_vals == False):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return [None, None, None]
    elif(input_repository == Repositories.fabian_controller):
        if((input_version[1] != ".") or (input_version[3] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isalpha()) or (input_version[2].isalpha()) or (input_version[4:].isalpha())):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_alarm_bootloader):
        if(input_version.isalpha()):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_alarm):
        return_vals = True
        for version in input_version:
            if(version != None):
                if((version[0].isalpha()) or (version[1] != ".") or (version[2:].isalpha())):
                    return_vals = False
        if(return_vals == False):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return [None, None]

    elif(input_repository == Repositories.fabian_blender):
        if((input_version[1] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isalpha()) or (input_version[2].isalpha())):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_HFO):
        if((input_version[1] != ".") or  (input_version[3] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isalpha()) or (input_version[2].isalpha()) or (input_version[4].isalpha())):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    elif(input_repository == Repositories.fabian_HFO_bootloader):
        if((input_version[1] != ".")):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
        if((input_version[0].isdigit()) or (input_version[2:].isalpha())):
            logger.warning("Incorrect version: " + str(input_repository) + " " + input_version)
            return None
    else:  # This is not a repository we support
        logger.warning("No Repository of this type: " + str(input_repository) + " " + input_version)
        return None

    return input_version


# TODO May want to change magic numbers of 1s, 2s, and -1s later on

def main():
    logger.info("Running INI")
    config_parser_ini("automate.ini")
    logger.info("Automation Start:")
    automate_process = AutomateBuild()
    automate_process.automate()


if __name__ == "__main__":
    main()
