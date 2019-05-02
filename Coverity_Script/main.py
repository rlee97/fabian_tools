import os
import git
import sys
from enum import Enum
from time import time
import logging
import configparser
from subprocess import check_output, CalledProcessError
from time import sleep

# Configuring the logger this will be used as a global over the whole program
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="coverity_analysis.log", level=logging.DEBUG, format=LOG_FORMAT, filemode='w')
logger = logging.getLogger()

# Username, password
login_credentials = [None, None]

# Function to get time duration of process
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


# The repository
class Repositories(Enum):
    fabian_gui = ["https://github.com/vyaire/fabian-gui.git"]
    fabian_monitor_bootloader = ["https://github.com/vyaire/fabian-monitor_bootloader.git"]
    fabian_monitor = ["https://github.com/vyaire/fabian-monitor.git"]
    fabian_power = ["https://github.com/vyaire/fabian-power.git"]
    fabian_power_evo = ["https://github.com/vyaire/fabian-power-evo.git"]
    fabian_controller_bootloader = ["https://github.com/vyaire/fabian-controller_bootloader.git"]
    fabian_controller = ["https://github.com/vyaire/fabian-controller.git"]
    fabian_alarm_bootloader = ["https://github.com/vyaire/fabian-alarm_bootloader.git"]
    fabian_alarm = ["https://github.com/vyaire/fabian-alarm.git"]
    fabian_blender = ["https://github.com/vyaire/fabian-blender.git"]
    fabian_hfo = ["https://github.com/vyaire/fabian-hfo.git"]
    fabian_hfo_bootloader = ["https://github.com/vyaire/fabian-hfo_bootloader.git"]


# True|False, File path, Repository, Commit SHA, Version number
CS_COMMIT_STREAM = 0
CS_FILE_PATH = 1
CS_REPOSITORY = 2
CS_STREAM = 3
CS_BUILD = 4
CS_COMMIT_SHA = -2
CS_VERSION_NUM = -1

