from bs4 import BeautifulSoup
import requests
import pandas as pd
from scrapy.http import HtmlResponse
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import random
import time

class EmbalsesScraperSelenium():

    def __init__(self, data):
        self.url = "https://www.embalses.net"
        self.data = data

        # Configuración de Selenium
        options = Options()
        options.add_argument("--headless")  # Ejecución en modo headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--user-agent=Your_User_Agent_String_Here") #User Agent
        self.driver = webdriver.Chrome(options=options)

    def __del__(self):
        self.driver.quit()
        self.service.stop()

    def __random_sleep(self):
        time.sleep(random.uniform(1, 3))  # Retraso aleatorio entre 1 y 3 segundos

    def __get_url_cuencas(self):
        urls=[]
        self.driver.get(self.url)
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.index_bodysecLisT2_list')))
        cuencas_hidrográfricas = self.driver.find_elements(By.CSS_SELECTOR, '.index_bodysecLisT2_list')[1].find_elements(By.TAG_NAME, 'a')
        for cuenca_hidográfica in cuencas_hidrográfricas:
            urls.append(cuenca_hidográfica.get_attribute('href'))
            self.__random_sleep()
        return urls

    def __get_url_embalses(self, url_cuencas):
        urls=[]
        for url in url_cuencas:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'tr.ResultadoCampo')))
            tabla_embalses = self.driver.find_elements(By.CSS_SELECTOR, 'tr.ResultadoCampo')
            for fila_embalse in tabla_embalses:
                link_embalse = fila_embalse.find_element(By.TAG_NAME, 'a')
                urls.append(link_embalse.get_attribute('href'))
                self.__random_sleep()
        return urls

    def __get_url_mapa(self, url_embalse):
        self.driver.get(url_embalse)
        url_mapa=WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[text()="Ver Mapa"]')))
        self.__random_sleep()
        url_mapa_href = url_mapa.get_attribute("href")
        return url_mapa_href

    def __get_nombre_embalse(self, url):
        match = re.search(r'\d+-(.*?)(?=.html)', url)
        if match:
            nombre_embalse = match.group(1)
        return nombre_embalse

    def __get_lonlat(self, url_embalse):
        url_mapa = self.__get_url_mapa(url_embalse)
        self.driver.get(url_mapa)

        # Esperar hasta que los scripts estén presentes
        WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'script[type="text/javascript"]')))

        javascript_mapa = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="text/javascript"]')
        pattern = r'center: ol\.proj\.fromLonLat\(\[(-?\d+\.\d+), (-?\d+\.\d+)\]\)'
        longitud = 0
        latitud = 0
        for script in javascript_mapa:
            matches = re.search(pattern, script.get_attribute('innerHTML'))
            if matches:
                # Extraer las coordenadas encontradas
                longitud = matches.group(1)
                latitud = matches.group(2)

        return longitud, latitud

    def __get_info_embalse(self, url_embalse):
        # Realizamos la solicitud GET para obtener el contenido de la página del embalse
        self.driver.get(url_embalse)
        self.__random_sleep()
        nombre_embalse = self.__get_nombre_embalse(url_embalse)
        # Inicializamos un diccionario para almacenar los datos
        data = {"Embalse": nombre_embalse}

        # Buscamos todas las filas de datos del embalse
        filas_datos_embalse = self.driver.find_elements(By.CLASS_NAME, 'FilaSeccion')

        # Iteramos sobre las filas de datos del embalse
        for fila_datos in filas_datos_embalse:
            # Verificamos si la fila pertenece a la primera tabla
            if not fila_datos.find_elements(By.CLASS_NAME, 'CampoInf'):
                # Primera tabla: 'Embalse: ___ '
                try:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'Campo').text.strip()
                    resultado = fila_datos.find_element(By.CLASS_NAME, 'Resultado').text.strip()
                    unidad = fila_datos.find_element(By.CLASS_NAME, 'Unidad').text.strip()
                except:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'Campo').text.strip()
                    resultado = fila_datos.find_element(By.CLASS_NAME, 'Resultado').text.strip()
                    unidad = fila_datos.find_element(By.CLASS_NAME, 'Unidad').text.strip()

                campo_unidad = campo + unidad

                # Añadimos los datos al diccionario
                data[campo_unidad] = resultado

            elif not fila_datos.find_elements(By.TAG_NAME, 'input'):
                # Segunda tabla: 'Datos del Embalse'
                try:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'CampoInf').text.strip()
                    resultado = fila_datos.find_element(By.CLASS_NAME, 'ResultadoInf').text.strip()
                except:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'CampoInf').text.strip()
                    resultado = fila_datos.find_element(By.CLASS_NAME, 'ResultadoInf').text.strip()

                # Añadimos los datos al diccionario
                data[campo] = resultado

            else:
                # Tercera tabla: 'Usos del Embalse'
                try:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'CampoInf').text.strip()
                except:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'CampoInf').text.strip()

                check = 'checked' in fila_datos.text

                # Añadimos los datos al diccionario
                data[campo] = check

        filas_pluviometro = self.driver.find_elements(By.CSS_SELECTOR, 'a[title*="Pluviometro"]')
        pluviometros = []
        for pluviometro in filas_pluviometro:
            pluviometro_name = pluviometro.get_attribute('title').replace('Pluviometro - ', '')
            if not pluviometro_name.startswith("Pluviometros"):
                pluviometros.append(pluviometro_name)

        data["Pluviometros"] = pluviometros
        
        longitud, latitud = self.__get_lonlat(url_embalse)

        data["Longitud"] = longitud
        data["Latitud"]  = latitud

        return data

    def __update_info_embalse(self, url_embalse):
        # Realizamos la solicitud GET para obtener el contenido de la página del embalse
        self.driver.get(url_embalse)
        self.__random_sleep()
        nombre_embalse = self.__get_nombre_embalse(url_embalse)
        # Inicializamos un diccionario para almacenar los datos
        data = {"Embalse": nombre_embalse}

        # Buscamos todas las filas de datos del embalse
        filas_datos_embalse = self.driver.find_elements(By.CLASS_NAME, 'FilaSeccion')

        # Iteramos sobre las filas de datos del embalse
        for fila_datos in filas_datos_embalse:
            # Verificamos si la fila pertenece a la primera tabla
            if not fila_datos.find_elements(By.CLASS_NAME, 'CampoInf'):
                # Primera tabla: 'Embalse: ___ '
                try:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'Campo').text.strip()
                    resultado = fila_datos.find_element(By.CLASS_NAME, 'Resultado').text.strip()
                    unidad = fila_datos.find_element(By.CLASS_NAME, 'Unidad').text.strip()
                except:
                    campo = fila_datos.find_element(By.CLASS_NAME, 'Campo').text.strip()
                    resultado = fila_datos.find_element(By.CLASS_NAME, 'Resultado').text.strip()
                    unidad = fila_datos.find_element(By.CLASS_NAME, 'Unidad').text.strip()

                campo_unidad = campo + unidad

                # Añadimos los datos al diccionario
                data[campo_unidad] = resultado
        return data

    def scrape(self):
        print("Web scraping of Spanish reservoirs data from", self.url)
        print("This process could take some minutes.")

        if self.data.empty:
            urls_cuencas = self.__get_url_cuencas()
            urls_embalses = self.__get_url_embalses(urls_cuencas)
            for embalse in urls_embalses:
                embalse_data = self.__get_info_embalse(embalse)
                df_temporal = pd.DataFrame([embalse_data])
                self.data = pd.concat([self.data, df_temporal], ignore_index=True)
        else:
            self.update_scrape()
    
    def update_scrape(self):
        urls_cuencas = self.__get_url_cuencas()
        urls_embalses = self.__get_url_embalses(urls_cuencas)
        df_updated=pd.DataFrame()
        for embalse in urls_embalses:
            embalse_data = self.__update_info_embalse(embalse)
            df_temporal = pd.DataFrame([embalse_data])
            df_updated  = pd.concat([df_updated, df_temporal], ignore_index=True)
        self.data.update(df_updated)

    def data2csv(self, outputfile):
        self.data.to_csv(outputfile, index=False)
