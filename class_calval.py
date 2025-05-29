import os
from typing import Optional, Union
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
    def __init__(self, cwd: Optional[str] = None):
        '''
        Initialize the class. 

        Args:
            cwd (str, optional): Path to the working directory. If None, defaults to the script's location.

        Raises:
            TypeError: If 'cwd' is not a string. 
        '''

        # ----------------------------------- Paths ---------------------------------- #
        # Current work directory (cwd)
        if cwd is not None:
            if isinstance(cwd, str):
                self._path_main = cwd
            else:
                raise TypeError("The path to the working directory can only be a string!")
        else:
            # If 
            self._path_main = os.path.realpath(os.path.dirname(__file__)) 
        # Output folder
        self._path_output = os.path.join(self._path_main, "Output")
        # The absolute path to the input .csv file, where the info of all sites are saved. 
        self._file_site_csv = os.path.join(self._path_main, "Sites.csv")
        # The absolute path to the folder, where interim files are saved. 
        self._path_cache = os.path.join(self._path_main, "Cache")
        # The absolute path to the folder of "Main - Optional Input.ini"
        self._file_optional = os.path.join(self._path_main, "Optional Input.ini")
        # A boolean variable which determines whether the cache files will be deleted unpon the completion of the code. False by default. 
        self._bool_delete_cache = False

        ### Automatically check
        self.__check_site_csv()
        self.__check_output()
        self.__check_cache()

    # ------------------------------ Private Methods ----------------------------- #

    # Create an output folder if not exists
    def __check_output(self):
        if not os.path.exists(self.path_output):
            print("No output folder found! Creating a new output folder......")
            os.makedirs(self.path_output)
            print(f"Output folder {self.path_output} created successfully!")

    # Check if "Sites.csv" exists. Otherwise gives error.  
    def __check_site_csv(self):
        if not os.path.exists(self.file_site_csv):
            raise FileNotFoundError(f"The working directory {self.path_main} doesn't contain the 'Sites.csv' file!")
        # else:
        #     print(f"'Sites.csv' file has been found in {self._path_Main}!")
        
    # Create a cache folder if not exists
    def __check_cache(self):
        if not os.path.exists(self._path_cache):
            os.makedirs(self._path_cache)
            # print("Cache folder created successfully!")
        # if not self._bool_delete_cache:
        #     print("The cache files will be saved in the following folder: " + self._path_cache)
        # else:
        #     print("Cache folder will be deleted upon the completion of the code.")

    # ------------------------------ Getter & Setter ----------------------------- #
    @property
    def path_main(self):
        return self._path_main

    @property
    def path_output(self):
        return self._path_output

    @property
    def file_site_csv(self):
        return self._file_site_csv
    @file_site_csv.setter
    def file_siteCSV(self, value):
        if not isinstance(value, str):
            raise TypeError('The path to sites.csv must be a string!')
        else:
            self._file_site_csv = value
        self.__check_site_csv()

    @property
    def file_optional(self):
        return self._file_optional
    @file_optional.setter
    def file_optional(self, value):
        if not isinstance(value, str):
            raise TypeError('The path to the optional input file must be a string!')
        elif not os.path.exists(value):
            raise FileNotFoundError(f"The file {self._file_optional} is not found!")
        else:
            self._file_optional = value
    # ------------------------------ Public Methods ------------------------------ #

    # Create a pandas dataframe using Sites.csv
    def get_site_info(self):
        df_sites = pd.read_csv(self.file_site_csv)
        # Site names
        site_name = df_sites["site_code"]
        if not site_name.notna().all():
            raise ValueError("Please make sure there is no missing site name in the .csv file!")
        # Convert site names to string
        site_name_str = [str(element) for element in site_name]

        # Site lat
        site_lat = df_sites["latitude"]
        if not site_lat.notna().all():
            raise ValueError("Please make sure there is no missing latitude in the .csv file!")
        if not pd.to_numeric(site_lat, errors='coerce').notna().all():
            raise ValueError("Please make sure latitudes are numeric values in the .csv file!")
        if not site_lat.between(-90, 90).all():
            raise ValueError("Please make sure latitudes are within the range of -90 to 90!")
        
        # Site lon
        site_lon = df_sites["longitude"]
        if not site_lon.notna().all():
            raise ValueError("Please make sure there is no missing latitude in the .csv file!")
        if not pd.to_numeric(site_lon, errors='coerce').notna().all():
            raise ValueError("Please make sure longtitudes are numeric values in the .csv file!")
        if not site_lon.between(-180, 180).all():
            raise ValueError("Please make sure longtitudes are within the range of -180 to 180!")
        
        # Create final CSV
        df_sites = pd.DataFrame({
            "Sites": site_name_str,
            "Latitude": site_lat,
            "Longitude": site_lon
        })
        print("'Sites.csv' read successfully!")
        return df_sites

