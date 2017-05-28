# Project obtain 4D data for snowmelt

Simon Filhol (simon.filhol@geo.uio.no)
Guillaume Sutter (sutterguigui@gmail.com)

## Objectives

 1. Obtain 2D snow cover extent map
 2. Derive 3D maps for pairs of time-lpase pictures
 3. improve design (targets, camera set up and settings, image preprocessing, number of camera...)
 4. Assess accuracy, precision: compare to lidar, dGPS snow-deph measurements. What paramters have the largest influence on the results
 5. try automating every steps of the algorithm, and combine scripts into one program (app)
 5. Success??!

## Description

This project will consist to develop an automated program to derive 4 dimentional (x,y,z,t) description of the snow surface within the field of view of several time-lapse camera.

The project should be based on open-source libraries, for public release. 

## Strategy

1- open RAW on Python and split image between snow area and other using threshold
2- expose using histogram equalizer both masked selection
3- recombine image to run through Micmac

4- run micmac script using different parameter (number of pics, position of camera, exposition
5- estimate model error against (lidar?)



## Ressources:

    - Micmac: http://micmac.ensg.eu/index.php/Accueil
    - relevant publications saved in Google drive
    - Image processing images: skimage, openCV, Pillow
    - rawpy, a package to open raw images in Python: https://pypi.python.org/pypi/rawpy
