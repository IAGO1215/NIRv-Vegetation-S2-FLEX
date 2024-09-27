# Project Introduction
The objective of this CAL/VAL prototype is to calculate coefficients of variation (CV) of regions of interest (ROI) centred at field sites, using Sentinel-2 (S2) images.  
First, this prototype checks the cloud coverage inside ROIs, and if the cloud coverage is below a specific threshold, it performs calculation of CV, and flags whether the CV is not greater than a given threshold, 1 if true and 0 if false.  
The final output is a .csv file, containing names of site, numbers of valid pixels, percentages of valid pixels, values of CV and the corresponding flags.  

# Required Python Packages

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

## 1. Clone this git repo to the desired location on your device:  

You can enter in the terminal the following command:

```
git clone https://github.com/IAGO1215/Sentinel-2-NIR-Vegetation.git
```

Or simply download the source code of this GitHub repo and unzip the file to the desired location. 

## 2. Install all required python packages

In order to run the code, it's necessary to install all the required packages. 

### 2-1. For conda users

1. Open terminal in conda and type the following code:

    ```
    conda env create -f path\to\environment.yml
    ```

    Please replace the "path\to\environment.yml" to the absolute address of the file "environment.yml" of this source code unzipped on your device.

2. Wait for conda to finish environment setup. You might need to manually input some commands during the setup. 
3. Next, go to the newly created virtual environment named "Sentinel-2-NIRv", select your preferred IDE and open the folder of this GitHub repo that you have just unzipped as a new workspace. 
4. Finally, prepare your inputs (Please refer to the "User Input" section below on how to prepare your inputs) and then run the "Main.py" code. 

### 2-2. For non-conda users

1. Open terminal and type the following command:
    ```
    pip install -r path\to\requirements.txt
    ```

    Please replace the "path\to\requirements.txt" to the absolute address of the file "requirements.txt" of this source code unzipped on your device.

2. Wait for the packages installation.
3. Finally, prepare your inputs (Please refer to the "User Input" section below on how to prepare your inputs) and then run the "Main.py" code. 

# User Input
## Mandatory Input
### 1. Prepare a .csv file containing the information of all sites

#### 1.1 Make a copy backup of Site.csv

First it's recommended to make a copy of "Site.csv" and rename it to "Site-Example.csv". Don't modify this renamed file but just keep it there for backup purpose.  
In this way, everytime in the future you can always refer to this .csv file for correct formats. 

#### 1.2 Write the infos of sites in Site.csv and save the file

Then open "Site.csv" file and write the names, latituldes and longitudes of all the sites.  
You should keep each name of sites unique. 
If there are multiple pairs of Sentinel-2 images for the same site, you can add some prefix or suffix to the name of the sites.  
For example, if there are two dates of Sentinel-2 images for the site San Rossore, you should write "San Rossore Date 1" and "San Rossore Date 2" as the names of the sites. 

### 2. Download Sentinel-2 L1C and L2A Raw Images
#### 2.1 Download Sentinel-2 raw images on Copernicus Broswer

