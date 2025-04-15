import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import math
import geopandas as gpd
from matplotlib.colors import ListedColormap
import shutil
import glob
import os
from matplotlib.colors import ListedColormap, BoundaryNorm

# Função para reorganizar a legenda em múltiplas colunas
def ajustar_legenda(ax, ncol=3):
    leg = ax.get_legend()
    if leg:
        leg.set_bbox_to_anchor((1.05, 1))  # Ajusta a posição da legenda
        leg._ncol = ncol  # Define o número de colunas da legenda
        leg.set_title("Legenda")  # Adiciona um título à legenda

# Função para plotar o mapa corrigido
def plotar_mapa(df_clustering, shapefile_path, cmap=None, ncol_legenda=3):
    gdf = gpd.read_file(shapefile_path)
    gdf_estacoes = gpd.GeoDataFrame(df_clustering, geometry=gpd.points_from_xy(df_clustering.Longitude, df_clustering.Latitude))
    gdf_estacoes.set_crs(epsg=4326, inplace=True)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(ax=ax, color='black', edgecolor='black')
    
    if cmap:
        cmap = ListedColormap(cmap)
    else:
        cmap = 'rainbow'
    
    gdf_estacoes.plot(ax=ax, column='Classificacao', cmap=cmap, markersize=50, legend=True)
    
    # Ajustar a legenda para múltiplas colunas
    ajustar_legenda(ax, ncol=ncol_legenda)
    
    plt.title("Mapa das Estações por Classificação de Clusters")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True)
    plt.savefig("mapa_estacoes_clusters_corrigido.png", dpi=300, bbox_inches="tight")
    plt.show()
    
    
def copypy(origem,destino):

    # Verificar se o diretório de destino existe, caso contrário, criar
    if not os.path.exists(destino):
        os.makedirs(destino)

    # Mover todos os arquivos .png
    for arquivo_png in glob.glob(os.path.join(origem, "*.png")):
        shutil.move(arquivo_png, destino)

    # Mover todos os arquivos .xlsx
    for arquivo_xlsx in glob.glob(os.path.join(origem, "*.xlsx")):
        shutil.move(arquivo_xlsx, destino)

    print("Arquivos movidos com sucesso!")
    return 0


