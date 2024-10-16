#-------------SOURCE LIBRARIES AND CODE-----
#source('cb_config.R')
#source('cb_utilities.R')
#source('cb_strategy_specific_functions.R')
#source('general_ssp_utilities.R')

from general_ssp_utilities import *
from cb_config import *
from cb_utilities import cb_calculate_system_costs, cb_calculate_transformation_costs
from data_reader import CBFilesReader
from cb_config import * 
import pickle

from typing import List
import pandas as pd 
import os 
import re 

def build_path(PATH : List[str]) -> str:
    return os.path.abspath(os.path.join(*PATH))

#-------------READ THE DATA-----------------
## ----------- DEFINE PATHS
CB_REFAC_PATH = build_path([os.getcwd(), ".."])
CB_REFAC_DATA_PATH = build_path([CB_REFAC_PATH, "data"])
STRATEGY_SPECIFIC_CB_PATH_FILES = build_path([CB_REFAC_DATA_PATH, "strategy_specific_cb_files"])
SSP_RESULTS_DATA_PATH = build_path([CB_REFAC_DATA_PATH, "ssp_model_results"])
DEFINITION_FILES_PATH = build_path([CB_REFAC_DATA_PATH, "definition_files"])

OUTPUT_PATH = build_path([CB_REFAC_PATH, "output"])

data_filename = build_path([SSP_RESULTS_DATA_PATH, "sisepuede_results_sisepuede_run_ssp.csv"] )
primary_filename = build_path([SSP_RESULTS_DATA_PATH, "ATTRIBUTE_PRIMARY.csv"])
strategy_filename = build_path([SSP_RESULTS_DATA_PATH, "ATTRIBUTE_STRATEGY.csv"])

output_file = pd.read_csv(data_filename)

#-------------PREPARE THE DATA--------------
#Read data
data = output_file.copy()


#Merge model output with strategy attributes (mainly the strategy_code)
run_attributes = ssp_merge_run_attributes(primary_filename, strategy_filename)
merged_data = run_attributes[['primary_id', 'strategy_code', 'future_id']].merge(right = data, on='primary_id')
data = merged_data.copy()

#clean the data of furnace gas and crude
temp_data_cols = data.columns

cols_to_keep = [string for string in temp_data_cols if not re.match(re.compile('totalvalue.*furnace_gas'), string)]
cols_to_keep = [string for string in cols_to_keep if not re.match(re.compile('totalvalue_.*_fuel_consumed_.*_fuel_crude'), string)]
cols_to_keep = [string for string in cols_to_keep if not re.match(re.compile('totalvalue_.*_fuel_consumed_.*_fuel_electricity'), string)] #10.13 ADDED THIS SO SECTOR FUELS EXCLUDE ELECTRICITY

data = data[cols_to_keep]

#add calculation of total TLUs to data
TLU_CONVERSION_FILE_PATH = build_path([STRATEGY_SPECIFIC_CB_PATH_FILES, "lvst_tlu_conversions.csv"]) 
tlu_conversions = pd.read_csv(TLU_CONVERSION_FILE_PATH)

pop_livestock = data[SSP_GLOBAL_SIMULATION_IDENTIFIERS + [i for i in cols_to_keep if "pop_lvst" in i]]
pop_livestock = pop_livestock.melt(id_vars=['primary_id', 'time_period', 'region', 'strategy_code', 'future_id'])
pop_livestock = pop_livestock.merge(right=tlu_conversions, on = "variable")

pop_livestock["total_tlu"] = pop_livestock["value"] * pop_livestock["TLU"]

pop_livestock_summarized = pop_livestock.groupby(SSP_GLOBAL_SIMULATION_IDENTIFIERS).\
                                            agg({"total_tlu" : sum}).\
                                            rename(columns={"total_tlu":"lvst_total_tlu"}).\
                                            reset_index()

data = data.merge(right = pop_livestock_summarized, on = SSP_GLOBAL_SIMULATION_IDENTIFIERS)

#replace any lagging references to "PFLO:SOCIOTECHNICAL" with "PFLO:CHANGE_CONSUMPTION"
data.loc[data["strategy_code"] == "PFLO:SOCIOTECHNICAL", "strategy_code"] = "PFLO:CHANGE_CONSUMPTION"
SSP_GLOBAL_list_of_strategies = data["strategy_code"].unique()
SSP_GLOBAL_list_of_variables = list(set(data.columns) - set(SSP_GLOBAL_SIMULATION_IDENTIFIERS))

#-------------REMOVE BASE FOR COST BENEFIT ANALYSIS------------
data = data.query("strategy_code!='BASE'").reset_index(drop=True)

#-------------READ DEFINITION FILES IN AND CALCULATE COSTS AND BENEFITS----------

#maps strategies to transformations, from James
#This file tells us which transformation in is in each strategy
strategy2tx = pd.read_csv(build_path([DEFINITION_FILES_PATH, 'attribute_strategy_code.csv']))

#tells us which strategies to evaluate costs and benefit iffor
strategy_cost_instructions = pd.read_csv(build_path([DEFINITION_FILES_PATH, 'strategy_cost_instructions.csv']))

#the list of all the cost factor files in the system, and the functions they should be evaluated with
cost_factor_names = pd.read_csv(build_path([DEFINITION_FILES_PATH, 'system_cost_factors_list.csv']))  

#defines how each transformation is evaluated, including difference variables, cost multipliers, etc.
transformation_cost_definitions = pd.read_csv(build_path([DEFINITION_FILES_PATH, 'transformation_cost_definitions.csv']), encoding="latin")

#calculate system costs
cb_data = CBFilesReader(CB_REFAC_DATA_PATH)
results_system = cb_calculate_system_costs(data, strategy_cost_instructions, cost_factor_names, cb_data, SSP_GLOBAL_list_of_variables, SSP_GLOBAL_list_of_strategies)

#calcualte transformation costs
results_tx = cb_calculate_transformation_costs(data, 
                                  strategy_cost_instructions,
                                  strategy2tx, 
                                  transformation_cost_definitions, 
                                  cb_data,
                                  SSP_GLOBAL_list_of_variables, 
                                  SSP_GLOBAL_list_of_strategies)

RESULTS_SYSTEMS_PATH = build_path([OUTPUT_PATH, "python", "results_system_python.csv"])
RESULTS_TX_SYSTEMS_PATH = build_path([OUTPUT_PATH, "python", "results_tx_python.csv"])

results_system.to_csv(RESULTS_SYSTEMS_PATH, index = False)
results_tx.to_csv(RESULTS_TX_SYSTEMS_PATH, index = False)


"""
with open('args_container_3.pickle', 'rb') as handle:
    args_container_to_function_param = pickle.load(handle)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("task_app")

DATA_FILE_PATH = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/local/data"
cb_reader = CBFilesReader(DATA_FILE_PATH, logger)
"""