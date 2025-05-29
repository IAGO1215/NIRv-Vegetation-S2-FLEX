# ---------------------------------------------------------------------------- #
#                            Import Python Packages                            #
# ---------------------------------------------------------------------------- #
import os
import time
import csv
from datetime import datetime
import shutil
import configparser
import numpy as np
import pandas as pd
import rasterio as rio
# Don't remove rasterio.mask this package otherwise it could cause errors
import rasterio.mask

# ---------------------------------------------------------------------------- #
#                                 Import Class                                 #
# ---------------------------------------------------------------------------- #
from class_calval import FLEX, S2
from class_sif_calculation import SIF
    
# ---------------------------------------------------------------------------- #
#                                   Main Code                                  #
# ---------------------------------------------------------------------------- #

def main():
    time_start = time.time()
    print("Code starts!")
    # Initiate classes
    flex = FLEX()
    sif = SIF()

    # -------------------------------- FLEX Images ------------------------------- #
    config = configparser.ConfigParser()
    # Read optional input
    config.read(flex.file_optional)
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

    # Read Sites.csv
    df_site = flex.get_site_info()
    print("Starting to proceed all FLEX images!")
    print("-"*20)
    list_site_name = []
    list_flex_date = []
    list_flex_time = []
    list_flex_filename = []
    # Iterate each site in Sites.csv!
    for index, row in df_site.iterrows():
        # Read site name, lat and lon
        temp_site_name = row['Sites']
        temp_site_lat = row['Latitude']
        temp_site_lon = row['Longitude']
        # Check if the current site has FLEX images!
        temp_site_path_input = os.path.join(flex.path_input,temp_site_name)

        if not os.path.exists(temp_site_path_input):
            print(f"{temp_site_name} doesn't have any input FLEX images! This site has been skipped!")
            print("-"*20)
            continue
        # Check if the current site has FLEX images!
        temp_site_flex_images_list = os.listdir(temp_site_path_input)
        temp_site_flex_images_list_nc = [i for i in temp_site_flex_images_list if i.endswith('.nc')]
        temp_site_flex_images_num = len(temp_site_flex_images_list_nc)
        if temp_site_flex_images_num == 0:
            print(f"{temp_site_name} doesn't have any input FLEX images! This site has been skipped!")
            print("-"*20)
            continue
        # Real work begins
        print(f"{temp_site_name} has {temp_site_flex_images_num} FLEX images!")
        # Processing all the FLEX images for the current site
        for i in range(temp_site_flex_images_num):
            temp_flex_filename = temp_site_flex_images_list_nc[i]
            # Check filename
            flex.check_filename(temp_flex_filename)

            ## Start to process the FLEX image
            print(f"Now starting with No.{i + 1} FLEX image '{temp_flex_filename}' of the site {temp_site_name}")

            # Veg pixel filter; pending!
            if flex._vegetation_pixel:
                print("There are enough vegetation pixels inside the ROI in this image! The date and the time of this image will be recorded!")
                list_site_name.append(temp_site_name)
                list_flex_filename.append(temp_flex_filename)
                list_flex_date.append(temp_flex_filename.split('.')[0].split('_')[-2])
                list_flex_time.append(temp_flex_filename.split('.')[0].split('_')[-1])
            else:
                print("There are enough vegetation pixels inside the ROI in this image! The date and the time of this image will be recorded!")

            # Calculation of SIF
            flex.cal_SIF(temp_site_name, temp_flex_filename, temp_site_lon, temp_site_lat, bool_save = True)
            sif.SIF_avg_output(temp_site_name, temp_flex_filename, temp_site_lon, temp_site_lat, bool_save = True)
            print(f"The FLEX image {temp_flex_filename} has been processed!")
        print(f"All the FLEX image(s) of the site {temp_site_name} has been processed!")
        print("-"*20)
    print("All the input FLEX images have been processed!")
    print("-"*20)

    print("Now starting to save the usable FLEX images to a .csv file!")
    with open(os.path.join(flex.path_output,"Usable FLEX Images.csv"), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Site","FLEX Filename","FLEX Date","FLEX Time"])
        for i in range(len(list_site_name)):
            writer.writerow([list_site_name[i],list_flex_filename[i],list_flex_date[i],list_flex_time[i]])
    print("The information of all usable FLEX images have been saved to a .csv file!")
    print("-"*20)

    print("Now starting to merge the SIF results of all the usable FLEX images of all sites into one .csv file!")
    df_flex_merged = []
    df_usable_flex = pd.read_csv(os.path.join(flex._path_output,"Usable FLEX Images.csv"))
    for index, row in df_usable_flex.iterrows():
        temp_site_name = row['Site']
        temp_filename = row['FLEX Filename']
        temp_df = pd.read_csv(os.path.join(flex._path_output,temp_site_name,temp_filename + " - sif avg.csv"))
        df_flex_merged.append(temp_df)
    df_flex_merged = pd.concat(df_flex_merged, ignore_index=True)
    df_flex_merged.to_csv(os.path.join(flex._path_output,"flex_sifparms_filt_flextime_aggr_avg_allsites.csv"), index = False)
    print("The SIF results of all the usable FLEX images have been merged into one .csv file!")
    print("-"*20)

    if os.path.exists(sif.file_flox_csv):
        print("The FLOX CSV file is found. The statistic calculation will be performed now!")
        sif.cal_statistic(bool_save = True)
    else:
        print("The FLOX CSV file is not found. The statistic calculation will be skipped!")
    print("-"*20)

    # ----------------------------- Sentinel-2 Images ---------------------------- #
    print("Now starting to process Sentinel-2 images based on usable FLEX images found in the last section!")
    print("-"*20)
    s2 = S2()
    if config["S2"]["threshold_CV"]:
        temp = config["S2"]["threshold_CV"]
        s2._threshold_CV = temp
        print(f"The threshold of CV has been modified to {temp}!")
    if config["S2"]["threshold_Cloud"]:
        s2._cloud = config["Optional Input"]["threshold_Cloud"]
        print(f"The threshold of cloud coverage has been modified to {config['Optional Input']['threshold_cloud']}!")
    if config["S2"]["area_ROI"]:
        s2._area = config["Optional Input"]["area_ROI"]
        print(f"The ROI has been modified to {config['Optional Input']['area_ROI']} m by {config['Optional Input']['area_ROI']} m!")
    if config["General"]["bool_delete_cache"] == "True":
        s2._bool_delete_cache = True
        # print("The cache foldeer will be deleted upon the completion of the code! ")
    
    # Read usable FLEX images .csv file
    df_flex = pd.read_csv(os.path.join(s2._path_output,"Usable FLEX Images.csv"))
    # Initiate some empty lists to save the output values of each loop
    list_valid_site_name = []
    list_flex_name = []
    list_valid_pixels_l1c = []
    list_valid_percentage_l1c = []
    list_valid_pixels_l2a = []
    list_valid_percentage_l2a = []
    list_cv = []
    list_flag = []
    if len(os.listdir(s2.path_input)) !=0 :
        for index, row in df_flex.iterrows():
            temp_start_time = time.time()
            temp_site_name = row["Site"]
            temp_flex_filename = row["FLEX Filename"]
            print(f"Now starting to process the site {temp_site_name} and its FLEX image {temp_flex_filename}!")
            temp_flex_date = row["FLEX Date"]
            temp_flex_time = row["FLEX Time"]
            temp_flex_datetime = datetime.strptime(str(temp_flex_date)+str(temp_flex_time), '%Y%m%d%H%M%S')
            # Get site name
            temp_site_index = df_site.index[df_site['Sites'] == temp_site_name].tolist()[0]
            temp_site_lat = df_site["Latitude"][temp_site_index]
            temp_site_lon = df_site["Longitude"][temp_site_index]
            temp_path_images_site = os.path.join(s2.path_input, temp_site_name)

            # Check usable FLEX images
            temp_s2_image_final = os.listdir(temp_path_images_site)
            if len(temp_s2_image_final) == 0:
                print(f"No Sentinel-2 images found for the site {temp_site_name}. This site has been skipped!")
                print("-"*20)
                continue
            else:
                temp_s2_image_final = temp_s2_image_final[0]
                for j in range(len(os.listdir(temp_path_images_site))):
                    temp_s2_image = os.listdir(temp_path_images_site)[j]
                    temp_s2_image_datetime = temp_s2_image[0:8] + temp_s2_image[-6:]
                    temp_s2_image_datetime = datetime.strptime(temp_s2_image_datetime, '%Y%m%d%H%M%S')
                    if j == 0:
                        temp_timediff_final = temp_s2_image_datetime - temp_flex_datetime
                    else:
                        temp_timediff = temp_s2_image_datetime - temp_flex_datetime
                        # print(f"Comparing S2 image {temp_s2_image} with FLEX image {temp_flex_filename}, the time difference is {temp_timediff}")
                        if abs(temp_timediff) < abs(temp_timediff_final):
                            temp_timediff_final = temp_timediff
                            temp_s2_image_final = temp_s2_image
                print(f"S2 image {temp_s2_image_final} has the nearest date and time to the FLEX image {temp_flex_filename}")
                list_valid_site_name.append(temp_site_name)
                list_flex_name.append(temp_flex_filename)
                print(f"The calculation and validation of the S2 image {temp_s2_image_final} of the site {temp_site_name} has started! ")
                # Get paths to B8 of L1C and B4, B8 of L2A
                temp_s2_image_path = os.path.join(temp_site_name,temp_s2_image_final)
                s2.create_cache_subfolder(temp_s2_image_path)
                path_l1c_b08_raw, path_l2a_b04_raw, path_l2a_b08_raw, path_l1c_mask, path_l2a_mask, path_l1c_xml_ds, path_l1c_xml_tl, path_l2a_xml_ds = s2.get_path_images(temp_s2_image_path)
                # Read images
                image_l1c_b08 = rio.open(path_l1c_b08_raw)
                image_l2a_b04 = rio.open(path_l2a_b04_raw)
                image_l2a_b08 = rio.open(path_l2a_b08_raw)
                # Get the values of the images
                values_l1c_b08 = image_l1c_b08.read(1).astype(np.int32)
                values_l2a_b04 = image_l2a_b04.read(1).astype(np.int32)
                values_l2a_b08 = image_l2a_b08.read(1).astype(np.int32)
                # Create a shapefile of our ROI and another one of the mask
                gdf_roi = s2.create_shapefile(image_l1c_b08, image_l2a_b04, temp_site_name, temp_site_lat, temp_site_lon)
                # Read masks of opaque clouds, cirrus clouds and snow ice areas
                mask_l1c = rio.open(path_l1c_mask)
                mask_l2a = rio.open(path_l2a_mask)
                mask_l1c_opaque_clouds = mask_l1c.read(1)
                mask_l1c_cirrus_clouds = mask_l1c.read(2)
                mask_l1c_snowice_areas = mask_l1c.read(3)
                mask_l2a_opaque_clouds = mask_l2a.read(1)
                mask_l2a_cirrus_clouds = mask_l2a.read(2)
                mask_l2a_snowice_areas = mask_l2a.read(3)
                # Check if all three masks are empty. If not empty, we should check if the masked
                mask_l2a_combined = mask_l2a_opaque_clouds + mask_l2a_cirrus_clouds + mask_l2a_snowice_areas
                mask_l1c_combined = mask_l1c_opaque_clouds + mask_l1c_cirrus_clouds + mask_l1c_snowice_areas
                temp_pass_l1c, temp_valid_pixels_l1c, temp_valid_pixels_percentage_l1c = s2.cal_valid_pixels(temp_site_name, image_l1c_b08, mask_l1c_combined, gdf_roi, note = "L1C")
                temp_pass_l2a, temp_valid_pixels_l2a, temp_valid_pixels_percentage_l2a = s2.cal_valid_pixels(temp_site_name, image_l2a_b04, mask_l2a_combined, gdf_roi, note = "L2A")
                list_valid_pixels_l1c.append(temp_valid_pixels_l1c)
                list_valid_pixels_l2a.append(temp_valid_pixels_l2a)
                list_valid_percentage_l1c.append(temp_valid_pixels_percentage_l1c)
                list_valid_percentage_l2a.append(temp_valid_pixels_percentage_l2a)
                if temp_pass_l1c and temp_pass_l2a:
                    # NDVI, Rad, NIRv
                    temp_ndvi = s2.cal_l2a_ndvi(path_l2a_xml_ds, values_l2a_b04, values_l2a_b08)
                    temp_rad = s2.cal_l1c_rad(path_l1c_xml_ds, path_l1c_xml_tl, values_l1c_b08)
                    temp_nirv = temp_ndvi * temp_rad
                    print(f"The NIRv of {temp_site_name} has been calculated successfully!")
                    # Save NIRv.tif to cache folder
                    src = image_l1c_b08
                    out_meta = src.meta
                    out_meta.update({
                        "driver": "GTiff",
                        "dtype": "float64"
                    })
                    with rio.open(os.path.join(s2._path_cache,temp_site_name,"NIRv.tif"), 'w', **out_meta) as dest:
                        dest.write(temp_nirv, 1)
                    
                    # Clip the NIRv.tif
                    image_nirv = rio.open(os.path.join(s2._path_cache,temp_site_name,"NIRv.tif"))
                    s2.clip_raster_by_shapefile(temp_s2_image_path, image_nirv, gdf_roi, suffix = "NIRv ROI")

                    # Read the clipped ROI NIRv.tif
                    image_nirv_roi = rio.open(os.path.join(s2._path_cache,temp_s2_image_path,"NIRv ROI.tif"))
                    values_nirv_roi = image_nirv_roi.read(1)
                    temp_cv = s2.cal_cv(values_nirv_roi)
                    temp_flag = s2.cal_flag(temp_cv)
                    list_cv.append(temp_cv)
                    list_flag.append(temp_flag)

                    temp_end_time = time.time()
                    temp_elapsed_time = temp_end_time - temp_start_time
                    print(f"The calculation and validation of site {temp_site_name} and its S2 image {temp_s2_image_final} has been finished successfully, which took {temp_elapsed_time:.2f} seconds! ")
                    print("-"*20)
                else:
                    print(f"The calculation and validation of site {temp_site_name} and its S2 image {temp_s2_image_final} has been skipped, due to exceeding invalid pixels!")
                    list_cv.append(None)
                    list_flag.append(None)
                    print("-"*20)
                    continue

        # Loop finished, now we save the output to a new .csv file
        df_output = pd.DataFrame({
            "Site": list_valid_site_name,
            "FLEX Filename": list_flex_name,
            "Valid Pixels L1C": list_valid_pixels_l1c,
            "Valid Pixels L2A": list_valid_percentage_l2a,
            "Valid Pixels Percentage L1C": list_valid_percentage_l1c,
            "Valid Pixels Percentage L2A": list_valid_percentage_l2a,
            "CV": list_cv,
            "Flag": list_flag
        })

        
        # Delete cache folder? 
        if s2._bool_delete_cache:
            del image_l1c_b08, image_l2a_b04, image_l2a_b08, image_nirv, image_nirv_roi
            shutil.rmtree(s2._path_cache)
            print("The cache folder and all its contents has been deleted permanently! ")

        print(f"Please find the final output.csv in the following folder: {s2._path_output}")
        df_output.to_csv(os.path.join(s2._path_output,"Output_S2.csv"), index = False)

    else:
        print("WARNING: There are no Sentinel-2 images found inside the input folder. ")
    

    # ------------------------------ Code Terminates ----------------------------- #
    time_end = time.time()
    time_elapsed = time_end - time_start
    print(f"This python code has finished its work, and in totale it has taken {time_elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()

