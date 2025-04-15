import argparse
import numpy as np
import xml.etree.ElementTree as ET
import requests
import pandas as pd

class ServiceANA:
    def __init__(self):
        self.url = 'http://telemetriaws1.ana.gov.br/ServiceANA.asmx/'

    def inventario(self, estado=''):
        url = self.url + (
            f'HidroInventario?codEstDE=&codEstATE='
            f'&tpEst=&nmEst=&nmRio=&codSubBacia='
            f'&codBacia=&nmMunicipio=&nmEstado={estado}'
            f'&sgResp=&sgOper=&telemetrica='
        )

        resposta = requests.get(url)
        tree = ET.ElementTree(ET.fromstring(resposta.content))
        root = tree.getroot()

        estacoes = []
        for estacao in root.iter("Table"):
            dados = {
                "codigo": [estacao.find("Codigo").text],
                "nome": [estacao.find("Nome").text],				
                "tipo": [estacao.find("TipoEstacao").text],
                "latitude": [float(estacao.find("Latitude").text)],
                "longitude": [float(estacao.find("Longitude").text)],
                "altitude": [float(estacao.find("Altitude").text) if estacao.find("Altitude").text else np.nan],
                "estado": [estacao.find("nmEstado").text],
                "municipio": [estacao.find("nmMunicipio").text],
                "BaciaCodigo": [estacao.find("BaciaCodigo").text], 
                "SubBaciaCodigo": [estacao.find("SubBaciaCodigo").text], 
                "Rio": [estacao.find("RioCodigo").text], 				
                "responsavel": [estacao.find("ResponsavelSigla").text],
                "Ultima Atualizacao": [estacao.find("UltimaAtualizacao").text],
                "data_ins": [estacao.find("DataIns").text],
                "data_alt": [estacao.find("DataAlt").text]
            }
            df = pd.DataFrame.from_dict(dados)
            df.set_index("codigo", inplace=True)
            estacoes.append(df)

        if estacoes:
            return pd.concat(estacoes)
        else:
            return pd.DataFrame()

    def salvar_xlsx(self, inventario, filename):
        if not inventario.empty:
            inventario.to_excel(filename)
        else:
            print("Nenhuma estação encontrada.")
            exit(0)

# Argumentos
parser = argparse.ArgumentParser(description="Gerador de inventário de estações ANA por UF.")
parser.add_argument("-s", "--saida", type=str, required=True, help="Nome do arquivo Excel de saída")
parser.add_argument("-u", "--uf", type=str, required=True, help="Nome da Unidade da Federação (ex: RIO DE JANEIRO)")
args = parser.parse_args()

# Execução
service = ServiceANA()
print(f"Gerando inventário para o estado: {args.uf}")
inventario = service.inventario(args.uf)
service.salvar_xlsx(inventario, args.saida)
print(f"Arquivo gerado: {args.saida}")
