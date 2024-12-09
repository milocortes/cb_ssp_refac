import pandas as pd 
from jinja2 import Environment, FileSystemLoader

import glob 

# Definimos la configuración de jinja
file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)

# Cargamos el template
template_output_tables = env.get_template('sqltemplate')

# Cargamos dataframe de tablas
tablas = [i.split("/")[-1].replace(".csv","") for i in glob.glob("csv2sqlite/*.csv") if not i.split("/")[-1] in ["tx_table.csv", "strategy_interaction_definitions.csv", "transformation_cost.csv"]]

# Enviamos la lista de tablas al template
output_tables = template_output_tables.render(tablas = tablas)

with open("cb_database", "w") as text_file:
    text_file.write(output_tables)