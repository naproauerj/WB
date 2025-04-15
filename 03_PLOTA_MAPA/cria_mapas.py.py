#-------------------------------------------------------------------------------------------------------
#
#      script plotar estações  
#
#--------------------------------------------------------------------------------------------------------
# by reginaldo.venturadesa@gmail.com  em agosto de 2023 
#
#  
#
#---------------------------------------------------------------------------------------------------------
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
import geopandas as gpd
import matplotlib.pyplot as plt



# Função para calcular a variancia no período
def plota_estacoes(df,arquivo_out_png, limite_max,limite_min,campo,legenda,cores,titulo):
    print("Plotagem do campo:",campo)
    if (campo == 'IDV'):
    
        periodo = df ## df[(df['IDV'] >=limite_min ) & (df['IDV'] <= limite_max)]
    else:
        periodo = df
        
    
    print("====",len(periodo),len(df))
	
    if not periodo.empty:
       dados = periodo[campo] 
       # Extrair as coordenadas das estações
       longitudes = periodo["Longitude"]
       latitudes = periodo["Latitude"]
       nomes = periodo["Nome"]

       # Definir mapeamento de cores com base nos intervalos especificados
       #cmap = ListedColormap(['red','purple','magenta','violet','pink', 'orange','yellow', 'lime','green', 'blue','black'])
       #intervals = [ 100,200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800,1900,2000,4000]
       # Definindo as cores e seus respectivos nomes

       # Definindo as cores e seus respectivos nomes
       colors1 = [
       ((139, 0, 0), 'Vermelho'),                       ##100
       ((234, 0, 0), 'Laranja'),                    ##200
       ((255, 44, 0), 'Amarelo'),                    ##300
       ((255, 113, 0), 'Verde'),                    ##400
       ((255, 179, 0), 'Azul'),                    ##500
       ((255, 219, 0), 'Roxo'),                    ##600
       ((255,251, 0), 'Vermelho'),                    ##700
       ((195, 255, 34), 'Amarelo'),                    ##800
       ((146, 253, 21), 'Verde'),                    ##900
       ((79, 207, 0), 'Azul'),                    ##1000
       ((9, 142, 9), 'Roxo'),                    ##1100
       ((50, 205, 50), 'Vermelho'),                    ##1200
       ((37, 151, 37), 'Laranja'),                    ##1300
       ((93, 213, 147), 'Amarelo'),                    ##1400
       ((69, 255, 232), 'Verde'),                    ##1500
       ((0, 238, 255), 'Azul'),                    ##1600
       ((0, 197, 255), 'Roxo'),                    ##1700
       ((0, 249, 255), 'Roxo'),                    ##1800
       ((14, 209, 232), 'Roxo'),                    ##1900
       ((29, 156, 207), 'Roxo'),                    ##2000
       ((0, 0, 0), 'Roxo'),                    ##4000   
       ]

       # Definindo as cores e seus respectivos nomes
       colors2 = [
                ((255, 0, 0), 'Vermelho'),                       ##100	   
                ((250, 0, 0), 'Vermelho'),                       ##100	         
                ((240, 0, 0), 'Vermelho'),                       ##100	 
                ((230, 0, 0), 'Vermelho'),                       ##100	 				
                ((200, 0, 0), 'Vermelho'),                       ##100	 				
                ((150, 0, 0), 'Vermelho'),                       ##100	 				
                ((100, 0, 0), 'Vermelho'),                       ##100	 
                ((50, 0, 0), 'Vermelho'),                       ##100	 
                ((173, 255, 47), 'Vermelho'),                       ##100	 
                ((0, 255, 0), 'Vermelho'),                       ##100	 
                ((0, 0, 255), 'Vermelho'),                       ##100	 				
                ]				
				
       if(cores == True): 
         colors=colors1
       else:
         colors=colors2
       		 
       # Criando o dicionário de cores para o colormap
       cmap_dict = {'red': [], 'green': [], 'blue': [], 'alpha': []}

       for i, color in enumerate(colors):
           rgb_color = tuple(channel / 255.0 for channel in color[0])
           cmap_dict['red'].append((i / (len(colors)-1), rgb_color[0], rgb_color[0]))
           cmap_dict['green'].append((i / (len(colors)-1), rgb_color[1], rgb_color[1]))
           cmap_dict['blue'].append((i / (len(colors)-1), rgb_color[2], rgb_color[2]))
           cmap_dict['alpha'].append((i / (len(colors)-1), 1.0, 1.0))

       # Criando o colormap customizado
       custom_cmap = LinearSegmentedColormap('custom_cmap', cmap_dict)

       if (campo == 'IDV'):
           bounds = [ 0, 0.1, 0.2, 0.3,  0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
           bounds = [ 0, 10, 20, 30,  40, 50, 60, 70, 80, 90, 100]
       else:
           bounds = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000,2300]
       
       norm = plt.Normalize(bounds[0], bounds[-1])

       # Plotar o gráfico com cores mapeadas
       plt.figure(figsize=(10, 8))
	   
	   # Definir os limites com base no shapefile
       plt.xlim(-47, -37)
       plt.ylim(-19, -8)
       #plt.xlim(gdf.bounds.minx.min(), gdf.bounds.maxx.max())
       #plt.ylim(gdf.bounds.miny.min(), gdf.bounds.maxy.max())
		
       scatter = plt.scatter(longitudes, latitudes, c=dados, cmap=custom_cmap, norm=norm, marker="o")
     
       # Plotar o shapefile
       #gdf.plot(ax=plt.gca(), color='gray')  # Use ax=plt.gca() para sobrepor o shapefile ao scatter plot
       #gdf.plot(ax=plt.gca(), edgecolor='gray')
       gdf.plot(ax=plt.gca(), edgecolor='gray', facecolor='none', lw=1)  # lw é a largura da linha da borda
	   
       # Adicionar rótulos de estação
       #for index, row in df.iterrows():
       #    plt.text(row['Longitude'], row['Latitude'], row['Nome'], fontsize=2, ha="right")

       plt.title(titulo)
       plt.xlabel("Longitude")
       plt.ylabel("Latitude")
       plt.grid(True)

       # Adicionar uma legenda de cores
       cbar = plt.colorbar(scatter)  # Use o objeto scatter como mappable
       cbar.set_label(legenda, labelpad=15)
       
       # Salvar o gráfico como arquivo PNG
       plt.savefig(arquivo_out_png, dpi=300, bbox_inches="tight")
       plt.show()
       return None
    else:
       print("O DataFrame está vazio. Verifique o arquivo Excel e os cabeçalhos das colunas.")
       return None




