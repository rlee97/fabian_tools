import os
from pywinauto import application, keyboard
from time import sleep

SLEEP_TIME = 0.1
PAUSE_LENGTH = 0.01

DEBUG_PAUSE = 0.05

class ICP_Automation:
    def __init__(self):
        self.app = application.Application()
        self.keyboard = keyboard
        print("Initializing ICP Automation")
        self.app.start("C:\\Softlog\\IcpWin\\ICP_Win.exe")
        sleep(1)
        self.keyboard.SendKeys("{ENTER}")
        sleep(13)
        self.keyboard.SendKeys("{ENTER}")
        print("Ready for ICP to start converting files")
        self.first_time = True

    def convert_files(self, input_file, input_pic_type, input_checksum, input_name_type, input_version):
        """
        This function will convert the files using the ICP2 and then
        :param input_file:
        :param input_pic_type:
        :return:
        """
        # These actions will get you through the ICP process
        if(self.first_time == True):
            self.keyboard.SendKeys("{RIGHT}", pause=DEBUG_PAUSE)

        self.keyboard.SendKeys("{F10}", pause=DEBUG_PAUSE)
        for i in range(0, 2):
            self.keyboard.SendKeys("{RIGHT}", pause=DEBUG_PAUSE)
        self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
        for i in range(0, 2):
            self.keyboard.SendKeys("{DOWN}", pause=DEBUG_PAUSE)

        if(self.first_time == True):
            for i in range(0, 2):
                self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
                sleep(SLEEP_TIME)
            for i in range(0, 2):
                self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
            for i in range(0, 3):
                self.keyboard.SendKeys("{DOWN}", pause=DEBUG_PAUSE)
            for i in range(0, 2):
                self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
        else:
            for i in range(0, 3):
                self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
                sleep(SLEEP_TIME)

        for i in range(0, 2):
            self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
        self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)

        self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
        # This is where the correct PIC type needs to be selected
        self.keyboard.SendKeys(input_pic_type, with_spaces=True, pause=PAUSE_LENGTH)
        # self.keyboard.SendKeys(input_pic_type, with_spaces=True)
        self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
        self.keyboard.SendKeys("{RIGHT}", pause=DEBUG_PAUSE)

        if(self.first_time == True):
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
            for i in range(0, 2):
                self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
            self.keyboard.SendKeys("{DOWN}", pause=DEBUG_PAUSE)
            for i in range(0, 10):
                self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
            for i in range(0, 2):
                self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
            self.first_time = False
        else:
            for i in range(0, 3):
                self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
                sleep(SLEEP_TIME)

        # If an error pop up window happens then just press enter and move on
        if(self.app.top_window().window_text() == "ICP for Windows"):
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)

        for i in range(0, 3):
            self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)

        self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
        sleep(SLEEP_TIME)
        self.keyboard.SendKeys(input_file, with_spaces=True, pause=PAUSE_LENGTH)
        # self.keyboard.SendKeys(input_file, with_spaces=True)
        # TODO This portion may be weird as it gives errors on the hex file
        self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)  # Open
        sleep(SLEEP_TIME)
        for i in range(0, 2):
            self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
        for i in range(0, 2):
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)  # Leaving Load HEX File then Load Serialization
            sleep(SLEEP_TIME)
        for i in range(0, 3):
            self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
        self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
        sleep(SLEEP_TIME)

        if((input_name_type == "") or (input_version == "")):
            self.keyboard.SendKeys(input_file[:-4] + "_chk-" + input_checksum + ".pj2", with_spaces=True, pause=PAUSE_LENGTH)  # Save the same as the input file and overwrite
        else:
            index = -1
            while(input_file[index] != "\\"):
                index -= 1

            name_path = input_file[:index]

            if("HW1." in input_file):
                final_name = name_path + "\\" + input_name_type + "hw1.x_v" + input_version + "_chk-" + input_checksum + ".pj2"
            elif("HW2." in input_file):
                final_name = name_path + "\\" + input_name_type + "hw2.x_v" + input_version + "_chk-" + input_checksum + ".pj2"
            elif("HW3." in input_file):
                final_name = name_path + "\\" + input_name_type + "hw3.x_v" + input_version + "_chk-" + input_checksum + ".pj2"
            elif("Neo_mon" in input_file):
                final_name = name_path + "\\" + input_name_type + "rev" + input_version + "_chk-" + input_checksum + ".pj2"
            else:
                final_name = name_path + "\\" + input_name_type + "v" + input_version + "_chk-" + input_checksum + ".pj2"

            self.keyboard.SendKeys(final_name, with_spaces=True, pause=PAUSE_LENGTH)  # Save the same as the input file and overwrite

        for i in range(0, 2):
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)  # Open
            sleep(SLEEP_TIME)
        for i in range(0, 2):
            self.keyboard.SendKeys("{TAB}", pause=DEBUG_PAUSE)
        for i in range(0, 3):
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)  # This portion goes to the finish and finalizes the pj2 files
            sleep(SLEEP_TIME)
        sleep(2)
        if("Environment 1" in self.app.top_window().window_text()):
            self.keyboard.SendKeys("{ENTER}", pause=DEBUG_PAUSE)
        sleep(1)

    def close_app(self):
        print("Closing ICP")
        sleep(SLEEP_TIME)
        os.system("TASKKILL /F /IM ICP_Win.exe")
        self.first_time = True


def main():
    pass
    # TODO this portion was used for testing
    # icp = ICP_Automation()
    # icp.convert_files("C:\\Users\\garrett.deguchi\\Desktop\\TEST\\fabian-blender\\Blender.X\\dist\\default\\production\\Blender.X.production.hex", "dsPIC33FJ128GP706A")
    # icp.convert_files("C:\\Users\\garrett.deguchi\\Desktop\\TEST\\fabian-power\\Akku_HFO_HW3.X\\dist\\default\\production\\Akku_HFO_HW3.X.production.hex", "PIC18F4423")
    # icp.convert_files("C:\\Users\\garrett.deguchi\\Desktop\\Automate_Release\\Automate_Build\\fabian-monitor_bootloader\\Neo_mon Bootloader UART.X\\dist\\default\production\\Neo_mon_Bootloader_UART.X.production.hex", "dsPIC33FJ128GP706")
    # icp.close_app()


if __name__ == "__main__":
    main()