class FLEX(CalVal):

    # FLEX image resolution
    _FLEX_RESOLUTION = 300

    def __init__(self):
        super().__init__()
        # Input FLEX Images path
        self._path_input = os.path.join(self._path_main,"Input FLEX Images")
        # ROI size
        self._area_roi = 900
        # Vegetation pixel percentage! 
        self._vegetation_pixel = 0.5

        # Check input flex images folder
        self.__check_input()
    # ------------------------------ Private Methods ----------------------------- #

    def __check_input(self):
        if not os.path.exists(self.path_input):
            raise FileNotFoundError(f"The working directory {self._path_main} doesn't contain the 'Input FLEX Images' Folder!")
        if not bool(os.listdir(self.path_input)):
            raise FileNotFoundError(f"There is no FLEX image found inside the 'Input FLEX Images' folder!")
        
    # ----------------------------- Getter and Setter ---------------------------- #

    # Getter and setter for FLEX input path
    @property
    def path_input(self):
        return self._path_input
    @path_input.setter
    def path_input(self, value):
        self._path_input = value
    
    # Getter and setter for ROI
    @property
    def area_roi(self):
        return self._area_roi
    @area_roi.setter
    def area_roi(self, value):
        if value < self.FLEX_RESOLUTION:
            raise ValueError("The ROI must be greater than 300m x 300m!")
        if value % self.FLEX_RESOLUTION != 0:
            raise ValueError("The ROI must contain complete FLEX pixel(s)!")
        self._area_ROI = value

    # Getter for FLEX image resolution; no setter since it is a constant!
    @property
    def FLEX_RESOLUTION(self):
        return self._FLEX_RESOLUTION

    # Getter for vegetation pixel
    @property
    def vegetation_pixel(self):
        return self._vegetation_pixel
    @vegetation_pixel.setter
    def vegetation_pixel(self, value):
        if value < 0 or value > 1:
            raise ValueError("The valid vegetation pixel percentage must be between 0 and 1!")
        self._vegetation_pixel = value

    # ------------------------------ Public Methods ------------------------------ #
    ## Check file name convention
    # PRS_TD_20230616_101431.nc 
    def check_filename(self, filename: str) -> None:
        '''
        A function used to check whether the filename of a FLEX image corresponds to the correct format. If not, it will raise an error. 
        '''
        if not re.fullmatch(r"^PRS_TD_\d{8}_\d{6}\.nc$", filename):
            raise ValueError(f"The filename '{filename}' is not correct! It should have the same format as 'PRS_TD_20230616_101431.nc'!")
    
    ## SIF Calculation
    def cal_SIF(self, site_name: str, filename: str, site_lon: Union[int, float], site_lat: Union[int, float], bool_save: Optional[bool] = False) -> None:
        temp_ds = rio.open(f'netcdf:{os.path.join(self.path_input,site_name,filename)}:Leaf Area Index')
        # Get the pixel where there is the site
        temp_index_x, temp_index_y = temp_ds.index(site_lon,site_lat)
        # print(f"FLEX image '{temp_FLEX_filename}' opened succesfully!")

        temp_list_sif_name = []
        temp_list_sif_avg = []
        temp_list_sif_std = []
        temp_ds = xr.open_dataset(os.path.join(self.path_input, site_name, filename))
        temp_name_rar = list(temp_ds.data_vars)

        for var_name in temp_name_rar:
            if "Sif Emission Spectrum_sif_wavelength_grid" in var_name:
                temp_array = temp_ds[var_name][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values
                temp_list_sif_name.append(var_name)
                temp_AVG = np.average(temp_array).item()
                temp_list_sif_avg.append(temp_AVG)
                temp_STD = np.std(temp_array).item()
                temp_list_sif_std.append(temp_STD)
        temp_df_sif = pd.DataFrame({
            "SIF": temp_list_sif_name,
            "Average": temp_list_sif_avg,
            "STD": temp_list_sif_std
        })
        if bool_save:
            if not os.path.exists(os.path.join(self._path_output,site_name)):
                os.makedirs(os.path.join(self._path_output,site_name))
            temp_df_sif.to_csv(os.path.join(self._path_output,site_name,filename + " - sif.csv"), index = False)

class S2(CalVal):

    def __init__(self):
        super().__init__()
        self.__S2_RESOLUTION = 10
        # Set a threshold of CV. You can change this value according to your own need, but note that there is no sense if the threshold is not greater than 0. The threshold of CV is set to 0.2 by default. 
        self._threshold_cv = 0.2
        # Set the side-length of the ROI. The ROI must be a squared area. This value must be a multiple of 10. The side-length of the ROI is 900 meters by default. 
        self._area = 900
        # Cloud coverage
        self._cloud = 0.5

        # The absolute path of the S2 images
        self._path_input = os.path.join(self._path_main,"Input S2 Images")

        self.__check_input()
        self.__check_FLEX()

    # ------------------------------ Private Methods ----------------------------- #

    def __check_input(self):
        if not os.path.exists(self.path_input):
            raise FileNotFoundError(f"The working directory {self._path_main} doesn't contain the 'Input S2 Images' Folder!")
        if not bool(os.listdir(self.path_input)):
            raise FileNotFoundError(f"There is no S2 image found inside the 'Input FLEX Images' folder!")
        
    def __check_FLEX(self):
        if not os.path.exists(os.path.join(self._path_output,"Usable FLEX Images.csv")):
            raise FileNotFoundError("There is no available FLEX image found ")
        
    # ------------------------------ Private Members ----------------------------- #

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
    def path_input(self):
        return self._path_input

    # ----------------------------- Protected Members ---------------------------- #

    # Getter 
    @property
    def threshold_cv(self):
        return self._threshold_cv
    
    # Setter
    @threshold_cv.setter
    def threshold_cv(self, value):
        if value <= 0:
            raise ValueError("The threshold of CV should be greater than 0!!!")
        self._threshold_cv = value

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

    # ------------------------------ Public Methods ------------------------------ #
    def create_cache_subfolder(self, path):
        temp = os.path.join(self._path_cache,path)
        if not os.path.exists(temp):
            os.makedirs(temp)

    # Get paths to S2 images and mask images. In this case we need B8 image of L1C and B4, B8 images of L2A
    def get_path_images(self, path_s2_image):
        # L1C
        temp_path_l1c = os.path.join(self.path_input,path_s2_image,"L1C")
        for path, subdirs ,files in os.walk(temp_path_l1c):
            for name in files:
                temp = os.path.join(path, name)
                if "IMG_DATA" in temp and temp[-3:] == 'jp2' and "B08" in temp:
                    path_l1c_b08_raw = temp
                # Path to the mask file
                if "MSK_CLASSI_B00" in temp and temp[-3:] == 'jp2':
                    path_l1c_mask = temp
                # Get the path to the XML file "MTD_DS" of L1C raster, where there are values of "U", "Solar Irradiance", "Quantification Value" and "Radiometric Offset"
                if "MTD_DS.xml" in temp:
                    path_l1c_xml_ds = temp
                # Get the path to the XML file "MTD_TL" of L1C raster, where there are values (matrices) of "Solar Zenith Angle". 
                if "MTD_TL.xml" in temp:
                    path_l1c_xml_tl = temp
        # L2A
        temp_path_l2a = os.path.join(self.path_input,path_s2_image,"L2A")
        for path, subdirs, files in os.walk(temp_path_l2a):
            for name in files:
                temp = os.path.join(path, name)
                if temp[-3:] == 'jp2'in temp and "10m" in temp and "B04" in temp :
                    path_l2a_b04_raw = temp
                if temp[-3:] == 'jp2'in temp and "10m" in temp and "B08" in temp :
                    path_l2a_b08_raw = temp
                # Path to the mask file
                if "MSK_CLASSI_B00" in temp and temp[-3:] == 'jp2':
                    path_l2a_mask = temp
                # Get the path to the XML file "MTD_DS" of L1C raster, where there are values of "Quantification Value" and "Radiometric Offset"
                if "MTD_DS.xml" in temp:
                    path_l2a_xml_ds = temp
        if not os.path.exists(temp_path_l1c) or not os.path.exists(temp_path_l2a):
            print("User Error: Please organise the input S2 images in correct folder structure. ")
            raise FileNotFoundError(f"The input S2 images folder {path_s2_image} doesn't contain the correct folder structure or doesn't contain S2 images! Please check the input S2 images folder!")
        else:
            return path_l1c_b08_raw, path_l2a_b04_raw, path_l2a_b08_raw, path_l1c_mask, path_l2a_mask, path_l1c_xml_ds, path_l1c_xml_tl, path_l2a_xml_ds
        
    def create_shapefile(self, img_l1c, img_l2a, site_name, site_lat, site_lon, bool_toSave = False):
        # Get the crs of input L1C image and L2A image
        crs_l1c = img_l1c.crs.data["init"].split(":")[1]
        crs_l2a = img_l2a.crs.data["init"].split(":")[1]
        # In the case that L1C and L2A have different crs, give an error. But this won't happen if the input images are correct. 
        if crs_l2a != crs_l1c:
            raise SystemExit("Stop right there!")
        crs_final = 'EPSG:' + crs_l1c
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
        site_row, site_col = img_l2a.index(site_x, site_y)
        site_pixel_x, site_pixel_y = img_l2a.xy(site_row, site_col)
        # Calculate the "cardinal" distance
        side_length_half = self._area / 2
        if side_length_half % 2 == 0:
            # If the half of the side length is even, we need to add another 5 meters to make sure the pixels on the borders will not be omitted when we clip the raster images. 
            length_cardinal = side_length_half + 5
        else:
            length_cardinal = side_length_half
        site_x_left_new = site_pixel_x - length_cardinal
        site_x_right_new = site_pixel_x + length_cardinal
        site_y_top_new = site_pixel_y + length_cardinal
        site_y_bottom_new = site_pixel_y - length_cardinal
        # Create a bounding box
        shp_new = shp.box(site_x_left_new, site_y_bottom_new, site_x_right_new, site_y_top_new)
        # Create shapefile! 
        gdf_new = gpd.GeoDataFrame(
            pd.DataFrame({"0": ["0"]}),
            geometry=[shp_new],
            crs = crs_final
        )
        return gdf_new
   
    def cal_l2a_ndvi(self, path_l2a_xml_ds, values_l2a_b04, values_l2a_b08):
        # Read the DS xml file of L2A
        with open(path_l2a_xml_ds, 'r') as f:
            data = f.read()
        bs_l2a_ds = BeautifulSoup(data, "xml")
        # Get the quantification value! 
        quantification_l2a = int(bs_l2a_ds.find("BOA_QUANTIFICATION_VALUE").text)
        # Get the radiometric offset!
        offset_l2a_b04 = int(bs_l2a_ds.find("BOA_ADD_OFFSET", {"band_id": "3"}).text)
        offset_l2a_b08 = int(bs_l2a_ds.find("BOA_ADD_OFFSET", {"band_id": "7"}).text)
        # Calculate NDVI of L2A! 
        temp_ndvi = ((values_l2a_b08 + offset_l2a_b08).astype(float) / quantification_l2a - (values_l2a_b04 + offset_l2a_b04).astype(float) / quantification_l2a) / ((values_l2a_b08 + offset_l2a_b08).astype(float) / quantification_l2a + (values_l2a_b04 + offset_l2a_b04).astype(float) / quantification_l2a )
        return temp_ndvi
    
    def cal_l1c_rad(self, path_l1c_xml_ds, path_l1c_xml_tl, values_l1c_b08):
        with open(path_l1c_xml_ds, 'r') as f:
            data = f.read()
        bs_l1c_ds = BeautifulSoup(data, "xml")
        # Get the quantification value! 
        quantification_l1c = int(bs_l1c_ds.find("QUANTIFICATION_VALUE").text)
        # Get the radiometric offset!
        offset_l1c = int(bs_l1c_ds.find("RADIO_ADD_OFFSET", {"band_id": "7"}).text)
        # Get the U
        u_l1c = float(bs_l1c_ds.find("U").text)
        # Get the solar irradiance
        solar_irradiance_l1c = float(bs_l1c_ds.find("SOLAR_IRRADIANCE", {"bandId": "7"}).text)
        # Read the TL xml file of L1C
        with open(path_l1c_xml_tl, 'r') as f:
            data = f.read()
        bs_l1c_ds = BeautifulSoup(data, "xml")
        # Get the sun zenith angle! There should be a 23 x 23 arrays in the xml. Now we save each row as an array and keep all these arrays into a list
        list_sun_zenith = []
        for row in bs_l1c_ds.find("Sun_Angles_Grid").find("Zenith").find_all("VALUES"):
            temp_list = row.text.split(" ")
            temp_arr = np.array(temp_list)
            temp_arr = temp_arr.astype(float)
            list_sun_zenith.append(temp_arr)
        # Now we stack these nested-in-list arrays into a 2d array
        index = 0
        for arr in list_sun_zenith:
            if index == 0:
                arr_sun_zenith = arr
            else:
                arr_sun_zenith = np.vstack((arr_sun_zenith, arr))
            index = index + 1
        # Get the shape of L1C image, which should be (10980, 10980)
        shape_l1c = values_l1c_b08.shape
        # Repeat each element of sun zenith angle array, in both axies. The final array should have a shape of (11500, 11500)
        arr_sun_zenith_repeat = np.repeat(arr_sun_zenith, 500, axis = 1)
        arr_sun_zenith_repeat = np.repeat(arr_sun_zenith_repeat, 500, axis = 0)
        # Index only the first 10980 of each dimension
        arr_sun_zenith_assigned = arr_sun_zenith_repeat[0:shape_l1c[0], 0:shape_l1c[1]]
        # radiance = reflectance * cos(radians(SunZenithAngle)) * solarIrradiance * U / pi
        temp_Radiance = (values_l1c_b08 + offset_l1c).astype(float)  * np.cos(np.radians(arr_sun_zenith_assigned)) * solar_irradiance_l1c / quantification_l1c / (math.pi * (1 / u_l1c))
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

    def cal_cv(self, value):
        return np.std(value) / np.mean(value)
    
    def cal_flag(self, value):
        if value <= self.threshold_cv:
            return 1
        else:
            return 0

