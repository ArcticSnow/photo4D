# coding : utf8


from datetime import datetime
import sys

import pyxif
import time

def load_date(filename):
    """
    Load date of the shot, according to te image metadata
    :param filename: name/path of the file
    :return: datetime format
    """
    try:
        zeroth_dict, exif_dict, gps_dict = pyxif.load(filename)
        date,time=exif_dict[36867][1].split(" ")
        year, month,day = date.split(":")
        hour,minute,sec = time.split(":")
        dateimage= datetime(int(year), int(month), int(day), int(hour), int(minute) ,int(sec))
        return dateimage
    except KeyError:
        print("WARNING No date for file " + filename)
        return None
    except FileNotFoundError:
        print("WARNING Could not find file " + filename )
        return None

def load_lum(filename):
    """
    Load luminosity of the shot scene, according to te image metadata
    :param filename: name/path of the file
    :return: float, level of brightness
    """
    try:
        zeroth_dict, exif_dict, gps_dict = pyxif.load(filename)
        num,denom=exif_dict[37379][1]
        brightness=num/denom
        return brightness
    except KeyError:
        print("WARNING No brightness data for file " + filename)
        return None
    except FileNotFoundError:
        print("WARNING Could not find file " + filename )
        return None

if __name__ == "__main__":
    tic = time.time()
    print(load_lum("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/MicMac_Test_06_11-22h/DSC00864.JPG"))
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
