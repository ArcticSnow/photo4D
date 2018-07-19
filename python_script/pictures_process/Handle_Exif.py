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
        date,time=exif_dict[pyxif.PhotoGroup.DateTimeOriginal][1].split(" ")
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
        num,denom=exif_dict[pyxif.PhotoGroup.BrightnessValue][1]
        brightness=num/denom
        return brightness
    except KeyError:
        print("WARNING No brightness data for file " + filename)
        return None
    except FileNotFoundError:
        print("WARNING Could not find file " + filename )
        return None

def write_sample_metadata(file_path,date,source_picture, gcp_name, pos_ini ):
    """
    write sample parameters in metadata (totally artifitial and ugly
    :param file_path:
    :return:
    """
    pos_ini = int(pos_ini[0]),int(pos_ini[1]) # todo trouver un moyen d'éviter cette perte
    metadata = {pyxif.ImageGroup.ImageDescription: gcp_name,
                  pyxif.ImageGroup.Software: "python 3.6.3",
                pyxif.ImageGroup.DocumentName:source_picture,
                pyxif.ImageGroup.WhitePoint :  pos_ini
                  }
    # convert datetime object to string and add date to exif data
    exifdata={pyxif.PhotoGroup.DateTimeOriginal:date.strftime("%Y:%m:%d %H:%M:%S")}
    exif_bytes = pyxif.dump(metadata, exif_ifd=exifdata)
    pyxif.insert(exif_bytes, file_path)

def load_sample_metadata(file_path):

    try:
        zeroth_dict, exif_dict, gps_dict = pyxif.load(file_path)
        gcp_name = zeroth_dict[pyxif.ImageGroup.ImageDescription][1]
        source_picture = zeroth_dict[pyxif.ImageGroup.DocumentName][1]
        pos_ini = zeroth_dict[pyxif.ImageGroup.WhitePoint][1]
        date = load_date(file_path)

        return date,source_picture, gcp_name, pos_ini

    except KeyError:
        print("WARNING Mising data for file " + file_path)
        return None
    except FileNotFoundError:
        print("WARNING Could not find file " + file_path)
        return None

if __name__ == "__main__":
    tic = time.time()

    write_sample_metadata("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Samples/GCP_4/sample_DSC00677.JPG", datetime.strptime('2018-06-04 03:16:14',"%Y-%m-%d %H:%M:%S"), "DSC00677.JPG", "GCP_4", (4753.29546896857, 1357.9374323565303))

    zeroth_dict, exif_dict, gps_dict = pyxif.load(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Samples/sample_DSC00677.JPG")
    print(load_sample_metadata("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Samples/sample_DSC00677.JPG"))
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
