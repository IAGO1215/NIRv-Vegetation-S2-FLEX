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
from class_improve import FLEX, S2
    
# ---------------------------------------------------------------------------- #
#                                   Main Code                                  #
# ---------------------------------------------------------------------------- #

def main():
    time_start = time.time()
    print("Code starts!")
    # Initiate classes
    flex = FLEX()

    # ---------------------------- Read Optional Input --------------------------- #
    config = configparser.ConfigParser()
    # Read optional input
    config.read(flex._path_optional)
    bool_optional_input = False
    if config["FLEX"]["area_ROI"]:
        temp = config["FLEX"]["area_ROI"]
        flex._area_ROI = temp
        print(f"The area of the ROI has been modified to {temp} (m) x {temp} (m)!")
        bool_optional_input = True
    if config["FLEX"]["threshold_vegetation_pixel"]:
        temp = config["FLEX"]["threshold_vegetation_pixel"]
        flex._vegetation_pixel = temp
        print(f"The threshold of vegetation pixel has been modified to {temp}!")
        bool_optional_input = True
    # Log if no optional input is provided
    if not bool_optional_input:
        print("No optional input found for FLEX images. The code will use the default values!")

    # -------------------------------- FLEX Images ------------------------------- #
    # Read Sites.csv
    df_site = flex.get_site_info()
    print("Starting to proceed all FLEX images!")
    print("-"*20)
    list_site_name = []
    list_FLEX_date = []
    list_FLEX_time = []
    list_FLEX_filename = []
    # Iterate each site in Sites.csv!
    for index, row in df_site.iterrows():
        # Read site name, lat and lon
        temp_site_name = row['Sites']
        temp_site_lat = row['Latitude']
        temp_site_lon = row['Longitude']
        # Check if the current site has FLEX images!
        temp_site_path_input = os.path.join(flex._path_input,temp_site_name)
        if not os.path.exists(temp_site_path_input):
            print(f"{temp_site_name} doesn't have any input FLEX images! This site has been skipped!")
            print("-"*20)
            continue
        # Check if the current site has FLEX images!
        temp_site_flex_images_list = os.listdir(temp_site_path_input)
        temp_site_flex_images_num = len(temp_site_flex_images_list)
        if temp_site_flex_images_num == 0:
            print(f"{temp_site_name} doesn't have any input FLEX images! This site has been skipped!")
            print("-"*20)
            continue
        # Real work begins
        print(f"{temp_site_name} has {temp_site_flex_images_num} FLEX images!")
        temp_site_path_output = os.path.join(flex._path_output, temp_site_name)
        # Processing all the FLEX images for the current site
        for i in range(temp_site_flex_images_num):
            temp_FLEX_filename = temp_site_flex_images_list[i]
            # Check filename
            flex.check_filename(temp_FLEX_filename)

            ## Start to process the FLEX image
            print(f"Now starting with No.{i + 1} FLEX image '{temp_FLEX_filename}' of the site {temp_site_name}")

            # Veg pixel filter
            if flex._vegetation_pixel:
                print("There are enough vegetation pixels inside the ROI in this image! The date and the time of this image will be recorded!")
                list_site_name.append(temp_site_name)
                list_FLEX_filename.append(temp_FLEX_filename)
                list_FLEX_date.append(temp_FLEX_filename.split('.')[0].split('_')[-2])
                list_FLEX_time.append(temp_FLEX_filename.split('.')[0].split('_')[-1])
            else:
                print("There are enough vegetation pixels inside the ROI in this image! The date and the time of this image will be recorded!")

            # Calculation of SIF
            flex.cal_SIF(temp_site_name, temp_FLEX_filename, temp_site_lon, temp_site_lat)
            print(f"The FLEX image {temp_FLEX_filename} has been processed!")

        print(f"All the FLEX image(s) of the site {temp_site_name} has been processed!")

    # ----------------------------- Sentinel-2 Images ---------------------------- #
    s2 = S2()
    if config["S2"]["threshold_CV"]:
        temp = config["S2"]["threshold_CV"]
        s2._threshold_CV = temp
        print(f"The threshold of CV has been modified to {temp}!")
    if config["S2"]["threshold_Cloud"]:
        s2._cloud = config["Optional Input"]["threshold_Cloud"]
        print(f"The threshold of cloud coverage has been modified to {config["Optional Input"]["threshold_cloud"]}!")
    if config["S2"]["area_ROI"]:
        s2._area = config["Optional Input"]["area_ROI"]
        print(f"The ROI has been modified to {config["Optional Input"]["area_ROI"]} m by {config["Optional Input"]["area_ROI"]} m!")
    if config["General"]["bool_delete_cache"] == "True":
        s2._bool_delete_cache = True
        print("The cache foldeer will be deleted upon the completion of the code! ")
    
    # Read usable FLEX images .csv file
    df_FLEX = pd.read_csv(os.path.join(s2._path_output,"Usable FLEX Images.csv"))
    # Initiate some empty lists to save the output values of each loop
    list_FLEXName = []
    list_ValidPixelsL1C = []
    list_ValidPercentageL1C = []
    list_ValidPixelsL2A = []
    list_ValidPercentageL2A = []
    list_CV = []
    list_Flag = []
    if len(os.listdir(s2._path_input)) !=0 :
        for index, row in df_FLEX.iterrows():
            temp_start_time = time.time()
            temp_site_name = row["Site"]
            temp_FLEX_filename = row["FLEX Filename"]
            temp_FLEX_date = row["FLEX Date"]
            temp_FLEX_time = row["FLEX Time"]
            temp_FLEX_datetime = datetime.strptime(str(temp_FLEX_date)+str(temp_FLEX_time), '%Y%m%d%H%M%S')
            # Get site name
            temp_site_index = df_site.index[df_site['Sites'] == temp_site_name].tolist()[0]
            temp_site_lat = df_site["Latitude"][temp_site_index]
            temp_site_lon = df_site["Longitude"][temp_site_index]
            temp_path_images_site = os.path.join(s2._path_input, temp_site_name)

            # Check usable FLEX images
            temp_S2_image_final = os.listdir(temp_path_images_site)[0]
            for j in range(len(os.listdir(temp_path_images_site))):
                temp_S2_image = os.listdir(temp_path_images_site)[j]
                temp_S2_image_datetime = temp_S2_image[0:8] + temp_S2_image[-6:]
                temp_S2_image_datetime = datetime.strptime(temp_S2_image_datetime, '%Y%m%d%H%M%S')
                if j == 0:
                    temp_timediff_final = temp_S2_image_datetime - temp_FLEX_datetime
                else:
                    temp_timediff = temp_S2_image_datetime - temp_FLEX_datetime
                    if abs(temp_timediff) < abs(temp_timediff_final):
                        temp_timediff_final = temp_timediff
                        temp_S2_image_final = temp_S2_image
            print(f"S2 image {temp_S2_image_final} has the nearest date and time to the FLEX image {temp_FLEX_filename}")
            list_FLEXName.append(temp_FLEX_filename)
            print(f"The calculation and validation of the S2 image {temp_S2_image_final} of the site {temp_site_name} has started! ")
            # Get paths to B8 of L1C and B4, B8 of L2A
            temp_S2_image_path = os.path.join(temp_site_name,temp_S2_image_final)
            s2.create_cache_folder(temp_S2_image_path)
            path_L1C_B08_raw, path_L2A_B04_raw, path_L2A_B08_raw, path_L1C_mask, path_L2A_mask, path_L1C_xml_DS, path_L1C_xml_TL, path_L2A_xml_DS = s2.get_path_images(temp_S2_image_path)
            # Read images
            image_L1C_B08 = rio.open(path_L1C_B08_raw)
            image_L2A_B04 = rio.open(path_L2A_B04_raw)
            image_L2A_B08 = rio.open(path_L2A_B08_raw)
            # Get the values of the images
            values_L1C_B08 = image_L1C_B08.read(1).astype(np.int32)
            values_L2A_B04 = image_L2A_B04.read(1).astype(np.int32)
            values_L2A_B08 = image_L2A_B08.read(1).astype(np.int32)
            # Create a shapefile of our ROI and another one of the mask
            gdf_ROI = s2.create_shapefile(image_L1C_B08, image_L2A_B04, temp_site_name, temp_site_lat, temp_site_lon)
            # Read masks of opaque clouds, cirrus clouds and snow ice areas
            mask_L1C = rio.open(path_L1C_mask)
            mask_L2A = rio.open(path_L2A_mask)
            mask_L1C_OpaqueClouds = mask_L1C.read(1)
            mask_L1C_CirrusClouds = mask_L1C.read(2)
            mask_L1C_SnowIceAreas = mask_L1C.read(3)
            mask_L2A_OpaqueClouds = mask_L2A.read(1)
            mask_L2A_CirrusClouds = mask_L2A.read(2)
            mask_L2A_SnowIceAreas = mask_L2A.read(3)
            # Check if all three masks are empty. If not empty, we should check if the masked
            mask_L2ACombined = mask_L2A_OpaqueClouds + mask_L2A_CirrusClouds + mask_L2A_SnowIceAreas
            mask_L1CCombined = mask_L1C_OpaqueClouds + mask_L1C_CirrusClouds + mask_L1C_SnowIceAreas
            temp_PassL1C, temp_ValidPixelsL1C, temp_ValidPixelsPercentageL1C = s2.cal_valid_pixels(temp_site_name, image_L1C_B08, mask_L1CCombined, gdf_ROI, note = "L1C")
            temp_PassL2A, temp_ValidPixelsL2A, temp_ValidPixelsPercentageL2A = s2.cal_valid_pixels(temp_site_name, image_L2A_B04, mask_L2ACombined, gdf_ROI, note = "L2A")
            list_ValidPixelsL1C.append(temp_ValidPixelsL1C)
            list_ValidPixelsL2A.append(temp_ValidPixelsL2A)
            list_ValidPercentageL1C.append(temp_ValidPixelsPercentageL1C)
            list_ValidPercentageL2A.append(temp_ValidPixelsPercentageL2A)
            if temp_PassL1C and temp_PassL2A:
                # NDVI, Rad, NIRv
                temp_NDVI = s2.cal_L2A_NDVI(path_L2A_xml_DS, values_L2A_B04, values_L2A_B08)
                temp_Rad = s2.cal_L1C_Rad(path_L1C_xml_DS, path_L1C_xml_TL, values_L1C_B08)
                temp_NIRv = temp_NDVI * temp_Rad
                print(f"The NIRv of {temp_site_name} has been calculated successfully!")
                # Save NIRv.tif to cache folder
                src = image_L1C_B08
                out_meta = src.meta
                out_meta.update({
                    "driver": "GTiff",
                    "dtype": "float64"
                })
                with rio.open(os.path.join(s2._path_cache,temp_site_name,"NIRv.tif"), 'w', **out_meta) as dest:
                    dest.write(temp_NIRv, 1)
                
                # Clip the NIRv.tif
                image_NIRv = rio.open(os.path.join(s2._path_cache,temp_site_name,"NIRv.tif"))
                s2.clip_raster_by_shapefile(temp_S2_image_path, image_NIRv, gdf_ROI, suffix = "NIRv ROI")

                # Read the clipped ROI NIRv.tif
                image_NIRv_ROI = rio.open(os.path.join(s2._path_cache,temp_S2_image_path,"NIRv ROI.tif"))
                values_NIRv_ROI = image_NIRv_ROI.read(1)
                temp_CV = s2.cal_CV(values_NIRv_ROI)
                temp_Flag = s2.cal_Flag(temp_CV)
                list_CV.append(temp_CV)
                list_Flag.append(temp_Flag)

                temp_end_time = time.time()
                temp_elapsed_time = temp_end_time - temp_start_time
                print(f"The calculation and validation of site {temp_site_name} and its S2 image {temp_S2_image_final} has been finished successfully, which took {temp_elapsed_time:.2f} seconds! ")
                print("-"*20)
            else:
                print(f"The calculation and validation of site {temp_site_name} and its S2 image {temp_S2_image_final} has been skipped, due to exceeding invalid pixels!")
                list_CV.append(None)
                list_Flag.append(None)
                print("-"*20)
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
        print(f"Please find the final output.csv in the following folder: {s2._path_output}")
        df_Output.to_csv(os.path.join(s2._path_output,"Output_S2.csv"), index = False)

        # Delete cache folder? 
        if s2._bool_delete_cache:
            del image_L1C_B08, image_L2A_B04, image_L2A_B08, image_NIRv, image_NIRv_ROI
            shutil.rmtree(s2._path_cache)
            print("The cache folder and all its contents has been deleted permanently! ")
    else:
        print("WARNING: There are no Sentinel-2 images found inside the input folder. ")
    

    # ------------------------------ Code Terminates ----------------------------- #
    time_end = time.time()
    time_elapsed = time_end - time_start
    print(f"This python code has finished its work, and in totale it has taken {time_elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()

