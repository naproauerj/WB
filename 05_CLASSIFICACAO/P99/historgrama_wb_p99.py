import pandas as pd
import matplotlib.pyplot as plt

# Caminho do arquivo e nome da aba
file_path = "../../04_FILTRAGEM/selecao_BAHIA.xlsx"
sheet_name = "ANUAL"

# Carregar os dados
try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Verificar se a coluna existe
    if "P90 NZ" in df.columns:
        # Criar o histograma
        plt.figure(figsize=(10, 6))
        plt.hist(df["P99 NZ"].dropna(), bins=20, edgecolor='black', alpha=0.7, range=(0, 100))
        plt.xlabel("Valores de P99 NZ")
        plt.ylabel("Frequência")
        plt.title("Histograma dos Valores do P99")
        plt.xticks(range(0, 101, 5))  # Colocar labels no eixo x de 0 a 100
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Salvar a imagem como PNG
        output_path = "histograma_p99_nz.png"
        plt.savefig(output_path, dpi=300)
        plt.show()
        
        print(f"Histograma salvo em: {output_path}")
    else:
        print("A coluna 'P99 NZ' não foi encontrada na aba 'ANUAL'.")
except Exception as e:
    print(f"Erro ao carregar ou processar o arquivo: {e}")
