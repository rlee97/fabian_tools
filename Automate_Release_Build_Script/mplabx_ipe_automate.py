import os
import sys


class MPLABxIPE_Automation:
    def __init__(self):
        print("Initializing MPLABx IPE Automation")
        self.executable_location = "C:\\Program Files (x86)\\Microchip\\MPLABX\\v5.05\\mplab_platform\\mplab_ipe\\"
        self.final_command = 'build_pm3.cmd'
        self.bad_starts = ["dsPIC", "PIC"]
        self.pm3_cmd = " -TPPM3 "
        self.checksum_finder = "Checksum = "
        self.operation_failed = "Environment operation failed"
        print("Ready for MPLABx IPE to start converting files")

    def convert_files(self, input_file, input_directory, input_pic_type, input_name_type = "", input_version = ""):
        """
        This function uses the MPLABx IPE backend to convert the corresponding hex file into .pm3 and .bin files and
        then it changes the filename according to the checksum found in the original hex
        :param input_file:
        :param input_directory:
        :param input_pic_type:
        :return:
        """
        # Open build_pm3.cmd file and modify it with the input file, input_directory, and input_pic_type
        cur_dir = os.getcwd()

        if(os.path.exists(self.final_command)):
            os.remove(self.final_command)

        file = open(self.final_command, "w+")

        # This needs the -F added
        temp_file = '-F"' + input_file + '"'

        # This need the ipecmd.exe -BSC at the beginning and the ev1 at the end
        if(not input_directory.endswith("\\")):
            input_directory = input_directory + "\\"

        temp_directory = 'ipecmd.exe -BSC"' + input_directory + 'ev1"'

        # Modifying the piv name for the ipecmd commands parser
        temp_pic = None
        for start in self.bad_starts:
            if(input_pic_type.startswith(start)):
                temp_pic = " -P" + input_pic_type[len(start):]

        # Add the output all together
        first_line = "cd " + self.executable_location + "\n"
        second_line = temp_directory + temp_pic + self.pm3_cmd + temp_file + " -K\n"
        third_line = "cd " + cur_dir

        file.write(first_line)
        file.write(second_line)
        file.write(third_line)

        file.close()

        # Save the file
        # Run the command
        buffer = os.popen(self.final_command).read()

        checksum_file = ""

        index = buffer.find(self.checksum_finder)
        if(index != -1):
            # 4 is th length of the checksum characters
            checksum_file = buffer[index + len(self.checksum_finder):(index + len(self.checksum_finder) + 4)]
            if(checksum_file.endswith("\n")):
                checksum_file = "0"+checksum_file[:-1]

        if(checksum_file != ""):
            # Change the file name to associate with the project that it is currently in
            index = -1
            while(input_file[index] != "\\"):
                index -= 1

            if((input_name_type == "") or (input_version == "")):
                new_name = input_file[index:-4]
            else:
                # TODO check for rev and hardware versions as well
                if("HW1." in input_file):
                    new_name = input_name_type + "hw1.x_v" + input_version
                elif("HW2." in input_file):
                    new_name = input_name_type + "hw2.x_v" + input_version
                elif("HW3." in input_file):
                    new_name = input_name_type + "hw3.x_v" + input_version
                elif("Neo_mon" in input_file):
                    new_name = input_name_type + "rev" + input_version
                else:
                    new_name = input_name_type + "v" + input_version

            get_ev1_dir = input_directory + "ev1\\"

            for file in os.listdir(get_ev1_dir):
                if((file.endswith(".pm3"))):
                    os.rename(get_ev1_dir + file, get_ev1_dir + new_name + "_chk-" + checksum_file + ".pm3")
                elif((file.endswith(".bin"))):
                    os.rename(get_ev1_dir + file, get_ev1_dir + new_name + "_chk-" + checksum_file + ".bin")

            return checksum_file
        else:
            print("Environment directory was already created! Please delete the directory!")
            return checksum_file

    def close_app(self):
        print("Closing MPLABx IPE")


def main(input_hex_file, input_dir_location, input_pic_type, input_file_name, input_version_name):
    mplabx_ipe = MPLABxIPE_Automation()
    mplabx_ipe.convert_files(input_hex_file, input_dir_location, input_pic_type, input_file_name, input_version_name)
    mplabx_ipe.close_app()


if __name__ == "__main__":
    try:
        hex_file = str(sys.argv[1])
        dir_location = str(sys.argv[2])
        pic_type = str(sys.argv[3])
    except IndexError:
        print("Not enough input parameters (path to hex file, path to directory, pic type)")
        print("EX: python mplabx_ipe_automate.py C:\\directory\\filename.hex C:\\directory PIC16F1826")
        sys.exit()

    try:
        file_name = str(sys.argv[4])
        version_name = str(sys.argv[5])
    except IndexError:
        file_name = ""
        version_name = ""

    main(hex_file, dir_location, pic_type, file_name, version_name)
