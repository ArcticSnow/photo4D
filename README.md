# Photo4D: open-source time-lapse photogrammetry 

Contributors by alphabetical orders:
- Simon Filhol (simon.filhol@geo.uio.no)
- Luc Girod (luc.girod@geo.uio.no)
- Alexis Perret (aperret2010@hotmail.fr)
- Guillaume Sutter (sutterguigui@gmail.com)

## Description

This project consists of an automated program to generate point cloud from time-lapse set of images from independent cameras. The software: 
​      1. sorts images by timestamps, 
​      2. assess the image quality based on lumincace and bluriness, 
​      3. identify automatically GCPs through the stacks of images, 
​      4. run Micmac to compute point clouds, and 
​      5. convert point cloud to rasters. (not implemented)

The project should be based on open-source libraries, for public release. 

## Installation
1. install the latest version of [micmac](https://micmac.ensg.eu/index.php/Install)

2. install python 3.6, and with anaconda, create a virtual environment with the following packages: 
     - opencv 
     - pandas 
     - matplotlib
     - lxml
     - pillow
     - pyxif (that needs to be downloaded from https://github.com/zenwerk/Pyxif)
     ```sh
     wget https://github.com/zenwerk/Pyxif/archive/master.zip
     unzip Pyxif-master.zip
     cd Pyxif-master
     python setup.py install
     ```

 3. The package is available via Pypi

     ```python
     pip install photo4d
     ```

## Usage

1. prepare your environment: 
      - create a Python >= 3.6 virtual environment in which you install the required libraries (see above)
      - create a folder for the project with inside the project folder a folder called Images containing itself one folder per
      - Organize your photo with one folder per camera. For instance folder /cam1 constains all the images from Camera 1.
       camera
       
```bash
├── Project
    └── Images
         ├── Cam1
         ├── Cam2
         ├── Cam3
         └── Cam...
```


2. Set the path correctly in the file MicmacApp/Class_photo4D.py

```python

############################################################
## Part 1

import photo4d as p4d

# Create a new photo4d object by indicating the Project path
myproj = p4d.Photo4d(project_path="point to project folder /Project")

# Algorithm to sort images in triplets, and create the reference table with sets :date, valid set, image names
myproj.sort_picture()

# Algorithm to check picture quality (exposure and blurriness)
myproj.check_picture_quality()

############################################################
## Part 2: Estimate camera orientation

# Compute camera orientation using the timeSIFT method:
myproj.timeSIFT_orientation()

# Convert a text file containing the GCP coordinates to the proper format (.xml) for Micmac
myproj.prepare_gcp_files(path_to_GCP_file, file_format="N_X_Y_Z")

# Select a set to input GCPs
myproj.set_selected_set("DSC02728.JPG")

# Input GCPs in 3 steps
# first select 3 to five GCPs to pre-orient the images
myproj.pick_initial_gcps()

# Apply transformation based on the few GCPs previously picked
myproj.compute_transform()

# Pick additionnal GCPs, that are now pre-estimated
myproj.pick_all_gcps()

############################################################
## Part2, optional: pick GCPs on extre image set
## If you need to pick GCPs on another set of images, change selected set (this can be repeated n times):
#myproj.compute_transform()
#myproj.set_selected_set("DSC02871.JPG")
#myproj.pick_all_gcps()

# Compute final transform using all picked GCPs
myproj.compute_transform(doCampari=True)

## FUNCTION TO CHANGE FOR TIMESIFT
# myproj.create_mask() #To be finished

############################################################
## Part3: Compute point clouds

# Compute point cloud, correlation matrix, and depth matrix for each set of image
myproj.process_all_timesteps()

# Clean (remove) the temporary working direction
myproj.clean_up_tmp()

```

## Ressources

- Micmac: http://micmac.ensg.eu/index.php/Accueil
- Image processing images: skimage, openCV, Pillow
- python package to read exif data: https://pip.pypa.io/en/latest/user_guide/

## Development

Message us to be added as a contributor, then if you can also modify the code to your own convenience with the following steps:

To work on a development version and keep using the latest change install it with the following

```shell
git clone git@github.com:ArcticSnow/photo4D.git
pip install -e [path2folder/photo4D]
```

and to upload latest change to Pypi.org, simply:

1. change the version number in the file ```photo4d/__version__.py```
2.  run from a terminal from the photo4D folder, given your $HOME/.pyc is correctly set:

```shell
python setup.py upload
```

