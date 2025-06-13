# Project Introduction

The objective of this CAL/VAL prototype is to calculate coefficients of variation (CV) of regions of interest (ROI) centred at field sites, using Sentinel-2 (S2) L1C and L2A images and FLEX images.  

First, this prototype processes all FLEX images and calculates the average and the standard deviation of the value “Sif Emission Spectrum“ inside the ROI. Besides, it will extract the date and the time of the FLEX images whose vegetation pixels inside the ROI are greater than a threshold.

After the process of FLEX images, this prototype will search for S2 images whose dates and time are the same to that of FLEX images; if there are not the same ones, it will find the S2 images with the nearest dates and time. Then, it will check the cloud coverage inside ROIs, and if it is below a specific threshold, it performs calculation of CV, and flags whether the CV is not greater than a given threshold, 1 if true and 0 if false. Otherwise, the S2 image will be skipped.  

The final output files are unanimously in .csv format. For FLEX images, this prototype will generate a .csv file for each FLEX image containing the average and the standard deviation of the value “Sif Emission Spectrum“ inside the ROI. After processing all FLEX images, it will create a single .csv file to record the dates and the time of the FLEX images that have sufficient vegetation pixels inside the ROI.  

For the output of S2 images, it contains names of site, numbers of valid pixels, percentages of valid pixels, values of CV and the corresponding flags. For the output of FLEX images, if a site has sufficient vegetation pixels in its ROI, then this prototype will generate two .csv files, one containing vegetation pixels percentage and another containing the average and standard deviation values of all bands; otherwise, this prototype will generate only one .csv file, containing vegetation pixels percentage.  

## Required Python Packages

python == 3.11

Note that other versions of these packages might work as well.  

The version numbers listed below are the ones that were used during the development of the project.  

1. numpy >=1.26.4
2. pandas >=2.2.2
3. shapely >=2.0.5
4. geopandas >=1.0.1
5. lxml >=5.2.2
6. beautifulsoup4 >=4.12.3
7. GDAL ==3.9.1
8. rasterio ==1.3.10
9. xarray >=2024.10.0
10. scipy >=1.14.1
11. netcdf4 >=1.7.2

## Installation

### 1. Clone this git repo to the desired location on your device

If you are cloning from GitHub, you can enter in the terminal the following command:

``` shell
git clone https://github.com/IAGO1215/NIRv-Vegetation-S2-FLEX.git
```

If you are cloning from GitLab, enter in the terminal the collowing command:  

``` shell
git clone https://gitlab.com/bicocca2/NIRv-Vegetation-S2-FLEX.git
```

Or simply download the source code of this GitHub repo and unzip the file to the desired location.  

### 2. Install all required python packages

In order to run the code, it's necessary to install all the required python packages.  

#### 2-1. For conda users

1. Open terminal in conda and type the following code:

    ```shell
    conda env create -f path\to\environment.yml
    ```

    Replace the "path\to\environment.yml" to the absolute address of the file "environment.yml".  

2. Wait for conda to finish environment setup. You might need to manually input some commands during the setup, by referring to the description prompt in the terminal.  
3. Next, go to the newly created virtual environment named "Sentinel-2-NIRv", select your preferred IDE and open the root folder of this repo. If you are using Visual Studio Code, you can simply use "File-Open Workspace from File" and select "NIRv-Rad-S2-FLEX".  
4. Finally, prepare your inputs (Please refer to the "User Input" section below on how to prepare your inputs) and then run the "Main.py" code.  

#### 2-2. For non-conda users

1. Open terminal and type the following command.  

    ``` shell
    pip install -r path\to\requirements.txt
    ```

    Please replace the "path\to\requirements.txt" to the absolute address of the file "requirements.txt".

2. Wait for the packages installation.
3. Finally, prepare your inputs (Please refer to the "User Input" section below on how to prepare your inputs) and then run the "Main.py" code.  

## User Input

