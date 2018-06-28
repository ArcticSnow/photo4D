# coding : utf8
import cv2 as cv
from matplotlib import pyplot as plt
import shutil


def read_txt_gps(path):
    keep = True
    while keep:
        i_min = int(input("indice minimum : "))
        i_max = int(input("indice maximum : "))
        file=open(path,'r')
        list_lines = file.readlines()
        file.close()
        print("file read")
        i = 1
        s_n,s_e,s_h =0,0,0
        compt = 0
        lenght = len(list_lines)
        while i<lenght and i<=i_max:
            if i>= i_min:
                compt +=1
                line = list_lines[i-1].split(',')
                s_n += float(line[2])
                s_e += float(line[3])
                s_h+= float(line[4].rstrip('\n'))
            i+=1
        n = s_n/compt
        e = s_e/compt
        h = s_h/compt
        print(n,e,h)

        ans = input("Continue ?  (y/n)")
        if ans != 'y':
            keep = False

if __name__ == "__main__":
    print(read_txt_gps("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/GCP/to_read.csv"))