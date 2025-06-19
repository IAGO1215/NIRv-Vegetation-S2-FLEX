import os
import csv
from typing import Optional, Union
import re
import numpy as np
import pandas as pd
import xarray as xr
from bs4 import BeautifulSoup
import shapely as shp
import geopandas as gpd
import rasterio as rio
import rasterio.mask
from sklearn.metrics import r2_score
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression

class CalVal:

    # Constuctor
    def __init__(self):
        '''
        Initialize the class. 
        '''

        # -------------------------------- Attributes -------------------------------- #
        # Current work directory (where the script is located)
        self._path_main = os.path.realpath(os.path.dirname(__file__)) 
        # Input folder
        self._path_input = os.path.join(self.path_main, "input")
        # The absolute path of the S2 images
        self._path_s2_input = os.path.join(self._path_main,"input_s2_images")
        # The absolute path of the FLEX images
        self._path_flex_input = os.path.join(self.path_main,"input_flex_images")
        # Output folder
        self._path_output = os.path.join(self.path_main, "output")
        # FLOX input
        self._file_flox_csv = os.path.join(self.path_input,'flox_sifparms_filt_flextime_aggr_avg_allsites.csv')
        # The absolute path to the input .csv file, where the info of all sites are saved. 
        self._file_site_csv = os.path.join(self.path_input, "sites.csv")
        # The absolute path to the folder, where interim files are saved. 
        self._path_cache = os.path.join(self.path_main, "cache")
        # A boolean variable which determines whether the cache files will be deleted unpon the completion of the code. False by default. 
        self._bool_delete_cache = True
        # Flex filename
        self.flex_filename = None

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
            raise FileNotFoundError(f"The input directory {self.path_input} doesn't contain the 'Sites.csv' file!")
        # else:
        #     print(f"'Sites.csv' file has been found in {self._path_Main}!")
        
    # Create a cache folder if not exists
    def __check_cache(self):
        if not os.path.exists(self._path_cache):
            os.makedirs(self._path_cache)

    # ------------------------------ Getter & Setter ----------------------------- #
    @property
    def path_main(self):
        return self._path_main

    @property
    def path_input(self):
        return self._path_input
    
    @property
    def path_s2_input(self):
        return self._path_s2_input
    
    @property
    def path_flex_input(self):
        return self._path_flex_input

    @property
    def path_output(self):
        return self._path_output

    @property
    def file_site_csv(self):
        return self._file_site_csv
    
    @property
    def path_cache(self):
        return self._path_cache
    
    @property
    def bool_delete_cache(self):
        return self._bool_delete_cache
    
    @property
    def file_flox_csv(self):
        return self._file_flox_csv
    @file_flox_csv.setter
    def file_flox_csv(self, value):
        self._file_flox_csv = value

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
        
        # reference_area
        site_roi = df_sites["reference_area(m)"]
        if not site_roi.isin([300, 600, 900]).all():
            raise ValueError("The input reference area(m) can only be 300, 600 or 900")

        # time_window_days
        site_time_window = df_sites["time_window(days)"]

        # threshold_cv
        site_threshold_cv = df_sites["threshold_CV(%)"] / 100

        # vegetation_pixel
        site_vegetation_pixel = df_sites["vegetation_pixel(%)"] / 100

        # threshold_cloud
        site_threshold_cloud = df_sites["threshold_cloud(%)"] / 100
        
        # Create final CSV
        df_sites = pd.DataFrame({
            "Sites": site_name_str,
            "Latitude": site_lat,
            "Longitude": site_lon,
            "ROI": site_roi,
            "Time Window Days": site_time_window,
            "Threshold CV": site_threshold_cv,
            "Vegetation Pixel": site_vegetation_pixel,
            "Threshold Cloud": site_threshold_cloud
        })
        print("'Sites.csv' read successfully!")
        return df_sites
    
    def create_matchup_report(self):
        # Merge transfer function output
        df_tf = pd.concat((pd.read_csv(os.path.join(self.path_cache,'TF',csv_file)) for csv_file in os.listdir(os.path.join(self.path_cache,'TF'))), ignore_index=True)
        df_tf['date'] = df_tf['date'].astype(str)
        df_tf.rename(columns={
            "SIF_O2A": "SIF_O2A_TF",
            "SIF_FARRED_max": "SIF_FARRED_max_TF",
            "SIF_int": "SIF_int_TF",
            "SIF_O2B": "SIF_O2B_TF",
            "SIF_RED_max": "SIF_RED_max_TF",
            "SIF_O2A_un": "SIF_O2A_un_TF",
            "SIF_FARRED_max_un": "SIF_FARRED_max_un_TF",
            "SIF_int_un": "SIF_int_un_TF",
            "SIF_O2B_un": "SIF_O2B_un_TF",
            "SIF_RED_max_un": "SIF_RED_max_un_TF"
        }, inplace = True)
        # Read FLOX
        df_flox = pd.read_csv(self.file_flox_csv, sep = ';')
        df_flox = df_flox[['ID_SITE','UTC_datetime','SIF_FARRED_max','SIF_FARRED_max_wvl','SIF_RED_max','SIF_RED_max_wvl','SIF_O2B','SIF_O2A','SIF_int','SIF_FARRED_max_un','SIF_FARRED_max_wvl_un','SIF_RED_max_un','SIF_RED_max_wvl_un','SIF_O2B_un','SIF_O2A_un','SIF_int_un']]
        df_flox.rename(columns={'ID_SITE': 'site_code', 'UTC_datetime': 'date'}, inplace=True)
        df_flox['date'] = pd.to_datetime(df_flox['date'], format='%d/%m/%Y %H:%M')
        # Convert to string date format
        df_flox['date'] = df_flox['date'].dt.strftime('%Y%m%d')
        # Read FLEX
        df_flex = pd.read_csv(os.path.join(self.path_cache,"L2B_FLEX_table.csv"))
        df_flex = df_flex[['site_code','latitude','longitude','flex_date','flex_time','flex_filename','s2_filename','SIF_FARRED_max','SIF_FARRED_max_wvl','SIF_RED_max','SIF_RED_max_wvl','SIF_O2B','SIF_O2A','SIF_int','SIF_FARRED_max_un','SIF_FARRED_max_wvl_un','SIF_RED_max_un','SIF_RED_max_wvl_un','SIF_O2B_un','SIF_O2A_un','SIF_int_un']]
        df_flex.rename(columns={'flex_date': 'date'}, inplace=True)
        df_flex['date'] = df_flex['date'].astype(str)
        # Merge into a single dataframe
        df_merge = pd.merge(df_flox,df_flex,how='inner',on=['site_code','date'], suffixes=('_flox','_flex'))
        df_merge = pd.merge(df_merge,df_tf,how='inner',on=['site_code','date'])
        df_merge.to_csv(os.path.join(self.path_output,"L2B_1P_matchup.csv"), index=False, na_rep= 'N/A')

