# coding: utf-8
"""
Some useful functions
"""
from subprocess import Popen, PIPE, STDOUT
import sys
import numpy as np



def exec_mm3d(command, display=True):
    """
    launch a MicMac command.
    As MicMac handle errors and wait for user's input, we needed a way to carry on when a command fails
    This function will kill the process if an error happens, allowing further process to be done
    :param command: MicMac command line, string beginning with mm3d
     to see every command allowed, see https://micmac.ensg.eu/index.php/Accueil, or Github
    :param display: display or not the logs from MicMac, boolean
    :return:
    """
    if(command[:5] != "mm3d "):
        print("WARNING The command must begin with mm3d\n")
        return 0, None

    process = Popen(command.split(" "), stdout=PIPE, stderr=STDOUT)
    for line_bin in iter(process.stdout.readline, b''):
        try:
            line = line_bin.decode(sys.stdout.encoding)
            if display:
                sys.stdout.write(line)
            # if waiting for input, which means an error was generated
            if '(press enter)' in line:
                print("Error in MicMac process, abort process")
                process.kill()
                return 1, None
            elif 'Warn tape enter to continue' in line:
                print("Value error in Tapas, abort process")
                process.kill()
                return 1,'Value error in Tapas'
        except UnicodeDecodeError:
            sys.stdout.write('---cannot decode this line---')

    # if no error occurs
    return 0, None


def pictures_array_from_file(filepath):
    """
    Could be way more efficient ! And does not handle any error for the moment
    :param filepath:
    :return:
    """
    print("\nRetrieving data from file " + filepath + "\n.......................................")
    all_lines = []
    with open(filepath, 'r') as file:
        for line in file.readlines():
            if line[0] != "#" :
                list_temp = line.split(',')
                length = len(list_temp)
                array_line = np.empty(length, dtype=object)
                if list_temp[0].rstrip(" ").lower() == "true":
                    array_line[0] = True
                else:
                    array_line[0] = False
                for i in range(1, length):
                    array_line[i] = list_temp[i].rstrip('\n')
                all_lines.append(array_line)
        print("Done")
        return np.array(all_lines)












