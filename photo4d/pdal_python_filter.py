'''
Custom python filters for pdal

'''
import numpy as np
import matplotlib.colors as cl
import pandas as pd
#import pdb

def add_XY_UTM(ins, outs):
	X = ins['X'] 
	X += float(pdalargs['x_offset'])
	Y = ins['Y'] 
	Y += float(pdalargs['y_offset'])
	outs['Y'] = Y
	outs['X'] = X
	return True


def voxelGrid(ins, outs):

	ROI = [float(pdalargs['Xmin']),
		float(pdalargs['Xmax']),
		float(pdalargs['Ymin']),
		float(pdalargs['Ymax']),
		float(pdalargs['Zmin']),
		float(pdalargs['Zmax'])]
	leaf = float(pdalargs['leaf'])

	df = pd.DataFrame({'X' : ins['X'] ,
		'Y' : ins['Y'] ,
		'Z' : ins['Z'],
		'Red':ins['Red'],
		'Green':ins['Green'],
		'Blue':ins['Blue']})

	for i in range(0,6):
		if ROI[i]==-9999:
			if i==0:
				ROI[i] = df.iloc[:,0].min()
			elif i==1:
				ROI[i] = df.iloc[:,0].max()
			elif i==2:
				ROI[i] = df.iloc[:,1].min()
			elif i==3:
				ROI[i] = df.iloc[:,1].max()
			elif i==4:
				ROI[i] = df.iloc[:,2].min()
			elif i==5:
				ROI[i] = df.iloc[:,2].max()
	
	#print(ROI)
	nx = np.int((ROI[1]-ROI[0])/leaf)
	ny = np.int((ROI[3]-ROI[2])/leaf)
	nz = np.int((ROI[5]-ROI[4])/leaf)

	bins_x = np.linspace(ROI[0], ROI[1], nx+1)
	df['x_cuts'] = pd.cut(df.X,bins_x, labels=False)
	bins_y = np.linspace(ROI[2],ROI[3], ny+1)
	df['y_cuts'] = pd.cut(df.Y,bins_y, labels=False)
	bins_z = np.linspace(ROI[4],ROI[5], nz+1)
	df['z_cuts'] = pd.cut(df.Z,bins_z, labels=False)

	grouped = df.groupby([df['x_cuts'],df['y_cuts'], df['z_cuts']])

	outf = pd.DataFrame()
	outf['X'] = np.hstack((grouped.X.mean().reset_index().X, np.zeros(ins['X'].shape[0] - grouped.X.mean().reset_index().X.shape[0])-9999))
	outf['Y'] = np.hstack((grouped.Y.mean().reset_index().Y, np.zeros(ins['X'].shape[0] - grouped.X.mean().reset_index().X.shape[0])-9999))
	outf['Z'] = np.hstack((grouped.Z.mean().reset_index().Z, np.zeros(ins['X'].shape[0] - grouped.X.mean().reset_index().X.shape[0])-9999))
	outf['Red'] = np.hstack((grouped.Red.mean().reset_index().Red, np.zeros(ins['X'].shape[0] - grouped.X.mean().reset_index().X.shape[0])-9999))
	outf['Green'] = np.hstack((grouped.Green.mean().reset_index().Green, np.zeros(ins['X'].shape[0] - grouped.X.mean().reset_index().X.shape[0])-9999))
	outf['Blue'] = np.hstack((grouped.Blue.mean().reset_index().Blue, np.zeros(ins['X'].shape[0] - grouped.X.mean().reset_index().X.shape[0])-9999))
	outf['Classification'] = (outf.X==-9999)*13
	outf = outf.dropna()

	outs['X'] = np.array(outf.X.astype('<f8'))
	outs['Y'] = np.array(outf.Y.astype('<f8'))
	outs['Z'] = np.array(outf.Z.astype('<f8'))
	outs['Red'] = np.array(outf.Red.astype('u2'))
	outs['Green'] = np.array(outf.Green.astype('u2'))
	outs['Blue'] = np.array(outf.Blue.astype('u2'))
	outs['Classification'] = np.array(outf.Classification.astype('u1'))

	return True


def reject_undefined_cloud(ins, outs):
	"""
	Filter to cut points below a certain threshold, and where there are two clouds within a cell exceeding a threshold distance
	
	Classifies points to reject with the value 10
	"""
	thresh = float(pdalargs['thresh'])
	Zmin = float(pdalargs['Zmin'])
	xstart = float(pdalargs['xstart'])-1
	xend = float(pdalargs['xend'])+1
	ystart = float(pdalargs['ystart'])-1
	yend = float(pdalargs['yend'])+1
	nx = float(pdalargs['nx'])+2
	ny = float(pdalargs['ny'])+2

	print("Cell size in X = " + str((xend-xstart)/nx))
	print("Cell size in Y = " + str((yend-ystart)/ny))
	
	df = pd.DataFrame({'X' : ins['X'] , 'Y' : ins['Y'] , 'Z' : ins['Z']})
	bins_x = np.linspace(xstart, xend, nx+1)
	df['x_cuts'] = pd.cut(df.X,bins_x, labels=False)
	bins_y = np.linspace(ystart,yend, ny+1)
	df['y_cuts'] = pd.cut(df.Y,bins_y, labels=False)

	grouped = df.groupby([df['x_cuts'],df['y_cuts']])
	ext = grouped.Z.max() - grouped.Z.min()
	ext = np.array(ext.unstack())

	df.range = ext[df.x_cuts.astype(int)-1, df.y_cuts.astype(int)-1]
	cls = ins['Classification']
	out = np.array((df.range>thresh) | (df.Z<Zmin))
	cls[out] = 12
	
	outs['Classification'] = cls.astype('u1')
	
	return True


def classify_SnowGround(ins, outs):
	"Classify points Snow/Ground based on point Value in the HSV colorspace, 1 for snow, 3 for ground"
	thresh = 180

	cls = ins['Classification']
	rgb = np.vstack((ins['Red'], ins['Green'], ins['Blue'])).T
	hsv = cl.rgb_to_hsv(rgb)
	snow = (hsv[:,2] > thresh) * 3
	ground = (hsv[:,2] <= thresh) * 2

	dt = np.dtype(('u1'))
	snow = snow.astype(dt)
	ground = ground.astype(dt)
	cls =  snow + ground

	outs['Classification'] = cls

	return True


def mask_ground(ins, outs):
	"Mask to keep ground patches only based on point Value in the HSV colorspace"
	thresh = 180

	rgb = np.vstack((ins['Red'], ins['Green'], ins['Blue'])).T
	hsv = cl.rgb_to_hsv(rgb)
	ground = hsv[:,2] <= thresh
	outs['Mask'] = ground

	return True


def rgb2value(ins, outs):
	rgb = np.vstack((ins.get('Red'), ins.get('Green'), ins.get('Blue'))).T
	hsv = cl.rgb_to_hsv(rgb)
	#pdb.set_trace()
	outs['Value'] = hsv[:,2].astype('float64')

	return True



def mask_snow(ins, outs):
	"Mask to keep ground patches only based on point Value in the HSV colorspace"
	thresh = 180

	rgb = np.vstack((ins['Red'], ins['Green'], ins['Blue'])).T
	hsv = cl.rgb_to_hsv(rgb)
	snow = hsv[:,2] > thresh
	outs['Mask'] = snow

	return True
