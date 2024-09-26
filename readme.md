# Project Introduction
The objective of this CAL/VAL prototype is to calculate coefficients of variation (CV) of regions of interest (ROI) centred at field sites, using Sentinel-2 (S2) images.  
First, this prototype checks the cloud coverage inside ROIs, and if the cloud coverage is below a specific threshold, it performs calculation of CV, and flags whether the CV is not greater than a given threshold, 1 if true and 0 if false.  
The final output is a .csv file, containing names of site, numbers of valid pixels, percentages of valid pixels, values of CV and the corresponding flags.  

# Required Packages

Note that other versions of these packages might work as well. The version numbers listed below are the ones that were used during the development of the project. 

1. Numpy >= 1.26.4
2. pandas >= 2.2.2
3. shapely >= 2.0.5
4. geopandas >= 1.0.1
5. lxml >= 5.2.2
6. beautifulsoup4 >= 4.12.3
7. GDAL == 3.9.1
8. rasterio == 1.3.10
9. configparser >= 7.1.0

# Installation

First, clone this git repo:  

```
git clone https://github.com/IAGO1215/Sentinel-2-NIR-Vegetation.git
```

## For conda users

1. 

## For non-conda users

1. 

# User Input
## Mandatory Input
### 1. Sentinel-2 L1C and L2A Raw Images
### 2. A .csv file containing the information of all sites

## Optional Input
### 1. Threshold of Coefficient of Variation
The default threshold of coefficient of variation (CV) is 0.2.  
Users can adjust the threshold of CV optionally. The code will flag the values not greater than this threshold as 1, and the values greater than this threshold as 0.   
#### Set a new threshold for CV
a). Open "Optional Input.ini" in a text editor and find the line "threshold_CV = ".  
b). Enter a new threshold at the end of this line. The threshold must be a positive number.  
c). Save the "Optional Input.ini".  
d). If you want to set this threshold back to default, just remove the entered value and leave it empty just as before. 

### 2. Maximum Cloud Coverage
The default threshold of maximum cloud coverage is 0.5.  
Users can adjust the threshold of maximum cloud coverage optionally. The code will not proceed the images whose cloud coverage is greater than this threshold, and hence not calculate the CV and add flags. 
#### Set a new threshold for maximum cloud coverage
a). Open "Optional Input.ini" in a text editor and find the line "threshold_cloud = ".  
b). Enter a new threshold at the end of this line. The threshold must be a positive number not greater than 1.  
c). Save the "Optional Input.ini".  
d). If you want to set this threshold back to default, just remove the entered value and leave it empty just as before. 

### 3. Size of Region of Interest
Open "Optional Input.ini" and find the line "area_ROI = ".  
Enter a new threshold at the end of this line. The threshold must be a positive number not lower than 0 and not greater than 1. 
The default threshold of CV is 0.5.  

# Folder Structure

# Output

# 