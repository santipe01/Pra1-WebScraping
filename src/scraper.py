from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from fake_useragent import UserAgent
import random
import time

class EmbalsesScraper():

    def __init__(self, data):
        self.url = "https://www.embalses.net"
        self.data = data
        self.user_agent = UserAgent()

    def __random_sleep(self):
        time.sleep(random.uniform(1, 3))  # Retraso aleatorio entre 1 y 3 segundos

    def __get_headers(self):
        # Genera una cabecera aleatoria para que en la web detecten a un ordenador diferente cada vez que accedemos
        return {'User-Agent': self.user_agent.random}


    def __get_url_cuencas(self):
        urls=[]
        web_embalses = requests.get(self.url, headers=self.__get_headers())
        self.__random_sleep()
        html_embalses = BeautifulSoup(web_embalses.text, 'html')
        cuencas_hidrográfricas = html_embalses.find_all('div', class_ = 'index_bodysecLisT2_list')[1].find_all('a')
        for cuenca_hidográfica in cuencas_hidrográfricas:
            urls.append(cuenca_hidográfica['href'])
        self.__random_sleep()
        return urls

    def __get_url_embalses(self, url_cuencas):
        urls=[]
        for url in url_cuencas:
            web_embalses_cataluña = requests.get(url, headers=self.__get_headers())
            self.__random_sleep()
            html_embalses = BeautifulSoup(web_embalses_cataluña.text, 'html')
            tabla_embalses = html_embalses.find_all('tr', class_ = 'ResultadoCampo')
            for fila_embalse in tabla_embalses:
                link_embalse = fila_embalse.find('a')
                urls.append(link_embalse['href'])
            self.__random_sleep()
        return urls

    def __get_nombre_embalse(self, url):
        match = re.search(r'\d+-(.*?)(?=.html)', url)
        if match:
            nombre_embalse = match.group(1)
        return nombre_embalse
    def __get_url_mapa(self, url_embalse):
        web_embalse = requests.get(url_embalse, headers=self.__get_headers())
        html_embalse = BeautifulSoup(web_embalse.text, 'html.parser')
        url_mapa = html_embalse.find('a', string='Ver Mapa')
        return url_mapa["href"]

    def __get_info_embalse(self, url_embalse, df=None):
        if df is None:
            df = pd.DataFrame()

        # Realizamos la solicitud GET para obtener el contenido de la página del embalse
        web_embalse = requests.get(url_embalse, headers=self.__get_headers())
        self.__random_sleep()
        html_embalse = BeautifulSoup(web_embalse.text, 'html.parser')
        nombre_embalse = self.__get_nombre_embalse(url_embalse)
        
        # Inicializamos un diccionario para almacenar los datos
        data = {"Embalse": nombre_embalse}

        # Buscamos todas las filas de datos del embalse
        filas_datos_embalse = html_embalse.find_all('div', class_='FilaSeccion')

        #Mapa
        url_mapa=self.__get_url_mapa(url_embalse)
        web_mapa=requests.get(url_mapa, headers=self.__get_headers())
        html_mapa = BeautifulSoup(web_mapa.text, 'html.parser')
        javascript_mapa = html_mapa.find_all('script', type = 'text/javascript')
        
        filas_pluviometro = html_embalse.find_all('a', title=lambda value: value and 'Pluviometro' in value)

        # Iteramos sobre las filas de datos del embalse
        for fila_datos in filas_datos_embalse:
            # Verificamos si la fila pertenece a la primera tabla
            if fila_datos.find('div', class_='CampoInf') is None:
                # Primera tabla: 'Embalse: ___ '
                try:
                    campo = fila_datos.find('div', class_='Campo').text.strip()
                    resultado = fila_datos.find('div', class_='Resultado').text.strip()
                    unidad = fila_datos.find('div', class_='Unidad').text.strip()
                except:
                    campo = fila_datos.find('div', class_='Campo').text.strip()
                    resultado = fila_datos.find('div', class_='Resultado').text.strip()
                    unidad = fila_datos.find('div', class_='Unidad').text.strip()

                campo_unidad = (campo," ",unidad)

                # Añadimos los datos al diccionario
                data[campo_unidad] = resultado

            elif fila_datos.find('input') is None:
                # Segunda tabla: 'Datos del Embalse'
                try:
                    campo = fila_datos.find('div', class_='CampoInf').text.strip()
                    resultado = fila_datos.find('div', class_='ResultadoInf').text.strip()
                except:
                    campo = fila_datos.find('div', class_='CampoInf').text.strip()
                    resultado = fila_datos.find('div', class_='ResultadoInf').text.strip()

                # Añadimos los datos al diccionario
                data[campo] = resultado

            else:
                # Tercera tabla: 'Usos del Embalse'
                try:
                    campo = fila_datos.find('div', class_='CampoInf').text.strip()
                except:
                    campo = fila_datos.find('div', class_='CampoInf').text.strip()

                check = 'checked' in fila_datos

                # Añadimos los datos al diccionario
                data[campo] = check

        #Añadimos la longitud y la latitud al dataset
        pattern = r'center: ol\.proj\.fromLonLat\(\[(-?\d+\.\d+), (-?\d+\.\d+)\]\)'
        matches = re.search(pattern, str(javascript_mapa))
        if matches:
            # Extraemos las coordenadas encontradas
            longitud = matches.group(1)
            latitud = matches.group(2)
            data["Longitud"]=longitud
            data["Latitud:"]=latitud
        else:
            data["Longitud"]=0
            data["Latitud:"]=0

        #Añadimos los pluviometros al dataset
        pluviometros=[]
        for pluviometro in filas_pluviometro:
            pluviometro_name = pluviometro.get('title').replace('Pluviometro - ', '')
            if not pluviometro_name.startswith("Pluviometros"):
                pluviometros.append(pluviometro_name)
        data["Pluviometros"]=pluviometros


        df_temporal = pd.DataFrame([data])
        df = pd.concat([df, df_temporal], ignore_index=True)

        return df


    def __update_info_embalse(self, url_embalse, df=None):
        if df is None:
            df = pd.DataFrame()

        # Realizamos la solicitud GET para obtener el contenido de la página del embalse
        web_embalse = requests.get(url_embalse, headers=self.__get_headers())
        html_embalse = BeautifulSoup(web_embalse.text, 'html.parser')
        self.__random_sleep()
        nombre_embalse = self.__get_nombre_embalse(url_embalse)
        # Inicializamos un diccionario para almacenar los datos
        data = {"Embalse": nombre_embalse}

        # Buscamos todas las filas de datos del embalse
        filas_datos_embalse = html_embalse.find_all('div', class_='FilaSeccion')

        # Iteramos sobre las filas de datos del embalse
        for fila_datos in filas_datos_embalse:
            # Verificamos si la fila pertenece a la primera tabla
            if fila_datos.find('div', class_='CampoInf') is None:
                # Primera tabla: 'Embalse: ___ '
                try:
                    campo = fila_datos.find('div', class_='Campo').text.strip()
                    resultado = fila_datos.find('div', class_='Resultado').text.strip()
                    unidad = fila_datos.find('div', class_='Unidad').text.strip()
                except:
                    campo = fila_datos.find('div', class_='Campo').text.strip()
                    resultado = fila_datos.find('div', class_='Resultado').text.strip()
                    unidad = fila_datos.find('div', class_='Unidad').text.strip()

                # Añadimos los datos al diccionario
                data[campo] = resultado

        df_temporal = pd.DataFrame([data])
        df = pd.concat([df, df_temporal], ignore_index=True)

        return df

    def update_scrape(self):
        urls_cuencas = self.__get_url_cuencas()
        urls_embalses = self.__get_url_embalses(urls_cuencas)

        for embalse in urls_embalses:
            self.data = self.__update_info_embalse(embalse, self.data)

    def scrape(self):
        print("Web scraping of spanish reservoirs data from", self.url)
        print("This process could take some minutes.")

        if self.data.empty:
            urls_cuencas = self.__get_url_cuencas()
            urls_embalses = self.__get_url_embalses(urls_cuencas)

            for embalse in urls_embalses:
                self.data = self.__get_info_embalse(embalse, self.data)
        else:
            update_scrape()

    def data2csv(self, outputfile):
        self.data.to_csv(outputfile, index=False)
