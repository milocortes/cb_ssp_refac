#-------------SOURCE LIBRARIES AND CODE-----
#source('cb_config.R')
#source('cb_utilities.R')
#source('cb_strategy_specific_functions.R')
#source('general_ssp_utilities.R')

from general_ssp_utilities import *
from cb_config import *
from cb_utilities import cb_calculate_system_costs
from data_reader import CBFilesReader
from cb_config import * 

from typing import List
import pandas as pd 
import os 
import re 

def build_path(PATH : List[str]) -> str:
    return os.path.join(*PATH)

#-------------READ THE DATA-----------------
DATA_PATH = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/local_exec/path_to_model_results"

data_filename = build_path([DATA_PATH, "sisepuede_results_sisepuede_run_ssp.csv"] )
primary_filename = build_path([DATA_PATH, "ATTRIBUTE_PRIMARY.csv"])
strategy_filename = build_path([DATA_PATH, "ATTRIBUTE_STRATEGY.csv"])

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
TLU_CONVERSION_PATH = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/local/data/strategy_specific_cb_files/lvst_tlu_conversions.csv"
tlu_conversions = pd.read_csv(TLU_CONVERSION_PATH)

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
STRATEGY_SPECIFIC_CB_FILES = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/local/data/definition_files"

strategy2tx = pd.read_csv(build_path([STRATEGY_SPECIFIC_CB_FILES, 'attribute_strategy_code.csv']))

#tells us which strategies to evaluate costs and benefit iffor
strategy_cost_instructions = pd.read_csv(build_path([STRATEGY_SPECIFIC_CB_FILES, 'strategy_cost_instructions.csv']))

#the list of all the cost factor files in the system, and the functions they should be evaluated with
cost_factor_names = pd.read_csv(build_path([STRATEGY_SPECIFIC_CB_FILES, 'system_cost_factors_list.csv']))  

#defines how each transformation is evaluated, including difference variables, cost multipliers, etc.
transformation_cost_definitions = pd.read_csv(build_path([STRATEGY_SPECIFIC_CB_FILES, 'transformation_cost_definitions.csv']), encoding="latin")


cb_data = CBFilesReader("/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/local/data")

results_system = cb_calculate_system_costs(data, strategy_cost_instructions, cost_factor_names, cb_data, SSP_GLOBAL_list_of_variables)

"""
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