### Mandatory Input

#### 1. Prepare a .csv file containing the information of all sites

##### 1.1 Make a copy backup of Site.csv

First it's recommended to make a backup copy of "Sites.csv" and rename it to "Sites-Example.csv". Don't modify this renamed file but just keep it there for backup purpose.  

In this way, in the future you can always refer to this .csv file for correct formats.  

#### 1.2 Write the infos of sites in Site.csv and save the file

Then open "Sites.csv" file and write the names, latituldes and longitudes of all the sites.  

You should keep each name of sites unique.  

#### 2. Download FLEX Images

Open "Input FLEX Images" and create sub-folders using the names you have written in "Sites.csv".  

Then in each sub-folder, put your FLEX images inside, whose names are expected to be in the format YYYYMMDD + "T" + HHMMSS, such as "20230821T100601".  (You can refer to the "Folder Structure" section in this Readme file)  

#### 3. Download Sentinel-2 L1C and L2A Raw Images

##### 3.1 Download Sentinel-2 raw images on Copernicus Broswer

You can only use raw Sentinel-2 images downloaded from [Copernicus Broswer](https://browser.dataspace.copernicus.eu/) as input images.  

Whenever you download images, you should always make sure that you download both L1C and L2A images that have the same date and cover the same area (check their codes before downloading).  

##### 3.2 Create sub-folders to keep the downloaded images

Open "Input S2 Images" and create sub-folders using the names you have written in "Site.csv".  

Then in each sub-folder, create another sub-folder in format YYYYMMDD + T + HHMMSS, such as "20230821T100601", and inside it create another two folders named "L1C" and "L2A".  (You can refer to the "Folder Structure" section in this Readme file)  

##### 3.3 Unzip downloaded images and put them into correct sub-folders

Just do what the title of this part says.  

### Optional Input

### 1. Threshold of Vegetation Pixel
The default threshold of vegetation pixel is 0.5.  
Users can adjust the threshold of vegetation pixel optionally. This threshold will be used to determine whether a FLEX image will be kept. 
#### Set a new threshold for Vegetation Pixel
1.1 Open "Optional Input.ini" in a text editor and find the line "threshold_Vegetation = ".  
1.2 Enter a new threshold at the end of this line. The threshold must be a positive number.  
1.3 Save the "Optional Input.ini".  
1.4 If you want to set this threshold back to default, just remove the entered value and leave it empty just as before.  

### 2. Threshold of Coefficient of Variation
The default threshold of coefficient of variation (CV) is 0.2.  
Users can adjust the threshold of CV optionally. The code will flag the values not greater than this threshold as 1, and the values greater than this threshold as 0.  
#### Set a new threshold for CV
1.1 Open "Optional Input.ini" in a text editor and find the line "threshold_CV = ".  
1.2 Enter a new threshold at the end of this line. The threshold must be a positive number.  
1.3 Save the "Optional Input.ini".  
1.4 If you want to set this threshold back to default, just remove the entered value and leave it empty just as before. 

### 3. Maximum Cloud Coverage
The default threshold of maximum cloud coverage is 0.5.  
Users can adjust the threshold of maximum cloud coverage optionally. The code will not proceed the images whose cloud coverage is greater than this threshold, and hence not calculate the CV and add flags. 
#### Set a new threshold for maximum cloud coverage
2.1 Open "Optional Input.ini" in a text editor and find the line "threshold_cloud = ".  
2.2 Enter a new threshold at the end of this line. The threshold must be a positive number not greater than 1.  
2.3 Save the "Optional Input.ini".  
2.4 If you want to set this threshold back to default, just remove the entered value and leave it empty just as before. 

### 4. Size of Region of Interest
The default region of interest (ROI) is a 900mx900m squared area. 
Users can set the size of the squared ROI.  
Other shapes of ROI are not supported. 
#### Change the Size of the ROI
3.1 Open "Optional Input.ini" in a text editor and find the line "area_ROI = ".  
3.2 Enter a new numeric value without the unit at the end of this line. This value must be greater than 10 and a multiple of 10.  
3.3 Save the "Optional Input.ini".  
3.4 If you want to set the size of the ROI back to default, just remove the entered value and leave it empty just as before. 

### 5. Keep Cache Folder upon Completion
During the process there will be a temporary folder named "Cache" created to save some intermediate files.  
By default, this folder will be delete permanently upon the completion of the code. 

#### Keep Cache Folder
1.1 Open "Optional Input.ini" in a text editor and find the line "bool_DeleteCache = True".  
1.2 Change "True" to "False".  
1.3 Save the "Optional Input.ini".  
1.4 If you want to change it back to default, then re-write "True". 

## Example

### 1. Download Example FLEX + S2 Images and Unzip

Download five images from this XXXXXXXX and unzip the file to the root folder of this source code. The size of the file is 7GB because all of them are unmodified raw S2 images downloaded from Copernicus Browser.  

### 2. Check "Sites.csv"

If you haven't modified this .csv file, make a backup of it. The example will use the default "Sites.csv", as shown below:

| Site            | Latitude  | Longitude |
|-----------------|-----------|-----------|
| castelPorziano  | 41.7043   | 12.3573   |
| JolandaDiSavoia | 44.874305 | 11.979201 |
| Nebraska        | 41.1797   | -96.44039 |
| SanRossore      | 43.732    | 10.291    |

### 3. Run "Main.py"

Open "Main.py" in your preferred IDE and run it.  

### 4. Open Output Folder

You can find the output files in "Output" folder.  

#### 4-1. Usable FLEX Images.csv

This file contains the filenames, dates and times of all FLEX images whose vegetation pixels inside the ROI are greater than the threshold.  

#### 4-2. Output_S2.csv

This file is the result of the process of all Sentinel-2 images, containing valid pixels, values of CV and flags. 

#### 4-3. SiteName\\Filename - sif.csv

For each input FLEX image there will be a .csv file, containing the values of the average and the standard deviation of sif.  

#### 4-4. SiteName\\Filename - sif.csv

For each input FLEX image there will be a .csv file, containing the values of the average and the standard deviation of sif.  

## Folder Structure

Sentinel-2-NIRv  
├── Cache  
├── Input FLEX Images  
│ ├── Site 1  
│ │ ├── Image1.nc --- In format PRS_TD_ + YYYYMMDD_HHMMSS, such as "PRS_TD_20230616_101431.nc"  
│ │ ├── Image2.nc  
│ │ ├── ...  
│ ├── Site 2  
│ ├── Site ...  
├── Input S2 Images  
│ ├── Site 1  
│ │ ├── $DateTTime --- In format YYYYMMDD + T + HHMMSS, such as "20230821T100601"  
│ │ │ ├── L1C  
│ │ │ │ ├── Unzipped S2 Raw Files  
│ │ │ ├── L2A  
│ │ │ │ ├── Unzipped S2 Raw Files  
│ ├── Site 2  
│ ├── Site ...  
├── Output  
│ │ ├── Output.csv  
├── .gitignore  
├── Class.py    
├── Example_prototype.docx    
├── Main.py    
├── Optional Input.ini    
├── readme.md    
├── requirements.txt    
├── Site.csv    

## Troubleshooting

### 1. Error "Found the following matches with the input file in xarray's IO backends: ['netcdf4','h5netcdf']. But their dependency may not be installed"

Install:  

``` shell
pip install netCDF4
```

If the error persists, also install:

``` bash
pip install h5netcdf
```

### 2. Error "Couldn't find a tree builder with the features you requested: xml" or "Couldn't find a tree builder with the features you requested: lxml"

Install:

``` shell
pip install lxml
```

## Authors

DISAT Gruppo Telerilevamento, Università degli Studi Milano-Bicocca  
