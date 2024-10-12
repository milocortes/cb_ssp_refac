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