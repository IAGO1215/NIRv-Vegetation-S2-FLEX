import os
from bs4 import BeautifulSoup
import math
import numpy as np
import shapely as shp
import pandas as pd
import geopandas as gpd
import rasterio as rio
import rasterio.mask

class S2:
    # Initialization
    def __init__(self):
        # Set a threshold of CV. You can change this value according to your own need, but note that there is no sense if the threshold is not greater than 0. The threshold of CV is set to 0.2 by default. 
        self._threshold_CV = 0.2
        # Set the side-length of the ROI. The ROI must be a squared area. This value must be a multiple of 10. The side-length of the ROI is 900 meters by default. 
        self._area = 900
        # Cloud coverage
        self._cloud = 0.5

        # The path to some essential folders and files. Don't modify these unless you know what you are going to do. 
        # The absolute path of the current working directory
        self.path_Main = os.path.realpath(os.path.dirname(__file__))
        # The absolute path of the output
        self.path_Output = self.path_Main + "\\Output"
        # The absolute path of the S2 images
        self.path_Image = self.path_Main + "\\Input S2 Images"
        # The absolute path to the input .csv file, where the info of all sites are saved. 
        self.path_SiteCSV = self.path_Main + "\\Sites.csv"
        # The absolute path to the folder, where interim files are saved. If you want to modify this path, be cautious. 
        self.path_Cache = self.path_Main + "\\Cache"
        # The absolute path to the folder of "Main - Optional Input.ini"
        self.path_Optional = self.path_Main + "\\Optional Input.ini"

        # A boolean variable which determines whether the cache files will be deleted unpon the completion of the code. False by default. 
        self.bool_DeleteCache = False

        if not os.path.exists(self.path_Cache):
            print("Creating cache folder")
            os.makedirs(self.path_Cache)
        else:
            if not self.bool_DeleteCache:
                print("The cache files will be saved in the following folder: " + self.path_Cache)

        if not os.path.exists(self.path_Output):
            print("Creating cache folder")
            os.makedirs(self.path_Output)

        def cache_Folder():
            temp_df = pd.read_csv(self.path_SiteCSV)
            for i in range(temp_df.shape[0]):
                temp_Name = temp_df["Site"][i]
                if not os.path.exists(self.path_Cache + "\\" + temp_Name):
                    os.makedirs(self.path_Cache + "\\" + temp_Name)
            if not self.bool_DeleteCache:
                print("Subfolders created successfully inside cache folder!")
        
        cache_Folder()

    @property
    def threshold_CV(self):
        return self._threshold_CV
    @property
    def area(self):
        return self._area
    @property
    def cloud(self):
        return self._cloud
    
    @threshold_CV.setter
    def threshold_CV(self, value):
        if value <=0:
            raise ValueError("The threshold of CV should be greater than 0!!!")
        self._threshold_CV = value
    @area.setter
    def area(self, value):
        if value % 10 != 0:
            raise ValueError("The side-length of ROI must be a multiple of 10 meters!!!")
        self._area = value
    @cloud.setter
    def cloud(self, value):
        if value < 0 or value > 1:
            raise ValueError("The cloud coverage must be between 0 and 1!!!")
        self._cloud = value

    # Get names, lat, lon of all sites from .csv file, returning a pandas dataframe
    def get_SiteInfo(self):
        temp_CSV = pd.read_csv(self.path_SiteCSV)
        temp_SiteName = list(temp_CSV["Site"])
        temp_SiteLat = list(temp_CSV["Latitude"])
        temp_SiteLon = list(temp_CSV["Longitude"])
        if len(temp_SiteName) == len(temp_SiteLat) == len(temp_SiteLon):
            return temp_CSV
        else:
            print("User Error: Please make sure there is no missing data in the .csv file!")
            return
    
    # Create subfolders inside Input S2 Images 
    def create_InputSubfolders(self, dataFrame):
        for i in range(dataFrame.shape[0]):
            if not os.path.exists(self.path_Image + "\\" + dataFrame.loc[i,"Site"]):
                os.makedirs(self.path_Image + "\\" + dataFrame.loc[i,"Site"])
                os.makedirs(self.path_Image + "\\" + dataFrame.loc[i,"Site"] + "\\L2A")
                os.makedirs(self.path_Image + "\\" + dataFrame.loc[i,"Site"] + "\\L1C")
                print(f"Subfolders of {dataFrame.loc[i,"Site"]} have been created succesfully inside input S2 image folder!")

    # Get paths to S2 images and mask images. In this case we need B8 image of L1C and B4, B8 images of L2A
    def get_PathImages(self, site_Name):
        # L1C
        temp_PathL1C = self.path_Image + "\\" + site_Name + "\\L1C"
        for path, subdirs ,files in os.walk(temp_PathL1C):
            for name in files:
                temp = os.path.join(path, name)
                if "IMG_DATA" in temp and temp[-3:] == 'jp2' and "B08" in temp:
                    path_L1C_B08_raw = temp
                # Path to the mask file
                if "MSK_CLASSI_B00" in temp and temp[-3:] == 'jp2':
                    path_L1C_Mask = temp
                # Get the path to the XML file "MTD_DS" of L1C raster, where there are values of "U", "Solar Irradiance", "Quantification Value" and "Radiometric Offset"
                if "MTD_DS.xml" in temp:
                    path_L1C_xml_DS = temp
                # Get the path to the XML file "MTD_TL" of L1C raster, where there are values (matrices) of "Solar Zenith Angle". 
                if "MTD_TL.xml" in temp:
                    path_L1C_xml_TL = temp
        # L2A
        temp_PathL2A = self.path_Image + "\\" + site_Name + "\\L2A"
        for path, subdirs, files in os.walk(temp_PathL2A):
            for name in files:
                temp = os.path.join(path, name)
                if temp[-3:] == 'jp2'in temp and "10m" in temp and "B04" in temp :
                    path_L2A_B04_raw = temp
                if temp[-3:] == 'jp2'in temp and "10m" in temp and "B08" in temp :
                    path_L2A_B08_raw = temp
                # Path to the mask file
                if "MSK_CLASSI_B00" in temp and temp[-3:] == 'jp2':
                    path_L2A_Mask = temp
                # Get the path to the XML file "MTD_DS" of L1C raster, where there are values of "Quantification Value" and "Radiometric Offset"
                if "MTD_DS.xml" in temp:
                    path_L2A_xml_DS = temp
        if not os.path.exists(temp_PathL1C) or not os.path.exists(temp_PathL2A):
            print("User Error: Please organise the input S2 images in correct folder hierarchy. Input S2 Images\\SiteName\\L1C\\ and Input S2 Images\\SiteName\\L2A\\")
            return
        else:
            return path_L1C_B08_raw, path_L2A_B04_raw, path_L2A_B08_raw, path_L1C_Mask, path_L2A_Mask, path_L1C_xml_DS, path_L1C_xml_TL, path_L2A_xml_DS
    
    # Create a ROI shapefile, centered at the site. You can modify the side-length of the shapefile by changing the value of "area" of this class. 
    def create_Shapefile(self, img_L1C, img_L2A, site_Name, site_Lat, site_Lon, bool_toSave = False):
        # Get the crs of input L1C image and L2A image
        crs_L1C = img_L1C.crs.data["init"].split(":")[1]
        crs_L2A = img_L2A.crs.data["init"].split(":")[1]
        # In the case that L1C and L2A have different crs, give an error. But this won't happen if the input images are correct. 
        if crs_L2A != crs_L1C:
            raise SystemExit("Stop right there!")
            return
        crs_Final = 'EPSG:' + crs_L1C
        # Create a point shapefile based on the site, using Lon-Lat
        df_4326 = pd.DataFrame({
            "Site": [site_Name],
            "Latitude": [site_Lat],
            "Longitude": [site_Lon]
        })
        gdf_4326 = gpd.GeoDataFrame(
            df_4326,
            geometry = gpd.points_from_xy(df_4326['Longitude'], df_4326['Latitude']),
            crs = "EPSG:4326"
        )
        gdf_New = gdf_4326.copy()
        gdf_New = gdf_New.to_crs(crs_Final)
        # First we retrieve the x, y coordinate of our site
        site_x = gdf_New.geometry.x.values[0]
        site_y = gdf_New.geometry.y.values[0]
        site_row, site_col = img_L2A.index(site_x, site_y)
        site_pixel_x, site_pixel_y = img_L2A.xy(site_row, site_col)
        # Calculate the "cardinal" distance
        side_length_half = self._area / 2
        if side_length_half % 2 == 0:
            # If the half of the side length is even, we need to add another 5 meters to make sure the pixels on the borders will not be omitted when we clip the raster images. 
            length_Cardinal = side_length_half + 5
        else:
            length_Cardinal = side_length_half
        site_x_left_New = site_pixel_x - length_Cardinal
        site_x_right_New = site_pixel_x + length_Cardinal
        site_y_top_New = site_pixel_y + length_Cardinal
        site_y_bottom_New = site_pixel_y - length_Cardinal
        # Create a bounding box
        shp_New = shp.box(site_x_left_New, site_y_bottom_New, site_x_right_New, site_y_top_New)
        # Create shapefile! 
        gdf_New = gpd.GeoDataFrame(
            pd.DataFrame({"0": ["0"]}),
            geometry=[shp_New],
            crs = crs_Final
        )
        return gdf_New

    def cal_L2ANDVI(self, path_L2A_xml_DS, values_L2A_B04, values_L2A_B08):
        # Read the DS xml file of L2A
        with open(path_L2A_xml_DS, 'r') as f:
            data = f.read()
        BS_L2A_dS = BeautifulSoup(data, "xml")
        # Get the quantification value! 
        quantification_L2A = int(BS_L2A_dS.find("BOA_QUANTIFICATION_VALUE").text)
        # Get the radiometric offset!
        offset_L2A_B04 = int(BS_L2A_dS.find("BOA_ADD_OFFSET", {"band_id": "3"}).text)
        offset_L2A_B08 = int(BS_L2A_dS.find("BOA_ADD_OFFSET", {"band_id": "7"}).text)
        # Calculate NDVI of L2A! 
        temp_NDVI = ((values_L2A_B08 + offset_L2A_B08).astype(float) / quantification_L2A - (values_L2A_B04 + offset_L2A_B04).astype(float) / quantification_L2A) / ((values_L2A_B08 + offset_L2A_B08).astype(float) / quantification_L2A + (values_L2A_B04 + offset_L2A_B04).astype(float) / quantification_L2A )
        return temp_NDVI
    
    def cal_L1CRad(self, path_L1C_xml_DS, path_L1C_xml_TL, values_L1C_B08):
        with open(path_L1C_xml_DS, 'r') as f:
            data = f.read()
        BS_L1C_dS = BeautifulSoup(data, "xml")
        # Get the quantification value! 
        quantification_L1C = int(BS_L1C_dS.find("QUANTIFICATION_VALUE").text)
        # Get the radiometric offset!
        offset_L1C = int(BS_L1C_dS.find("RADIO_ADD_OFFSET", {"band_id": "7"}).text)
        # Get the U
        U_L1C = float(BS_L1C_dS.find("U").text)
        # Get the solar irradiance
        SolarIrr = float(BS_L1C_dS.find("SOLAR_IRRADIANCE", {"bandId": "7"}).text)
        # Read the TL xml file of L1C
        with open(path_L1C_xml_TL, 'r') as f:
            data = f.read()
        BS_L1C_dS = BeautifulSoup(data, "xml")
        # Get the sun zenith angle! There should be a 23 x 23 arrays in the xml. Now we save each row as an array and keep all these arrays into a list
        list_SunZenith = []
        for row in BS_L1C_dS.find("Sun_Angles_Grid").find("Zenith").find_all("VALUES"):
            temp_List = row.text.split(" ")
            temp_Arr = np.array(temp_List)
            temp_Arr = temp_Arr.astype(float)
            list_SunZenith.append(temp_Arr)
        # Now we stack these nested-in-list arrays into a 2d array
        index = 0
        for arr in list_SunZenith:
            if index == 0:
                arr_SunZenith = arr
            else:
                arr_SunZenith = np.vstack((arr_SunZenith, arr))
            index = index + 1
        # Get the shape of L1C image, which should be (10980, 10980)
        shape_L1C = values_L1C_B08.shape
        # Repeat each element of sun zenith angle array, in both axies. The final array should have a shape of (11500, 11500)
        arr_SunZenith_Repeat = np.repeat(arr_SunZenith, 500, axis = 1)
        arr_SunZenith_Repeat = np.repeat(arr_SunZenith_Repeat, 500, axis = 0)
        # Index only the first 10980 of each dimension
        arr_SunZenith_Assigned = arr_SunZenith_Repeat[0:shape_L1C[0], 0:shape_L1C[1]]
        # radiance = reflectance * cos(radians(SunZenithAngle)) * solarIrradiance * U / pi
        temp_Radiance = (values_L1C_B08 + offset_L1C).astype(float)  * np.cos(np.radians(arr_SunZenith_Assigned)) * SolarIrr / quantification_L1C / (math.pi * (1 / U_L1C))
        return temp_Radiance
        
    def clip_RasterbySHP(self, site_Name, raster, shp, suffix = None):
        out_image, out_transform = rio.mask.mask(raster, shp.geometry, crop=True)
        out_meta = raster.meta
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})

        with rio.open(self.path_Cache + "\\" + site_Name + "\\" + suffix + ".tif", "w", **out_meta) as dest:
            dest.write(out_image)
        return 
    
    def cal_ValidPixels(self, site_Name, raster, mask_Combined, shp, note = None):
        if np.max(mask_Combined) >= 1:
            # Upscale 60mx60m mask to 10mx10m without modifying any pixel values
            mask_Combined_Upscale = np.repeat(mask_Combined, 6, axis = 0)
            mask_Combined_Upscale = np.repeat(mask_Combined_Upscale, 6, axis = 1)
            # Save this mask
            mask_meta = raster.meta
            with rio.open(self.path_Cache + "\\" + site_Name + "\\Mask.tif", "w", **mask_meta) as dest:
                dest.write(mask_Combined_Upscale, indexes = 1)
            # clip and save
            temp_Mask = rio.open(self.path_Cache + "\\" + site_Name + "\\Mask.tif")
            self.clip_RasterbySHP(site_Name, temp_Mask, shp, suffix = "Mask ROI")
            temp_MaskClipped = rio.open(self.path_Cache + "\\" + site_Name + "\\Mask ROI.tif")
            temp_MaskCombined = temp_MaskClipped.read(1)
            if np.max(temp_MaskCombined) >= 1:
                temp_ValidPixels = np.count_nonzero(temp_MaskCombined == 0)
                temp_InvalidPixels = np.count_nonzero(temp_MaskCombined != 0)
                temp_TotalPixels = temp_ValidPixels + temp_InvalidPixels
                temp_ValidPixelsRatio = temp_ValidPixels / temp_TotalPixels
                print(f"There are {temp_ValidPixels} valid pixels in the S2 {note} image of {site_Name}!")
                if temp_ValidPixelsRatio >= self._cloud:
                    print(f"But the ratio of valid pixels is {temp_ValidPixelsRatio:.2%}, equal to or greater than {self._cloud:.2%}, so we can use these S2 images. ")
                    temp_Pass = True
                    return temp_Pass, temp_ValidPixels, temp_ValidPixelsRatio
                else:
                    print(f"And the ratio of valid pixels is {temp_ValidPixelsRatio:.2%}, lower than {self._cloud:.2%}, so we can't use these S2 images and hence we can't proceed. ")
                    temp_Pass = False
                    return temp_Pass, temp_ValidPixels, temp_ValidPixelsRatio
            else:
                print(f"All pixels in the S2 {note} image of {site_Name} are valid! ")
                temp_Pass = True
                return temp_Pass, (self._area / 10) ** 2, 1   
        else:
            print(f"All pixels in the S2 {note} image of {site_Name} are valid! ")
            temp_Pass = True
            return temp_Pass, (self._area / 10) ** 2, 1   

    def cal_CV(self, value):
        return np.std(value) / np.mean(value)
    
    def cal_Flag(self, value):
        if value <= self._threshold_CV:
            return 1
        else:
            return 0
        
