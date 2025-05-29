import os
import csv
from typing import Optional, Union
import numpy as np
import pandas as pd
import xarray as xr
import rasterio as rio

from class_calval import FLEX

class SIF(FLEX):

    def __init__(self):
         super().__init__()
         self._band_O2A = '760'
         self._band_O2B = '686'
         self._band_max_red = '684'
         self._band_max_farred = '740'
         self._list_header = ['site','filename','date','time','SIF_FARRED_max','SIF_FARRED_max_wvl','SIF_RED_max','SIF_RED_max_wvl','SIF_O2B','SIF_O2A','SIF_int','SIF_O2B_un','SIF_O2A_un']
         self._file_flox_csv = os.path.join(self._path_main,'flox_sifparms_filt_flextime_aggr_avg_allsites.csv')
    
    # ------------------------------ Getter & Setter ----------------------------- #
    @property
    def band_O2A(self):
        return self._band_O2A
    @band_O2A.setter
    def band_O2A(self, value):
        self._band_O2A = self.__check_input_wavelength__(value)
    @property
    def band_O2B(self):
        return self._band_O2B
    @band_O2B.setter
    def band_O2B(self, value):
        self._band_O2B = self.__check_input_wavelength__(value)
    @property
    def band_max_red(self):
        return self._band_max_red
    @band_max_red.setter
    def band_max_red(self, value):
        self._band_max_red = self.__check_input_wavelength__(value)
    @property
    def band_max_farred(self):
        return self._band_max_farred
    @band_max_farred.setter
    def band_max_farred(self, value):
        self._band_max_farred = self.__check_input_wavelength__(value)
    @property
    def list_header(self):
        return self._list_header
    @list_header.setter
    def list_header(self, value):
        if value:
            raise ValueError('User error: Cannot modify variables to calculate!!!')
    @property
    def file_flox_csv(self):
        return self._file_flox_csv
    @file_flox_csv.setter
    def file_flox_csv(self, value):
        self._file_flox_csv = value

    # ------------------------------ Private Methods ------------------------------ #
    def __check_input_wavelength__(self, value):
        if isinstance(value, str):
            # The string must only contain numbers
            if value.isdigit():
                return value
            else:
                raise ValueError('Please enter the correct wavelength in nm (without the unit)!')
        elif isinstance(value, int):
            temp = str(value)
            return temp
        else:
            raise ValueError('Please enter the correct wavelength in nm (without the unit)!')
        
    # ------------------------------ Public Methods ------------------------------ #
    def SIF_avg_output(self, site_name: str, filename: str, site_lon: Union[int, float], site_lat: Union[int, float], bool_save: Optional[bool] = False) -> list:
        '''
        This function is used to calculate average values of a series of SIF metrics in a 3x3 pixel ROI of a FLEX image of a site. 

        Parameters:
        - site_name: str, the name of the site
        - filename: str, the name of the FLEX image
        - site_lon: Union[int, float], the longitude of the site
        - site_lat: Union[int, float], the latitude of the site

        Returns:
            list_value: list, a list of average values of SIF metrics in a 3x3 pixel ROI of a FLEX image of a site: ['site','filename','date','time','SIF_FARRED_max','SIF_FARRED_max_wvl','SIF_RED_max','SIF_RED_max_wvl','SIF_O2B','SIF_O2A','SIF_int','SIF_O2B_un','SIF_O2A_un']
        '''
        temp_ds = rio.open(f'netcdf:{os.path.join(self.path_input,site_name,filename)}:Leaf Area Index')
        # Get the pixel where there is the site
        temp_index_x, temp_index_y = temp_ds.index(site_lon,site_lat)
        print(f"FLEX image '{filename}' opened succesfully!")
        # Prepare for the output
        # Date + Time
        temp_date = filename.split('.')[0].split('_')[-2]
        temp_time = filename.split('.')[0].split('_')[-1]
        # Read dataset
        temp_ds = xr.open_dataset(os.path.join(self.path_input, site_name, filename))
        # Calculate metrics
        temp_avg_max_red = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self.band_max_red}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_max_farred = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self.band_max_farred}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2A = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self.band_O2A}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2B = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self.band_O2B}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_int = np.average(temp_ds[f"Total Integrated SIF"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2A_un = np.average(temp_ds[f"Sif Emission Spectrum Uncertainty_sif_wavelength_grid={self.band_O2A}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2B_un = np.average(temp_ds[f"Sif Emission Spectrum Uncertainty_sif_wavelength_grid={self.band_O2B}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        # Output as a list
        list_value = [site_name,filename,temp_date,temp_time,temp_avg_max_farred,self.band_max_farred,temp_avg_max_red,self.band_max_red,temp_avg_O2B,temp_avg_O2A,temp_avg_int,temp_avg_O2A_un,temp_avg_O2B_un]
        # The header line
        if bool_save:
            if not os.path.join(self._path_output,site_name):
                os.makedirs(os.path.join(self._path_output,site_name))
            with open(os.path.join(self._path_output,site_name,filename + " - sif avg.csv"), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.list_header)
                writer.writerow(list_value)
        return list_value
    
    def cal_statistic(self, bool_save: Optional[bool] = False) -> list:
        df_flox = pd.read_csv(self.file_flox_csv)
        df_flox = df_flox[['FLOX_site_code','SIF_FARRED_max','SIF_RED_max','SIF_O2B','SIF_O2A','SIF_int','SIF_O2B_un','SIF_O2A_un']]
        df_flox.rename(columns={'FLOX_site_code': 'site'}, inplace=True)
        df_flex = pd.read_csv(os.path.join(self._path_output,"flex_sifparms_filt_flextime_aggr_avg_allsites.csv"))
        df_flex = df_flex[['site','SIF_FARRED_max','SIF_RED_max','SIF_O2B','SIF_O2A','SIF_int','SIF_O2B_un','SIF_O2A_un']]
        df_merge = pd.merge(df_flox,df_flex,how='inner',on=['site'], suffixes=('_flox','_flex'))
        column_pairs = [('SIF_FARRED_max_flox','SIF_FARRED_max_flex'),('SIF_RED_max_flox','SIF_RED_max_flex'),('SIF_O2B_flox','SIF_O2B_flex'),('SIF_O2A_flox','SIF_O2A_flex'),('SIF_int_flox','SIF_int_flex'),('SIF_O2B_un_flox','SIF_O2B_un_flex'),('SIF_O2A_un_flox','SIF_O2A_un_flex')]
        list_r_2 = []
        list_rmse = []
        list_mean_residual = []
        list_random_uncertainty = []
        for pair in column_pairs:
            temp_r_2 = self.cal_r_2(df_merge[pair[1]],df_merge[pair[0]])
            temp_rmse = self.cal_rmse(df_merge[pair[1]],df_merge[pair[0]])
            temp_mean_residual = self.cal_mean_residual(df_merge[pair[1]],df_merge[pair[0]])
            temp_random_uncertainty = self.cal_random_uncertainty(df_merge[pair[1]],df_merge[pair[0]],temp_mean_residual)
            list_r_2.append(temp_r_2)
            list_rmse.append(temp_rmse)
            list_mean_residual.append(temp_mean_residual)
            list_random_uncertainty.append(temp_random_uncertainty)
        if bool_save:
            with open(os.path.join(self._path_output,"statistics.csv"), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['SIF metrics','R^2','RMSE','Mean residual','Random uncertainty'])
                writer.writerow(['SIF_FARRED_max',list_r_2[0],list_rmse[0],list_mean_residual[0],list_random_uncertainty[0]])
                writer.writerow(['SIF_RED_max',list_r_2[1],list_rmse[1],list_mean_residual[1],list_random_uncertainty[1]])
                writer.writerow(['SIF_O2B',list_r_2[2],list_rmse[2],list_mean_residual[2],list_random_uncertainty[2]])
                writer.writerow(['SIF_O2A',list_r_2[3],list_rmse[3],list_mean_residual[3],list_random_uncertainty[3]])
                writer.writerow(['SIF_int',list_r_2[4],list_rmse[4],list_mean_residual[4],list_random_uncertainty[4]])
                writer.writerow(['SIF_O2B_un',list_r_2[5],list_rmse[5],list_mean_residual[5],list_random_uncertainty[5]])
                writer.writerow(['SIF_O2A_un',list_r_2[6],list_rmse[6],list_mean_residual[6],list_random_uncertainty[6]])
        return list_r_2, list_rmse, list_mean_residual, list_random_uncertainty

    def cal_r_2(self, x: np.array, y: np.array) -> float:
        return 1 - ((x - y) ** 2).sum() / ((x - x.mean()) ** 2).sum()

    def cal_rmse(self, x: np.array, y: np.array) -> float:
        return np.sqrt(((x - y) ** 2).mean())
    
    def cal_mean_residual(self, x: np.array, y: np.array) -> float:
        return (x - y).mean()
    
    def cal_random_uncertainty(self, x: np.array, y: np.array, mean_residual: float) -> float:
        return ((x - y - mean_residual) ** 2).mean()
    



