import os
import re
import numpy as np
import pandas as pd
import xarray as xr
from bs4 import BeautifulSoup
import math
import shapely as shp
import geopandas as gpd
import rasterio as rio
import rasterio.mask

class CalVal:

    # Constuctor
    def __init__(self, cwd = None):

        ### Protected members
        ## Paths
        # cwd
        if cwd is not None:
            if isinstance(cwd, str):
                self._path_main = cwd
            else:
                raise TypeError("The path to the working directory can only be a string!")
        else:
            self._path_main = os.path.realpath(os.path.dirname(__file__)) 
        # Output folder
        self._path_output = os.path.join(self._path_main, "Output")
        # The absolute path to the input .csv file, where the info of all sites are saved. 
        self._path_siteCSV = os.path.join(self._path_main, "Sites.csv")
        # The absolute path to the folder, where interim files are saved. If you want to modify this path, be cautious. 
        self._path_cache = os.path.join(self._path_main, "Cache")
        # The absolute path to the folder of "Main - Optional Input.ini"
        self._path_optional = os.path.join(self._path_main, "Optional Input.ini")
        # A boolean variable which determines whether the cache files will be deleted unpon the completion of the code. False by default. 
        self._bool_delete_cache = False

        ### Automatically check
        self.__check_siteCSV()
        self.__check_output()
        self.__check_cache()

    ### Private Methods

    # Check if "Sites.csv" exists. Otherwise gives error.  
    def __check_siteCSV(self):
        if not os.path.exists(self._path_siteCSV):
            raise FileNotFoundError(f"The working directory {self._path_main} doesn't contain the 'Sites.csv' file!")
        # else:
        #     print(f"'Sites.csv' file has been found in {self._path_Main}!")
        
    # Create an output folder if not exists
    def __check_output(self):
        if not os.path.exists(self._path_output):
            print("No output folder found! Creating a new output folder......")
            os.makedirs(self._path_output)
            print(f"Output folder {self._path_output} created successfully!")

    # Create a cache folder if not exists
    def __check_cache(self):
        if not os.path.exists(self._path_cache):
            os.makedirs(self._path_cache)
            print("Cache folder created successfully!")
        # if not self._bool_delete_cache:
        #     print("The cache files will be saved in the following folder: " + self._path_cache)
        # else:
        #     print("Cache folder will be deleted upon the completion of the code.")

    ### Public Methods

    # Create a pandas dataframe using Sites.csv
    def get_site_info(self):
        temp_CSV = pd.read_csv(self._path_siteCSV)
        # Site names
        temp_site_name = temp_CSV["Site"]
        if not temp_site_name.notna().all():
            raise ValueError("Please make sure there is no missing site name in the .csv file!")
        temp_site_name_str = [str(element) for element in temp_site_name]
        # Site lat
        temp_site_lat = temp_CSV["Latitude"]
        if not temp_site_lat.notna().all():
            raise ValueError("Please make sure there is no missing latitude in the .csv file!")
        if not pd.to_numeric(temp_site_lat, errors='coerce').notna().all():
            raise ValueError("Please make sure latitudes are numeric values in the .csv file!")
        # Site lon
        temp_site_lon = temp_CSV["Longitude"]
        if any(np.isnan(element) for element in temp_site_lon):
            raise ValueError("Please make sure there is no missing data in the .csv file!")
        if not pd.to_numeric(temp_site_lon, errors='coerce').notna().all():
            raise ValueError("Please make sure longtitudes are numeric values in the .csv file!")
        CSV = pd.DataFrame({
            "Sites": temp_site_name_str,
            "Latitude": temp_site_lat,
            "Longitude": temp_site_lon
        })
        print("'Sites.csv' read successfully!")
        return CSV

