import pandas as pd

# Caminhos dos arquivos
inventario_path = "estacoes_com_regiao.xlsx"
dados_chuva_path = "../02_DOWNLOAD_E_AVALIACAO/dados_BAHIA.xlsx"

# Leitura dos dados
inventario = pd.read_excel(inventario_path)
dados_chuva = pd.read_excel(dados_chuva_path)

# Obter o mapeamento de Código da estação para Região
mapa_estacao_regiao = inventario.set_index('Codigo')['regiao'].to_dict()

# Extrair o ano da primeira coluna (data)
dados_chuva['ano'] = pd.to_datetime(dados_chuva.iloc[:, 0]).dt.year

# Converter os nomes das colunas de estações para inteiros se possível
colunas_convertidas = {}
for col in dados_chuva.columns[1:-1]:  # ignora data e ano
    try:
        colunas_convertidas[col] = int(col)
    except:
        continue

# Renomear as colunas com os inteiros convertidos
dados_chuva.rename(columns=colunas_convertidas, inplace=True)

# Agora identificar as estações válidas
colunas_estacoes = [col for col in dados_chuva.columns if isinstance(col, int)]
estacoes_validas = [cod for cod in colunas_estacoes if cod in mapa_estacao_regiao]

# Criar dataframe com colunas válidas e ano
dados_filtrados = dados_chuva[['ano'] + estacoes_validas]

# Criar nova tabela separada para mm/dia e mm/ano
linhas_dia = []
linhas_ano = []
for ano, grupo in dados_filtrados.groupby('ano'):
    linha_dia = {'ano': ano}
    linha_ano = {'ano': ano}
    for regiao in set(mapa_estacao_regiao.values()):
        estacoes_da_regiao = [cod for cod in estacoes_validas if mapa_estacao_regiao[cod] == regiao]
        if estacoes_da_regiao:
            medias_diarias = grupo[estacoes_da_regiao].mean(axis=1)
            linha_dia[f"regiao_{regiao}"] = medias_diarias.mean()   # média diária (mm/dia)
            linha_ano[f"regiao_{regiao}"] = medias_diarias.sum()    # total anual (mm/ano)
    linhas_dia.append(linha_dia)
    linhas_ano.append(linha_ano)

# Criar DataFrames finais
resultado_dia = pd.DataFrame(linhas_dia).sort_values(by='ano').set_index('ano')
resultado_ano = pd.DataFrame(linhas_ano).sort_values(by='ano').set_index('ano')

# Cálculo de percentis e máximos por ano e região
limite_chuva = 1
percentis_por_regiao = {}
maximos_anuais = {'ano': []}
percentis_medios = []
superacoes_por_regiao = {}

for regiao in set(mapa_estacao_regiao.values()):
    estacoes_da_regiao = [cod for cod in estacoes_validas if mapa_estacao_regiao[cod] == regiao]
    todos_valores = dados_filtrados[estacoes_da_regiao]
    todos_valores = todos_valores[todos_valores >= limite_chuva].stack()

    p90_medio = todos_valores.quantile(0.90)
    p95_medio = todos_valores.quantile(0.95)
    p99_medio = todos_valores.quantile(0.99)

    percentis_medios.append({
        "regiao": regiao,
        "p90_medio": p90_medio,
        "p95_medio": p95_medio,
        "p99_medio": p99_medio
    })

    superacoes = {"ano": []}
    for p in [90, 95, 99]:
        superacoes[f"supera_p{p}"] = []

    for ano, grupo in dados_filtrados.groupby('ano'):
        grupo_validos = grupo[estacoes_da_regiao]
        grupo_valores = grupo_validos[grupo_validos >= limite_chuva].stack()
        superacoes["ano"].append(ano)
        superacoes["supera_p90"].append((grupo_valores > p90_medio).sum())
        superacoes["supera_p95"].append((grupo_valores > p95_medio).sum())
        superacoes["supera_p99"].append((grupo_valores > p99_medio).sum())

    superacoes_por_regiao[regiao] = pd.DataFrame(superacoes).set_index("ano")

    percentis_ano = []
    maximos = []
    for ano, grupo in dados_filtrados.groupby('ano'):
        dados_validos = grupo[estacoes_da_regiao]
        dados_chuva_validos = dados_validos[dados_validos >= limite_chuva].stack()
        percentis = {
            'ano': ano,
            'p90': dados_chuva_validos.quantile(0.90),
            'p95': dados_chuva_validos.quantile(0.95),
            'p99': dados_chuva_validos.quantile(0.99)
        }
        percentis_ano.append(percentis)
        maximos.append({"ano": ano, f"regiao_{regiao}": dados_validos.max().max()})
    percentis_por_regiao[regiao] = pd.DataFrame(percentis_ano).set_index('ano')
    for m in maximos:
        ano = m["ano"]
        if ano not in maximos_anuais['ano']:
            maximos_anuais['ano'].append(ano)
        maximos_anuais.setdefault(f"regiao_{regiao}", []).append(m[f"regiao_{regiao}"])

df_maximos = pd.DataFrame(maximos_anuais).set_index('ano')
df_percentis_medios = pd.DataFrame(percentis_medios).set_index("regiao")

# Exportar para Excel com múltiplas abas
with pd.ExcelWriter("medias_anuais_por_regiao.xlsx") as writer:
    resultado_dia.to_excel(writer, sheet_name='Media_mm_dia')
    resultado_ano.to_excel(writer, sheet_name='Total_mm_ano')
    for regiao, df in percentis_por_regiao.items():
        df.to_excel(writer, sheet_name=f'Percentis_R{regiao}')
    df_maximos.to_excel(writer, sheet_name='Maximos_Ano')
    df_percentis_medios.to_excel(writer, sheet_name='PXX_Medios')
    for regiao, df in superacoes_por_regiao.items():
        df.to_excel(writer, sheet_name=f'Superacoes_R{regiao}')

print("Arquivo 'medias_anuais_por_regiao.xlsx' com todas as métricas gerado com sucesso!")