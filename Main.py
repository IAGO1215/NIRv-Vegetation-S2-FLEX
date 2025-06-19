# ---------------------------------------------------------------------------- #
#                            Import Python Packages                            #
# ---------------------------------------------------------------------------- #
import os
import time
from datetime import datetime
import shutil
import pandas as pd

# ---------------------------------------------------------------------------- #
#                                 Import Class                                 #
# ---------------------------------------------------------------------------- #
from class_calval import FLEX, S2
    
# ---------------------------------------------------------------------------- #
#                                   Main Code                                  #
# ---------------------------------------------------------------------------- #

def main():
    time_start = time.time()
    print("Code starts!")
    # Initiate classes
    flex = FLEX()
    
    # --------------------------------- FLOX FILE -------------------------------- #
    if os.path.exists(flex.file_flox_csv):
        print("Reading FLOX input!")
        dict_flox_dates = flex.check_flox_dates()
        print(dict_flox_dates)
        time.sleep(1)
        print(f"FLOX input has been read successfully!")
        print("-"*80)
    else:
        raise FileNotFoundError("The FLOX CSV file is not found! Code aborted!")

    # ------------------------------ LOOP EACH SITE ------------------------------ #
    # Read Sites.csv
    df_site = flex.get_site_info()
    print("Now start to proceed all FLEX images!")
    print("-"*80)
    # Create empty lists to store the results
    list_site_name = []
    list_site_lat = []
    list_site_lon = []
    list_roi = []
    list_threshold_cv = []
    list_vegetation_pixel = []
    list_threshold_cloud = []
    list_time_window_days = []

    list_flex_date = []
    list_flex_time = []
    list_flex_filename = []
    list_flex_valid_pixels = []
    list_s2_filename = []
    list_s2_date = []
    list_s2_time = []
    list_s2_valid_pixels = []
    list_time_difference = []
    list_s2_nirv_avg = []
    list_s2_nirv_std = []
    list_s2_nirv_cv = []
    list_s2_nirv_cv_flag = []
    list_s2_ndvi_avg = []
    list_s2_ndvi_std = []
    list_s2_ndvi_cv = []
    list_s2_ndvi_cv_flag = []

    list_note = []

    # Some nested lists for empty output
    list_list_others = [list_flex_date, list_flex_time, list_flex_filename,
                        list_flex_valid_pixels, list_s2_filename, list_s2_date,
                        list_s2_time, list_s2_valid_pixels, list_time_difference,list_s2_nirv_avg,
                        list_s2_nirv_std, list_s2_nirv_cv, list_s2_ndvi_avg, list_s2_ndvi_std,
                        list_s2_ndvi_cv, list_s2_nirv_cv_flag, list_s2_ndvi_cv_flag]
    list_list_others_noflex = [list_s2_filename, list_s2_date,
                    list_s2_time, list_s2_valid_pixels, list_time_difference,list_s2_nirv_avg,
                    list_s2_nirv_std, list_s2_nirv_cv, list_s2_ndvi_avg, list_s2_ndvi_std,
                    list_s2_ndvi_cv, list_s2_nirv_cv_flag, list_s2_ndvi_cv_flag]
    
    # Iterate each site in Sites.csv!
    for index, row in df_site.iterrows():
        temp_start_time = time.time()

        # Read current line site info
        temp_site_name = row['Sites']
        temp_site_lat = row['Latitude']
        temp_site_lon = row['Longitude']
        temp_site_roi = row['ROI']
        temp_site_time_window_days = row['Time Window Days']
        temp_site_threshold_cv = row['Threshold CV']
        temp_site_vegetation_pixel = row['Vegetation Pixel']
        temp_site_threshold_cloud = row['Threshold Cloud']
        # Save current line site info into the lists
        list_site_name.append(temp_site_name)
        list_site_lat.append(temp_site_lat)
        list_site_lon.append(temp_site_lon)
        list_roi.append(temp_site_roi)
        list_threshold_cv.append(temp_site_threshold_cv * 100)
        list_vegetation_pixel.append(temp_site_vegetation_pixel * 100)
        list_time_window_days.append(temp_site_time_window_days)
        list_threshold_cloud.append(temp_site_threshold_cloud * 100)
        # Modify the class attributes accordingly
        flex.vegetation_pixel = temp_site_vegetation_pixel

        # ----------------------------- FLEX IMAGE CHECK ----------------------------- #
        time.sleep(1)
        print("\033[92m" + "*" * 5 + "FLEX IMAGES CHECK" + "*" * 5 + "\033[0m")
        time.sleep(1)
        # Check if there is a folder inside "input_flex_images" for the current site
        temp_site_path_input = os.path.join(flex.path_flex_input,temp_site_name)
        if not os.path.exists(temp_site_path_input):
            print(f"{temp_site_name} doesn't have any input FLEX images! This site has been skipped!")
            print("\033[92m" + "*" * 5 + "FLEX IMAGES CHECK DONE" + "*" * 5 + "\033[0m")
            print("-"*80)
            time.sleep(1)
            for temp_list in list_list_others:
                temp_list.append('N/A')
            list_note.append('No input FLEX images')
            continue
        # Check if there are any FLEX images inside the folder for the current site
        temp_site_flex_images_list = os.listdir(temp_site_path_input)
        temp_site_flex_images_list_nc = [i for i in temp_site_flex_images_list if i.endswith('.nc')]
        temp_site_flex_images_num = len(temp_site_flex_images_list_nc)
        if temp_site_flex_images_num == 0:
            print(f"{temp_site_name} doesn't have any input FLEX images! This site has been skipped!")
            print("\033[92m" + "*" * 5 + "FLEX IMAGES CHECK DONE" + "*" * 5 + "\033[0m")
            print("-"*80)
            time.sleep(1)
            for temp_list in list_list_others:
                temp_list.append('N/A')
            list_note.append('No input FLEX images')
            continue

        # Real work begins here
        print(f"{temp_site_name} has {temp_site_flex_images_num} FLEX image(s)!")
        time.sleep(0.5)
        # Processing all the FLEX images for the current site
        for i in range(temp_site_flex_images_num):
            temp_flex_filename = temp_site_flex_images_list_nc[i]
            print(f"Now starting with No.{i + 1} FLEX image '{temp_flex_filename}' of the site {temp_site_name}")
            # Check FLEX filename format
            flex.check_filename(temp_flex_filename)
            # Get the date of the FLEX image
            temp_flex_date = temp_flex_filename.split('.')[0].split('_')[-2]
            if temp_flex_date not in dict_flox_dates[temp_site_name]:
                print(f"The date of the current FLEX image is {temp_flex_date}, not found in the FLOX input! This site has been skipped!")
                print("\033[92m" + "*" * 5 + "FLEX IMAGES CHECK DONE" + "*" * 5 + "\033[0m")
                print("-"*80)
                time.sleep(1)
                for temp_list in list_list_others:
                    temp_list.append('N/A')
                list_note.append(f'No FLOX data on the same date {temp_flex_date}')
                continue

            ## Start to process the FLEX image
            print(f"The date of the current FLEX image is {temp_flex_date}, found in the FLOX input!!")
            time.sleep(0.5)

            # Veg pixel check - PENDING!!!!!!!!!!
            # if temp_site_vegetation_pixel:
            #     flex.vegetation_pixel = temp_site_vegetation_pixel
            #     print(f"The vegetation pixel threshold for the site {temp_site_name} has been set to {temp_site_vegetation_pixel}!")
            # else:
            #     print("The vegetation pixel threshold is not set, the default value will be used!")
            print("There are enough vegetation pixels inside the ROI in this image! The date and the time of this image will be recorded!")
            time.sleep(0.5)

            # Save the FLEX image information into the lists
            list_flex_filename.append(temp_flex_filename)
            list_flex_date.append(temp_flex_filename.split('.')[0].split('_')[-2])
            list_flex_time.append(temp_flex_filename.split('.')[0].split('_')[-1])
            list_flex_valid_pixels.append(100)
            print("\033[92m" + "*" * 5 + "FLEX IMAGES CHECK DONE" + "*" * 5 + "\033[0m")
            time.sleep(1)
            # ----------------------------- FINDING S2 IMAGE ----------------------------- #
            print("\033[92m" + "*" * 5 + "SEARCHING ONE S2 IMAGE WITH THE NEAREST DATE" + "*" * 5 + "\033[0m")
            time.sleep(0.5)
            # Now look for S2 images
            print(f"Now looking for the nearest Sentinel-2 image for the site {temp_site_name}, within {temp_site_time_window_days} days!")
            temp_flex_image_datetime = datetime.strptime(temp_flex_filename.split('.')[0].split('_')[-2], '%Y%m%d')
            temp_path_s2_images = os.path.join(flex.path_s2_input, temp_site_name)
            temp_s2_image_final = os.listdir(temp_path_s2_images)
            if len(temp_s2_image_final) == 0:
                print(f"No Sentinel-2 images found for the site {temp_site_name}. This site has been skipped!")
                print("-"*80)
                time.sleep(1)
                for temp_list in list_list_others_noflex:
                    temp_list.append('N/A')
                list_note.append(f'No input Sentinel-2 images')
                continue
            else:
                print(f"Found {len(temp_s2_image_final)} Sentinel-2 images for the site {temp_site_name}!")
                time.sleep(1)
                temp_s2_image_final = temp_s2_image_final[0]
                for j in range(len(os.listdir(temp_path_s2_images))):
                    temp_s2_image = os.listdir(temp_path_s2_images)[j]
                    temp_s2_image_date = temp_s2_image.split('_')[2].split('T')[0]
                    temp_s2_image_datetime = datetime.strptime(temp_s2_image_date, '%Y%m%d')
                    if j == 0:
                        temp_timediff_final = temp_s2_image_datetime - temp_flex_image_datetime
                    else:
                        temp_timediff = temp_s2_image_datetime - temp_flex_image_datetime
                        # print(f"Comparing S2 image {temp_s2_image} with FLEX image {temp_flex_filename}, the time difference is {temp_timediff}")
                        if abs(temp_timediff) < abs(temp_timediff_final):
                            temp_timediff_final = temp_timediff
                            temp_s2_image_final = temp_s2_image
                # Check if the difference between the FLEX image date and the S2 image date is greater than the input time_window_days
                if temp_timediff_final.days > temp_site_time_window_days:
                    print(f"The nearest S2 images found for the site {temp_site_name} has time difference greater than {temp_site_time_window_days} days. This site has been skipped!")
                    print("-"*80)
                    time.sleep(1)
                    for temp_list in list_list_others_noflex:
                        temp_list.append('N/A')
                    list_note.append(f'No input Sentinel-2 images available within {temp_site_time_window_days} days')
                    continue
                list_s2_filename.append(temp_s2_image_final)
                list_s2_date.append(temp_s2_image_final.split('_')[2].split('T')[0])
                list_s2_time.append(temp_s2_image_final.split('_')[2].split('T')[1])
                list_time_difference.append(temp_timediff_final.days)
                print(f"S2 image '{temp_s2_image_final}' has the nearest date ({temp_timediff_final.days} days) to the FLEX image {temp_flex_filename}")
                time.sleep(0.5)
                print(f"Now reading the metadata of the S2 image......")
                # Finally we can initiate the S2 class provided we already find the S2 image to use! 
                s2 = S2(temp_site_name, temp_site_lat, temp_site_lon, temp_s2_image_final)
                s2.area = temp_site_roi
                s2.threshold_cv = temp_site_threshold_cv
                s2.cloud = temp_site_threshold_cloud
                s2.flex_filename = temp_flex_filename
                print("\033[92m" + "*" * 5 + "SEARCHING ONE S2 IMAGE WITH THE NEAREST DATE DONE" + "*" * 5 + "\033[0m")
                time.sleep(1)

                # ------------------------------ S2 IMAGE CHECK ------------------------------ #
                print("\033[92m" + "*" * 5 + "S2 Valid Pixel Check" + "*" * 5 + "\033[0m")
                time.sleep(1)

                # Create the cache subfolder for the current site
                s2.create_cache_subfolder(temp_site_name)

                print(f"Checking the valid pixels of the S2 image. Only if the valid pixels are greater than {temp_site_threshold_cloud * 100}% of the total pixels, the S2 image will be used for further processing!")

                # Read masks of opaque clouds, cirrus clouds and snow ice areas
                temp_pass_l2a, temp_valid_pixels_l2a, temp_valid_pixels_percentage_l2a = s2.cal_valid_pixels()
                # Save valid pixel result
                list_s2_valid_pixels.append(temp_valid_pixels_percentage_l2a * 100)

                time.sleep(1)
                # Valid pixels check
                if temp_pass_l2a:
                    print(f"{temp_site_name} and its S2 image {temp_s2_image_final} has sufficient valid pixels!")
                    print("\033[92m" + "*" * 5 + "S2 Valid Pixel Check DONE" + "*" * 5 + "\033[0m")
                    time.sleep(1)
                    # ------------------------------ S2 NDVI NIRvREF ----------------------------- #

                    print("\033[92m" + "*" * 5 + "S2 NDVI & NIRvREF Calculation" + "*" * 5 + "\033[0m")
                    print(f"Now calculating NDVI and NIRvREF inside the ROI of the site {temp_site_name}......")
                    temp_ndvi_std, temp_ndvi_avg, temp_ndvi_cv, temp_ndvi_flag, temp_nirv_std, temp_nirv_avg, temp_nirv_cv, temp_nirv_flag = s2.cal_l2a_indices()
                    list_s2_ndvi_std.append(temp_ndvi_std)
                    list_s2_ndvi_avg.append(temp_ndvi_avg)
                    list_s2_ndvi_cv.append(temp_ndvi_cv * 100)
                    list_s2_ndvi_cv_flag.append(temp_ndvi_flag)
                    list_s2_nirv_std.append(temp_nirv_std)
                    list_s2_nirv_avg.append(temp_nirv_avg)
                    list_s2_nirv_cv.append(temp_nirv_cv * 100)
                    list_s2_nirv_cv_flag.append(temp_nirv_flag)
                    print("\033[92m" + "*" * 5 + "S2 NDVI & NIRvREF Calculation DONE" + "*" * 5 + "\033[0m")

                    # --------------------------------- FLEX SIF --------------------------------- #

                    print("\033[92m" + "*" * 5 + "FLEX SIF Calculation" + "*" * 5 + "\033[0m")
                    time.sleep(0.5)
                    print(f"Now starting to calculate the SIF for the site {temp_site_name} and its FLEX image {temp_flex_filename}!")
                    # Read converted FLEX .tiff file from the cache folder
                    flex.cal_sif(temp_site_name, temp_flex_filename, temp_site_lon, temp_site_lat, temp_site_roi, temp_s2_image_final)
                    flex.sif_output(temp_site_name, temp_flex_filename, temp_site_lon, temp_site_lat, temp_site_roi, temp_s2_image_final)
                    print("\033[92m" + "*" * 5 + "FLEX SIF Calculation DONE" + "*" * 5 + "\033[0m")
                    time.sleep(1)

                    # ----------------------------- Transfer Function ---------------------------- #

                    print("\033[92m" + "*" * 5 + "TRANSFER FUNCTION" + "*" * 5 + "\033[0m")
                    time.sleep(0.5)
                    print(f"Now applying transfer functions for the site {temp_site_name} and its FLEX image {temp_flex_filename}!")
                    bool_flox_invalid = s2.cal_transfer_function(temp_flex_date)
                    if bool_flox_invalid:
                        list_note.append('FLOX is on an invalid pixel')
                    else:
                        list_note.append("N/A")
                    print("\033[92m" + "*" * 5 + "TRANSFER FUNCTION DONE" + "*" * 5 + "\033[0m")

                    temp_end_time = time.time()
                    temp_elapsed_time = temp_end_time - temp_start_time
                    print(f"The calculation and validation of site {temp_site_name} has been finished successfully, which took {temp_elapsed_time:.2f} seconds! ")
                    time.sleep(0.5)
                    print("-"*80)
                    s2.remove_cache()
                    time.sleep(1)

                else:
                    print(f"\033[92mThe calculation and validation of site {temp_site_name} and its S2 image {temp_s2_image_final} has been skipped, due to exceeding invalid pixels!\033[0m")
                    list_s2_nirv_avg.append('N/A')
                    list_s2_nirv_std.append('N/A')
                    list_s2_nirv_cv.append('N/A')
                    list_s2_nirv_cv_flag.append('N/A')
                    list_s2_ndvi_avg.append('N/A')
                    list_s2_ndvi_std.append('N/A')
                    list_s2_ndvi_cv.append('N/A')
                    list_s2_ndvi_cv_flag.append('N/A')
                    list_note.append(f"The percentage of invalid pixels exceeding {s2.cloud * 100}%")
                    print("-"*80)
                    time.sleep(1)
                    continue

    # Loop finished, now we save the output to a new .csv file

    # ---------------------------------- output ---------------------------------- #

    # log report

    df_log_report = pd.DataFrame({
        "site_code": list_site_name,
        "latitude": list_site_lat,
        "longitude": list_site_lon,
        "reference_area": list_roi,
        "time_window": list_time_window_days,
        "threshold_CV": list_threshold_cv,
        "vegetation_pixel": list_vegetation_pixel,
        "threshold_cloud": list_threshold_cloud,
        "flex_date": list_flex_date,
        "flex_time": list_flex_time,
        "flex_filename": list_flex_filename,
        "flex_valid_pixels": list_flex_valid_pixels,
        "s2_filename": list_s2_filename,
        "s2_date": list_s2_date,
        "s2_time": list_s2_time,
        "time_difference_s2_flex": list_time_difference,
        "s2_valid_pixels": list_s2_valid_pixels,
        "s2_ndvi_avg": list_s2_ndvi_avg,
        "s2_ndvi_sd": list_s2_ndvi_std,
        "s2_ndvi_cv": list_s2_ndvi_cv,
        "s2_ndvi_cv_flag": list_s2_ndvi_cv_flag,
        "s2_nirv_avg": list_s2_nirv_avg,
        "s2_nirv_sd": list_s2_nirv_std,
        "s2_nirv_cv": list_s2_nirv_cv,
        "s2_nirv_cv_flag": list_s2_nirv_cv_flag,
        "note": list_note
    })
    df_log_report.to_csv(os.path.join(s2.path_output,"L2B_log_report.csv"), index = False)

    # sif avg
    list_csv_file_avg = []
    for csv_file in os.listdir(os.path.join(s2.path_cache, 'FLEX', 'avg')):
        if csv_file.endswith('.csv'):
            list_csv_file_avg.append(os.path.join(s2.path_cache,'FLEX', 'avg', csv_file))
    df_sif_avg = pd.concat([pd.read_csv(f) for f in list_csv_file_avg], ignore_index=True)
    df_sif_avg.to_csv(os.path.join(s2.path_output, "Full_Spectrum_avg_FLEX_table.csv"), index=False)

    # sif std
    list_csv_file_std = []
    for csv_file in os.listdir(os.path.join(s2.path_cache, 'FLEX', 'std')):
        if csv_file.endswith('.csv'):
            list_csv_file_std.append(os.path.join(s2.path_cache,'FLEX', 'std', csv_file))
    df_sif_std = pd.concat([pd.read_csv(f) for f in list_csv_file_std], ignore_index=True)
    df_sif_std.to_csv(os.path.join(s2.path_output, "Full_Spectrum_std_FLEX_table.csv"), index=False)

    # sif
    list_csv_file = []
    for csv_file in os.listdir(os.path.join(s2.path_cache, 'FLEX', 'sif')):
        if csv_file.endswith('.csv'):
            list_csv_file.append(os.path.join(s2.path_cache,'FLEX', 'sif', csv_file))
    df_sif = pd.concat([pd.read_csv(f) for f in list_csv_file], ignore_index=True)
    df_sif.to_csv(os.path.join(s2.path_cache, "L2B_FLEX_table.csv"), index=False)

    flex.create_matchup_report()
    flex.cal_statistic_flex_flox()
    flex.cal_statistic_flex_tf()
    
    # Delete cache folder? 
    if s2.bool_delete_cache:
        shutil.rmtree(s2.path_cache)
        print("The cache folder and all its contents has been deleted permanently! ")

    print(f"Please find the final output.csv in the following folder: {s2.path_output}")

    # ------------------------------ Code Terminates ----------------------------- #
    time_end = time.time()
    time_elapsed = time_end - time_start
    print(f"This python code has finished its work, and in totale it has taken {time_elapsed:.2f} seconds!")


if __name__ == "__main__":
    main()