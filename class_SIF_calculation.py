import os
import csv
import numpy as np
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
    
    # ----------------------------- Protected Members ---------------------------- #
    @property
    def band_O2A(self):
        return self._band_O2A
    def band_O2A(self, value):
        self._band_O2A = self.__check_input_wavelength__(value)
    @property
    def band_O2B(self):
        return self._band_O2B
    def band_O2B(self, value):
        self._band_O2B = self.__check_input_wavelength__(value)
    @property
    def band_max_red(self):
        return self._band_max_red
    def band_max_red(self, value):
        self._band_max_red = self.__check_input_wavelength__(value)
    @property
    def band_max_farred(self):
        return self._band_max_farred
    def band_max_farred(self, value):
        self._band_max_farred = self.__check_input_wavelength__(value)

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
    def SIF_avg_output(self, site_name, filename, site_lon, site_lat):
        temp_ds = rio.open(f'netcdf:{os.path.join(self._path_input,site_name,filename)}:Leaf Area Index')
        # Get the pixel where there is the site
        temp_index_x, temp_index_y = temp_ds.index(site_lon,site_lat)
        print(f"FLEX image '{filename}' opened succesfully!")
        # Prepare for the output
        # Date + Time
        temp_date = filename.split('.')[0].split('_')[-2]
        temp_time = filename.split('.')[0].split('_')[-1]
        # Read dataset
        temp_ds = xr.open_dataset(os.path.join(self._path_input, site_name, filename))
        # Calculate metrics
        temp_avg_max_red = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self._band_max_red}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_max_farred = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self._band_max_farred}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2A = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self._band_O2A}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2B = np.average(temp_ds[f"Sif Emission Spectrum_sif_wavelength_grid={self._band_O2B}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_int = np.average(temp_ds[f"Total Integrated SIF"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2A_un = np.average(temp_ds[f"Sif Emission Spectrum Uncertainty_sif_wavelength_grid={self._band_O2A}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        temp_avg_O2B_un = np.average(temp_ds[f"Sif Emission Spectrum Uncertainty_sif_wavelength_grid={self._band_O2B}"][(temp_index_x-1):(temp_index_x+2),(temp_index_y-1):(temp_index_y+2)].values).item()
        # The header line
        list_header = ['site','filename','date','time','SIF_FARRED_max','SIF_FARRED_max_wvl','SIF_RED_max','SIF_RED_max_wvl','SIF_O2B','SIF_O2A','SIF_int','SIF_O2B_un','SIF_O2A_un']
        list_value = [site_name,filename,temp_date,temp_time,temp_avg_max_farred,self._band_max_farred,temp_avg_max_red,self._band_max_red,temp_avg_O2B,temp_avg_O2A,temp_avg_int,temp_avg_O2B_un,temp_avg_O2A_un]
        # Output
        with open(os.path.join(self._path_output,site_name,filename + " - Sif avg.csv"), "w", newline='', encoding = 'utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(list_header)
            writer.writerow(list_value)
        
