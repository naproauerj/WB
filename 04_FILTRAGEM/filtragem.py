import pandas as pd

# Carregar o arquivo Excel
file_path = "../02_DOWNLOAD_E_AVALIACAO/sumario_BAHIA.xlsx"
output_file_path = 'selecao_BAHIA.xlsx'

excel_data = pd.ExcelFile(file_path)

# Carregar a aba ANUAL
anual_df = pd.read_excel(excel_data, sheet_name='ANUAL')

# Filtrar as estações com Num Anos Validos > 19 e IDV > 79
filtered_df = anual_df[(anual_df['Num Anos Validos'] >= 24) & (anual_df['IDV'] >= 80)]

# Salvar o resultado em uma nova planilha
output_file_path = 'selecao_BAHIA.xlsx'
filtered_df.to_excel(output_file_path, index=False)

# Recarregar o arquivo Excel para garantir que todas as abas sejam lidas
excel_data = pd.ExcelFile(file_path)

# Carregar as estações filtradas da aba ANUAL
estacoes_selecionadas = filtered_df['Codigo']

# Criar um dicionário para armazenar os dados filtrados de todas as abas "MENSAL"
mensal_filtered_data = {}

# Iterar sobre todas as abas que começam com "MENSAL"
for sheet_name in excel_data.sheet_names:
    if sheet_name.startswith("MENSAL"):
        mensal_df = pd.read_excel(excel_data, sheet_name=sheet_name)
        
        # Filtrar usando as estações selecionadas
        filtered_mensal_df = mensal_df[mensal_df['Codigo'].isin(estacoes_selecionadas)]
        
        # Armazenar os dados filtrados
        mensal_filtered_data[sheet_name] = filtered_mensal_df

# Escrever os resultados em novas abas na planilha de saída usando openpyxl
with pd.ExcelWriter(output_file_path, mode='a', engine='openpyxl') as writer:
    for sheet_name, data in mensal_filtered_data.items():
        data.to_excel(writer, sheet_name=sheet_name, index=False)
