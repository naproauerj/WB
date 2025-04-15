import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import geopandas as gpd
from glob import glob

# Grade desejada
new_lat = np.arange(-19.99, -8.0 + 0.1, 0.1)
new_lon = np.arange(-47.99, -37.0 + 0.1, 0.1)

# Escala fixa para os mapas
levels = [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600]
cmap_custom = ListedColormap([
    'darkred', 'red', 'orange', 'yellow', 'greenyellow', 'limegreen',
    'green', 'cyan', 'deepskyblue', 'blue', 'mediumblue', 'darkblue'
])

# Shapefile de contorno
shapefile_path = "../00_STUFF/regioes.shp"
shape = gpd.read_file(shapefile_path)

# Climatologia observada
clim_path = "../06_INTERPOLACAO/MEDIA/bahia_1981a2010__interpolacao_Kriging_exponential.nc"
clim_ds = xr.open_dataset(clim_path)
climatologia = clim_ds['Interpolacao']

# Diretório com arquivos históricos
caminho = "../07_HISTORICO/"
arquivos = glob(os.path.join(caminho, "pr_Amon_*.nc"))

for arquivo in arquivos:
    print(f"🔄 Processando: {os.path.basename(arquivo)}")

    try:
        # Abrir e selecionar período
        try:
            ds = xr.open_dataset(arquivo, use_cftime=True)
        except ValueError as ve:
            print(f"⚠️ Tentando abrir sem decodificar tempo: {arquivo}")
            ds = xr.open_dataset(arquivo, decode_times=False)
        ds_sel = ds.sel(time=slice("1981-01-01", "2010-12-31"))

        # Corrigir longitudes para -180 a 180
        ds_sel = ds_sel.assign_coords(
            lon=(((ds_sel.lon + 180) % 360) - 180)
        ).sortby('lon')

        # Remover duplicatas de coordenadas (forma segura)
        _, unique_lat_idx = np.unique(ds_sel.lat.values, return_index=True)
        _, unique_lon_idx = np.unique(ds_sel.lon.values, return_index=True)
        ds_sel = ds_sel.isel(lat=sorted(unique_lat_idx), lon=sorted(unique_lon_idx))

        if ds_sel.time.size == 0:
            print(f"⚠️ Nenhum dado entre 1981 e 2010 em {arquivo}")
            continue

        # Média climatológica e conversão para mm/ano
        pr_mean = ds_sel['pr'].mean(dim='time') * 24 * 3600 * 365
        pr_mean.attrs["units"] = "mm/ano"
        pr_mean.name = "precipitacao"

        # Interpolação para a mesma grade da climatologia
        pr_interp = pr_mean.interp_like(climatologia)

        if np.isnan(pr_interp).all():
            print(f"⚠️ Todos os valores são NaN após interpolação: {arquivo}")
            continue

        # Nome do modelo
        modelo = os.path.basename(arquivo).split("_")[2]

        # Verificação de compatibilidade
        if not pr_interp.dims == climatologia.dims:
            print(f"❌ Dimensões incompatíveis entre climatologia e modelo {modelo}")
            continue

        if pr_interp.shape != climatologia.shape:
            print(f"❌ Tamanho da grade não compatível em {modelo}: {pr_interp.shape} vs {climatologia.shape}")
            continue

        # ----- Diferença e Erro Relativo -----
        diferenca = climatologia - pr_interp
        diferenca.name = "diferenca"
        diferenca.attrs["units"] = "mm/ano"

        erro_relativo = 100 * (diferenca / climatologia)
        erro_relativo.name = "erro_relativo"
        erro_relativo.attrs["units"] = "%"

        # Salvar arquivos NetCDF
        pr_interp.to_netcdf(f"{modelo}_HISTORICO.nc")
        diferenca.to_netcdf(f"{modelo}_DIFERENCA.nc")
        erro_relativo.to_netcdf(f"{modelo}_ERRO_RELATIVO.nc")
        print(f"💾 NetCDFs salvos para {modelo}")

        # ----- Painel 2x2 -----
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))

        # Climatologia
        climatologia.plot(
            ax=axs[0, 0],
            cmap=cmap_custom,
            levels=levels,
            vmin=levels[0],
            vmax=levels[-1],
            cbar_kwargs={"label": "mm/ano", "ticks": levels}
        )
        axs[0, 0].set_title("(a) Climatologia 1981–2010")
        shape.boundary.plot(ax=axs[0, 0], edgecolor='black', linewidth=1)
        axs[0, 0].set_xlim([-47.99, -37])
        axs[0, 0].set_ylim([-19.99, -8])

        # Modelo
        pr_interp.plot(
            ax=axs[0, 1],
            cmap=cmap_custom,
            levels=levels,
            vmin=levels[0],
            vmax=levels[-1],
            cbar_kwargs={"label": "mm/ano", "ticks": levels}
        )
        axs[0, 1].set_title(f"(b) HISTÓRICO - {modelo}")
        shape.boundary.plot(ax=axs[0, 1], edgecolor='black', linewidth=1)
        axs[0, 1].set_xlim([-47.99, -37])
        axs[0, 1].set_ylim([-19.99, -8])

        # Diferença
        escala_dif = list(np.linspace(-2000, 2000, 21))
        diferenca.plot(
            ax=axs[1, 0],
            cmap="RdBu_r",
            levels=escala_dif,
            vmin=min(escala_dif),
            vmax=max(escala_dif),
            cbar_kwargs={"label": "Diferença (mm/ano)", "ticks": escala_dif}
        )
        axs[1, 0].set_title("(c) Diferença Climatologia - Modelo")
        shape.boundary.plot(ax=axs[1, 0], edgecolor='black', linewidth=1)
        axs[1, 0].set_xlim([-47.99, -37])
        axs[1, 0].set_ylim([-19.99, -8])

        # Erro relativo
        escala_erro = [-100, -90, -80, -70, -60, -50, -40, -30, -25, -20, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100]
        erro_relativo.plot(
            ax=axs[1, 1],
            cmap=ListedColormap(['navy', 'blue', 'deepskyblue', 'cyan', 'white', 'mistyrose', 'salmon', 'red', 'darkred']),
            levels=escala_erro,
            vmin=min(escala_erro),
            vmax=max(escala_erro),
            cbar_kwargs={"label": "%", "ticks": escala_erro}
        )
        axs[1, 1].set_title("(d) Erro Relativo (%)")
        shape.boundary.plot(ax=axs[1, 1], edgecolor='black', linewidth=1)
        axs[1, 1].set_xlim([-47.99, -37])
        axs[1, 1].set_ylim([-19.99, -8])

        fig.suptitle(f"Comparativo Climatologia x Modelo - {modelo}", fontsize=16, y=1.02)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.savefig(f"{modelo}_painel_4plots.png", dpi=300)
        plt.close()
        print(f"🖼️ Painel salvo: {modelo}_painel_4plots.png\n")

    except Exception as e:
        print(f"❌ Erro ao processar {arquivo}: {e}")