You can only use raw Sentinel-2 images downloaded from [Copernicus Broswer](https://browser.dataspace.copernicus.eu/) as input images.  
Whenever you download images, you should always make sure that you download both L1C and L2A images that have the same date and cover the same area (check their codes before downloading). 

#### 2.2 Create sub-folders to keep the downloaded images

Open "Input S2 Images" and create sub-folders using the names you have written in "Site.csv".  
Then in each sub-folder, create two folders named "L1C" and "L2A".  
I also provide a supplementary python code that can automate this process. Simply run "Batch create subfolders.py" and then you are good to go. 

#### 2.3 Unzip downloaded images and put them into correct sub-folders

Just do what the title of this part says. 

## Optional Input
### 1. Threshold of Coefficient of Variation
The default threshold of coefficient of variation (CV) is 0.2.  
Users can adjust the threshold of CV optionally. The code will flag the values not greater than this threshold as 1, and the values greater than this threshold as 0.   
#### Set a new threshold for CV
1.1 Open "Optional Input.ini" in a text editor and find the line "threshold_CV = ".  
1.2 Enter a new threshold at the end of this line. The threshold must be a positive number.  
1.3 Save the "Optional Input.ini".  
1.4 If you want to set this threshold back to default, just remove the entered value and leave it empty just as before. 

### 2. Maximum Cloud Coverage
The default threshold of maximum cloud coverage is 0.5.  
Users can adjust the threshold of maximum cloud coverage optionally. The code will not proceed the images whose cloud coverage is greater than this threshold, and hence not calculate the CV and add flags. 
#### Set a new threshold for maximum cloud coverage
2.1 Open "Optional Input.ini" in a text editor and find the line "threshold_cloud = ".  
2.2 Enter a new threshold at the end of this line. The threshold must be a positive number not greater than 1.  
2.3 Save the "Optional Input.ini".  
2.4 If you want to set this threshold back to default, just remove the entered value and leave it empty just as before. 

### 3. Size of Region of Interest
The default region of interest (ROI) is a 900mx900m squared area. 
Users can set the size of the squared ROI.  
Other shapes of ROI are not supported. 
#### Change the Size of the ROI
3.1 Open "Optional Input.ini" in a text editor and find the line "area_ROI = ".  
3.2 Enter a new numeric value without the unit at the end of this line. This value must be greater than 10 and a multiple of 10.  
3.3 Save the "Optional Input.ini".  
3.4 If you want to set the size of the ROI back to default, just remove the entered value and leave it empty just as before. 

### 4. Keep Cache Folder upon Completion
During the process there will be a temporary folder named "Cache" created to save some intermediate files.  
By default, this folder will be delete permanently upon the completion of the code. 

#### Keep Cache Folder
1.1 Open "Optional Input.ini" in a text editor and find the line "bool_DeleteCache = True".  
1.2 Change "True" to "False".  
1.3 Save the "Optional Input.ini".  
1.4 If you want to change it back to default, then re-write "True". 

# Example

## 1. Download Example S2 Images and Unzip

Download five images from this [link](https://drive.google.com/file/d/1KG2Ifpp80LRS1XWY4D5PfzD-879_nfGp/view?usp=sharing) and unzip the file to the root folder of this source code. The size of the file is 7GB because all of them are unmodified raw S2 images downloaded from Copernicus Browser. 

## 2. Check "Site.csv"

If you haven't modified this .csv file, make a backup of it. The example will use the default "Site.csv", as shown below:

| Site          | Latitude  | Longitude |
|---------------|-----------|-----------|
| FR-FBn        | 43.24079  | 5.67865   |
| GF-GUY Clouds | 5.2787    | -52.9248  |
| IT-BFt        | 45.197754 | 10.741966 |
| IT-SR2        | 43.732    | 10.291    |
| IT-SR2 Clouds | 43.732    | 10.291    |

## 3. Run "Main.py"

Open "Main.py" in your preferred IDE and run it. 

## 4. Open Output

You can find the output file named "Output.csv" in "Output" folder. Its content should be exactly the same as that in "Example_Output.csv", as shown below: 

| Site          | Valid Pixels L1C | Valid Pixels L2A | Valid Pixels Percentage L1C | Valid Pixels Percentage L2a | CV                  | Flag |
|---------------|------------------|------------------|-----------------------------|-----------------------------|---------------------|------|
| FR-FBn        | 8100.0           | 8100.0           | 1.0                         | 1.0                         | 0.16534960486724762 | 1.0  |
| GF-GUY Clouds | 2550.0           | 2550.0           | 0.3079338244173409          | 0.3079338244173409          |                     |      |
| IT-BFt        | 8100.0           | 8100.0           | 1.0                         | 1.0                         | 0.19972333349756258 | 1.0  |
| IT-SR2        | 8100.0           | 8100.0           | 1.0                         | 1.0                         | 0.2513329617906446  | 0.0  |
| IT-SR2 Clouds | 0.0              | 0.0              | 0.0                         | 0.0                         |                     |      |

# Folder Structure

Sentinel-2-NIRv  
├── Cache  
├── Input S2 Images  
│ ├── Site 1  
│ │ ├── L1C  
│ │ │ ├── Unzipped S2 Raw Files  
│ │ ├── L2A  
│ │ │ ├── Unzipped S2 Raw Files  
│ ├── Site 2  
│ ├── Site ...  
├── Output  
│ │ ├── Output.csv  
├── .gitignore  
├── Batch create subfolders.py  
├── Class.py    
├── Example_prototype.docx    
├── Main.py    
├── Optional Input.ini    
├── readme.md    
├── requirements.txt    
├── Site.csv    

# Authors

DISAT Gruppo Telerilevamento, Università degli Studi Milano-Bicocca