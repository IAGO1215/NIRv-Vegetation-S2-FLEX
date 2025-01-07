# ---------------------------------------------------------------------------- #
#                            Import Python Packages                            #
# ---------------------------------------------------------------------------- #
import os
import time
from datetime import datetime
import shutil
import configparser
import numpy as np
import pandas as pd
import rasterio as rio
# Don't remove rasterio.mask this package otherwise it could cause errors
import rasterio.mask
import xarray as xr

# ---------------------------------------------------------------------------- #
#                                 Import Class                                 #
# ---------------------------------------------------------------------------- #
from Class import S2
from Class import FLEX
    
# ---------------------------------------------------------------------------- #
#                                   Main Code                                  #
# ---------------------------------------------------------------------------- #

start_Time = time.time()
config = configparser.ConfigParser()
# Initiate classes
flex = FLEX()
s2 = S2()
print("Code starts")

# Read optional input
config.read(s2.path_Optional)
if config["OptionalInput"]["threshold_Vegetation"]:
    flex._vegetationPixel = config["Optional Input"]["threshold_Vegetation"]
    print(f"The threshold of vegetation pixel has been modified to {config["Optional Input"]["threshold_Vegetation"]}!")
if config["OptionalInput"]["threshold_CV"]:
    s2._threshold_CV = config["Optional Input"]["threshold_CV"]
    print(f"The threshold of CV has been modified to {config["Optional Input"]["threshold_CV"]}!")
if config["OptionalInput"]["threshold_Cloud"]:
    s2._cloud = config["Optional Input"]["threshold_Cloud"]
    print(f"The threshold of cloud coverage has been modified to {config["Optional Input"]["threshold_cloud"]}!")
if config["OptionalInput"]["area_ROI"]:
    s2._area = config["Optional Input"]["area_ROI"]
    print(f"The ROI has been modified to {config["Optional Input"]["area_ROI"]} m by {config["Optional Input"]["area_ROI"]} m!")
if config["OptionalInput"]["bool_DeleteCache"] == "True":
    s2.bool_DeleteCache = True
    print("The cache foldeer will be deleted upon the completion of the code! ")