class FLEX(CalVal):

    # FLEX image resolution
    _FLEX_RESOLUTION = 300

    def __init__(self):
        super().__init__()
        # Input FLEX Images path

        # ROI size
        self._area_roi = 900
        # Vegetation pixel percentage! 
        self._vegetation_pixel = 0.5

        # Check input flex images folder
        self.__check_input()
    # ------------------------------ Private Methods ----------------------------- #

    def __check_input(self):
        if not os.path.exists(self.path_flex_input):
            raise FileNotFoundError(f"The working directory {self._path_main} doesn't contain the 'Input FLEX Images' Folder!")
        if not bool(os.listdir(self.path_flex_input)):
            raise FileNotFoundError(f"There is no FLEX image found inside the 'Input FLEX Images' folder!")
        
    # ----------------------------- Getter and Setter ---------------------------- #
    
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
    
    ## Check FLOX dates
    def check_flox_dates(self) -> dict:
        # Read FLOX CSV input file
        df_flox = pd.read_csv(self.file_flox_csv, sep=';')
        # Regulate datetime format
        df_flox['UTC_datetime'] = pd.to_datetime(df_flox['UTC_datetime'], format='%d/%m/%Y %H:%M')
        # Convert to string date format
        df_flox['UTC_datetime'] = df_flox['UTC_datetime'].dt.strftime('%Y%m%d')
        # Remove useless columns
        df_flox = df_flox[['ID_SITE','UTC_datetime']]
        # Export
        df_flox_dict = df_flox.groupby('ID_SITE')['UTC_datetime'].apply(list).to_dict()
        return df_flox_dict

    ## SIF Calculation
    def cal_sif(self, site_name: str, filename: str, site_lon: Union[int, float], site_lat: Union[int, float], roi: int, s2_filename: str) -> None:
        # Open the FLEX image
        temp_ds = xr.open_dataset(os.path.join(self.path_flex_input,site_name,filename))
        # Read longitudes and latitudes from the dataset
        longitudes = temp_ds['longitude'].values
        latitudes = temp_ds['latitude'].values
        # Get the indices of the closest longitudes and latitudes to the site
        lon_left = np.where(longitudes <= site_lon)[0][-1]
        lon_right = np.where(longitudes >= site_lon)[0][0]
        lat_top = np.where(latitudes >= site_lat)[0][-1]
        lat_bottom = np.where(latitudes <= site_lat)[0][0]
        # print(f"lon_left: {lon_left}, lon_right: {lon_right}, lat_top: {lat_top}, lat_bottom: {lat_bottom}")
        # Now find the indices of the pixel where the site is located
        if abs(site_lon - longitudes[lon_left]) < abs(site_lon - longitudes[lon_right]):
            lon_index = lon_left
        else:
            lon_index = lon_right
        if abs(site_lat - latitudes[lat_top]) < abs(site_lat - latitudes[lat_bottom]):
            lat_index = lat_top
        else:
            lat_index = lat_bottom

        # Prepare empty lists to store results of each loop
        temp_list_sif_name = []
        temp_list_sif_avg = []
        temp_list_sif_std = []
        temp_name_rar = list(temp_ds.data_vars)

        for var_name in temp_name_rar:
            if "Sif Emission Spectrum_sif_wavelength_grid" in var_name:
                if roi == 300:
                    temp_array = temp_ds[var_name][lat_index,lon_index].values
                elif roi == 600:
                    if abs(site_lat - latitudes[lat_index - 1]) < abs(site_lat - latitudes[lat_index + 1]):
                        lat_index_600 = lat_index - 1
                    else:
                        lat_index_600 = lat_index + 1
                    if abs(site_lon - longitudes[lon_index - 1]) < abs(site_lon - longitudes[lon_index + 1]):
                        lon_index_600 = lon_index - 1
                    else:
                        lon_index_600 = lon_index + 1
                    lat_index_start = min(lat_index_600, lat_index)
                    lat_index_end = max(lat_index_600, lat_index)
                    lon_index_start = min(lon_index_600, lon_index)
                    lon_index_end = min(lon_index_600, lon_index)
                    temp_array = temp_ds[var_name][lat_index_start:(lat_index_end+1),lon_index_start:(lon_index_end+1)].values
                else:
                    temp_array = temp_ds[var_name][(lat_index-1):(lat_index+2),(lon_index-1):(lon_index+2)].values
                temp_list_sif_name.append(var_name)
                temp_avg = np.average(temp_array).item()
                temp_list_sif_avg.append(temp_avg)
                temp_std = np.std(temp_array).item()
                temp_list_sif_std.append(temp_std)
        temp_list_sif_name = ['site_code','latitude','longitude','flex_date','flex_time','flex_filename','s2_filename'] + temp_list_sif_name
        temp_list_sif_avg = [site_name, site_lat, site_lon, filename.split('.')[0].split('_')[-2], filename.split('.')[0].split('_')[-1], filename, s2_filename] + temp_list_sif_avg
        temp_list_sif_std = [site_name, site_lat, site_lon, filename.split('.')[0].split('_')[-2], filename.split('.')[0].split('_')[-1], filename, s2_filename] + temp_list_sif_std
        temp_df_sif_avg = pd.DataFrame([temp_list_sif_avg], columns = temp_list_sif_name)
        temp_df_sif_std = pd.DataFrame([temp_list_sif_std], columns = temp_list_sif_name)
        if not os.path.exists(os.path.join(self.path_cache,'FLEX', 'avg')):
            os.makedirs(os.path.join(self.path_cache,'FLEX', 'avg'))
        if not os.path.exists(os.path.join(self.path_cache,'FLEX', 'std')):
            os.makedirs(os.path.join(self.path_cache,'FLEX', 'std'))
        temp_df_sif_avg.to_csv(os.path.join(self.path_cache,'FLEX','avg',site_name + "_" + filename + ".csv"), index = False)
        temp_df_sif_std.to_csv(os.path.join(self.path_cache,'FLEX','std',site_name + "_" + filename + ".csv"), index = False)

    def sif_output(self, site_name: str, filename: str, site_lon: Union[int, float], site_lat: Union[int, float], roi: int, s2_filename: str) -> list:
        '''
        This function is used to calculate average values of a series of SIF metrics in a 3x3 pixel ROI of a FLEX image of a site. 

        Parameters:
        - site_name: str, the name of the site
        - filename: str, the name of the FLEX image
        - site_lon: Union[int, float], the longitude of the site
        - site_lat: Union[int, float], the latitude of the site

        Returns:
            list_value: list, a list of average values of SIF metrics in a 3x3 pixel ROI of a FLEX image of a site: 
        '''
        # Open the FLEX image
        temp_ds = xr.open_dataset(os.path.join(self.path_flex_input,site_name,filename))
        # Read longitudes and latitudes from the dataset
        longitudes = temp_ds['longitude'].values
        latitudes = temp_ds['latitude'].values
        # Get the indices of the closest longitudes and latitudes to the site
        lon_left = np.where(longitudes <= site_lon)[0][-1]
        lon_right = np.where(longitudes >= site_lon)[0][0]
        lat_top = np.where(latitudes >= site_lat)[0][-1]
        lat_bottom = np.where(latitudes <= site_lat)[0][0]
        # print(f"lon_left: {lon_left}, lon_right: {lon_right}, lat_top: {lat_top}, lat_bottom: {lat_bottom}")
        # Now find the indices of the pixel where the site is located
        if abs(site_lon - longitudes[lon_left]) < abs(site_lon - longitudes[lon_right]):
            lon_index = lon_left
        else:
            lon_index = lon_right
        if abs(site_lat - latitudes[lat_top]) < abs(site_lat - latitudes[lat_bottom]):
            lat_index = lat_top
        else:
            lat_index = lat_bottom

        # Prepare empty lists to store results of each loop
        temp_list_sif_name = []
        temp_list_sif_avg = []

        # Get all variable names in the dataset
        temp_name_rar = list(temp_ds.data_vars)
        list_indices = ['SIF_FARRED_max','SIF_FARRED_max_wvl','SIF_RED_max','SIF_RED_max_wvl','SIF_O2B','SIF_O2A','SIF_int','SIF_FARRED_max_un','SIF_FARRED_max_wvl_un','SIF_RED_max_un','SIF_RED_max_wvl_un','SIF_O2B_un','SIF_O2A_un','SIF_int_un']

        # Loop through each variable name and calculate the average value in the ROI
        for var_name in temp_name_rar:
            if var_name in list_indices:
                if roi == 300:
                    temp_array = temp_ds[var_name][lat_index,lon_index].values
                elif roi == 600:
                    if abs(site_lat - latitudes[lat_index - 1]) < abs(site_lat - latitudes[lat_index + 1]):
                        lat_index_600 = lat_index - 1
                    else:
                        lat_index_600 = lat_index + 1
                    if abs(site_lon - longitudes[lon_index - 1]) < abs(site_lon - longitudes[lon_index + 1]):
                        lon_index_600 = lon_index - 1
                    else:
                        lon_index_600 = lon_index + 1
                    lat_index_start = min(lat_index_600, lat_index)
                    lat_index_end = max(lat_index_600, lat_index)
                    lon_index_start = min(lon_index_600, lon_index)
                    lon_index_end = min(lon_index_600, lon_index)
                    temp_array = temp_ds[var_name][lat_index_start:(lat_index_end+1),lon_index_start:(lon_index_end+1)].values
                else:
                    temp_array = temp_ds[var_name][(lat_index-1):(lat_index+2),(lon_index-1):(lon_index+2)].values
                temp_list_sif_name.append(var_name)
                temp_avg = np.average(temp_array).item()
                temp_list_sif_avg.append(temp_avg)

        # Output as a list
        list_header = ['site_code', 'latitude', 'longitude', 'flex_date', 'flex_time', 'flex_filename', 's2_filename'] + temp_list_sif_name
        list_value = [site_name, site_lat, site_lon, filename.split('.')[0].split('_')[-2], filename.split('.')[0].split('_')[-1], filename, s2_filename] + temp_list_sif_avg

        # Export to the cache folder. This output csv file will be used for validation with FLOX data later. 
        if not os.path.exists(os.path.join(self.path_cache, 'FLEX', 'sif')):
            os.makedirs(os.path.join(self.path_cache, 'FLEX', 'sif'))
        pd.DataFrame([list_value], columns=list_header).to_csv(os.path.join(self.path_cache, 'FLEX', 'sif',f'{site_name}_{filename}.csv'), index=False)
    
    def cal_statistic_flex_flox(self) -> None:
        # Read matchup.csv
        df_merge = pd.read_csv(os.path.join(self.path_output,"L2B_1P_matchup.csv"))
        num_sites = df_merge['site_code'].nunique()
        num_flex_img = df_merge['date'].nunique()
        #
        column_pairs = [
            ['SIF_FARRED_max_flox', 'SIF_FARRED_max_flex'],
            ['SIF_FARRED_max_wvl_flox', 'SIF_FARRED_max_wvl_flex'],
            ['SIF_RED_max_flox', 'SIF_RED_max_flex'],
            ['SIF_RED_max_wvl_flox', 'SIF_RED_max_wvl_flex'],
            ['SIF_O2B_flox', 'SIF_O2B_flex'],
            ['SIF_O2A_flox', 'SIF_O2A_flex'],
            ['SIF_int_flox', 'SIF_int_flex'],
            ['SIF_FARRED_max_un_flox', 'SIF_FARRED_max_un_flex'],
            ['SIF_FARRED_max_wvl_un_flox', 'SIF_FARRED_max_wvl_un_flex'],
            ['SIF_RED_max_un_flox', 'SIF_RED_max_un_flex'],
            ['SIF_RED_max_wvl_un_flox', 'SIF_RED_max_wvl_un_flex'],
            ['SIF_O2B_un_flox', 'SIF_O2B_un_flex'],
            ['SIF_O2A_un_flox', 'SIF_O2A_un_flex'],
            ['SIF_int_un_flox', 'SIF_int_un_flex']]
        list_num_sites = []
        list_num_flex_img = []
        list_r_2 = []
        list_rmse = []
        list_mean_residual = []
        list_random_uncertainty = []
        list_slope = []
        list_intercept = []
        for pair in column_pairs:
            list_num_sites.append(num_sites)
            list_num_flex_img.append(num_flex_img)
            # print(f"Calculating statistics for {pair[0]} and {pair[1]}...")
            temp_r_2, temp_slope, temp_intercept = self.cal_r_2(df_merge[pair[0]],df_merge[pair[1]])
            temp_rmse = self.cal_rmse(df_merge[pair[0]],df_merge[pair[1]])
            temp_mean_residual = self.cal_mean_residual(df_merge[pair[0]],df_merge[pair[1]])
            temp_random_uncertainty = self.cal_random_uncertainty(df_merge[pair[0]],df_merge[pair[1]],temp_mean_residual)
            list_r_2.append(temp_r_2)
            list_rmse.append(temp_rmse)
            list_mean_residual.append(temp_mean_residual)
            list_random_uncertainty.append(temp_random_uncertainty)
            list_slope.append(temp_slope)
            list_intercept.append(temp_intercept)
        df_output = pd.DataFrame({
            "SIF metrics": ["SIF_FARRED_max","SIF_FARRED_max_wvl","SIF_RED_max","SIF_RED_max_wvl","SIF_O2B","SIF_O2A","SIF_int","SIF_FARRED_max_un","SIF_FARRED_max_wvl_un","SIF_RED_max_un","SIF_RED_max_wvl_un","SIF_O2B_un","SIF_O2A_un","SIF_int_un"],
            'n_sites': list_num_sites,
            'n_images': list_num_flex_img,
            'R^2': list_r_2,
            'RMSE': list_rmse,
            'Bias': list_mean_residual,
            'Slope': list_slope,
            'Intercept': list_intercept,
            'Random uncertainty': list_random_uncertainty
        })
        df_output.to_csv(os.path.join(self.path_output,"L2B_1P_validation_report.csv"), index = False)
    
    def cal_statistic_flex_tf(self) -> None:
        # Read matchup.csv
        df_merge = pd.read_csv(os.path.join(self.path_output,"L2B_1P_matchup.csv"))
        # Remove empty rows
        df_merge.replace('', np.nan, inplace=True)
        df_merge.replace('N/A', np.nan, inplace=True)
        df_merge.dropna(inplace = True)
        # Get number of sites and iamges
        num_sites = df_merge['site_code'].nunique()
        num_flex_img = df_merge['date'].nunique()
        #
        column_pairs = [
            ['SIF_FARRED_max_TF', 'SIF_FARRED_max_flex'],
            ['SIF_RED_max_TF', 'SIF_RED_max_flex'],
            ['SIF_O2B_TF', 'SIF_O2B_flex'],
            ['SIF_O2A_TF', 'SIF_O2A_flex'],
            ['SIF_int_TF', 'SIF_int_flex'],
            ['SIF_FARRED_max_un_TF', 'SIF_FARRED_max_un_flex'],
            ['SIF_RED_max_un_TF', 'SIF_RED_max_un_flex'],
            ['SIF_O2B_un_TF', 'SIF_O2B_un_flex'],
            ['SIF_O2A_un_TF', 'SIF_O2A_un_flex'],
            ['SIF_int_un_TF', 'SIF_int_un_flex']]
        list_num_sites = []
        list_num_flex_img = []
        list_r_2 = []
        list_rmse = []
        list_mean_residual = []
        list_random_uncertainty = []
        list_slope = []
        list_intercept = []
        for pair in column_pairs:
            list_num_sites.append(num_sites)
            list_num_flex_img.append(num_flex_img)
            # print(f"Calculating statistics for {pair[0]} and {pair[1]}...")
            temp_r_2, temp_slope, temp_intercept = self.cal_r_2(df_merge[pair[0]],df_merge[pair[1]])
            temp_rmse = self.cal_rmse(df_merge[pair[0]],df_merge[pair[1]])
            temp_mean_residual = self.cal_mean_residual(df_merge[pair[0]],df_merge[pair[1]])
            temp_random_uncertainty = self.cal_random_uncertainty(df_merge[pair[0]],df_merge[pair[1]],temp_mean_residual)
            list_r_2.append(temp_r_2)
            list_rmse.append(temp_rmse)
            list_mean_residual.append(temp_mean_residual)
            list_random_uncertainty.append(temp_random_uncertainty)
            list_slope.append(temp_slope)
            list_intercept.append(temp_intercept)
        df_output = pd.DataFrame({
            "SIF metrics": ["SIF_FARRED_max","SIF_RED_max","SIF_O2B","SIF_O2A","SIF_int","SIF_FARRED_max_un","SIF_RED_max_un","SIF_O2B_un","SIF_O2A_un","SIF_int_un"],
            'n_sites': list_num_sites,
            'n_images': list_num_flex_img,
            'R^2': list_r_2,
            'RMSE': list_rmse,
            'Bias': list_mean_residual,
            'Slope': list_slope,
            'Intercept': list_intercept,
            'Random uncertainty': list_random_uncertainty
        })
        df_output.to_csv(os.path.join(self.path_output,"L2B_1P_TF_validation_report.csv"), index = False)

    def cal_r_2(self, x: np.array, y: np.array) -> float:
        # Fit linear model
        model = LinearRegression()
        model.fit(y.to_numpy().reshape(-1,1), x.to_numpy())

        # Predict using model
        y_pred_from_model = model.predict(y.to_numpy().reshape(-1,1))

        # Now compute R²
        r2 = r2_score(x.to_numpy(), y_pred_from_model)
        # Get linear regression parameters
        slope = model.coef_[0]      # coefficient (slope)
        intercept = model.intercept_  # intercept
        
        return r2, slope, intercept

    def cal_rmse(self, x: np.array, y: np.array) -> float:
        return np.sqrt(((x - y) ** 2).mean())
    
    def cal_mean_residual(self, x: np.array, y: np.array) -> float:
        return (x - y).mean()
    
    def cal_random_uncertainty(self, x: np.array, y: np.array, mean_residual: float) -> float:
        return ((x - y - mean_residual) ** 2).mean()