def realizar_classificacao(file_path, sheet_name, coluna_variavel="Média mm/ano", intervals=None, case="CLUSTER",shapefile_path=None,cmap=None):
    # Carregar os dados do arquivo Excel):
    # Carregar os dados do arquivo Excel
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Criar a variável x baseada na coluna escolhida
    x = data[coluna_variavel]
    y = data['Codigo']

    # Calcular o valor mínimo e máximo
    min_value = x.min()
    max_value = x.max()
    num_observations = len(x)

    num_intervals_inicial = int(np.sqrt(num_observations))
    freq_minima = ((max_value - min_value) / num_intervals_inicial) 

    if intervals is None:
        metricas=True
        intervals = np.arange(math.floor(min_value), max_value + freq_minima, freq_minima)
    else:
        intervals = np.array(intervals)
        metricas=False

    # Adicionar a coluna de classificação
    data["Classificacao"] = pd.cut(x, bins=intervals, labels=intervals[:-1])

    # Adicionar a coluna do número do intervalo
    data["Intervalo"] = pd.cut(x, bins=intervals, labels=np.arange(1, len(intervals)))

    # Criar o DataFrame com as colunas necessárias para a clusterização
    df_clustering = data[["Codigo", coluna_variavel, "Classificacao", "Intervalo","Latitude","Longitude"]].dropna()

    # Definir o conjunto de dados para a clusterização (somente a classificação)
    x_for_clustering = df_clustering[["Classificacao"]]

    # Realizar a clusterização hierárquica
    linkage_matrix = linkage(x_for_clustering, method='ward')

    print("------------------------------------------------")
    print("Valor mínimo                      :", min_value)
    print("Valor máximo                      :", max_value)
    print("Número de intervalos (first guess):", len(intervals))
    print("Número de observações             :", num_observations)
    print("Frequência mínima                 :", freq_minima)
    print("Intervalos                        :", intervals)
    print("------------------------------------------------")

    # Criar o histograma dos resultados
    titulo2 = "Total de dados: " + str(len(x))
    plt.figure(figsize=(10, 6))
    counts, bins, patches=plt.hist(data["Classificacao"].dropna(), bins=intervals, edgecolor='black', rwidth=0.8, alpha=0.75, label=titulo2, density=False)
    plt.xlabel('Intervalos (Média mm/ano)')
    plt.ylabel('Frequência')
    plt.title(f'Histograma dos Intervalos de Classificação{case}')
    plt.xticks(intervals, rotation=45)
    plt.grid(axis='y')
       # Adicionar as porcentagens no eixo y
    for i, count in enumerate(counts):
        plt.text(bins[i], count + 0.5, f'{count:.1f}', ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{case}_histogram_" + sheet_name + ".png", dpi=300, bbox_inches="tight")
    plt.show()

    # Criar o histograma dos resultados
    titulo2 = "Total de dados: " + str(len(data["Classificacao"].dropna()))
    plt.figure(figsize=(10, 6))

    # Criar o histograma e obter os valores das contagens para cada intervalo (bin)
    counts, bins, patches = plt.hist(data["Classificacao"].dropna(), bins=intervals, edgecolor='black', rwidth=0.8, alpha=0.75)

    # Converter as contagens para porcentagens
    counts_percentage = (counts / counts.sum()) * 100

    # Agora plotar novamente, mas com as porcentagens
    plt.bar(bins[:-1], counts_percentage, width=np.diff(bins), edgecolor='black', align='edge', alpha=0.75)

    # Adicionar rótulos e título
    plt.xlabel('Intervalos (Média mm/ano)')
    plt.ylabel('Porcentagem')
    plt.title(f'Histograma dos Intervalos de Classificação {case}')
    plt.xticks(intervals, rotation=45)
    plt.grid(axis='y')

    # Adicionar as porcentagens no eixo y
    for i, count in enumerate(counts_percentage):
        plt.text(bins[i], count + 0.5, f'{count:.1f}%', ha='center', fontsize=10)

    # Layout ajustado e salvar a figura
    plt.tight_layout()
    plt.savefig(f"{case}_histogram2_" + sheet_name + ".png", dpi=300, bbox_inches="tight")
    plt.show()





    # Plotar o dendrograma
    plt.figure(figsize=(12, 6))
    dendro = dendrogram(
        linkage_matrix, 
        labels=df_clustering["Codigo"].values,  # Utilizar os códigos das estações como rótulos
        orientation="top", 
        distance_sort='descending'
    )
    plt.title(f'{case}_Dendrogram - {coluna_variavel}')
    plt.savefig(f"{case}_DENDOGRAMA.png", dpi=300, bbox_inches="tight")
    plt.show()
    

    if metricas:
        # Métricas de avaliação
        print("---------- Calculando métricas e gerando gráficos")
        distortions = []
        silhouette_scores = []
        davies_bouldin_scores = []
        calinski_harabasz_scores = []

        # Ajuste aqui o intervalo para evitar pedir mais clusters do que existem
        K = range(2, min(len(np.unique(x_for_clustering)), num_intervals_inicial))

        for k in K:
            kmeanModel = KMeans(n_clusters=k, n_init='auto')
            kmeanModel.fit(x_for_clustering)
            
            distortions.append(kmeanModel.inertia_)
            silhouette_scores.append(silhouette_score(x_for_clustering, kmeanModel.labels_))
            davies_bouldin_scores.append(davies_bouldin_score(x_for_clustering, kmeanModel.labels_))
            calinski_harabasz_scores.append(calinski_harabasz_score(x_for_clustering, kmeanModel.labels_))

        # Plotar Métricas
        plt.figure(figsize=(14, 8))

        plt.subplot(2, 2, 1)
        plt.plot(K, distortions, 'bx-')
        plt.xlabel('Número de Clusters')
        plt.ylabel('Variação Intra-Cluster (Inertia)')
        plt.title(f'Método do Cotovelo para Determinação do Número de Clusters {case}')

        plt.subplot(2, 2, 2)
        plt.plot(K, silhouette_scores, 'bx-')
        plt.xlabel('Número de Clusters')
        plt.ylabel('Índice de Silhueta')
        plt.title(f'Índice de Silhueta para Determinação do Número de Clusters {case}')

        plt.subplot(2, 2, 3)
        plt.plot(K, davies_bouldin_scores, 'bx-')
        plt.xlabel('Número de Clusters')
        plt.ylabel('Índice de Davies-Bouldin')
        plt.title(f'Índice de Davies-Bouldin para Determinação do Número de Clusters {case}')

        plt.subplot(2, 2, 4)
        plt.plot(K, calinski_harabasz_scores, 'bx-')
        plt.xlabel('Número de Clusters')
        plt.ylabel('Índice de Calinski-Harabasz')
        plt.title(f'Índice de Calinski-Harabasz para Determinação do Número de Clusters {case}')

        plt.tight_layout()
        plt.savefig(f"{case}_cluster_metrics_{sheet_name}.png", dpi=300, bbox_inches="tight")
        plt.show()

        # Definir o número ideal de clusters (por exemplo, o que minimiza o índice de Davies-Bouldin)
        best_k = K[np.argmin(davies_bouldin_scores)]
        print(f"Melhor número de clusters baseado no índice de Davies-Bouldin: {best_k}")

        # Reajustar o modelo KMeans com o número ideal de clusters
        kmeanModel = KMeans(n_clusters=best_k, n_init='auto')
        kmeanModel.fit(x_for_clustering)
        df_clustering['Cluster'] = kmeanModel.labels_

        # Gráfico de Dispersão mostrando os Clusters
        plt.figure(figsize=(10, 6))
        plt.scatter(df_clustering[coluna_variavel], df_clustering['Intervalo'], c=df_clustering['Cluster'], cmap='viridis', marker='o')
        plt.xlabel(coluna_variavel)
        plt.ylabel('Intervalo')
        plt.title(f'Distribuição dos Dados e Clusters (k={best_k}) - {case}')
        plt.colorbar(label='Cluster')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{case}_cluster_scatter_{sheet_name}.png", dpi=300, bbox_inches="tight")
        plt.show()

        # Determinação do número ideal de clusters para GMM
        print("---------- Calculando métricas para GMM")
        bic_scores = []
        gmm_silhouette_scores = []
        gmm_davies_bouldin_scores = []

        for k in K:
            gmm = GaussianMixture(n_components=k, n_init=10, covariance_type='full')
            gmm.fit(x_for_clustering)

            labels = gmm.predict(x_for_clustering)
            
            bic_scores.append(gmm.bic(x_for_clustering))
            gmm_silhouette_scores.append(silhouette_score(x_for_clustering, labels))
            gmm_davies_bouldin_scores.append(davies_bouldin_score(x_for_clustering, labels))

        # Plotar Métricas para GMM
        plt.figure(figsize=(14, 6))

        plt.subplot(1, 3, 1)
        plt.plot(K, bic_scores, 'bx-')
        plt.xlabel('Número de Componentes')
        plt.ylabel('BIC')
        plt.title(f'Critério de Informação Bayesiano (BIC) para GMM_{case}')

        plt.subplot(1, 3, 2)
        plt.plot(K, gmm_silhouette_scores, 'bx-')
        plt.xlabel('Número de Componentes')
        plt.ylabel('Índice de Silhueta')
        plt.title(f'Índice de Silhueta para GMM_{case}')

        plt.subplot(1, 3, 3)
        plt.plot(K, gmm_davies_bouldin_scores, 'bx-')
        plt.xlabel('Número de Componentes')
        plt.ylabel('Índice de Davies-Bouldin')
        plt.title(f'Índice de Davies-Bouldin para GMM_{case}')

        plt.tight_layout()
        plt.savefig(f"{case}_gmm_metrics_{sheet_name}.png", dpi=300, bbox_inches="tight")
        plt.show()

        # Definir o melhor modelo GMM baseado no BIC
        best_gmm_k = K[np.argmin(bic_scores)]
        print(f"Melhor número de componentes para GMM baseado no BIC: {best_gmm_k}")

        # Ajustar o modelo GMM com o número ideal de componentes
        gmm = GaussianMixture(n_components=best_gmm_k, n_init=10, covariance_type='full')
        gmm.fit(x_for_clustering)
        df_clustering['GMM_Cluster'] = gmm.predict(x_for_clustering)

        # Gráfico de Dispersão para GMM
        plt.figure(figsize=(10, 6))

        plt.scatter(df_clustering[coluna_variavel], df_clustering['Intervalo'], c=df_clustering['GMM_Cluster'], cmap='viridis', marker='o')
        
        plt.xlabel(coluna_variavel)
        plt.ylabel('Intervalo')
        plt.title(f'Distribuição dos Dados e GMM Clusters (k={best_gmm_k}) - {case}')
        plt.colorbar(label='GMM Cluster')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{case}_gmm_cluster_scatter_{sheet_name}.png", dpi=300, bbox_inches="tight")
        plt.show()


    # Gerar mapa das estações por classificação dos clusters
    if shapefile_path:
        print("---------- Gerando o mapa das estações com clusters")

        # Carregar o shapefile do Rio de Janeiro
        shp2= shapefile_path##"/home/regis/PROJETOS/UERJ/CLIMATOLOGIA_REGIAOSERRANA/SHAPEFILES/buffer_final_regiaoserrana_srtm30metrosPoly.shp"
        gdf = gpd.read_file(shapefile_path)
        gdf1 = gpd.read_file(shp2)
        

        # Criar um GeoDataFrame para as estações
        gdf_estacoes = gpd.GeoDataFrame(df_clustering, geometry=gpd.points_from_xy(df_clustering.Longitude, df_clustering.Latitude))

        # Definir o sistema de coordenadas para o GeoDataFrame das estações (WGS84)
        gdf_estacoes.set_crs(epsg=4326, inplace=True)

        # Plotar o mapa
        fig, ax = plt.subplots(figsize=(10, 10))

        # Plotar o shapefile (mapa do Rio de Janeiro)
        gdf1.plot(ax=ax, color='lightgray', edgecolor='black')
        gdf.plot(ax=ax, color='black', edgecolor='black')
       
        if cmap:
           cmap = ListedColormap(cmap) ##,'magenta','violet','pink',  'lime','green'])
        else:
            cmap='rainbow'
        
       

        # Plotar as estações, colorindo-as de acordo com os clusters
        gdf_estacoes.plot(ax=ax, column='Classificacao', cmap=cmap, markersize=50, legend=True)
        #gdf_estacoes.plot(ax=ax, column='Intervalo', cmap=cmap, markersize=50, legend=True)
        
        # Adicionar o valor de cada estação no mapa
        #for x, y, label in zip(gdf_estacoes.geometry.x, gdf_estacoes.geometry.y, gdf_estacoes[coluna_variavel]):
        #    ax.annotate(f'{label:.1f}', xy=(x, y), xytext=(3, 3),
        #                textcoords="offset points", fontsize=8, color='black')
            
        # Adicionar a legenda à esquerda
        leg = ax.get_legend()
        leg._ncol=3
        leg.set_bbox_to_anchor((1, 1))  # Move a legenda para a posição superior esquerda
        leg.set_title("Legenda")  # Título da legenda (opcional)


        # Adicionar títulos e rótulos
        plt.title(f"Mapa das Estações por Classificação de Clusters{case}")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True)

        # Salvar o mapa
        plt.savefig(f"{case}_mapa_estacoes_clusters.png", dpi=300, bbox_inches="tight")

        # Mostrar o mapa
        plt.show()


    # Salvar os resultados finais com os clusters adicionados
    data.to_excel(f"{case}_classified_" + sheet_name + ".xlsx", index=False)

    return data


