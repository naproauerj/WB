import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
from matplotlib.colors import ListedColormap, TwoSlopeNorm
from scipy.interpolate import griddata

# --- Arquivos ---
clim_path = "../06_INTERPOLACAO/MEDIA/bahia_1981a2010__interpolacao_Kriging_exponential.nc"
hist_path = "../07_HISTORICO/MRI-ESM2-0_HISTORICO.nc"
prev_path = "./pr_Amon_MRI-ESM2-0_ssp585_r1i1p1f1_gn_201501-210012.nc"
shapefile_path = "../00_STUFF/regioes.shp"

# --- Extrair nome do modelo e cenário do arquivo de previsão ---
import os
import re

prev_filename = os.path.basename(prev_path)
modelo_match = re.search(r'_([A-Za-z0-9\-]+)_ssp', prev_filename)
cenario_match = re.search(r'_ssp(\d+)', prev_filename)

modelo = modelo_match.group(1) if modelo_match else "modelo"
cenario = str(cenario_match.group(1)) if cenario_match else "cenario"

# --- Grade desejada ---
new_lat = np.arange(-19.99, -8.0 + 0.1, 0.1)
new_lon = np.arange(-47.99, -37.0 + 0.1, 0.1)
lon2d, lat2d = np.meshgrid(new_lon, new_lat)

# --- Escalas de cores ---
levels = [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]
escala100 = [-100, -80, -60, -40, -20, -10, -5, 0, 5, 10, 20, 40, 60, 80, 100]
errorel= [-100,-90,-70,-50,-30,-20,-15,-10,-5,0,5,10,15,20,30,50,70,90,100 ] 
cmap_custom = ListedColormap([
    'darkred', 'red', 'orange', 'yellow', 'greenyellow', 'limegreen',
    'green', 'cyan', 'deepskyblue', 'blue', 'mediumblue', 'darkblue'
])
diverging_cmap = 'RdBu_r'

# --- Leitura dos dados ---
clim_ds = xr.open_dataset(clim_path)
clim = clim_ds['Interpolacao']
hist = xr.open_dataset(hist_path)['precipitacao']
prev = xr.open_dataset(prev_path)['pr']

# --- Conversão de unidades (se necessário) ---

prev = prev * 24 * 3600 * 365

# --- Seleção e correção da projeção para 2030-2040 ---
ds = xr.open_dataset(prev_path)

# Selecionar o período desejado
prev_sel = ds.sel(time=slice("2030", "2040"))

# Corrigir longitudes para -180 a 180 e ordenar
prev_sel = prev_sel.assign_coords(lon=(((prev_sel.lon + 180) % 360) - 180)).sortby('lon')

# Remover duplicatas de coordenadas (forma segura)
_, unique_lat_idx = np.unique(prev_sel.lat.values, return_index=True)
_, unique_lon_idx = np.unique(prev_sel.lon.values, return_index=True)
prev_sel = prev_sel.isel(lat=sorted(unique_lat_idx), lon=sorted(unique_lon_idx))

# Média climatológica e conversão para mm/ano
prev_mean_raw = prev_sel['pr'].mean(dim='time') * 24 * 3600 * 365
prev_mean_raw.attrs["units"] = "mm/ano"
prev_mean_raw.name = "precipitacao"

# Interpolação para a mesma grade da climatologia
prev_mean = prev_mean_raw.interp_like(clim)

# Verificar NaNs totais
if np.isnan(prev_mean).all():
    print(f"⚠️ Todos os valores são NaN após interpolação: {prev_path}")

prev_interp = prev_mean

# --- Interpolação da projeção para a grade da climatologia ---
# (removida - já foi feita com interp_like)

# --- Dados já na grade final ---
clim_interp = clim
hist_interp = hist

# --- Cálculos ---
percentual = 1 - (prev_interp / hist_interp)
aplicacao = percentual * clim_interp
cenario_calculado = aplicacao + clim_interp

erro_relativo = ((cenario_calculado / clim_interp) - 1) * 100

