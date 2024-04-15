from scraper import EmbalsesScraper
import pandas as pd
import time

df = pd.DataFrame()
output_file="embalses.csv"

scraper = EmbalsesScraper(df)
scraper.scrape()
scraper.data2csv(output_file)

print("Quieres que se actualice cada semana el dataset? (Si/No)")
respuesta = input()
if respuesta in ["Si", "si", "SI"]:
  while True:
    scraper.update_scrape()
    print("Quieres exportar el dataset actualizado? (Si/No)")
    respuesta2 = input()
      if respuesta2 in ["Si", "si", "SI"]:
        scraper.data2csv(output_file)
    time.sleep(604800)