# Exemplo de uso da função
file_path = "../../04_FILTRAGEM/selecao_BAHIA.xlsx"        ## anual 
#file_path = "../FILTRO/selecao_modificada.xlsx"         ## mensal 
#file_path = "../FILTRO/selecao_dados_P99 NZ.xlsx"       ## mensal 


sheet_name = "ANUAL"
shapefile_path =  '../../00_STUFF/regioes_bahia.shp'
escala_de_cores = ['red', 'green', 'blue' ]

intervals=[300,820,1200,2600]

# Opção 1: Deixar o algoritmo escolher os intervalos e usar a média anual
realizar_classificacao(file_path, sheet_name,coluna_variavel="Média mm/ano",intervals=intervals, case="ANUAL_MEDIA", shapefile_path = shapefile_path,cmap=escala_de_cores)




# Diretório de origem e destino
origem = "../04_FILTRAGEM/selecao_BAHIA.xlsx" ##  "  # Altere para o caminho correto
destino = "./ANUAL"  # Altere para o caminho correto
copypy(origem,destino)
exit(0)




conjunto="MEDIA"
# Lista de meses e respectivos diretórios de destino
meses = [
    ("01_JAN", "./jan"),
    ("02_FEV", "./fev"),
    ("03_MAR", "./mar"),
    ("04_ABR", "./abr"),
    ("05_MAI", "./mai"),
    ("06_JUN", "./jun"),
    ("07_JUL", "./jul"),
    ("08_AGO", "./ago"),
    ("09_SET", "./set"),
    ("10_OUT", "./out"),
    ("11_NOV", "./nov"),
    ("12_DEZ", "./dez")
]

escala_de_cores = [
    'darkred', 'red', 'orangered', 'orange', 'gold', 'yellow', 'greenyellow', 'limegreen',
    'green', 'mediumseagreen', 'lightgreen', 'cyan', 'deepskyblue', 'dodgerblue', 'blue',
    'mediumblue', 'darkblue' ]
# Loop para realizar a classificação e copiar os arquivos para cada mês
for i, (mes, dir_mes) in enumerate(meses, start=1):
    coluna_variavel = f"Média mm/mes"
    realizar_classificacao(
        file_path, 
        sheet_name,
        coluna_variavel=coluna_variavel,
        case=mes,
        shapefile_path=shapefile_path,
        cmap=escala_de_cores
    )
    
    # Diretório de origem e destino
    origem = "./"  # Altere para o caminho correto, se necessário
    destino=f"{conjunto}/{dir_mes}"
    copypy(origem, destino)