# --- Função de plotagem ---
def plot_map(data, title, fname, units='mm', cmap=cmap_custom, levels=None, center_zero=False):
    if np.isnan(data).all():
        print(f"⚠️ Dados ausentes para '{title}', gráfico não gerado.")
        return

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    shapefile = gpd.read_file(shapefile_path)
    shapefile.boundary.plot(ax=ax, edgecolor='black', linewidth=1)

    lons, lats = data.lon, data.lat
    if center_zero:
        try:
            vmin = np.nanmin(data)
            vmax = np.nanmax(data)
            if vmin == vmax:
                print(f"⚠️ Dados constantes em '{title}', gráfico não gerado.")
                return
            if not (vmin < 0 < vmax):
                norm = None
                im = ax.contourf(lons, lats, data, cmap=cmap, levels=levels, extend='both')
            else:
                norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
                im = ax.contourf(lons, lats, data, cmap=cmap, norm=norm, levels=levels, extend='both')
            im = ax.contourf(lons, lats, data, cmap=cmap, norm=norm, levels=levels, extend='both')
            ax.contour(lons, lats, data, levels=levels, colors='black', linewidths=0.5, linestyles='solid')
            ax.clabel(ax.contour(lons, lats, data, levels=levels, colors='black', linewidths=0.5), fmt="%.0f%%", fontsize=8)
            ax.contour(lons, lats, data, levels=levels, colors='black', linewidths=0.5)
        except ValueError as e:
            print(f"⚠️ Erro ao gerar mapa '{title}': {e}")
            return
    else:
        norm = None
        im = ax.contourf(lons, lats, data, cmap=cmap, levels=levels, extend='both')

    cbar = plt.colorbar(im, ax=ax, orientation='vertical', label=units)
    if not center_zero:
        cbar.set_ticks(levels)
        cbar.set_ticklabels([str(v) for v in levels])
    ax.set_title(title)
    ax.coastlines()
    xmin, ymin, xmax, ymax = shapefile.total_bounds
    ax.set_extent([xmin, xmax, ymin, ymax], crs=ccrs.PlateCarree())
    plt.savefig(f"{fname}.png", dpi=300, bbox_inches='tight')
    plt.close()

# --- Gerar mapas ---
plot_map(clim_interp, f"Climatologia - {modelo} SSP{cenario}", f"climatologia_{modelo}_ssp{cenario}", levels=levels)
plot_map(hist_interp, f"Histórico (1981–2010) - {modelo} SSP{cenario}", f"historico_{modelo}_ssp{cenario}", levels=levels)
plot_map(prev_interp, f"Projeção (2030–2040) - {modelo} SSP{cenario}", f"previsao_{modelo}_ssp{cenario}", levels=levels)
plot_map(
     percentual * 100,
     f"PREVISÃO PERCENTUAL DE CHUVA PERÍODO: 2030–2040 MODELO {modelo} - CENÁRIO SSP{cenario}",
     f"percentual_{modelo}_ssp{cenario}",
     units="%",
     cmap='RdBu',  #'bwr', 
     levels=np.arange(-30, 30, 1),
     center_zero=True
)
plot_map(aplicacao, f"Aplicação - {modelo} SSP{cenario}", f"aplicacao_{modelo}_ssp{cenario}", levels=escala100)
plot_map(cenario_calculado, f"Cenário - {modelo} SSP{cenario}", f"cenario_{modelo}_ssp{cenario}", levels=levels)
plot_map(erro_relativo, f"Erro Relativo (%) - {modelo} SSP{cenario}", f"erro_relativo_{modelo}_ssp{cenario}", units="%", cmap='RdBu', levels=np.linspace(-100, 100, 101), center_zero=True)

print(f"🔎 Projeção interpolada - min: {float(prev_interp.min().values):.2f}, max: {float(prev_interp.max().values):.2f}")

# --- Salvar projeção interpolada em NetCDF ---
prev_interp.to_netcdf(f"prev_interpolado_{modelo}_ssp{cenario}.nc")

print("✅ Tudo pronto: cálculos, mapas e NetCDF gerado.")