class FLEX:
    # Initialization
    def __init__(self):
        # Vegetation pixel
        self._vegetationPixel = 0.5

        # The path to some essential folders and files. Don't modify these unless you know what you are going to do. 
        # The absolute path of the current working directory
        self.path_Main = os.path.realpath(os.path.dirname(__file__))
        # The absolute path of the output
        self.path_Output = self.path_Main + "\\Output"
        # The absolute path of the fake FLEX images
        self.path_Input = self.path_Main + "\\Input FLEX Images\\"
        # The absolute path to the input .csv file, where the info of all sites are saved. 
        self.path_SiteCSV = self.path_Main + "\\Sites.csv"

    @property
    def VegetationPixel(self):
        return self._vegetationPixel

        # Get names, lat, lon of all sites from .csv file, returning a pandas dataframe
    def get_SiteInfo(self):
        temp_CSV = pd.read_csv(self.path_SiteCSV)
        temp_SiteName = list(temp_CSV["Site"])
        temp_SiteLat = list(temp_CSV["Latitude"])
        temp_SiteLon = list(temp_CSV["Longitude"])
        if len(temp_SiteName) == len(temp_SiteLat) == len(temp_SiteLon):
            return temp_CSV
        else:
            print("User Error: Please make sure there is no missing data in the .csv file!")
            return