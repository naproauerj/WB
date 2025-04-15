import numpy as np
from pykrige.ok import OrdinaryKriging
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from netCDF4 import Dataset
from matplotlib.colors import ListedColormap, BoundaryNorm

def save_to_netcdf(filename, longitude, latitude, variable_name, data):
    rootgrp = Dataset(filename, "w", format="NETCDF4")
    rootgrp.createDimension("lon", len(longitude))
    rootgrp.createDimension("lat", len(latitude))
    
    lon_var = rootgrp.createVariable("lon", "f4", ("lon",))
    lon_var[:] = longitude
    
    lat_var = rootgrp.createVariable("lat", "f4", ("lat",))
    lat_var[:] = latitude
    
    var = rootgrp.createVariable(variable_name, "f4", ("lat", "lon"))
    var[:, :] = data
    
    rootgrp.close()

def interpola(obs_longitudes, obs_latitudes, values_to_interpolate, variograma, grid):
    grid_x, grid_y = np.meshgrid(grid['lon'], grid['lat'])
    OK = OrdinaryKriging(
         obs_longitudes,
         obs_latitudes,
         values_to_interpolate,
         variogram_model=variograma,
    )
    z, ss = OK.execute("grid", grid['lon'], grid['lat'])
    return z, grid_x, grid_y

def plota_interp(grid_x, grid_y, z, bounds, obs_longitudes, obs_latitudes, valores, nomevar, nome_figura, modelo):
    cmap = ListedColormap(['darkred', 'red', 'orangered', 'orange', 'gold', 'yellow', 'greenyellow', 'lawngreen', 'lime', 'limegreen', 'forestgreen', 'aquamarine', 'aqua', 'deepskyblue', 'blue', 'indigo'])
    norm = BoundaryNorm(bounds, cmap.N)
    
    plt.figure(figsize=(10, 8))
    plt.contourf(grid_x, grid_y, z, levels=bounds, cmap=cmap, norm=norm)
    gdf.plot(ax=plt.gca(), edgecolor='gray', facecolor='none', lw=1)
    
    cbar = plt.colorbar()
    cbar.set_label(nomevar)
    
    plt.title("Interpolação com " + modelo)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True)
    plt.savefig(nome_figura, dpi=300, bbox_inches="tight")
    plt.close()

# Carregar o shapefile
shapefile_path = '../00_STUFF/BAHIA.shp'
gdf = gpd.read_file(shapefile_path)
lon_min, lat_min, lon_max, lat_max = gdf.total_bounds

# Carregar os dados do arquivo Excel
file_path = "../04_FILTRAGEM/selecao_BAHIA_1991a2020.xlsx"
sheet_name = "ANUAL"
df = pd.read_excel(file_path, sheet_name=sheet_name)

obs_latitudes = df["Latitude"]
obs_longitudes = df["Longitude"]
values_to_interpolate = df["Média mm/ano"]

resolucao = 0.1
tamx = int(abs(lon_max - lon_min) / resolucao)
tamy = int(abs(lat_max - lat_min) / resolucao)

grid = {
    "lat": np.linspace(lat_min, lat_max, tamy),
    "lon": np.linspace(lon_min, lon_max, tamx)
}

bounds = [400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]
modelos = ["hole-effect", "power", "gaussian", "spherical", "exponential", "linear"]

for model in modelos:
    z, grid_x, grid_y = interpola(obs_longitudes, obs_latitudes, values_to_interpolate, model, grid)
    nome_figura = f"interp_clima_krigging_1991a2020_{model}.png"
    plota_interp(grid_x, grid_y, z, bounds, obs_longitudes, obs_latitudes, values_to_interpolate, "Media", nome_figura, "Krigging " + model)
    save_to_netcdf(f"interp_clima_krigging_1991a2020_{model}.nc", grid_x[0, :], grid_y[:, 0], "Media", z)
