from typing import List
import pandas as pd 
import os 

def build_path(PATH : List[str]) -> str:
    return os.path.abspath(os.path.join(*PATH))

#-------------READ THE DATA-----------------
## ----------- DEFINE PATHS
CB_REFAC_PATH = build_path([os.getcwd(), ".."])
OUTPUT_PATH = build_path([CB_REFAC_PATH, "output"])
OUTPUT_PYTHON_PATH = build_path([OUTPUT_PATH, "python"])
OUTPUT_R_PATH = build_path([OUTPUT_PATH, "r"])

### Compara results system
RESULTS_SYSTEMS_PYTHON = build_path([OUTPUT_PYTHON_PATH, "results_system_python.csv"])
RESULTS_SYSTEMS_R = build_path([OUTPUT_R_PATH, "results_system_r.csv"])

results_system_python = pd.read_csv(RESULTS_SYSTEMS_PYTHON)
results_system_r = pd.read_csv(RESULTS_SYSTEMS_R)

set(results_system_r.variable.unique()) - set(results_system_python.variable.unique())
set(results_system_r.difference_variable.unique()) - set(results_system_python.difference_variable.unique())


def parser_to_kdl(difference_variable : str , 
                  multiplier : str ,
                  multiplier_unit : str ,
                  annual_change : str ,
                  output_variable_name : str ,
                  output_display_name : str ,
                  sum : str ,
                  natural_multiplier_units : str ,
                  display_notes : str ,
                  internal_notes)  -> str:


import kdl

doc = kdl.parse('''
  data sector="afolu_crop_livestock_production_cost_factors" {
    var_node difference_variable="pop_lvst_buffalo" multiplier=260.0 multiplier_unit="$/head"

    var_node difference_variable="pop_lvst_cattle_dairy" multiplier=260.0 multiplier_unit="$/head"
  }
''')

