import time
import shutil
import configparser
import pandas as pd
import rasterio as rio
import rasterio.mask

### Class
from Class import CALVALPrototype
    
### Main Code
start_Time = time.time()
# Initiate the class
calval_Prototype = CALVALPrototype()
# Read optional input
config = configparser.ConfigParser()
config.read(calval_Prototype.path_Optional)
if config["OptionalInput"]["threshold_CV"]:
    calval_Prototype._threshold_CV = config["Optional Input"]["threshold_CV"]
    print(f"The threshold of CV has been modified to {config["Optional Input"]["threshold_CV"]}!")
if config["OptionalInput"]["threshold_cloud"]:
    calval_Prototype._cloud = config["Optional Input"]["threshold_cloud"]
    print(f"The threshold of cloud coverage has been modified to {config["Optional Input"]["threshold_cloud"]}!")
if config["OptionalInput"]["area_ROI"]:
    calval_Prototype._area = config["Optional Input"]["area_ROI"]
    print(f"The ROI has been modified to {config["Optional Input"]["area_ROI"]} m by {config["Optional Input"]["area_ROI"]} m!")
if config["OptionalInput"]["bool_DeleteCache"] == "True":
    calval_Prototype.bool_DeleteCache = True
    print("The cache foldeer will be deleted upon the completion of the code! ")

# Read .csv files to retrieve info of each site
df_Site = calval_Prototype.get_SiteInfo()
# Initiate some empty lists to save the output values of each loop
list_ValidPixelsL1C = []
list_ValidPercentageL1C = []
list_ValidPixelsL2A = []
list_ValidPercentageL2A = []
list_CV = []
list_Flag = []

# Start the main part, a loop that will iterate each site in our input .csv file
for i in range(df_Site.shape[0]):
    temp_StartTime = time.time()
    # Get site name
    temp_SiteName = df_Site["Site"][i]
    temp_SiteLat = df_Site["Latitude"][i]
    temp_SiteLon = df_Site["Longitude"][i]
    print(f"The calculation and validation of site {temp_SiteName} has started! ")
    # Get paths to B8 of L1C and B4, B8 of L2A
    path_L1C_B08_raw, path_L2A_B04_raw, path_L2A_B08_raw, path_L1C_Mask, path_L2A_Mask, path_L1C_xml_DS, path_L1C_xml_TL, path_L2A_xml_DS = calval_Prototype.get_PathImages(temp_SiteName)
    # Read images
    image_L1C_B08 = rio.open(path_L1C_B08_raw)
    image_L2A_B04 = rio.open(path_L2A_B04_raw)
    image_L2A_B08 = rio.open(path_L2A_B08_raw)
    # Get the values of the images
    values_L1C_B08 = image_L1C_B08.read(1)
    values_L2A_B04 = image_L2A_B04.read(1)
    values_L2A_B08 = image_L2A_B08.read(1)
    # Create a shapefile of our ROI and another one of the mask
    gdf_ROI = calval_Prototype.create_Shapefile(image_L1C_B08, image_L2A_B04, temp_SiteName, temp_SiteLat, temp_SiteLon)
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
    temp_PassL1C, temp_ValidPixelsL1C, temp_ValidPixelsPercentageL1C = calval_Prototype.cal_ValidPixels(temp_SiteName, image_L1C_B08, mask_L1CCombined, gdf_ROI, note = "L1C")
    temp_PassL2A, temp_ValidPixelsL2A, temp_ValidPixelsPercentageL2A = calval_Prototype.cal_ValidPixels(temp_SiteName, image_L2A_B04, mask_L2ACombined, gdf_ROI, note = "L2A")
    list_ValidPixelsL1C.append(temp_ValidPixelsL1C)
    list_ValidPixelsL2A.append(temp_ValidPixelsL2A)
    list_ValidPercentageL1C.append(temp_ValidPixelsPercentageL1C)
    list_ValidPercentageL2A.append(temp_ValidPixelsPercentageL2A)
    if temp_PassL1C and temp_PassL2A:
        # NDVI, Rad, NIRv
        temp_NDVI = calval_Prototype.cal_L2ANDVI(path_L2A_xml_DS, values_L2A_B04, values_L2A_B08)
        temp_Rad = calval_Prototype.cal_L1CRad(path_L1C_xml_DS, path_L1C_xml_TL, values_L1C_B08)
        temp_NIRv = temp_NDVI * temp_Rad
        print(f"The NIRv of {temp_SiteName} has been calculated successfully!")
        # Save NIRv.tif to cache folder
        src = image_L1C_B08
        out_meta = src.meta
        out_meta.update({
            "driver": "GTiff",
            "dtype": 'float64'
        })
        with rio.open(calval_Prototype.path_Cache + "\\" + temp_SiteName + "\\NIRv.tif", 'w', **out_meta) as dest:
            dest.write(temp_NIRv, 1)
        
        # Clip the NIRv.tif
        image_NIRv = rio.open(calval_Prototype.path_Cache + "\\" + temp_SiteName + "\\NIRv.tif")
        calval_Prototype.clip_RasterbySHP(temp_SiteName, image_NIRv, gdf_ROI, suffix = "NIRv ROI")

        # Read the clipped ROI NIRv.tif
        image_NIRv_ROI = rio.open(calval_Prototype.path_Cache + "\\" + temp_SiteName + "\\NIRv ROI.tif")
        values_NIRv_ROI = image_NIRv_ROI.read(1)
        temp_CV = calval_Prototype.cal_CV(values_NIRv_ROI)
        temp_Flag = calval_Prototype.cal_Flag(temp_CV)
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
    "Site": list(df_Site["Site"]),
    "Valid Pixels L1C": list_ValidPixelsL1C,
    "Valid Pixels L2A": list_ValidPixelsL2A,
    "Valid Pixels Percentage L1C": list_ValidPercentageL1C,
    "Valid Pixels Percentage L2A": list_ValidPercentageL2A,
    "CV": list_CV,
    "Flag": list_Flag
})
print(f"Please find the final output.csv in the following folder: {calval_Prototype.path_Output}")
df_Output.to_csv(calval_Prototype.path_Output + "\\Output.csv", index = False)

# Elapsed Time
end_Time = time.time()
elapsed_Time = end_Time - start_Time
num_Sites = df_Site.shape[0]
average_Time = elapsed_Time / num_Sites
# Delete cache folder? 
if calval_Prototype.bool_DeleteCache:
    del image_L1C_B08, image_L2A_B04, image_L2A_B08, image_NIRv, image_NIRv_ROI
    shutil.rmtree(calval_Prototype.path_Cache)
    print("The cache folder and all its contents has been deleted permanently! ")
print(f"This python code has finished its work, and in totale it has taken {elapsed_Time:.2f}!")
print(f"All {num_Sites} sites have been validated, and the average process time for each site is {average_Time:.2f} seconds! ")

  
