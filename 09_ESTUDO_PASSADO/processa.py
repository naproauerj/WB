import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# 1. Carregar a planilha com as estações
excel_path = "../05_CLASSIFICACAO/ANUAL_classified_ANUAL.xlsx"
df = pd.read_excel(excel_path)

# 2. Criar GeoDataFrame com pontos das estações
# Substitua pelos nomes corretos se forem diferentes
latitude_col = 'Latitude'
longitude_col = 'Longitude'

gdf_estacoes = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df[longitude_col], df[latitude_col]),
    crs="EPSG:4326"
)

# 3. Carregar o shapefile de regiões (formato GeoJSON)
regioes_gdf = gpd.read_file("../00_STUFF/BAHIA.geojson")

# 4. Garantir que ambos estão no mesmo sistema de coordenadas
regioes_gdf = regioes_gdf.to_crs(gdf_estacoes.crs)

# 5. Realizar o spatial join: associar cada estação a uma região
resultado = gpd.sjoin(gdf_estacoes, regioes_gdf, how="left", predicate="within")

# 6. Preencher a coluna de região com os valores encontrados no join
if 'regiao' in resultado:
    df['regiao'] = resultado['regiao']
else:
    df['regiao'] = resultado['index_right']

# 7. Identificar estações sem região atribuída e associar à região mais próxima
nao_classificadas = resultado[resultado['index_right'].isna()].copy()

if not nao_classificadas.empty:
    print(f"🔎 Corrigindo {len(nao_classificadas)} estações fora dos limites...")
    for idx, row in nao_classificadas.iterrows():
        ponto = row.geometry
        # Calcular distância até todas as regiões e pegar a mais próxima
        regioes_gdf['distancia'] = regioes_gdf.geometry.distance(ponto)
        mais_proxima = regioes_gdf.sort_values('distancia').iloc[0]
        df.loc[idx, 'regiao'] = mais_proxima['regiao'] if 'regiao' in regioes_gdf.columns else mais_proxima.name

# 8. Verificar quais regiões foram atribuídas
print("Regiões únicas atribuídas:", sorted(df['regiao'].dropna().unique()))
if 'regiao' in regioes_gdf.columns:
    print("Regiões no shapefile:", sorted(regioes_gdf['regiao'].unique()))
else:
    print("Índices no shapefile:", sorted(regioes_gdf.index))

# 9. Exportar para novo Excel
df.to_excel("estacoes_com_regiao.xlsx", index=False)

print("✅ Arquivo salvo como 'estacoes_com_regiao.xlsx'")