class CoverityStreams(Enum):
    fabian_gui_hfo_release = ["temp_0", "\\fabian-gui\\FabianHFO\\MVModel.cpp", "\\fabian-gui", "fabian-gui-hfo-master", "build-hfo.cmd", None, None]
    fabian_gui_evo_release = ["temp_1", "\\fabian-gui\\FabianEvo\\MVModel.cpp", "\\fabian-gui", "fabian-gui-evo-master", "build-evo.cmd", None, None]
    fabian_alarm_pic_v4 = ["temp_2", "\\fabian-alarm\\AlarmPIC_Fabian_V4.X\\src\\application\\common.h", "\\fabian-alarm", "fabian-alarm-pic-v4", "build_v4.cmd", None, None]
    fabian_alarm_pic_v5 = ["temp_3", "\\fabian-alarm\\AlarmPIC_Fabian_V5.X\\src\\application\\common.h", "\\fabian-alarm", "fabian-alarm-pic-v5", "build_v5.cmd", None, None]
    fabian_blender_pic = ["temp_4", "\\fabian-blender\\Blender.X\\Src\\common.h", "\\fabian-blender", "fabian-blender-pic", "build.cmd", None, None]
    fabian_controller_pic_evo_2520 = ["temp_5", "\\fabian-controller\\src\\Define.h", "\\fabian-controller", "fabian-controller-pic-evo-2520", "buildEvo_2520.cmd", None, None]
    fabian_controller_pic_hfo_2520 = ["temp_6", "\\fabian-controller\\src\\Define.h", "\\fabian-controller", "fabian-controller-pic-hfo-2520", "buildHFO_2520.cmd", None, None]
    fabian_controller_pic_evo_26k80 = ["temp_7", "\\fabian-controller\\src\\Define.h", "\\fabian-controller", "fabian-controller-pic-evo-26k80", "buildEvo_26k80", None, None]
    fabian_controller_pic_hfo_46k80 = ["temp_8", "\\fabian-controller\\src\\Define.h", "\\fabian-controller", "fabian-controller-pic-hfo-46k80", "buildHFO_46k80", None, None]
    fabian_hfo_pic = ["temp_9", "\\fabian-hfo\\src\\Define.h", "\\fabian-hfo", "fabian-hfo-pic", "build.cmd", None, None]
    fabian_monitor_pic = ["temp_10", "\\fabian-monitor\\SRC\\common.h", "\\fabian-monitor", "fabian-monitor-pic", "build.cmd", None, None]
    fabian_power_pic_hfo_hw1 = ["temp_11", "\\fabian-power\\Akku_4.C", "\\fabian-power", "fabian-power-pic-hfo-hw1", "buildHW1.cmd", None, None]
    fabian_power_pic_hfo_hw2 = ["temp_12", "\\fabian-power\\Akku_4.C", "\\fabian-power", "fabian-power-pic-hfo-hw2", "buildHW2.cmd", None, None]
    fabian_power_pic_hfo_hw3 = ["temp_13", "\\fabian-power\\Akku_4.C", "\\fabian-power", "fabian-power-pic-hfo-hw3", "buildHW3.cmd", None, None]
    fabian_power_pic_evo_hw1 = ["temp_14", "\\fabian-power-evo\\src\\Akku_5.C", "\\fabian-power-evo", "fabian-power-pic-evo-hw1", "buildHW1.cmd", None, None]
    fabian_power_pic_evo_hw2 = ["temp_15", "\\fabian-power-evo\\src\\Akku_5.C", "\\fabian-power-evo", "fabian-power-pic-evo-hw2", "buildHW2.cmd", None, None]
    fabian_power_pic_evo_hw3 = ["temp_16", "\\fabian-power-evo\\src\\Akku_5.C", "\\fabian-power-evo", "fabian-power-pic-evo-hw3", "buildHW3.cmd",  None, None]
    fabian_alarm_pic_bootloader = ["temp_17", "\\fabian-alarm_bootloader\\AlarmPIC_Fabian_UART_loader.X\\common.h", "\\fabian-alarm_bootloader", "fabian-alarm-pic-bootloader", "build.cmd", None, None]
    fabian_controller_pic_bootloader_pre_ed4 = ["temp_18", "\\fabian-controller_bootloader\\Ctrl_Bootloader.X\\bootldr_neo.c", "\\fabian-controller_bootloader", "fabian-controller-pic-bootloader-pre-ed4", "build_pre_ed4.cmd", None, None]
    fabian_controller_pic_bootloader_hfo_ed4 = ["temp_19", "\\fabian-controller_bootloader\\Ctrl_Bootloader_ed4.X\\bootldr_neo.c", "\\fabian-controller_bootloader", "fabian-controller-pic-bootloader-hfo-ed4", "build_ed4.cmd", None, None]
    fabian_controller_pic_bootloader_evo_ed4 = ["temp_20", "\\fabian-controller_bootloader\\Ctrl_Bootloader_EVO_ed4.X\\bootldr_neo.c", "\\fabian-controller_bootloader", "fabian-controller-pic-bootloader-evo-ed4", "build_ed4-EVO.cmd", None, None]
    fabian_monitor_pic_bootloader = ["temp_21", "\\fabian-monitor_bootloader\\Neo_mon Bootloader UART.X\\main_debug.c", "\\fabian-monitor_bootloader", "fabian-monitor-pic-bootloader", "build.cmd", None, None]
    fabian_hfo_pic_bootloader = ["temp_22", "\\fabian-hfo_bootloader\\bootldr_HF_Mod.c", "\\fabian-hfo_bootloader", "fabian-hfo-pic-bootloader", "build.cmd", None, None]


# Intialize coverity static analysis settings
class CoverityInitialize(Enum):
    configure_msvc = "cov-configure.exe --msvc"
    configure_xc8 = "cov-configure.exe --comptype picc --compiler=xc8.exe --template"
    configure_xc16 = "cov-configure.exe --comptype picc --compiler=xc16-gcc --template"


