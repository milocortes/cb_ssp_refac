from typing import List
import pandas as pd 
import numpy as np
import glob
import os 
import kdl


def build_path(PATH : List[str]) -> str:
    return os.path.abspath(os.path.join(*PATH))

#-------------READ THE DATA-----------------
## ----------- DEFINE PATHS
CB_REFAC_PATH = build_path([os.getcwd(), ".."])
CB_REFAC_DATA_PATH = build_path([CB_REFAC_PATH, "data"])
CB_COST_FACTORS_PATH_FILES = build_path([CB_REFAC_DATA_PATH, "cost_factors"])

renombra_cols = {"ï»¿difference_variable" : "difference_variable",
'difference_variable' : "difference_variable" , 
'multiplier' :"multiplier" ,
'multiplier unit' : "multiplier_unit" ,
'annual change' : "annual_change" ,
'output_variable_name' : "output_variable_name" ,
'output_display_name' : "output_display_name" ,
'sum' : "sum" ,
'natural multiplier units' : "natural_multiplier_units" ,
'display_notes' : "display_notes" ,
'internal_notes' : "internal_notes"}


cost_factors = {i.split("/")[-1].replace(".csv", "") : pd.read_csv(i, encoding = "latin").rename(columns = renombra_cols)
                 for i in glob.glob(CB_COST_FACTORS_PATH_FILES+"/*.csv")}

obten_nulo = lambda valor : "null" if valor in [np.nan, "", "none"] else valor
    

def parser_to_kdl(difference_variable : str , 
                  multiplier : float ,
                  multiplier_unit : str ,
                  annual_change : float ,
                  output_variable_name : str ,
                  output_display_name : str ,
                  sum : float ,
                  natural_multiplier_units : str ,
                  display_notes : str ,
                  internal_notes : str,
                  **others)  -> str:

    return f"""\t\t\tvar_node difference_variable=r"{obten_nulo(difference_variable)}" multiplier={obten_nulo(multiplier)} multiplier_unit=r"{obten_nulo(multiplier_unit)}" annual_change={obten_nulo(annual_change) } output_variable_name=r"{obten_nulo(output_variable_name)}" output_display_name=r"{obten_nulo(output_display_name)}" sum={obten_nulo(sum)} display_notes=r"{obten_nulo(display_notes)}" output_variable_name=r"{obten_nulo(output_variable_name)}" internal_notes=r"{obten_nulo(internal_notes)}"\n\n"""

with open("cost_factors.kdl", "w") as file:
    file.write(f"""cost_factors{{\n""")

for sector,data in cost_factors.items():
    acumula_line = ""
    

    for line in range(data.shape[0]):
        data_line = dict(data.iloc[line])
        acumula_line += parser_to_kdl(
            **data_line
        )

    acumula_line = acumula_line.replace('r"null"', "null")
    acumula_line = acumula_line.replace('r"nan"', "null")
    
    with open("cost_factors.kdl", "a") as file:
        file.write(f"""\tdata sector="{sector}" {{\n""")
        file.write(acumula_line)
        file.write("\t}\n")


with open("cost_factors.kdl", "a") as file:
    file.write("}\n")


with open("cost_factors.kdl", "r") as file:
    juan = "".join([i for i in file.readlines()])

doc = kdl.parse(juan)

cost_factors = doc.nodes[0].nodes

for sector in cost_factors:
    print(f'\nsector : {sector.props["sector"]}')
    for data_var in sector.nodes:
        print(data_var.props["difference_variable"])