class FLEX(CalVal):

    def __init__(self):
        super().__init__()
        # FLEX image resolution
        self.__FLEX_RESOLUTION = 300
        # Input FLEX Images path
        self._path_input = os.path.join(self._path_main,"Input FLEX Images")
        # ROI size
        self._area_ROI = 900
        # Vegetation pixel
        self._vegetation_pixel = 0.5

        # Check input flex images folder
        self.__check_input()

    def __check_input(self):
        if not os.path.exists(self._path_input):
            raise FileNotFoundError(f"The working directory {self._path_main} doesn't contain the 'Input FLEX Images' Folder!")
        if not bool(os.listdir(self._path_input)):
            raise FileNotFoundError(f"There is no FLEX image found inside the 'Input FLEX Images' folder!")

    # Getter for FLEX image resolution
    @property
    def flex_resolution(self):
        return self.__FLEX_RESOLUTION
    
    # Setter for FLEX image resolution
    def flex_resolution(self, value):
        if value:
            raise AttributeError("Cannot modify the resolution of FLEX images!")

    # Getter for vegetation pixel
    @property
    def vegetation_pixel(self):
        return self._vegetation_pixel

    # Setter for vegetation pixel
    @vegetation_pixel.setter
    def vegetation_pixel(self, value):
        if value < 0 or value > 1:
            raise ValueError("The valid vegetation pixel percentage must be between 0 and 1!")
        self._vegetation_pixel = value
    
    # Getter for the ROI
    @property
    def area_ROI(self):
        return self._area_ROI
    
    # Setter for the ROI
    @area_ROI.setter
    def area_ROI(self, value):
        if value < self.__FLEX_RESOLUTION:
            raise ValueError("The ROI must be greater than 300m x 300m!")
        if value % self.__FLEX_RESOLUTION != 0:
            raise ValueError("The ROI must contain complete pixels!")
        self._area_ROI = value

    ## Check file name convention
    # PRS_TD_20230616_101431.nc 
    def check_filename(self, filename):
        if not re.fullmatch(r"^PRS_TD_\d{8}_\d{6}\.nc$", filename):
            raise ValueError(f"The filename '{filename}' is not correct!")
    
    ## SIF Calculation
    def cal_SIF(self, site_name, filename, site_lon, site_lat):
        temp_ds = rio.open(f'netcdf:{os.path.join(self._path_input,site_name,filename)}:Leaf Area Index')
        # Get the pixel where there is the site
        temp_index_x, temp_index_y = temp_ds.index(site_lon,site_lat)
        # print(f"FLEX image '{temp_FLEX_filename}' opened succesfully!")

        temp_list_SIF_Name = []
        temp_list_SIF_AVG = []
        temp_list_SIF_STD = []
        temp_ds = xr.open_dataset(os.path.join(self._path_input, site_name, filename))
        temp_Name_Var = list(temp_ds.data_vars)

        for var_name in temp_Name_Var:
            if "Sif Emission Spectrum_sif_wavelength_grid" in var_name:
                temp_array = temp_ds[var_name][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values
                temp_list_SIF_Name.append(var_name)
                temp_AVG = np.average(temp_array).item()
                temp_list_SIF_AVG.append(temp_AVG)
                temp_STD = np.std(temp_array).item()
                temp_list_SIF_STD.append(temp_STD)
        temp_df_SIF = pd.DataFrame({
            "SIF": temp_list_SIF_Name,
            "Average": temp_list_SIF_AVG,
            "STD": temp_list_SIF_STD
        })
        temp_df_SIF.to_csv(os.path.join(self._path_output,site_name,filename + " - Sif.csv"), index = False)

class S2(CalVal):

    def __init__(self):
        super().__init__()
        self.__S2_RESOLUTION = 10
        # Set a threshold of CV. You can change this value according to your own need, but note that there is no sense if the threshold is not greater than 0. The threshold of CV is set to 0.2 by default. 
        self._threshold_CV = 0.2
        # Set the side-length of the ROI. The ROI must be a squared area. This value must be a multiple of 10. The side-length of the ROI is 900 meters by default. 
        self._area = 900
        # Cloud coverage
        self._cloud = 0.5

        # The absolute path of the S2 images
        self._path_input = os.path.join(self._path_main,"Input S2 Images")

        self.__check_input()
        self.__check_FLEX()

    def __check_input(self):
        if not os.path.exists(self._path_input):
            raise FileNotFoundError(f"The working directory {self._path_main} doesn't contain the 'Input S2 Images' Folder!")
        if not bool(os.listdir(self._path_input)):
            raise FileNotFoundError(f"There is no S2 image found inside the 'Input FLEX Images' folder!")
        
    def __check_FLEX(self):
        if not os.path.exists(os.path.join(self._path_output,"Usable FLEX Images.csv")):
            raise FileNotFoundError("There is no available FLEX image found ")
        
    # Getter
    @property
    def s2_resolution(self):
        return self.__S2_RESOLUTION
    # Setter
    @s2_resolution.setter
    def s2_resolution(self, value):
        if value:
            raise AttributeError("Cannot modify the spatial resolution of Sentinel-2 images!")

    # Getter 
    @property
    def threshold_CV(self):
        return self._threshold_CV
    
    # Setter
    @threshold_CV.setter
    def threshold_CV(self, value):
        if value <= 0:
            raise ValueError("The threshold of CV should be greater than 0!!!")
        self._threshold_CV = value

    # Getter
    @property
    def area(self):
        return self._area

    # Setter
    @area.setter
    def area(self, value):
        if value < self.__S2_RESOLUTION:
            raise ValueError()
        if value % self.__S2_RESOLUTION != 0:
            raise ValueError("The size of the ROI must be a multiple of 100 squared meters!!!")
        self._area = value

    # Getter
    @property
    def cloud(self):
        return self._cloud
    
    # Setter
    @cloud.setter
    def cloud(self, value):
        if value < 0 or value > 1:
            raise ValueError("The cloud coverage must be between 0 and 1!!!")
        self._cloud = value

    def create_cache_folder(self,path):
        temp = os.path.join(self._path_cache,path)
        if not os.path.exists(temp):
            os.makedirs(temp)
        
    # Get paths to S2 images and mask images. In this case we need B8 image of L1C and B4, B8 images of L2A
    def get_path_images(self, path_S2_image):
        # L1C
        temp_path_L1C = os.path.join(self._path_input,path_S2_image,"L1C")
        for path, subdirs ,files in os.walk(temp_path_L1C):
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
        temp_path_L2A = os.path.join(self._path_input,path_S2_image,"L2A")
        for path, subdirs, files in os.walk(temp_path_L2A):
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
        if not os.path.exists(temp_path_L1C) or not os.path.exists(temp_path_L2A):
            print("User Error: Please organise the input S2 images in correct folder structure. ")
            return
        else:
            return path_L1C_B08_raw, path_L2A_B04_raw, path_L2A_B08_raw, path_L1C_Mask, path_L2A_Mask, path_L1C_xml_DS, path_L1C_xml_TL, path_L2A_xml_DS
        
    def create_shapefile(self, img_L1C, img_L2A, site_name, site_lat, site_lon, bool_toSave = False):
        # Get the crs of input L1C image and L2A image
        crs_L1C = img_L1C.crs.data["init"].split(":")[1]
        crs_L2A = img_L2A.crs.data["init"].split(":")[1]
        # In the case that L1C and L2A have different crs, give an error. But this won't happen if the input images are correct. 
        if crs_L2A != crs_L1C:
            raise SystemExit("Stop right there!")
        crs_final = 'EPSG:' + crs_L1C
        # Create a point shapefile based on the site, using Lon-Lat
        df_4326 = pd.DataFrame({
            "Site": [site_name],
            "Latitude": [site_lat],
            "Longitude": [site_lon]
        })
        gdf_4326 = gpd.GeoDataFrame(
            df_4326,
            geometry = gpd.points_from_xy(df_4326['Longitude'], df_4326['Latitude']),
            crs = "EPSG:4326"
        )
        gdf_new = gdf_4326.copy()
        gdf_new = gdf_new.to_crs(crs_final)
        # First we retrieve the x, y coordinate of our site
        site_x = gdf_new.geometry.x.values[0]
        site_y = gdf_new.geometry.y.values[0]
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
            crs = crs_final
        )
        return gdf_New
   
    def cal_L2A_NDVI(self, path_L2A_xml_DS, values_L2A_B04, values_L2A_B08):
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
    
    def cal_L1C_Rad(self, path_L1C_xml_DS, path_L1C_xml_TL, values_L1C_B08):
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
        
    def clip_raster_by_shapefile(self, path, raster, shp, suffix = None):
        out_image, out_transform = rio.mask.mask(raster, shp.geometry, crop=True)
        out_meta = raster.meta
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})

        with rio.open(os.path.join(self._path_cache,path,suffix + ".tif"), "w", **out_meta) as dest:
            dest.write(out_image)
    
    def cal_valid_pixels(self, path, raster, mask_Combined, shp, note = None):
        if np.max(mask_Combined) >= 1:
            # Upscale 60mx60m mask to 10mx10m without modifying any pixel values
            mask_Combined_Upscale = np.repeat(mask_Combined, 6, axis = 0)
            mask_Combined_Upscale = np.repeat(mask_Combined_Upscale, 6, axis = 1)
            # Save this mask
            mask_meta = raster.meta
            with rio.open(os.path.join(self._path_cache,path,"Mask.tif"), "w", **mask_meta) as dest:
                dest.write(mask_Combined_Upscale, indexes = 1)
            # clip and save
            temp_Mask = rio.open(os.path.join(self._path_cache,path,"Mask.tif"))
            self.clip_RasterbySHP(path, temp_Mask, shp, suffix = "Mask ROI")
            temp_MaskClipped = rio.open(os.path.join(self._path_cache,path,"Mask ROI.tif"))
            temp_MaskCombined = temp_MaskClipped.read(1)
            if np.max(temp_MaskCombined) >= 1:
                temp_ValidPixels = np.count_nonzero(temp_MaskCombined == 0)
                temp_InvalidPixels = np.count_nonzero(temp_MaskCombined != 0)
                temp_TotalPixels = temp_ValidPixels + temp_InvalidPixels
                temp_ValidPixelsRatio = temp_ValidPixels / temp_TotalPixels
                print(f"There are {temp_ValidPixels} valid pixels in the S2 {note} image of {path}!")
                if temp_ValidPixelsRatio >= self._cloud:
                    print(f"But the ratio of valid pixels is {temp_ValidPixelsRatio:.2%}, equal to or greater than {self._cloud:.2%}, so we can use these S2 images. ")
                    temp_Pass = True
                    return temp_Pass, temp_ValidPixels, temp_ValidPixelsRatio
                else:
                    print(f"And the ratio of valid pixels is {temp_ValidPixelsRatio:.2%}, lower than {self._cloud:.2%}, so we can't use these S2 images and hence we can't proceed. ")
                    temp_Pass = False
                    return temp_Pass, temp_ValidPixels, temp_ValidPixelsRatio
            else:
                print(f"All pixels in the S2 {note} image of {path} are valid! ")
                temp_Pass = True
                return temp_Pass, (self._area / 10) ** 2, 1   
        else:
            print(f"All pixels in the S2 {note} image of {path} are valid! ")
            temp_Pass = True
            return temp_Pass, (self._area / 10) ** 2, 1   

    def cal_CV(self, value):
        return np.std(value) / np.mean(value)
    
    def cal_Flag(self, value):
        if value <= self._threshold_CV:
            return 1
        else:
            return 0