class S2(CalVal):

    def __init__(self, site_name, site_lat, site_lon, s2_l2a_name):
        '''
        Args:
            site_name (str): the name of the site. 
            site_lat (float): the latitude of the site. 
            site_lon (float): the longitude of the site. 
            s2_name (str): the name of the S2 L2A image, ending with ".SAFE". 
        '''
        super().__init__()
        self.__S2_RESOLUTION = 10
        # Default threshold of CV
        self._threshold_cv = 0.2
        # Default ROI
        self._area = 900
        # Default cloud coverage
        self._cloud = 0.5

        # Site name
        self.site_name = site_name
        self.site_lat = site_lat
        self.site_lon = site_lon
        # S2 L2A name
        self.s2_l2a_name = s2_l2a_name
        # S2 L2A images
        self.path_l2a_b04 = None
        self.path_l2a_b08 = None
        # S2 L2A MASK
        self.path_l2a_mask = None
        # S2 L2A MTD_DS
        self.path_l2a_mtd_ds = None
        # S2 L2A MTD_TL
        self.path_l2a_mtd_tl = None
        # S2 image CRS
        self.s2_crs = None
        # S2 image quantification
        self.s2_l2a_quantification = None
        # S2 image offsets
        self.s2_l2a_offset_b4 = None
        self.s2_l2a_offset_b8 = None

        self.__s2_initialization()
        
    # ------------------------------ Private Members ----------------------------- #

    @property
    def s2_resolution(self):
        return self.__S2_RESOLUTION
    @s2_resolution.setter
    def s2_resolution(self, value):
        if value:
            raise AttributeError("Cannot modify the spatial resolution of Sentinel-2 images!")

    @property
    def threshold_cv(self):
        return self._threshold_cv
    @threshold_cv.setter
    def threshold_cv(self, value):
        if not value:
            self._threshold_cv = 0.2
        else:
            if value <= 0:
                raise ValueError("The threshold of CV should be greater than 0!!!")
            self._threshold_cv = value

    @property
    def area(self):
        return self._area
    @area.setter
    def area(self, value):
        if not value:
            self._area = 900
        else:
            if value % self.__S2_RESOLUTION != 0:
                raise ValueError("The size of the ROI must be a multiple of 100 squared meters!!!")
            self._area = value

    @property
    def cloud(self):
        return self._cloud
    @cloud.setter
    def cloud(self, value):
        if not value:
            self._cloud = 0.5
        else:
            if value < 0 or value > 1:
                raise ValueError("The cloud coverage must be between 0 and 1!!!")
            self._cloud = value

    # ------------------------------ Private Methods ------------------------------ #
    def __s2_initialization(self) -> None:
        '''
        Get all necessary data of the current S2 image. 
        '''
        self.path_l2a_b04, self.path_l2a_b08, self.path_l2a_mask, self.path_l2a_mtd_ds, self.path_l2a_mtd_tl = self.get_s2_l2a_paths()
        self.s2_crs = self.get_s2_crs()
        self.quantification_l2a, self.offset_l2a_b04, self.offset_l2a_b08 = self.get_s2_l2a_metadata()

    # ------------------------------ Public Methods ------------------------------ #

    def create_cache_subfolder(self, subpath) -> None:
        '''
        Create subfolder inside the cache folder. 
        Args:
            subpath (str): the part of the subfolder path (after 'cache').  
        '''
        temp = os.path.join(self.path_cache, subpath)
        if not os.path.exists(temp):
            os.makedirs(temp)

    def get_s2_l2a_paths(self) -> tuple:
        '''
        Get the paths to S2 B4, B8, MSK_CLASSI_B00, MTD_DS and MTD_TL files. 
        Returns:
            tuple: (path_l2a_b04, path_l2a_b08, path_l2a_mask, path_l2a_xml_ds, path_l2a_xml_tl)
        '''
        temp_path_l2a = os.path.join(self.path_s2_input, self.site_name, self.s2_l2a_name)
        for path, subdirs, files in os.walk(temp_path_l2a):
            for name in files:
                temp = os.path.join(path, name)
                if temp[-3:] == 'jp2'in temp and "10m" in temp and "B04" in temp :
                    path_l2a_b04 = temp
                if temp[-3:] == 'jp2'in temp and "10m" in temp and "B08" in temp :
                    path_l2a_b08 = temp
                # Path to the mask file
                if "MSK_CLASSI_B00" in temp and temp[-3:] == 'jp2':
                    path_l2a_mask = temp
                # Get the path to the XML file "MTD_DS" of L1C raster, where there are values of "Quantification Value" and "Radiometric Offset"
                if "MTD_DS.xml" in temp:
                    path_l2a_xml_ds = temp
                if "MTD_TL.xml" in temp:
                    path_l2a_xml_tl = temp
        if not os.path.exists(temp_path_l2a):
            print("User Error: Please organise the input S2 images in correct folder structure. ")
            raise FileNotFoundError(f"The input S2 images folder {temp_path_l2a} doesn't contain the correct folder structure or doesn't contain S2 images! Please check the input S2 images folder!")
        else:
            return path_l2a_b04, path_l2a_b08, path_l2a_mask, path_l2a_xml_ds, path_l2a_xml_tl
        
    def get_s2_crs(self) -> str:
        '''
        Get the coordinate reference system (CRS) of the S2 image.
        Returns:
            str: The CRS of the S2 image in EPSG format.
        '''
        # Read the DS xml file of L2A
        with open(self.path_l2a_mtd_tl, 'r') as f:
            data = f.read()
        bs_l2a_tl = BeautifulSoup(data, "xml")
        # Get the quantification value! 
        l2a_crs = str(bs_l2a_tl.find("HORIZONTAL_CS_CODE").text)
        return l2a_crs
    
    def get_s2_l2a_metadata(self) -> tuple:
        '''
        Retrieve quantification, offset_b04 and offset_b08 from the L2A metadata MTD_DS.xml file. 
        Returns:
            tuple: (quantification_l2a, offset_l2a_b04, offset_l2a_b08)
        '''
        # Read the DS xml file of L2A
        with open(self.path_l2a_mtd_ds, 'r') as f:
            data = f.read()
        bs_l2a_ds = BeautifulSoup(data, "xml")
        # Get the quantification value! 
        quantification_l2a = int(bs_l2a_ds.find("BOA_QUANTIFICATION_VALUE").text)
        # Get the radiometric offset!
        offset_l2a_b04 = int(bs_l2a_ds.find("BOA_ADD_OFFSET", {"band_id": "3"}).text)
        offset_l2a_b08 = int(bs_l2a_ds.find("BOA_ADD_OFFSET", {"band_id": "7"}).text)
        return quantification_l2a, offset_l2a_b04, offset_l2a_b08
    
    def create_clipping_shapefile(self) -> gpd.GeoDataFrame:
        '''
        Create a shapefile to be used for S2 image clipping. This shapefile overlapps perfectly with the pixels of the S2 images. 
        Returns:
            gpd.GeoDataFrame: the new shapefile that will used to clip the S2 image. 
        '''
        # Open the FLEX image
        temp_ds = xr.open_dataset(os.path.join(self.path_flex_input,self.site_name,self.flex_filename))
        # Read longitudes and latitudes from the dataset
        longitudes = temp_ds['longitude'].values
        latitudes = temp_ds['latitude'].values
        # Get the indices of the closest longitudes and latitudes to the site
        lon_left = np.where(longitudes <= self.site_lon)[0][-1]
        lon_right = np.where(longitudes >= self.site_lon)[0][0]
        lat_top = np.where(latitudes >= self.site_lat)[0][-1]
        lat_bottom = np.where(latitudes <= self.site_lat)[0][0]
        # print(f"lon_left: {lon_left}, lon_right: {lon_right}, lat_top: {lat_top}, lat_bottom: {lat_bottom}")
        # Now find the indices of the pixel where the site is located
        if abs(self.site_lon - longitudes[lon_left]) <= abs(self.site_lon - longitudes[lon_right]):
            lon_index = lon_left
        else:
            lon_index = lon_right
        if abs(self.site_lat - latitudes[lat_top]) <= abs(self.site_lat - latitudes[lat_bottom]):
            lat_index = lat_top
        else:
            lat_index = lat_bottom
        print(f"Site {self.site_name} is located at pixel: {lat_index}, {lon_index} with coordinates: {latitudes[lat_index]}, {longitudes[lon_index]}")
        lat_dif = abs(latitudes[1] - latitudes[0]) / 2.0
        lon_dif = abs(longitudes[1] - longitudes[0]) / 2.0
        # Create a box geometry
        if self.area == 300:
            miny = latitudes[lat_index] - lat_dif
            maxy = latitudes[lat_index] + lat_dif
            minx = longitudes[lon_index] - lon_dif
            maxx = longitudes[lon_index] + lon_dif
            # print(f"Creating a shapefile for a 300 m² ROI at {self.site_name} with coordinates: {minx}, {miny}, {maxx}, {maxy}")
        elif self.area == 600:
            if abs(self.site_lat - latitudes[lat_index - 1]) < abs(self.site_lat - latitudes[lat_index + 1]):
                lat_index_600 = lat_index - 1
            else:
                lat_index_600 = lat_index + 1
            if abs(self.site_lon - longitudes[lon_index - 1]) < abs(self.site_lon - longitudes[lon_index + 1]):
                lon_index_600 = lon_index - 1
            else:
                lon_index_600 = lon_index + 1
            miny = min(latitudes[lat_index_600], latitudes[lat_index]) - lat_dif
            maxy = max(latitudes[lat_index_600], latitudes[lat_index]) + lat_dif
            minx = min(longitudes[lon_index_600], longitudes[lon_index]) - lon_dif
            maxx = min(longitudes[lon_index_600], longitudes[lon_index]) + lon_dif
            # print(f"Creating a shapefile for a 600 m² ROI at {self.site_name} with coordinates: {minx}, {miny}, {maxx}, {maxy}")
        else:  
            miny = min(latitudes[lat_index - 1], latitudes[lat_index + 1]) - lat_dif
            maxy = max(latitudes[lat_index - 1], latitudes[lat_index + 1]) + lat_dif
            minx = min(longitudes[lon_index - 1],longitudes[lon_index + 1]) - lon_dif
            maxx = max(longitudes[lon_index - 1],longitudes[lon_index + 1]) + lon_dif
            # print(f"Creating a shapefile for a 900 m² ROI at {self.site_name} with coordinates: {minx}, {miny}, {maxx}, {maxy}")
        # Create a shapefile!
        geom = shp.geometry.box(minx, miny, maxx, maxy)
        gdf_new = gpd.GeoDataFrame({'value': [0], 'geometry': geom}, crs="EPSG:4326")
        gdf_new_utm = gdf_new.to_crs(self.s2_crs)

        # Export shapefiles
        gdf_new.to_file(os.path.join(self.path_cache,self.site_name,"roi_4326.shp"))
        gdf_new_utm.to_file(os.path.join(self.path_cache,self.site_name,"roi_utm.shp"))
        return gdf_new_utm
    
    def create_clipping_raster(self, list_indices = ['NDVI','NIRvREF','TF2']) -> None:
        '''
        '''
        # Suppress divide by zero warning
        np.seterr(all='ignore')

        # Read values
        img_l2a_b04 = rio.open(self.path_l2a_b04)
        img_l2a_b08 = rio.open(self.path_l2a_b08)
        values_l2a_b04 = img_l2a_b04.read(1).astype(np.int32)
        values_l2a_b08 = img_l2a_b08.read(1).astype(np.int32)

        # Get metadata
        src = img_l2a_b04
        out_meta = src.meta
        out_meta.update({
            "driver": "GTiff",
            "dtype": "float64",
            "crs": src.crs,
            "transform": src.transform
        })
        # ------------------------------- Read Mask ROI ------------------------------ #
        img_mask = rio.open(os.path.join(self.path_cache,self.site_name,"Mask.tif"))
        values_mask = img_mask.read(1)
        values_mask = np.where(values_mask == 0, 1, np.nan)

        # ----------------------------------- NDVI ----------------------------------- #
        if not os.path.exists(os.path.join(self.path_cache, self.site_name)):
            os.makedirs(os.path.join(self.path_cache, self.site_name))                              
        # Calculate NDVI of L2A! 
        # NDVI = (B8 - B4) / (B8 + B4)
        temp_ndvi = ((values_l2a_b08 + self.offset_l2a_b08).astype(float) / self.quantification_l2a - (values_l2a_b04 + self.offset_l2a_b04).astype(float) / self.quantification_l2a) / ((values_l2a_b08 + self.offset_l2a_b08).astype(float) / self.quantification_l2a + (values_l2a_b04 + self.offset_l2a_b04).astype(float) / self.quantification_l2a )
        temp_ndvi = temp_ndvi * values_mask
        if 'NDVI' in list_indices:
            # Save
            with rio.open(os.path.join(self.path_cache, self.site_name, "NDVI.tif"), 'w',**out_meta) as dest:
                dest.write(temp_ndvi, 1)
            # Clip to the ROI! 
            self.clip_raster_by_shapefile(os.path.join(self.path_cache, self.site_name, "NDVI.tif"))

        # ---------------------------------- NIRvREF --------------------------------- #
        if 'NIRvREF' in list_indices:
            # Calculate NIRvREF of L2A! 
            # NIRvREF = NDVI * B8
            temp_nirvref = temp_ndvi * (values_l2a_b08 + self.offset_l2a_b08).astype(float) / self.quantification_l2a
            temp_nirvref = temp_nirvref * values_mask
            # Save
            with rio.open(os.path.join(self.path_cache, self.site_name, "NIRv.tif"), 'w',**out_meta) as dest:
                dest.write(temp_nirvref, 1)
            # Clip to the ROI! 
            self.clip_raster_by_shapefile(os.path.join(self.path_cache, self.site_name, "NIRv.tif"))

        # ------------------------------------ TF2 ----------------------------------- #
        if 'TF2' in list_indices:
            # Calculate transfer function 2! B4 * NIRvREF ^ 2
            temp_tf2 = (values_l2a_b04 + self.offset_l2a_b04).astype(float) / self.quantification_l2a * (temp_nirvref ** 2)
            temp_tf2 = temp_tf2 * values_mask
            # Save
            with rio.open(os.path.join(self.path_cache, self.site_name, "TF2.tif"), 'w',**out_meta) as dest:
                dest.write(temp_tf2, 1)
            # Clip to the ROI! 
            self.clip_raster_by_shapefile(os.path.join(self.path_cache, self.site_name, "TF2.tif"))

    def cal_l2a_indices(self) -> dict:
        '''
        Calculate the NDVI and NIRVref of L2A images using the values of B04 and B08 bands.
        Returns:
            dict: A dict containing the NDVI, NIRVref and transfer function 2 values of L2A images.
        '''
        # Suppress divide by zero warning
        np.seterr(all='ignore')
        if not os.path.exists(os.path.join(self.path_cache, self.site_name, "NDVI_ROI.tif")) or not os.path.exists(os.path.join(self.path_cache, self.site_name, "NIRvREF_ROI.tif")):
            self.create_clipping_raster(['NDVI','NIRvREF'])

        # Calculate avg, std, cv of NDVI inside the ROI
        image_ndvi_roi = rio.open(os.path.join(self.path_cache, self.site_name, "NDVI_ROI.tif"))
        values_ndvi_roi = image_ndvi_roi.read(1)
        temp_ndvi_std = self.cal_std(values_ndvi_roi)
        temp_ndvi_avg = self.cal_avg(values_ndvi_roi)
        temp_ndvi_cv = self.cal_cv(values_ndvi_roi)
        temp_ndvi_flag = self.cal_flag(temp_ndvi_cv)

        # Calculate avg, std, cv of NIRvREF inside the ROI
        image_nirv_roi = rio.open(os.path.join(self.path_cache, self.site_name, "NIRv_ROI.tif"))
        values_nirv_roi = image_nirv_roi.read(1)
        temp_nirv_std = self.cal_std(values_nirv_roi)
        temp_nirv_avg = self.cal_avg(values_nirv_roi)
        temp_nirv_cv = self.cal_cv(values_nirv_roi)
        temp_nirv_flag = self.cal_flag(temp_nirv_cv)

        # Manually ensure available memory
        image_nirv_roi.close()
        image_ndvi_roi.close()

        return temp_ndvi_std, temp_ndvi_avg, temp_ndvi_cv, temp_ndvi_flag, temp_nirv_std, temp_nirv_avg, temp_nirv_cv, temp_nirv_flag
        
    def clip_raster_by_shapefile(self, path_raster) -> None:
        '''
        Clip the raster to the shapefile and save to local storage. 
        Args:
            path_raster (str): path to the raster to be clipped. 
        '''
        # Create the clipping shapefile
        shp_clipping = self.create_clipping_shapefile()
        # Read the raster to be clipped
        raster = rio.open(path_raster)
        # Clipping! 
        out_image, out_transform = rio.mask.mask(raster, shp_clipping.geometry, crop=True)
        out_meta = raster.meta
        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})
        # Save!
        with rio.open(os.path.join(self.path_cache, self.site_name, os.path.splitext(os.path.basename(path_raster))[0] + "_ROI.tif"), "w", **out_meta) as dest:
            dest.write(out_image)
        
        # Manually ensure available memory
        raster.close()
    
    def cal_valid_pixels(self) -> tuple:
        '''
        Check if there are sufficient valid pixels (not snow, ice or cloud). 
        Returns:
            tuple: (bool_pass, num_valid_pixels, percentage_valid_pixels)
        '''
        mask_l2a = rio.open(self.path_l2a_mask)
        mask_l2a_opaque_clouds = mask_l2a.read(1)
        mask_l2a_cirrus_clouds = mask_l2a.read(2)
        mask_l2a_snowice_areas = mask_l2a.read(3)
        # Check if all three masks are empty. If not empty, we should check if the masked
        mask_combined = mask_l2a_opaque_clouds + mask_l2a_cirrus_clouds + mask_l2a_snowice_areas
        if np.max(mask_combined) >= 1:
            # Upscale 60mx60m mask to 10mx10m without modifying any pixel values
            mask_combined_upscale = np.repeat(mask_combined, 6, axis = 0)
            mask_combined_upscale = np.repeat(mask_combined_upscale, 6, axis = 1)
            # Read a random S2 image to retrieve metadata
            img_l2a_b04 = rio.open(self.path_l2a_b04)
            mask_meta = img_l2a_b04.meta
            # Save this mask to the cache folder
            with rio.open(os.path.join(self.path_cache,self.site_name,"Mask.tif"), "w", **mask_meta) as dest:
                dest.write(mask_combined_upscale, indexes = 1)
            # clip and save the mask raster
            self.clip_raster_by_shapefile(os.path.join(self.path_cache, self.site_name, "Mask.tif"))
            # Validate pixels in the ROI
            temp_mask_clipped = rio.open(os.path.join(self.path_cache, self.site_name, "Mask_ROI.tif"))
            temp_mask_clipped_values = temp_mask_clipped.read(1)
            # Manually ensure available memory
            mask_l2a.close()
            img_l2a_b04.close()
            temp_mask_clipped.close()
            if np.max(temp_mask_clipped_values) >= 1:
                temp_valid_pixels = np.count_nonzero(temp_mask_clipped_values == 0)
                temp_invalid_pixels = np.count_nonzero(temp_mask_clipped_values != 0)
                temp_total_pixels = temp_valid_pixels + temp_invalid_pixels
                temp_valid_pixels_ratio = temp_valid_pixels / temp_total_pixels
                if temp_valid_pixels_ratio >= self.cloud:
                    print(f"But the ratio of valid pixels is {temp_valid_pixels_ratio:.2%}, equal to or greater than {self.cloud:.2%}, so we can use these S2 images. ")
                    bool_pass = True
                    return bool_pass, temp_valid_pixels, temp_valid_pixels_ratio
                else:
                    print(f"And the ratio of valid pixels is {temp_valid_pixels_ratio:.2%}, lower than {self.cloud:.2%}, so we can't use these S2 images and hence we can't proceed. ")
                    bool_pass = False
                    return bool_pass, temp_valid_pixels, temp_valid_pixels_ratio
            else:
                print(f"All pixels in the current S2 image are valid! ")
                bool_pass = True
                return bool_pass, (self.area / 10) ** 2, 1  

        else:
            print(f"All pixels in the current S2 image are valid! ")
            bool_pass = True

        # Manually ensure available memory
        mask_l2a.close()
        return bool_pass, (self.area / 10) ** 2, 1   

    def cal_std(self, value):
        return np.nanstd(value)
        
    def cal_avg(self, value):
        return np.nanmean(value)

    def cal_cv(self, value):
        return np.nanstd(value) / np.nanmean(value)
    
    def cal_flag(self, value):
        if value <= self.threshold_cv:
            return 1
        else:
            return 0

    def cal_transfer_function(self, flex_date) -> bool:
        '''
        Application of transfer function, and then save the calculated averages into a temporary .csv file in "Cache\\TF
        Args:
            flex_date (int): The date of the current flex image. 
        Returns:
            bool: The validality of FLOX
        '''
        if not os.path.exists(os.path.join(self.path_cache, self.site_name, "NIRv_ROI.tif")) or not os.path.exists(os.path.join(self.path_cache, self.site_name, "TF2_ROI.tif")):
            self.create_clipping_raster(['NIRvREF','TF2'])

        # ------------------------ Find the index of the site ------------------------ #
        # Create a point shapefile of the site, using Lon-Lat
        df_4326 = pd.DataFrame({
            "Site": [self.site_name],
            "Latitude": [self.site_lat],
            "Longitude": [self.site_lon]
        })
        gdf_4326 = gpd.GeoDataFrame(
            df_4326,
            geometry = gpd.points_from_xy(df_4326['Longitude'], df_4326['Latitude']),
            crs = "EPSG:4326"
        )
        # Convert the crs from lat-lon to that of the S2 image
        gdf_s2_crs = gdf_4326.to_crs(self.s2_crs)
        # Retrieve the coordinates in the new crs of our site
        site_x = gdf_s2_crs.geometry.x.values[0]
        site_y = gdf_s2_crs.geometry.y.values[0]
        # Open image
        img_tf1 = rio.open(os.path.join(self.path_cache, self.site_name, "NIRv_ROI.tif"))
        img_tf2 = rio.open(os.path.join(self.path_cache, self.site_name, "TF2_ROI.tif"))
        # Read values
        value_tf1 = img_tf1.read(1)
        value_tf2 = img_tf2.read(1)

        # Get the corresponding FLOX data
        df_flox = pd.read_csv(self.file_flox_csv, sep = ';')
        df_flox.rename(columns={'UTC_datetime': 'date'}, inplace=True)
        df_flox['date'] = pd.to_datetime(df_flox['date'], format='%d/%m/%Y %H:%M')
        # Convert to string date format
        df_flox['date'] = df_flox['date'].dt.strftime('%Y%m%d').astype(str)
        df_flox_site = df_flox[(df_flox['ID_SITE'] == self.site_name) & (df_flox['date'] == flex_date)]

        # Create an empty dict
        temp_dict = {'site_code': self.site_name, 'date': str(flex_date),
            'SIF_O2A': 0, 'SIF_FARRED_max': 0, 'SIF_int': 0, 'SIF_O2B': 0, 'SIF_RED_max': 0,
            'SIF_O2A_un': 0, 'SIF_FARRED_max_un': 0, 'SIF_int_un': 0, 'SIF_O2B_un': 0, 'SIF_RED_max_un': 0,
        }

        # ------------------------------------ TF1 ----------------------------------- #
        for var_name in ['SIF_O2A','SIF_FARRED_max','SIF_int']:
            # Get the pixel index of the site
            site_row, site_col = img_tf1.index(site_x, site_y)
            # Get the value of the site based on the transfer function
            value_s2_flox = value_tf1[site_row, site_col]
            # Get the value of the flox of the current index
            value_flox = df_flox_site[var_name].values[0].item()
            if isinstance(value_s2_flox, np.float64) and np.isnan(value_s2_flox) or not value_s2_flox:
                print(f"{self.site_name} is inside an invalid pixel. The transfer function won't be applied!")
                temp_dict[var_name] = 'N/A'
                bool_flox_invalid = True
            else:
                # Apply transfer function 1
                value_tf = value_tf1 / value_s2_flox * value_flox
                # Calculate average
                value_tf_avg = np.nanmean(value_tf)
                # Update the dicct
                temp_dict[var_name] = str(value_tf_avg)
                bool_flox_invalid = False
        # ------------------------------------ TF2 ----------------------------------- #
        for var_name in ['SIF_O2B','SIF_RED_max']:
            # Get the pixel index of the site
            site_row, site_col = img_tf2.index(site_x, site_y)
            # Get the value of the site based on the transfer function
            value_s2_flox = value_tf2[site_row, site_col]
            # Get the value of the flox of the current index
            value_flox = df_flox_site[var_name].values[0].item()
            if isinstance(value_s2_flox, np.float64) and np.isnan(value_s2_flox) or not value_s2_flox:
                print(f"{self.site_name} is inside an invalid pixel. The transfer function won't be applied!")
                temp_dict[var_name] = 'N/A'
            else:
                # Apply transfer function 2
                value_tf = value_tf2 / value_s2_flox * value_flox
                # Calculate average
                value_tf_avg = np.nanmean(value_tf)
                # Update the dicct
                temp_dict[var_name] = str(value_tf_avg)

        # Save to local storage  
        df_dict = pd.DataFrame([temp_dict])
        if not os.path.exists(os.path.join(self.path_cache,"TF")):
            os.makedirs(os.path.join(self.path_cache,"TF"))
        df_dict.to_csv(os.path.join(self.path_cache,"TF",self.site_name + "_" + flex_date + ".csv"), index = False, na_rep= 'N/A')
        return bool_flox_invalid

    def remove_cache(self):
        # Delete cache folder? 
        if self.bool_delete_cache:
            if os.path.exists(os.path.join(self.path_cache, self.site_name, "NDVI.tif")):
                os.remove(os.path.join(self.path_cache, self.site_name, "NDVI.tif"))
            if os.path.exists(os.path.join(self.path_cache, self.site_name, "NIRv.tif")):           
                os.remove(os.path.join(self.path_cache, self.site_name, "NIRv.tif"))
            if os.path.exists(os.path.join(self.path_cache, self.site_name, "TF2.tif")):
                os.remove(os.path.join(self.path_cache, self.site_name, "TF2.tif"))
            if os.path.exists(os.path.join(self.path_cache, self.site_name, "NDVI_ROI.tif")):
                os.remove(os.path.join(self.path_cache, self.site_name, "NDVI_ROI.tif"))
            if os.path.exists(os.path.join(self.path_cache, self.site_name, "NIRv_ROI.tif")):           
                os.remove(os.path.join(self.path_cache, self.site_name, "NIRv_ROI.tif"))
            if os.path.exists(os.path.join(self.path_cache, self.site_name, "TF2_ROI.tif")):
                os.remove(os.path.join(self.path_cache, self.site_name, "TF2_ROI.tif"))