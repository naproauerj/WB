import os
import numpy as np
import xml.etree.ElementTree as ET
import requests
import xmltodict
import pandas as pd
import geopandas as gpd
import pendulum
import plotly.figure_factory as ff
import csv 
from datetime import datetime
import math
from pathlib import Path

class ServiceANA:
    def __init__(self) -> None:
        self.url = 'http://telemetriaws1.ana.gov.br/ServiceANA.asmx/'

    def inventario2(self,estacao='',estado='',orgao=''):
        string = ''
        url = self.url + \
            f'HidroInventario?codEstDE={string}&codEstATE={estacao}' + \
            f'&tpEst={string}&nmEst={string}&nmRio={string}&codSubBacia={string}' + \
            f'&codBacia={string}&nmMunicipio={string}&nmEstado={estado}' + \
            f'&sgResp={orgao}&sgOper={string}&telemetrica={string}'

        resposta = requests.get(url)

        tree = ET.ElementTree(ET.fromstring(resposta.content))
        root = tree.getroot()

        estacoes = list()
       
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

        if len(estacoes) == 0:
            inventario = []
        else:
            inventario = pd.concat(estacoes)

        return inventario















    def salvar_inventario_xlsx(self, inventario, filename):
        if not inventario.empty:
            inventario.to_excel(filename, index=True)
        else:
            print("Erro ao gravar aquivo ",filename)
            exit(0)         




    def serie_historica(self, codigo, tipoDados='', data_i='', data_f='', consistencia=''):
        """ ServiceANA API reference request:
            codigo(str): Código da estação
            data_i(str): Data de início da série observada [(d/m/Y) format]
            data_f(str): Data de fim da série observada. Caso data_f='', retorna leitura mais recente
            tipoDados(str): 1-Cotas, 2-Chuvas ou 3-Vazões
            consistencia(str): 1-Bruto ou 2-Consistido
        """
        params = {'codEstacao': codigo,
                'dataInicio': data_i,
                'dataFim': data_f,
                'tipoDados': tipoDados,
                'nivelConsistencia': consistencia}

        url = self.url + '/HidroSerieHistorica'
        r = requests.get(url, params)
        data_min = ''
        data_max = ''
        
        if r.status_code == 200:
            xml = xmltodict.parse(r.content)
            element = xml.get("DataTable", {}).get('diffgr:diffgram', {}).get('DocumentElement', {})
            
            if 'SerieHistorica' in element:
                serie_historica = element['SerieHistorica']
                
                if isinstance(serie_historica, list) and len(serie_historica) > 0:
                    df = pd.DataFrame(serie_historica)
                    if not df.empty:
                        if tipoDados == '2':  # Modifiquei para tipoDados 2 (Chuva)
                            var = 'Chuva'
                            cod = str(df['EstacaoCodigo'][0])
                            cols_vaz = [f"{var}%02d" % (i,) for i in range(1, 32)]
                            cols = ['DataHora'] + cols_vaz
                            df = df[cols]
                            df = df.melt(id_vars=['DataHora'], value_vars=cols_vaz).rename(columns={'value': f'{cod}'}).dropna()

                            try:
                                df['date_m'] = df.apply(lambda row: pendulum.from_format(row['DataHora'], 'YYYY-MM-DD HH:mm:ss').naive(), axis=1)
                            except ValueError:
                                return None, data_min, data_max
                            
                            def safe_date(row):
                                try:
                                    return pendulum.datetime(row['date_m'].year, row['date_m'].month, int(row['variable'][-2:])).naive()
                                except ValueError:
                                    return None
                            
                            df['date'] = df.apply(safe_date, axis=1)
                            df = df.dropna(subset=['date'])
                            df = df[['date', cod]].set_index('date').sort_index()
                            
                            # Calculando as datas mínimas e máximas
                            data_min = df.index.min()
                            data_max = df.index.max()

                            return df.astype(float), data_min, data_max
                elif isinstance(serie_historica, dict):
                    df = pd.DataFrame([serie_historica])
                    
                    # Calculando as datas mínimas e máximas
                    data_min = df['DataHora'].min()
                    data_max = df['DataHora'].max()

                    return df, data_min, data_max
        else:
            print(f"Request error: {r.status_code}")
        return None, data_min, data_max


  

    def baixar_dados_por_estacao(self, df, tipoDados='2', data_i='', data_f='', consistencia='1'):
    
        # Função para calcular o número de dias entre duas datas
        def calcular_num_dias(data_min, data_max):
            formato = "%Y-%m-%d %H:%M:%S"
            try:
                if data_min and data_max:
                    data_i_obj = datetime.strptime(str(data_min), formato)
                    data_f_obj = datetime.strptime(str(data_max), formato)
                    diferenca = data_f_obj - data_i_obj
                    num_de_dias = diferenca.days
                    num_anos = math.ceil(diferenca.days / 365.25)
                    return num_de_dias, num_anos
                else:
                    return None, None
            except ValueError:
                return None, None
        
        # Função para gravar histórico em CSV
        def grava_historico(historico, df, indice, modo, tamanho, data_min, data_max, status): 
            if modo == "w":
                with open(historico, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(list(df.columns) + ["tamanho", "data_min", "data_max", "status"])
                    
            else:
                with open(historico, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    item = df.iloc[indice]
                    linha = list(item) + [tamanho, data_min, data_max, status]
                    writer.writerow(linha)


        # Função para verificar se um ano é bissexto
        def eh_bissexto(ano):
            return (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0)

        # Função para calcular o número total de dias em um mês específico entre dois anos
        def total_dias_mes(mes, data_min, data_max):
            formato = "%Y-%m-%d %H:%M:%S"
            #data_min = datetime.strptime(data_min, formato)
           # data_max = datetime.strptime(data_max, formato)
            ano_inicio=data_min.year
            ano_fim=data_max.year
            
            dias_no_mes = 0
            
            for ano in range(ano_inicio, ano_fim + 1):
                if mes == 2:
                    if eh_bissexto(ano):
                        dias_no_mes += 29
                    else:
                        dias_no_mes += 28
                elif mes in [4, 6, 9, 11]:
                    dias_no_mes += 30
                else:
                    dias_no_mes += 31
            
            return dias_no_mes



        codigos = df['codigo']
        dados_estado = []
        num_estacao = len(codigos)   
        k = -1 
        resultados_completos = []
        estatisticas_mensais=[]
        estatisticas_anuais = []
        
        grava_historico(historico, df, 0, "w", 0, 0, 0, '')  # Inicializando o histórico

        for codigo in codigos:
            k += 1
            lon = df.iloc[k]['longitude']
            lat = df.iloc[k]['latitude']
            altitude = df.iloc[k]['altitude']
            nome = df.iloc[k]['nome']
            cidade = df.iloc[k]['municipio']
            UF = df.iloc[k]['estado']
            bacia = df.iloc[k]['BaciaCodigo']
            subbacia = df.iloc[k]['SubBaciaCodigo']
            rio = df.iloc[k]['Rio']
            orgao = df.iloc[k]['responsavel']
            data_ultimo_dado = df.iloc[k]['Ultima Atualizacao']
            
            #print("Código:", codigo, k, " de ", num_estacao, " ", nome, " ", UF)
            dados_estacao, data_min, data_max = self.serie_historica(codigo, tipoDados, data_i, data_f, consistencia)
           
            
            num_de_dias, num_anos = calcular_num_dias(data_min, data_max)

            if dados_estacao is not None and len(dados_estacao) > 1:
                dados_estacao[str(codigo)] = pd.to_numeric(dados_estacao[str(codigo)], errors='ignore')
                tamanho = len(dados_estacao)

                # Estatísticas
                dados_totais = dados_estacao[str(codigo)]
                num_dados_totais = len(dados_totais)
                dados_validos = dados_estacao[str(codigo)][dados_estacao[str(codigo)] >= 0.0].dropna()
                dados_validos = dados_validos.loc[~dados_validos.index.duplicated(keep='first')]
                num_dados_validos = len(dados_validos)
                limite_chuva = 1.0
                dados_LDU = dados_estacao[str(codigo)][dados_estacao[str(codigo)] >= limite_chuva].dropna()
                dados_LDU = dados_LDU.loc[~dados_LDU.index.duplicated(keep='first')]
                num_dados_validos_acima_limite = len(dados_LDU)
                chuva_non_zero = dados_estacao[str(codigo)][dados_estacao[str(codigo)] >= 0.1].dropna()
                chuva_non_zero = chuva_non_zero.loc[~chuva_non_zero.index.duplicated(keep='first')]
                num_chuva_non_zero = len(chuva_non_zero)

                idv = (num_dados_validos / num_de_dias) * 100 if num_de_dias else 0
                idv_limite = (num_dados_validos_acima_limite / num_de_dias) * 100 if num_de_dias else 0
                id_nonzero = (num_chuva_non_zero / num_de_dias) * 100 if num_de_dias else 0

                resultados_completos.append({
                    "Codigo": codigo,
                    "Num Total de registros": num_dados_totais,
                    "Nome": nome,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Altitude": altitude,
                    "cidade": cidade,
                    "UF": UF,
                    "Bacia": bacia,
                    "Sub Bacia": subbacia,
                    "Rio": rio,
                    "orgao": orgao,
                    "data Ultimo dado": data_ultimo_dado,
                    "CONTAGEM": " - ",
                    "Data Inicial": data_min,
                    "Data Final": data_max,
                    "Num de Dias": num_de_dias,
                    "Num de Anos Total": num_anos,
                    "Num Anos Validos": math.ceil(num_anos * (idv / 100)),
                    "Num Dados Válidos": len(dados_validos),
                    "Num Dados chuva non_zero": len(chuva_non_zero),
                    "Num Dados >= LDU": len(dados_LDU),
                    "IDV": idv,
                    "IDV LDU": idv_limite,
                    "IDV Nonzero": id_nonzero,
                    "STAT-ALL": " - ",
                    "Média mm/dia": dados_validos.mean(),
                    "Média mm/mes": dados_validos.mean()*30,
                    "Média mm/ano": dados_validos.mean()*365,
                    "Mediana": dados_validos.median(),
                    "Moda": float(dados_validos.mode().iloc[0]) if not dados_validos.mode().empty else None,
                    "Máximo": dados_validos.max(),
                    "Mínimo": dados_validos.min(),
                    "Desvio Padrao": dados_validos.std(),
                    "Variancia": dados_validos.var(),
                    "P25": dados_validos.quantile(0.25) if not dados_validos.empty else None,
                    "P50": dados_validos.quantile(0.50) if not dados_validos.empty else None,
                    "P75": dados_validos.quantile(0.75) if not dados_validos.empty else None,
                    "P90": dados_validos.quantile(0.90) if not dados_validos.empty else None,
                    "P95": dados_validos.quantile(0.95) if not dados_validos.empty else None,
                    "P99": dados_validos.quantile(0.99) if not dados_validos.empty else None,
                    "CHUVA NON-ZERO": " - ",
                    "Média NZ mm/dia": chuva_non_zero.mean(),
                    "Média NZ mm/mes": chuva_non_zero.mean()*30,
                    "Média NZ mm/ano": chuva_non_zero.mean()*365,
                    "Mediana NZ": chuva_non_zero.median(),
                    "Moda NZ": float(chuva_non_zero.mode().iloc[0]) if not chuva_non_zero.mode().empty else None,
                    "Máximo NZ": chuva_non_zero.max(),
                    "Mínimo NZ": chuva_non_zero.min(),
                    "Desvio Padrao NZ": chuva_non_zero.std(),
                    "Variancia NZ": chuva_non_zero.var(),
                    "P25 NZ": chuva_non_zero.quantile(0.25) if not chuva_non_zero.empty else None,
                    "P50 NZ": chuva_non_zero.quantile(0.50) if not chuva_non_zero.empty else None,
                    "P75 NZ": chuva_non_zero.quantile(0.75) if not chuva_non_zero.empty else None,
                    "P90 NZ": chuva_non_zero.quantile(0.90) if not chuva_non_zero.empty else None,
                    "P95 NZ": chuva_non_zero.quantile(0.95) if not chuva_non_zero.empty else None,
                    "P99 NZ": chuva_non_zero.quantile(0.99) if not chuva_non_zero.empty else None,
                    "CHUVA LDU": " - ",
                    "Média LDU mm/dia": dados_LDU.mean(),
                    "Média LDU mm/mes": dados_LDU.mean()*30,
                    "Média LDU mm/ano": dados_LDU.mean()*365,
                    "Mediana LDU": dados_LDU.median(),
                    "Moda LDU": float(dados_LDU.mode().iloc[0]) if not dados_LDU.mode().empty else None,
                    "Máximo LDU": dados_LDU.max(),
                    "Mínimo LDU": dados_LDU.min(),
                    "Desvio Padrao LDU": dados_LDU.std(),
                    "Variancia LDU": dados_LDU.var(),
                    "P25(LDU)": dados_LDU.quantile(0.25) if not dados_LDU.empty else None,
                    "P50(LDU)": dados_LDU.quantile(0.50) if not dados_LDU.empty else None,
                    "P75(LDU)": dados_LDU.quantile(0.75) if not dados_LDU.empty else None,
                    "P90(LDU)": dados_LDU.quantile(0.90) if not dados_LDU.empty else None,
                    "P95(LDU)": dados_LDU.quantile(0.95) if not dados_LDU.empty else None,
                    "P99(LDU)": dados_LDU.quantile(0.99) if not dados_LDU.empty else None
                })
                # Cálculo de estatísticas mensais

                idv = (num_dados_validos / num_de_dias) * 100 if num_de_dias else 0
                idv_limite = (num_dados_validos_acima_limite / num_de_dias) * 100 if num_de_dias else 0
                id_nonzero = (num_chuva_non_zero / num_de_dias) * 100 if num_de_dias else 0
                for mes in range(1, 13):
                    # 
                    # numero de dias do mes 
                    #
                    total_dias_no_mes=total_dias_mes(mes,data_min,data_max)
                    #
                    #
                    #
                    dados_mes = dados_validos[dados_validos.index.month == mes]
                    dados_mes_non_zero = chuva_non_zero[chuva_non_zero.index.month == mes]
                    dados_mes_LDU = dados_LDU[dados_LDU.index.month == mes]
                    #
                    #
                    #
                    num_dias_mes_validos=len(dados_mes)
                    idv_mes=(num_dias_mes_validos/total_dias_no_mes) * 100 if total_dias_no_mes else 0
                    num_dias_mes_validos_noz_zero=len(dados_mes_non_zero)
                    idv_mes_non_zero=(num_dias_mes_validos_noz_zero/total_dias_no_mes) * 100 if total_dias_no_mes else 0
                    num_dias_mes_validos_LDU=len(dados_mes_LDU)
                    idv_mes_LDU=(num_dias_mes_validos_LDU/total_dias_no_mes) * 100 if total_dias_no_mes else 0
                    



                    
                    if not dados_mes.empty:
                       estatisticas_mensais.append (
                            {

                                "Codigo": codigo,
                                "Nome": nome,
                                "Latitude": lat,
                                "Longitude": lon,
                                "Altitude": altitude,
                                "cidade": cidade,
                                "UF": UF,
                                "Bacia": bacia,
                                "Sub Bacia": subbacia,
                                "Rio": rio,
                                "orgao": orgao,
                                "CONTAGEM": " - ",
                                "mes":mes,
                                "Data Inicial": data_min,
                                "Data Final": data_max,
                                "Num de Dias": total_dias_no_mes,
                                "Num de Dias válidos": num_dias_mes_validos,
                                "Num Dias Validos": math.ceil(total_dias_no_mes * (idv_mes / 100)),
                                "Num Dados chuva non_zero": num_dias_mes_validos_noz_zero,
                                "Num Dados >= LDU": num_dias_mes_validos_LDU,
                                "IDV": idv_mes,
                                "IDV LDU": idv_mes_LDU,
                                "ID Nonzero": idv_mes_non_zero,
                                "STAT-ALL": " - ", #--------------------------------------------------------------------------------------
                                "Média mm/dia":  dados_mes.mean(),
                                "Média mm/mes":  dados_mes.mean()*30,
                                "Média mm/ano":  dados_mes.mean()*365,
                                "Mediana":  dados_mes.median(),
                                "Moda": float( dados_mes.mode().iloc[0]) if not  dados_mes.mode().empty else None,
                                "Máximo":  dados_mes.max(),
                                "Mínimo":  dados_mes.min(),
                                "Desvio Padrao":  dados_mes.std(),
                                "Variancia":  dados_mes.var(),
                                "P25":  dados_mes.quantile(0.25) if not  dados_mes.empty else None,
                                "P50":  dados_mes.quantile(0.50) if not  dados_mes.empty else None,
                                "P75":  dados_mes.quantile(0.75) if not  dados_mes.empty else None,
                                "P90":  dados_mes.quantile(0.90) if not  dados_mes.empty else None,
                                "P95":  dados_mes.quantile(0.95) if not  dados_mes.empty else None,
                                "P99":  dados_mes.quantile(0.99) if not  dados_mes.empty else None,
                                "CHUVA NON-ZERO": " - ",
                                "Média NZ mm/dia": dados_mes_non_zero.mean(),
                                "Média NZ mm/mes": dados_mes_non_zero.mean()*30,
                                "Média NZ mm/ano": dados_mes_non_zero.mean()*365,
                                "Mediana NZ": dados_mes_non_zero.median(),
                                "Moda NZ": float(dados_mes_non_zero.mode().iloc[0]) if not dados_mes_non_zero.mode().empty else None,
                                "Máximo NZ": dados_mes_non_zero.max(),
                                "Mínimo NZ": dados_mes_non_zero.min(),
                                "Desvio Padrao NZ": dados_mes_non_zero.std(),
                                "Variancia NZ": dados_mes_non_zero.var(),
                                "P25 NZ": dados_mes_non_zero.quantile(0.25) if not dados_mes_non_zero.empty else None,
                                "P50 NZ": dados_mes_non_zero.quantile(0.50) if not dados_mes_non_zero.empty else None,
                                "P75 NZ": dados_mes_non_zero.quantile(0.75) if not dados_mes_non_zero.empty else None,
                                "P90 NZ": dados_mes_non_zero.quantile(0.90) if not dados_mes_non_zero.empty else None,
                                "P95 NZ": dados_mes_non_zero.quantile(0.95) if not dados_mes_non_zero.empty else None,
                                "P99 NZ": dados_mes_non_zero.quantile(0.99) if not dados_mes_non_zero.empty else None,
                                "CHUVA LDU": " - ",
                                "Média LDU mm/dia":  dados_mes_LDU.mean(),
                                "Média LDU mm/mes":  dados_mes_LDU.mean()*30,
                                "Média LDU mm/ano":  dados_mes_LDU.mean()*365,
                                "Mediana LDU":  dados_mes_LDU.median(),
                                "Moda LDU": float( dados_mes_LDU.mode().iloc[0]) if not  dados_mes_LDU.mode().empty else None,
                                "Máximo LDU":  dados_mes_LDU.max(),
                                "Mínimo LDU":  dados_mes_LDU.min(),
                                "Desvio Padrao LDU":  dados_mes_LDU.std(),
                                "Variancia LDU":  dados_mes_LDU.var(),
                                "P25(LDU)":  dados_mes_LDU.quantile(0.25) if not  dados_mes_LDU.empty else None,
                                "P50(LDU)":  dados_mes_LDU.quantile(0.50) if not  dados_mes_LDU.empty else None,
                                "P75(LDU)":  dados_mes_LDU.quantile(0.75) if not  dados_mes_LDU.empty else None,
                                "P90(LDU)":  dados_mes_LDU.quantile(0.90) if not  dados_mes_LDU.empty else None,
                                "P95(LDU)":  dados_mes_LDU.quantile(0.95) if not  dados_mes_LDU.empty else None,
                                "P99(LDU)":  dados_mes_LDU.quantile(0.99) if not  dados_mes_LDU.empty else None
                            })

 
     
                            # Salvando estatísticas mensais na aba correspondente do Excel
                            # df_estatisticas_mensais = pd.DataFrame([estatisticas_mensais])
                            # df_estatisticas_mensais.to_excel(writer, sheet_name=f"Mensal_{mes}", index=False, header=not writer.sheets)

               
               

                for ano in range(dados_validos.index.year.min(), dados_validos.index.year.max() + 1):
                    
                    dados_ano = dados_validos[dados_validos.index.year == ano]
                    dados_ano_non_zero = chuva_non_zero[chuva_non_zero.index.year == ano]
                    dados_ano_LDU = dados_LDU[dados_LDU.index.year == ano]

                    num_dias_ano = len(pd.date_range(start=f'{ano}-01-01', end=f'{ano}-12-31'))
                    num_dias_ano_validos = len(dados_ano)
                    num_dias_ano_validos_nonzero = len(dados_ano_non_zero)
                    num_dias_ano_validos_LDU = len(dados_ano_LDU)
                    
                    idv_ano = (num_dias_ano_validos / num_dias_ano) * 100 if num_dias_ano else 0
                    idv_ano_non_zero = (num_dias_ano_validos / num_dias_ano) * 100 if num_dias_ano else 0
                    idv_ano_LDU = (num_dias_ano_validos / num_dias_ano) * 100 if num_dias_ano else 0
                    
                    if not dados_ano.empty:
                       estatisticas_anuais.append (
                            {

                                "Codigo": codigo,
                                "Nome": nome,
                                "Latitude": lat,
                                "Longitude": lon,
                                "Altitude": altitude,
                                "cidade": cidade,
                                "UF": UF,
                                "Bacia": bacia,
                                "Sub Bacia": subbacia,
                                "Rio": rio,
                                "orgao": orgao,
                                "CONTAGEM": " - ",
                                "ano":ano,
                                "Data Inicial": data_min,
                                "Data Final": data_max,
                                "Num de Dias": num_dias_ano,
                                "Num de Dias válidos": num_dias_ano_validos,
                                "Num Dias Validos": math.ceil(num_dias_ano * (idv_ano / 100)),
                                "Num Dados chuva non_zero": num_dias_ano_validos_nonzero,
                                "Num Dados >= LDU": num_dias_ano_validos_LDU,
                                "IDV": idv_ano,
                                "IDV LDU": idv_ano_LDU,
                                "IDV Nonzero": idv_ano_non_zero,
                                "STAT-ALL": " - ", #--------------------------------------------------------------------------------------
                                "Média mm/dia":  dados_ano.mean(),
                                "Média mm/ano":  dados_ano.mean()*30,
                                "Média mm/ano":  dados_ano.mean()*365,
                                "Mediana":  dados_ano.median(),
                                "Moda": float( dados_ano.mode().iloc[0]) if not  dados_ano.mode().empty else None,
                                "Máximo":  dados_ano.max(),
                                "Mínimo":  dados_ano.min(),
                                "Desvio Padrao":  dados_ano.std(),
                                "Variancia":  dados_ano.var(),
                                "P25":  dados_ano.quantile(0.25) if not  dados_ano.empty else None,
                                "P50":  dados_ano.quantile(0.50) if not  dados_ano.empty else None,
                                "P75":  dados_ano.quantile(0.75) if not  dados_ano.empty else None,
                                "P90":  dados_ano.quantile(0.90) if not  dados_ano.empty else None,
                                "P95":  dados_ano.quantile(0.95) if not  dados_ano.empty else None,
                                "P99":  dados_ano.quantile(0.99) if not  dados_ano.empty else None,
                                "CHUVA NON-ZERO": " - ",
                                "Média NZ mm/dia": dados_ano_non_zero.mean(),
                                "Média NZ mm/ano": dados_ano_non_zero.mean()*30,
                                "Média NZ mm/ano": dados_ano_non_zero.mean()*365,
                                "Mediana NZ": dados_ano_non_zero.median(),
                                "Moda NZ": float(dados_ano_non_zero.mode().iloc[0]) if not dados_ano_non_zero.mode().empty else None,
                                "Máximo NZ": dados_ano_non_zero.max(),
                                "Mínimo NZ": dados_ano_non_zero.min(),
                                "Desvio Padrao NZ": dados_ano_non_zero.std(),
                                "Variancia NZ": dados_ano_non_zero.var(),
                                "P25 NZ": dados_ano_non_zero.quantile(0.25) if not dados_ano_non_zero.empty else None,
                                "P50 NZ": dados_ano_non_zero.quantile(0.50) if not dados_ano_non_zero.empty else None,
                                "P75 NZ": dados_ano_non_zero.quantile(0.75) if not dados_ano_non_zero.empty else None,
                                "P90 NZ": dados_ano_non_zero.quantile(0.90) if not dados_ano_non_zero.empty else None,
                                "P95 NZ": dados_ano_non_zero.quantile(0.95) if not dados_ano_non_zero.empty else None,
                                "P99 NZ": dados_ano_non_zero.quantile(0.99) if not dados_ano_non_zero.empty else None,
                                "CHUVA LDU": " - ",
                                "Média LDU mm/dia":  dados_ano_LDU.mean(),
                                "Média LDU mm/ano":  dados_ano_LDU.mean()*30,
                                "Média LDU mm/ano":  dados_ano_LDU.mean()*365,
                                "Mediana LDU":  dados_ano_LDU.median(),
                                "Moda LDU": float( dados_ano_LDU.mode().iloc[0]) if not  dados_ano_LDU.mode().empty else None,
                                "Máximo LDU":  dados_ano_LDU.max(),
                                "Mínimo LDU":  dados_ano_LDU.min(),
                                "Desvio Padrao LDU":  dados_ano_LDU.std(),
                                "Variancia LDU":  dados_ano_LDU.var(),
                                "P25(LDU)":  dados_ano_LDU.quantile(0.25) if not  dados_ano_LDU.empty else None,
                                "P50(LDU)":  dados_ano_LDU.quantile(0.50) if not  dados_ano_LDU.empty else None,
                                "P75(LDU)":  dados_ano_LDU.quantile(0.75) if not  dados_ano_LDU.empty else None,
                                "P90(LDU)":  dados_ano_LDU.quantile(0.90) if not  dados_ano_LDU.empty else None,
                                "P95(LDU)":  dados_ano_LDU.quantile(0.95) if not  dados_ano_LDU.empty else None,
                                "P99(LDU)":  dados_ano_LDU.quantile(0.99) if not  dados_ano_LDU.empty else None
                            })

                
                grava_historico(historico, df, k, "a", tamanho, data_min, data_max, 'OK')
                dados_estado.append(dados_validos)
                print("Código:", codigo, k, " de ", num_estacao, " ", nome, " ", UF," ",data_min," ",data_max, "tamanho:",tamanho)
            else:
                grava_historico(historico, df, k, "a", 0, '', '', 'NO DATA')
                print("Código:", codigo, k, " de ", num_estacao, " ", nome, " ", UF,"  NAO CONTÉM DADOS ")

        if dados_estado:
            dados_estado_df = pd.concat(dados_estado, axis=1)
            dados_estado_df = dados_estado_df.loc[~dados_estado_df.index.duplicated(keep='first')]
            df_resultados_completos = pd.DataFrame(resultados_completos)
            #df_resultados_completos.to_excel(resultado_completo_path, sheet_name="ANUAL" , index=False)

            df_estatisticas_mensais = pd.DataFrame(estatisticas_mensais)
            # # Crie o arquivo vazio se ele não existir
            # if not Path(resultado_completo_path).exists():
            #    with open(resultado_completo_path, 'w') as f:
            #         pass
            df_estatisticas_anuais = pd.DataFrame(estatisticas_anuais)   

            with pd.ExcelWriter(resultado_completo_path, mode='w', engine='openpyxl') as writer:
                df_resultados_completos.to_excel(writer, sheet_name="ANUAL", index=False)

            with pd.ExcelWriter(resultado_completo_path, mode='a', engine='openpyxl',if_sheet_exists='replace') as writer:    
                df_estatisticas_anuais.to_excel(writer, sheet_name="ANUAIS", index=False)
                df_estatisticas_mensais.to_excel(writer, sheet_name="MENSAL", index=False)
                for mes in df_estatisticas_mensais['mes'].unique():
                    df_mes = df_estatisticas_mensais[df_estatisticas_mensais['mes'] == mes]
                    df_mes.to_excel(writer, sheet_name=f"MENSAL_{mes}", index=False)        

            return dados_estado_df
        else:
            grava_historico(historico, df, k, "a", 0, '', '', 'NO DATA2')
            print("Nenhum dado disponível para as estações dadas")
            return None




global historico
global limite_chuva 
global  resultado_completo_path


"""

CONFIGURAÇÃO  DO DOWNLAOD 

historico   => NOME DO ARQUIVO DE CONTROLE 
limite_chuva=1.0   => limite de chuva válida 
file_path =        => local da planilha do inventario 

    exemplo:
    '../01_INVENTARIO/inventario_BAHIA.xlsx'

resultado_completo_path = Nome da planilha com o sumário das estações. 

    exemplo:
        'sumario_BAHIA.xlsx'

arquivos_dados         > Nome dos arquivos que contém os dados de chuva 
    exemplo:
        'dados_BAHIA.xlsx'         

        
        Datas inicial e final. Se tdeixadas em braco vão baixar todo o inventário 
        Se definidas , farão o downlaod somente entre as datas informadas. 

        
data_inicial=''
data_final=''

"""
historico="historico_BAHIA.csv"
limite_chuva=1.0
file_path = '../01_INVENTARIO/inventario_BAHIA.xlsx'
resultado_completo_path = 'sumario_BAHIA.xlsx'
arquivos_dados='dados_BAHIA.xlsx'
data_inicial=''
data_final=''





# Instanciando a classe e obtendo o inventário
service = ServiceANA()

# Lendo o arquivo Excel e especificando que queremos apenas a coluna 'código'
df= pd.read_excel(file_path, usecols=['codigo'],index_col=None)
codigos = df['codigo'].tolist()

df= pd.read_excel(file_path,index_col=None)
dados_rj = service.baixar_dados_por_estacao(df, tipoDados='2', data_i=data_inicial, data_f=data_final, consistencia='1')



# Ler o CSV
historico_df = pd.read_csv(historico)
historico_df = historico_df[historico_df['status'] == 'OK']




# Salvando os dados em uma planilha XLSX
if dados_rj is not None:
    dados_rj.to_excel(arquivos_dados)

    with pd.ExcelWriter(arquivos_dados, mode='a', engine='openpyxl') as writer:
        historico_df.to_excel(writer, sheet_name='Historico', index=False)
else:
    print("Nenhum dado de chuva disponível para o estado do Rio de Janeiro.")

 