# ---------------------------------------------------------------------------- #
#                                For FLEX Images                               #
# ---------------------------------------------------------------------------- #
if len(os.listdir(flex.path_Input)) !=0 :
    list_Name_Site = []
    list_FLEX_Date = []
    list_FLEX_Time = []
    list_FLEX_Filename = []
    # Read .csv files to retrieve info of each site
    df_Site = flex.get_SiteInfo()
    # Start the main part, a loop that will iterate each site in our input .csv file
    for i in range(df_Site.shape[0]):
        temp_StartTime = time.time()
        # Get site name
        temp_SiteName = df_Site["Site"][i]
        temp_SitePath = flex.path_Input + "\\" + temp_SiteName
        if (not os.path.exists(temp_SitePath)) or (len(os.listdir(temp_SitePath)) == 0):
            print(f"WARNING: The site {temp_SiteName} doesn't have input FLEX images. This site has been skipped! ")
        else:
            temp_Path_Output = flex.path_Output + "\\" + temp_SiteName
            os.makedirs(temp_Path_Output, exist_ok = True)
            print(f"{temp_SiteName} starts!")
            temp_FileName = os.listdir(temp_SitePath)
            temp_NumFLEXImages = len(temp_FileName)
            print(f"There are {temp_NumFLEXImages} FLEX images available for the site {temp_SiteName}!")
            temp_SiteLat = df_Site["Latitude"][i]
            temp_SiteLon = df_Site["Longitude"][i]
            for k in range(temp_NumFLEXImages):
                print(f"Now starting with No.{k + 1} FLEX image '{temp_FileName[k]}' of the site {temp_SiteName}")
                temp_ds = rio.open(f'netcdf:{flex.path_Input + "\\" + temp_SiteName + "\\" + temp_FileName[k]}:Leaf Area Index')
                print(f"{temp_FileName[k]} opened succesfully!")
                temp_index_x, temp_index_y = temp_ds.index(temp_SiteLon,temp_SiteLat)
                # Veg pixel filter

                list_Name_Site.append(temp_SiteName)
                list_FLEX_Filename.append(temp_FileName[k])
                list_FLEX_Date.append(temp_FileName[k].split('.')[0].split('_')[-2])
                list_FLEX_Time.append(temp_FileName[k].split('.')[0].split('_')[-1])
                
                # Calculate SIF
                temp_xr_ds = xr.open_dataset(flex.path_Input + "\\" + temp_SiteName + "\\" + temp_FileName[k])
                temp_Name_Var = list(temp_xr_ds.data_vars)
                temp_list_SIF_Name = []
                temp_list_SIF_AVG = []
                temp_list_SIF_STD = []
                for var_name in temp_Name_Var:
                    if "Sif Emission Spectrum_sif_wavelength_grid" in var_name:
                        temp_Array = temp_xr_ds[var_name][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values
                        # print(temp_Array)
                        temp_list_SIF_Name.append(var_name)
                        temp_AVG = np.average(temp_Array).item()
                        temp_list_SIF_AVG.append(temp_AVG)
                        temp_STD = np.std(temp_Array).item()
                        temp_list_SIF_STD.append(temp_STD)
                temp_df_SIF = pd.DataFrame({
                    "SIF": temp_list_SIF_Name,
                    "Average": temp_list_SIF_AVG,
                    "STD": temp_list_SIF_STD
                })
                temp_df_SIF.to_csv(temp_Path_Output + "\\" + temp_FileName[k] + " - Sif.csv", index = False)
    temp_df_Sites = pd.DataFrame({
        "Site": list_Name_Site,
        "FLEX Filename": list_FLEX_Filename,
        "FLEX Date": list_FLEX_Date,
        "FLEX Time": list_FLEX_Time
    })
    temp_df_Sites.to_csv(flex.path_Output + "\\Usable FLEX Images.csv", index = False)
else:
    print("WARNING: There are no FLEX images found inside the input folder. ")

# ---------------------------------------------------------------------------- #
#                             For Sentinel-2 Images                            #
# ---------------------------------------------------------------------------- #

# Read Site.csv files to retrieve info of each site
df_Site = s2.get_SiteInfo()
# Read usable FLEX images .csv file
df_FLEX = pd.read_csv(s2.path_Output + "\\Usable FLEX Images.csv")
# Initiate some empty lists to save the output values of each loop
list_FLEXName = []
list_ValidPixelsL1C = []
list_ValidPercentageL1C = []
list_ValidPixelsL2A = []
list_ValidPercentageL2A = []
list_CV = []
list_Flag = []
if len(os.listdir(s2.path_Image)) !=0 :
    # Start the main part, a loop that will iterate each row in our output "Usable FLEX Images.csv" file
    for i in range(df_FLEX.shape[0]):
        temp_StartTime = time.time()
        # Get FLEX image date and time
        temp_SiteName = df_FLEX["Site"][i]
        temp_FLEX_Filename = df_FLEX["FLEX Filename"][i]
        temp_FLEX_Date = df_FLEX["FLEX Date"][i]
        temp_FLEX_Time = df_FLEX["FLEX Time"][i]
        temp_FLEX_DateTime = datetime.strptime(str(temp_FLEX_Date)+str(temp_FLEX_Time), '%Y%m%d%H%M%S')
        # Get site name
        temp_Site_Index = df_Site.index[df_Site['Site'] == temp_SiteName].tolist()[0]
        temp_SiteLat = df_Site["Latitude"][temp_Site_Index]
        temp_SiteLon = df_Site["Longitude"][temp_Site_Index]

        # 
        temp_Path_Images_Site = s2.path_Image + "\\" + temp_SiteName

        # Check usable FLEX images
        temp_S2_Image_Final = os.listdir(temp_Path_Images_Site)[0]
        for j in range(len(os.listdir(temp_Path_Images_Site))):
            temp_S2_Image = os.listdir(temp_Path_Images_Site)[j]
            temp_S2_Image_DateTime = temp_S2_Image[0:8] + temp_S2_Image[-6:]
            temp_S2_Image_DateTime = datetime.strptime(temp_S2_Image_DateTime, '%Y%m%d%H%M%S')
            if j == 0:
                temp_TimeDiff_Final = temp_S2_Image_DateTime - temp_FLEX_DateTime
            else:
                temp_TimeDiff = temp_S2_Image_DateTime - temp_FLEX_DateTime
                if abs(temp_TimeDiff) < abs(temp_TimeDiff_Final):
                    temp_TimeDiff_Final = temp_TimeDiff
                    temp_S2_Image_Final = temp_S2_Image
        print(f"S2 image {temp_S2_Image_Final} has the nearest date and time to the FLEX image {temp_FLEX_Filename}")
        list_FLEXName.append(temp_FLEX_Filename)
        print(f"The calculation and validation of the S2 image {temp_S2_Image_Final} of the site {temp_SiteName} has started! ")
        # Get paths to B8 of L1C and B4, B8 of L2A
        path_L1C_B08_raw, path_L2A_B04_raw, path_L2A_B08_raw, path_L1C_Mask, path_L2A_Mask, path_L1C_xml_DS, path_L1C_xml_TL, path_L2A_xml_DS = s2.get_PathImages(temp_SiteName + "\\" + temp_S2_Image_Final)
        # Read images
        image_L1C_B08 = rio.open(path_L1C_B08_raw)
        image_L2A_B04 = rio.open(path_L2A_B04_raw)
        image_L2A_B08 = rio.open(path_L2A_B08_raw)
        # Get the values of the images
        values_L1C_B08 = image_L1C_B08.read(1).astype(np.int32)
        values_L2A_B04 = image_L2A_B04.read(1).astype(np.int32)
        values_L2A_B08 = image_L2A_B08.read(1).astype(np.int32)
        # Create a shapefile of our ROI and another one of the mask
        gdf_ROI = s2.create_Shapefile(image_L1C_B08, image_L2A_B04, temp_SiteName, temp_SiteLat, temp_SiteLon)
        # Read masks of opaque clouds, cirrus clouds and snow ice areas
        mask_L1C = rio.open(path_L1C_Mask)
        mask_L2A = rio.open(path_L2A_Mask)
        mask_L1C_OpaqueClouds = mask_L1C.read(1)
        mask_L1C_CirrusClouds = mask_L1C.read(2)
        mask_L1C_SnowIceAreas = mask_L1C.read(3)
        mask_L2A_OpaqueClouds = mask_L2A.read(1)
        mask_L2A_CirrusClouds = mask_L2A.read(2)
        mask_L2A_SnowIceAreas = mask_L2A.read(3)
        # Check if all three masks are empty. If not empty, we should check if the masked
        mask_L2ACombined = mask_L2A_OpaqueClouds + mask_L2A_CirrusClouds + mask_L2A_SnowIceAreas
        mask_L1CCombined = mask_L1C_OpaqueClouds + mask_L1C_CirrusClouds + mask_L1C_SnowIceAreas
        temp_PassL1C, temp_ValidPixelsL1C, temp_ValidPixelsPercentageL1C = s2.cal_ValidPixels(temp_SiteName, image_L1C_B08, mask_L1CCombined, gdf_ROI, note = "L1C")
        temp_PassL2A, temp_ValidPixelsL2A, temp_ValidPixelsPercentageL2A = s2.cal_ValidPixels(temp_SiteName, image_L2A_B04, mask_L2ACombined, gdf_ROI, note = "L2A")
        list_ValidPixelsL1C.append(temp_ValidPixelsL1C)
        list_ValidPixelsL2A.append(temp_ValidPixelsL2A)
        list_ValidPercentageL1C.append(temp_ValidPixelsPercentageL1C)
        list_ValidPercentageL2A.append(temp_ValidPixelsPercentageL2A)
        if temp_PassL1C and temp_PassL2A:
            # NDVI, Rad, NIRv
            temp_NDVI = s2.cal_L2ANDVI(path_L2A_xml_DS, values_L2A_B04, values_L2A_B08)
            temp_Rad = s2.cal_L1CRad(path_L1C_xml_DS, path_L1C_xml_TL, values_L1C_B08)
            temp_NIRv = temp_NDVI * temp_Rad
            print(f"The NIRv of {temp_SiteName} has been calculated successfully!")
            # Save NIRv.tif to cache folder
            src = image_L1C_B08
            out_meta = src.meta
            out_meta.update({
                "driver": "GTiff",
                "dtype": "float64"
            })
            with rio.open(s2.path_Cache + "\\" + temp_SiteName + "\\NIRv.tif", 'w', **out_meta) as dest:
                dest.write(temp_NIRv, 1)
            
            # Clip the NIRv.tif
            image_NIRv = rio.open(s2.path_Cache + "\\" + temp_SiteName + "\\NIRv.tif")
            s2.clip_RasterbySHP(temp_SiteName, image_NIRv, gdf_ROI, suffix = "NIRv ROI")

            # Read the clipped ROI NIRv.tif
            image_NIRv_ROI = rio.open(s2.path_Cache + "\\" + temp_SiteName + "\\NIRv ROI.tif")
            values_NIRv_ROI = image_NIRv_ROI.read(1)
            temp_CV = s2.cal_CV(values_NIRv_ROI)
            temp_Flag = s2.cal_Flag(temp_CV)
            list_CV.append(temp_CV)
            list_Flag.append(temp_Flag)

            temp_EndTime = time.time()
            temp_ElapsedTime = temp_EndTime - temp_StartTime
            print(f"The calculation and validation of site {temp_SiteName} has been finished successfully, which took {temp_ElapsedTime:.2f} seconds! ")
        else:
            list_CV.append(None)
            list_Flag.append(None)
            continue

    # Loop finished, now we save the output to a new .csv file
    df_Output = pd.DataFrame({
        "Site": list(df_FLEX["Site"]),
        "FLEX Filename": list_FLEXName,
        "Valid Pixels L1C": list_ValidPixelsL1C,
        "Valid Pixels L2A": list_ValidPixelsL2A,
        "Valid Pixels Percentage L1C": list_ValidPercentageL1C,
        "Valid Pixels Percentage L2A": list_ValidPercentageL2A,
        "CV": list_CV,
        "Flag": list_Flag
    })
    print(f"Please find the final output.csv in the following folder: {s2.path_Output}")
    df_Output.to_csv(s2.path_Output + "\\Output_S2.csv", index = False)

    # Delete cache folder? 
    if s2.bool_DeleteCache:
        del image_L1C_B08, image_L2A_B04, image_L2A_B08, image_NIRv, image_NIRv_ROI
        shutil.rmtree(s2.path_Cache)
        print("The cache folder and all its contents has been deleted permanently! ")

else:
    print("WARNING: There are no Sentinel-2 images found inside the input folder. ")


# Elapsed Time
end_Time = time.time()
elapsed_Time = end_Time - start_Time
print(f"This python code has finished its work, and in totale it has taken {elapsed_Time:.2f} seconds!")