# Carregar o shapefile
shapefile_path = '../00_STUFF/BAHIA.shp'
gdf = gpd.read_file(shapefile_path)
#
#
#
# Carregar os dados do arquivo Excel
#
#
#
#file_path = "relatorio_ana_19070701_a_20230531_e_19910101_a_20201231.xlsx"
#sheet_name = "TODOS"  # Substitua pelo nome correto da planilha, se necessário





#
#
#  ABA TODOS
#
#
# sheet_name = "TODOS"
# df = pd.read_excel(file_path, sheet_name=sheet_name)
# plota_estacoes(df,"estacoes_SELECAO_BAHIA_1907a2022_ALL",0.0,0.0,'ANUAL',"Media anual em mm","Distribuição das estações de 1907 a 2022 - MEDIA ANUAL - ALL - SEM FILTROS") 
# plota_estacoes(df,"estacoes_SELECAO_BAHIA_1907a2022_PDV_ALL",1.0,0.00,'Per. Dados Validos',"Percentagem de Dados Válidos","Distribuição das estações de 1907 a 2022 - Todos os  Dados") 
# Carregar os dados do arquivo Excel

# file_path = "../02_DOWNLOAD_E_AVALIACAO/sumario_BAHIA.xlsx"
# sheet_name = "ANUAL"
# df = pd.read_excel(file_path, sheet_name=sheet_name)
# plota_estacoes(df,"mapa_todas_as_estacoes_IDV.png",0.0,100.0,'IDV',"Percentual(%)",True,"Distribuição das estações de 1907 a 2024 - Percentual de dados validos") 
# plota_estacoes(df,"mapa_todas_as_estacoes_MEDIA.png",0.0,0.0,'Média mm/ano',"mm/ano",True,"Distribuição das estações de 1907 a 2024 - Média anual") 

file_path = "../02_DOWNLOAD_E_AVALIACAO/sumario_BAHIA.xlsx"
file_path = "../02_DOWNLOAD_E_AVALIACAO/sumario_BAHIA_1991_2020.xlsx"
file_path ='../04_FILTRAGEM/selecao_BAHIA_1981a2010.xlsx'
file_path ='../04_FILTRAGEM/selecao_BAHIA.xlsx'

sheet_name = "ANUAL"
df = pd.read_excel(file_path, sheet_name=sheet_name)

nome_da_figura="mapa_todas_as_estacoes_IDV_FILTRAGEM_INVENTARIO.png"
Limite_inferior=0.0 
Limite_Superior=100.0 
Titulo="Distribuição das estações (Filtragem) - Percentual de dados validos - INVENTARIO"
plota_estacoes(df,
               nome_da_figura,
               Limite_inferior,
               Limite_Superior,
               'IDV',"Percentual(%)",True,
               Titulo 
               ) 


nome_da_figura="mapa_todas_as_estacoes_MEDIA_FILTRAGEM_INVENTARIO.png"
Limite_inferior=0.0 
Limite_Superior=0.0 
Titulo="Distribuição das estações  (filtragem)  - Média anual - INVENTARIO"
plota_estacoes(df,
               nome_da_figura,
               Limite_inferior,
               Limite_Superior,
               'Média mm/ano',"mm/ano",True,
               Titulo 
               ) 



# file_path = "../02_DOWNLOAD_E_AVALIACAO/sumario_BAHIA_1991_2020.xlsx"
# sheet_name = "ANUAL"
# df = pd.read_excel(file_path, sheet_name=sheet_name)
# plota_estacoes(df,"mapa_todas_as_estacoes_1991a2020_IDV.png",0.0,100.0,'IDV',"Percentual(%)",True,"Distribuição das estações de 1991 a 2020 - Percentual de dados validos") 
# plota_estacoes(df,"mapa_todas_as_estacoes_1991a2020_MEDIA.png",0.0,0.0,'Média mm/ano',"mm/ano",True,"Distribuição das estações de 1991 a 2020 - Média anual") 


# ile_path = "../02_DOWNLOAD_E_AVALIACAO/sumario_BAHIA_1981_2010.xlsx"
# sheet_name = "ANUAL"
# df = pd.read_excel(file_path, sheet_name=sheet_name)
# plota_estacoes(df,"mapa_todas_as_estacoes_1981a2010_IDV.png",0.0,100.0,'IDV',"Percentual(%)",True,"Distribuição das estações de 1981 a 2010 - Percentual de dados validos") 
# plota_estacoes(df,"mapa_todas_as_estacoes_1981a2010_MEDIA.png",0.0,0.0,'Média mm/ano',"mm/ano",True,"Distribuição das estações de 1981 a 2010 - Média anual") 
