import os
from pywinauto import application, keyboard, mouse
from time import sleep
import shutil
import fileinput

SLEEP_TIME = 0.1
PAUSE_LENGTH = 0.01


class MIM_Automation:
    def __init__(self, input_app_location):
        self.app = application.Application()
        self.keyboard = keyboard
        self.mouse = mouse
        self.finder = "Checksum:"
        print("Initializing MIM Automation")
        self.app.start(input_app_location + "post_processing_tool.exe")
        print("Ready for MIM to start converting files")

    def convert_files(self, input_mim_file, input_checksum, input_version, input_logger):
        """
        This function will convert the files using the ICP2 and then
        :param input_mim_file:
        :return:
        """
        if((input_mim_file == None) or (input_checksum == None) or (input_version == None)):
            if(input_logger != None):
                input_logger.warning("Failed to convert mim files! " + str(input_mim_file) + str(input_checksum) + str(input_version))
            else:
                print("MIM Automate Failure")
        else:
            # If there us a MIM output directory then delete it and all its contents
            all_files = os.listdir(input_mim_file)
            for file in all_files:
                if(file.find("MIM output") != -1):
                    if(input_logger != None):
                        input_logger.info("Deleting old " + str(file))
                    shutil.rmtree(input_mim_file + file)

            # Modify the memory file with the correct checksum
            mem_settings_path = input_mim_file + "memory_settings.mem"

            for line in fileinput.input(mem_settings_path, inplace=True):
                index = line.find(self.finder)
                if(index != -1):
                    # 3 accounts for the space and the 0x " 0x" in the mem file
                    new_line = line[:index+len(self.finder) + 3] + input_checksum + "\n"
                    print("%s" % new_line, end="")
                else:
                    print("%s" % line, end="")

            for i in range(0, 3):
                self.keyboard.SendKeys("{TAB}")

            self.keyboard.SendKeys("{SPACE}")
            sleep(SLEEP_TIME)
            self.keyboard.SendKeys(mem_settings_path, with_spaces=True, pause=PAUSE_LENGTH)
            self.keyboard.SendKeys("{ENTER}")
            sleep(SLEEP_TIME)

            for i in range(0, 2):
                self.keyboard.SendKeys("{TAB}")

            self.keyboard.SendKeys("{SPACE}")
            # This amount of time is how long it takes to build the corresponding mim files
            sleep(4)

            descent_dir = input_mim_file + "MIM output\\"
            find_dir = os.listdir(descent_dir)
            if(len(find_dir) == 1):
                descent_dir += find_dir[0] + "\\"

            find_file = os.listdir(descent_dir)
            flag = False
            for file in find_file:
                if(file.endswith(".mim")):
                    flag = True
                    os.rename(descent_dir + file, descent_dir + input_version + ".alr")

            if(flag == True):
                return descent_dir + input_version + ".alr"
            else:
                return None

    def close_app(self):
        print("Closing MIM application")
        sleep(SLEEP_TIME)
        os.system("TASKKILL /F /IM post_processing_tool.exe")


def main():
    pass  # TODO this portion was used for testing
    # mim = MIM_Automation("C:\\Users\\garrett.deguchi\\Desktop\\Automate_Release\\Automate_Build\\fabian-alarm\\")
    # mim.convert_files("C:\\Users\\garrett.deguchi\\Desktop\\Automate_Release\\Automate_Build\\fabian-alarm\\", "ABCD", "7.7", None)
    # mim.close_app()


if __name__ == "__main__":
    main()
