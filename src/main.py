from scraper import EmbalsesScraperSelenium
import pandas as pd

df = pd.DataFrame()
output_file="embalses.csv"

scraper = EmbalsesScraperSelenium(df)

print("Quieres hacer scrape o actualizar? (scrape/actualizar)")
respuesta = input()
if respuesta == "actualizar":
  scraper.update_scrape(df)
  print("Quieres exportar el dataset actualizado? (Si/No)")
  respuesta2 = input()
    if respuesta2 in ["Si", "si", "SI"]:
      scraper.data2csv(output_file)
else:
  scraper.scrape()
  scraper.data2csv(output_file)