# This will grab the current repositories and then do an analysis check on them
class AutomateStaticAnalysis:

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

        # This will clone all the necessary repositories associated in the Repositories class
        logger.info("Cloning Repositories")
        for repository in Repositories:
            self.clone_repositories(None, repository)

        # Does the initialization for the coverity static analysis
        logger.info("Setting up coverity static analysis")
        self.initialize_coverity_analysis()

        # Goes through each coverity stream and then does the analysis on each of them
        logger.info("Running Coverity Analysis of Repositories")
        for stream in CoverityStreams:
            if stream[0] == True: # If we want to do analysis on the coverity stream
                # This will get the version number and place it into the Coverity Streams Enum Class
                if stream == CoverityStreams.fabian_gui_hfo_release:
                    self.check_file_versions_gui(stream[CS_FILE_PATH])
                elif stream == CoverityStreams.fabian_gui_evo_release:
                    self.check_file_versions_gui(stream[CS_FILE_PATH])
                else:
                    self.check_file_versions_pic(stream[CS_FILE_PATH], stream)

                # Go into directory and get the commit sha
                self.get_commit_sha(stream, stream[CS_REPOSITORY])

                # Start running the coverity static analysis for each repository
                self.coverity_static_analysis(stream)

        # Finished
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

    def clone_repositories(self, input_your_directory, input_dir):
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

    def check_file_versions_gui(self, input_file_path):
        """
        This function will grab the current gui version number for hfo and evo
        :param input_file_path:
        :return:
        """

        cf_cwd = os.getcwd()

        skip = 0
        if (os.path.exists(cf_cwd + input_file_path)):
            file = open(cf_cwd + input_file_path, "r")

            find_string = "m_szBuildVersion = _T("

            for line in file:
                if (skip == 0):
                    if (line.find("MEDKOM_VERSION") != -1):
                        skip = 3
                    index = line.find(find_string)
                    if (index != -1):
                        new_index = line.find(")")
                        if ("HFO" in input_file_path):
                            CoverityStreams.fabian_gui_hfo_release.value[CS_VERSION_NUM] = line[index + len(find_string):new_index]
                        else:
                            CoverityStreams.fabian_gui_evo_release.value[CS_VERSION_NUM] = line[index + len(find_string):new_index]
                if (skip > 0):
                    skip -= 1
        else:
            logger.warning("Check Version GUI :: Path does not exist! " + str(cf_cwd + input_file_path))

    # TODO change this to fit for coverity streams instead
    def check_file_versions_pic(self, input_file_path, input_file):
        cur_dir = os.getcwd()
        cur_dir += input_file_path

        if (os.path.exists(cur_dir)):
            # Write to the correct version line
            if (input_file == CoverityStreams.fabian_monitor_pic_bootloader):
                string_search = ["#define VERSION"]
                CoverityStreams.fabian_monitor_pic_bootloader.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_monitor_pic):
                string_search = ["#define", "Vers_hi", "Vers_mid", "Vers_lo"]
                CoverityStreams.fabian_monitor_pic.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_power_pic_hfo_hw1):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                CoverityStreams.fabian_power_pic_hfo_hw1.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_power_pic_hfo_hw2):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                CoverityStreams.fabian_power_pic_hfo_hw2.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_power_pic_hfo_hw3):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                CoverityStreams.fabian_power_pic_hfo_hw3.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_power_pic_evo_hw1):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                CoverityStreams.fabian_power_pic_evo_hw1.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_power_pic_evo_hw2):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                CoverityStreams.fabian_power_pic_evo_hw2.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_power_pic_evo_hw3):
                string_search = ["#define VERS_BASE_HIGH", "#define VERS_BASE_LOW"]
                CoverityStreams.fabian_power_pic_evo_hw3.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_bootloader_pre_ed4):
                string_search = ["#define", "Vers_hi", "Vers_lo"]
                CoverityStreams.fabian_controller_pic_bootloader_pre_ed4.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_bootloader_hfo_ed4):
                string_search = ["#define", "Vers_hi", "Vers_lo"]
                CoverityStreams.fabian_controller_pic_bootloader_hfo_ed4.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_bootloader_evo_ed4):
                string_search = ["#define", "Vers_hi", "Vers_lo"]
                CoverityStreams.fabian_controller_pic_bootloader_evo_ed4.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_evo_2520):
                string_search = ["#define", "VERS_0", "VERS_1", "VERS_2", "VERS_3", "VERS_4", "VERS_5"]
                CoverityStreams.fabian_controller_pic_evo_2520.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_hfo_2520):
                string_search = ["#define", "VERS_0", "VERS_1", "VERS_2", "VERS_3", "VERS_4", "VERS_5"]
                CoverityStreams.fabian_controller_pic_hfo_2520.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_evo_26k80):
                string_search = ["#define", "VERS_0", "VERS_1", "VERS_2", "VERS_3", "VERS_4", "VERS_5"]
                CoverityStreams.fabian_controller_pic_evo_26k80.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_controller_pic_hfo_46k80):
                string_search = ["#define", "VERS_0", "VERS_1", "VERS_2", "VERS_3", "VERS_4", "VERS_5"]
                CoverityStreams.fabian_controller_pic_hfo_46k80.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_alarm_pic_v4):
                string_search = ["#define VERSION_HI", "#define VERSION_LO"]
                CoverityStreams.fabian_alarm_pic_v4.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_alarm_pic_v5):
                string_search = ["#define VERSION"]
                CoverityStreams.fabian_alarm_pic_v5.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_alarm_pic_bootloader):
                string_search = ["#define VERSION"]
                CoverityStreams.fabian_alarm_pic_bootloader.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_blender_pic):
                string_search = ["#define VERSION_HI", "#define VERSION_LO"]
                CoverityStreams.fabian_blender_pic.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_hfo_pic):
                string_search = ["#define", "Vers_0", "Vers_1", "Vers_2", "Vers_3", "Vers_4"]
                CoverityStreams.fabian_hfo_pic.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            elif (input_file == CoverityStreams.fabian_hfo_pic_bootloader):
                string_search = ["#define Vers_hi", "#define Vers_lo"]
                CoverityStreams.fabian_hfo_pic_bootloader.value[CS_VERSION_NUM] = self._check_file_versions_pic(cur_dir, string_search, input_file)
            else:
                # print("Input file does not exists in the PIC repositories! ", input_file)
                logger.warning("Check Version PIC :: Input file does not exists in the PIC repositories! " + str(input_file))
        else:
            # print("File does not exist! ", cur_dir)
            logger.warning("Check Version PIC :: File does not exist! " + str(cur_dir))

    def _check_file_versions_pic(self, input_file_path, input_string_search, input_file):
        if ((input_file == CoverityStreams.fabian_monitor_pic) or (input_file == CoverityStreams.fabian_controller_pic_bootloader_pre_ed4)
            or (input_file == CoverityStreams.fabian_controller_pic_bootloader_hfo_ed4) or (input_file == CoverityStreams.fabian_controller_pic_bootloader_evo_ed4)
                or (input_file == CoverityStreams.fabian_controller_pic_evo_2520) or (input_file == CoverityStreams.fabian_controller_pic_hfo_2520)
                or (input_file == CoverityStreams.fabian_controller_pic_evo_26k80) or (input_file == CoverityStreams.fabian_controller_pic_hfo_46k80)
                or (input_file == CoverityStreams.fabian_hfo_pic_bootloader)):

            length = len(input_string_search)

            version_number = [""] * (length - 1)

            file = open(input_file_path, "r")

            for line in file:
                for i in range(1, len(input_string_search)):
                    found_string, string_search_index = input_string_search[i], i - 1
                    index_define = line.find(input_string_search[0])
                    index = line.find(input_string_search[i])

                    if ((index_define != -1) and (index != -1)):
                        break

                if ((index_define != -1) and (index != -1)):
                    if (string_search_index != length - 2):
                        version_number[string_search_index] = str(line[index + len(input_string_search[i]):])
                    else:
                        version_number[string_search_index] = str(line[index + len(input_string_search[i]):])

            file.close()
            new_version_number = self._check_file_versions_pic_helper(version_number, input_file)
            return "".join(new_version_number)

        else:
            length = len(input_string_search)

            version_number = [""] * length

            file = open(input_file_path, "r")

            for line in file:
                for i in range(0, len(input_string_search)):
                    found_string, string_search_index = input_string_search[i], i
                    index = line.find(input_string_search[i])
                    if (index != -1):
                        break

                if (index != -1):
                    if (string_search_index != length - 1):
                        version_number[string_search_index] = str(line[index + len(input_string_search[i]):]) + "."
                    else:
                        version_number[string_search_index] = str(line[index + len(input_string_search[i]):])

            file.close()
            new_version_number = self._check_file_versions_pic_helper(version_number, input_file)
            return "".join(new_version_number)

    def _check_file_versions_pic_helper(self, input_version_number, input_file):
        for i in range(0, len(input_version_number)):
            input_version_number[i] = input_version_number[i].replace("\t", "")
            input_version_number[i] = input_version_number[i].replace("\n", "")
            input_version_number[i] = input_version_number[i].replace(" ", "")
            input_version_number[i] = input_version_number[i].replace("/", "")
            input_version_number[i] = input_version_number[i].replace(".", "")
            input_version_number[i] = input_version_number[i].replace("'", "")
            input_version_number[i] = input_version_number[i].replace('"', "")

            if (input_version_number[i] == ''):
                input_version_number[i] = "."

            index = input_version_number[i].find("*")
            if (index != -1):
                input_version_number[i] = input_version_number[i][:index]

            if ((input_file == CoverityStreams.fabian_monitor_pic)):
                if (i == 0):
                    input_version_number[i] = input_version_number[i][:1]

            if (input_file == CoverityStreams.fabian_alarm_pic_v5):
                input_version_number[i] = input_version_number[i][0] + "." + input_version_number[i][1:]

            if ((input_file != CoverityStreams.fabian_controller_pic_evo_2520) and (input_file != CoverityStreams.fabian_controller_pic_hfo_2520)
                and (input_file != CoverityStreams.fabian_controller_pic_evo_26k80) and (input_file != CoverityStreams.fabian_controller_pic_hfo_46k80)
                and (input_file != CoverityStreams.fabian_hfo_pic)):
                if (i != len(input_version_number) - 1):
                    input_version_number[i] = input_version_number[i] + "."

        return input_version_number

    # Commit sha from repository
    def get_commit_sha(self, input_stream, input_path):
        cur_dir = os.getcwd()
        input_stream.value[CS_COMMIT_SHA] = str(git.Repo(cur_dir+input_path, search_parent_directories=True).head.object.hexsha)[:8]

    # Initializes the coverity static analysis setup items
    def initialize_coverity_analysis(self):
        for setup in CoverityInitialize:
            return_value = os.system(setup.value)
            if(return_value == 1):
                logger.warning("Command Error: " + str(setup.value))

    # Does the main commands for the static analysis
    def coverity_static_analysis(self, input_stream):
        '''cov-build.exe --dir {path to directory, ex: cov} {path to build command here, ex: build.cmd}'''
        '''cov-analyze.exe --dir {path to directory, ex: cov} --all --enable-constraint-fpp'''
        '''cov-commit-defects.exe --dir {path to directory, ex: cov} --stream {stream to enter, ex: fabian-alarm-pic-bootloader}
            --host coverity-rsp --user {username, ex: firstname.lastname} --password {password, ex: caretrees}
            --description {"Put description with version number and commit sha", ex: "5.1.0.10 1992499"}'''

        cur_dir = os.getcwd()

        command_build = "cov-build.exe --dir cov " + input_stream[CS_BUILD]
        command_analyze = "cov-analyze.exe --dir cov --all --enable-constraint-fpp"
        command_commit = "cov-commit-defects.exe --dir cov --stream " + input_stream[CS_STREAM] + " --host coverity-rsp" \
                         " --user " + login_credentials[0] + " --password " + login_credentials[1] + \
                         " --description " + input_stream[CS_VERSION_NUM] + " " + input_stream[CS_COMMIT_SHA]

        # Go into the corresponding directory
        os.chdir(cur_dir + input_stream[CS_REPOSITORY])

        return_value = os.system(command_build)
        if return_value == 1:
            logger.warning("Command Error: " + str(command_build))
        return_value = os.system(command_analyze)
        if return_value == 1:
            logger.warning("Command Error: " + str(command_analyze))
        return_value = os.system(command_commit)
        if return_value == 1:
            logger.warning("Command Error: " + str(command_commit))

        # Go back to the original current working directory
        os.chdir(cur_dir)

        # if input_stream == CoverityStreams.fabian_gui_hfo_release:
        #     # Go into directory
        #     # Come back our to cur_dir directory
        # elif input_stream == CoverityStreams.fabian_gui_evo_release:
        #
        # elif input_stream == CoverityStreams.fabian_alarm_pic_v4:
        #
        # elif input_stream == CoverityStreams.fabian_alarm_pic_v5:
        #
        # elif input_stream == CoverityStreams.fabian_blender_pic:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_evo_2520:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_hfo_2520:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_evo_26k80:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_hfo_46k80:
        #
        # elif input_stream == CoverityStreams.fabian_hfo_pic:
        #
        # elif input_stream == CoverityStreams.fabian_monitor_pic:
        #
        # elif input_stream == CoverityStreams.fabian_power_pic_hfo_hw1:
        #
        # elif input_stream == CoverityStreams.fabian_power_pic_hfo_hw2:
        #
        # elif input_stream == CoverityStreams.fabian_power_pic_hfo_hw3:
        #
        # elif input_stream == CoverityStreams.fabian_power_pic_evo_hw1:
        #
        # elif input_stream == CoverityStreams.fabian_power_pic_evo_hw2:
        #
        # elif input_stream == CoverityStreams.fabian_power_pic_evo_hw3:
        #
        # elif input_stream == CoverityStreams.fabian_alarm_pic_bootloader:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_bootloader_pre_ed4:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_bootloader_hfo_ed4:
        #
        # elif input_stream == CoverityStreams.fabian_controller_pic_bootloader_evo_ed4:
        #
        # elif input_stream == CoverityStreams.fabian_monitor_pic_bootloader_bootloader:
        #
        # elif input_stream == CoverityStreams.fabian_hfo_pic_bootloader:
        #
        # else:
        #     logger.warning("This stream does not exist")

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

        hfo = True if config['DEFAULT']['fabian_gui_hfo_release'] == "True" else False
        evo = True if config['DEFAULT']['fabian_gui_evo_release'] == "True" else False
        CoverityStreams.fabian_gui_hfo_release[0] = hfo
        CoverityStreams.fabian_gui_evo_release[0] = evo
        if (hfo or evo) is False: Repositories.fabian_gui[0] = None

        alarm_v4 = True if config['DEFAULT']['fabian_alarm_pic_v4'] == "True" else False
        alarm_v5 = True if config['DEFAULT']['fabian_alarm_pic_v5'] == "True" else False
        CoverityStreams.fabian_alarm_pic_v4[0] = alarm_v4
        CoverityStreams.fabian_alarm_pic_v5[0] = alarm_v5
        if (alarm_v4 or alarm_v5) is False: Repositories.fabian_alarm[0] = None

        blender = True if config['DEFAULT']['fabian_blender_pic'] == "True" else False
        CoverityStreams.fabian_blender_pic[0] = blender
        if blender is False: Repositories.fabian_blender[0] = None

        controller_evo_2520 = True if config['DEFAULT']['fabian_controller_pic_evo_2520'] == "True" else False
        controller_hfo_2520 = True if config['DEFAULT']['fabian_controller_pic_hfo_2520'] == "True" else False
        controller_evo_26k80 = True if config['DEFAULT']['fabian_controller_pic_evo_26k80'] == "True" else False
        controller_hfo_46k80 = True if config['DEFAULT']['fabian_controller_pic_hfo_46k80'] == "True" else False
        CoverityStreams.fabian_controller_pic_evo_2520[0] = controller_evo_2520
        CoverityStreams.fabian_controller_pic_hfo_2520[0] = controller_hfo_2520
        CoverityStreams.fabian_controller_pic_evo_26k80[0] = controller_evo_26k80
        CoverityStreams.fabian_controller_pic_hfo_46k80[0] = controller_hfo_46k80
        if (controller_evo_2520 or controller_hfo_2520 or controller_evo_26k80 or controller_hfo_46k80) is False:
            Repositories.fabian_controller[0] = None

        hfo = True if config['DEFAULT']['fabian_hfo_pic'] == "True" else False
        CoverityStreams.fabian_hfo_pic[0] = hfo
        if hfo is False: Repositories.fabian_hfo[0] = None

        monitor = True if config['DEFAULT']['fabian_monitor_pic'] == "True" else False
        CoverityStreams.fabian_monitor_pic[0] = monitor
        if monitor is False: Repositories.fabian_monitor[0] = None

        power_hfo_hw1 = True if config['DEFAULT']['fabian_power_pic_hfo_hw1'] == "True" else False
        power_hfo_hw2 = True if config['DEFAULT']['fabian_power_pic_hfo_hw2'] == "True" else False
        power_hfo_hw3 = True if config['DEFAULT']['fabian_power_pic_hfo_hw3'] == "True" else False
        CoverityStreams.fabian_power_pic_hfo_hw1[0] = power_hfo_hw1
        CoverityStreams.fabian_power_pic_hfo_hw2[0] = power_hfo_hw2
        CoverityStreams.fabian_power_pic_hfo_hw3[0] = power_hfo_hw3
        if (power_hfo_hw1 or power_hfo_hw2 or power_hfo_hw3) is False: Repositories.fabian_power = None

        power_evo_hw1 = True if config['DEFAULT']['fabian_power_pic_evo_hw1'] == "True" else False
        power_evo_hw2 = True if config['DEFAULT']['fabian_power_pic_evo_hw2'] == "True" else False
        power_evo_hw3 = True if config['DEFAULT']['fabian_power_pic_evo_hw3'] == "True" else False
        CoverityStreams.fabian_power_pic_evo_hw1[0] = power_evo_hw1
        CoverityStreams.fabian_power_pic_evo_hw2[0] = power_evo_hw2
        CoverityStreams.fabian_power_pic_evo_hw3[0] = power_evo_hw3
        if (power_evo_hw1 or power_evo_hw2 or power_evo_hw3) is False: Repositories.fabian_power_evo[0] = None

        alarm_bootloader = True if config['DEFAULT']['fabian_alarm_pic_bootloader'] == "True" else False
        CoverityStreams.fabian_alarm_pic_bootloader[0] = alarm_bootloader
        if alarm_bootloader is False: Repositories.fabian_alarm_bootloader[0] = None

        controller_pre_ed4_bootloader = True if config['DEFAULT']['fabian_controller_pic_bootloader_pre_ed4'] == "True" else False
        controller_hfo_ed4_bootloader = True if config['DEFAULT']['fabian_controller_pic_bootloader_hfo_ed4'] == "True" else False
        controller_evo_ed4_bootloader = True if config['DEFAULT']['fabian_controller_pic_bootloader_evo_ed4'] == "True" else False
        CoverityStreams.fabian_controller_pic_bootloader_pre_ed4[0] = controller_pre_ed4_bootloader
        CoverityStreams.fabian_controller_pic_bootloader_hfo_ed4[0] = controller_hfo_ed4_bootloader
        CoverityStreams.fabian_controller_pic_bootloader_evo_ed4[0] = controller_evo_ed4_bootloader
        if (controller_pre_ed4_bootloader or controller_hfo_ed4_bootloader or controller_evo_ed4_bootloader) is False:
            Repositories.fabian_controller_bootloader[0] = None

        monitor_bootloader = True if config['DEFAULT']['fabian_monitor_pic_bootloader'] == "True" else False
        CoverityStreams.fabian_monitor_pic_bootloader[0] = monitor_bootloader
        if monitor_bootloader is False: Repositories.fabian_monitor_bootloader[0] = None

        hfo_bootloader = True if config['DEFAULT']['fabian_hfo_pic_bootloader'] == "True" else False
        CoverityStreams.fabian_hfo_pic_bootloader[0] = hfo_bootloader
        if hfo_bootloader is False: Repositories.fabian_hfo_bootloader[0] = None

        # Gets the credentials of the username and password
        login_credentials[0] = config['INFO']['username']
        login_credentials[1] = config['INFO']['password']

    else:
        logger.warning("INI file does not exists in current working directory! " + str(input_ini))

# TODO May want to change magic numbers of 1s, 2s, and -1s later on

def main():
    logger.info("Running INI")
    config_parser_ini("coverity_script.ini")
    logger.info("Coverity Script Start:")
    automate_process = AutomateStaticAnalysis()
    automate_process.automate()


if __name__ == "__main__":
    main()
