## Cargamos paqueterías
from costs_benefits_ssp.cb_calculate import CostBenefits
import numpy as np
import pandas as pd 
import os 

from costs_benefits_ssp.model.cb_data_model import TXTable,CostFactor,TransformationCost,StrategyInteraction


##---- Definimos directorios

DIR_PATH = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/package"

build_path = lambda PATH  : os.path.abspath(os.path.join(*PATH))

### Directorio de salidas de SSP
SSP_RESULTS_PATH = build_path([DIR_PATH,"ssp_results"])

### Directorio de configuración de tablas de costos
CB_DEFAULT_DEFINITION_PATH = build_path([DIR_PATH, "cb_definition_data"])

### Directorio de salidas del módulo de costos y beneficios
OUTPUT_CB_PATH = build_path([DIR_PATH, "output_cb_mod"])

### Directorio de datos requeridos paragenerar el archivo whirlpool_plot_data_QA_QC.csv
INPUT_WHIRLPOOL_QA_PATH = build_path([DIR_PATH, "input_data_whirlpool_QA"])

### Directorio de salidas del archivo whirlpool_plot_data_QA_QC.csv
OUTPUT_WHIRLPOOL_QA_PATH = build_path([DIR_PATH, "output_whirlpool_QA"])


## Cargamos los datos
ssp_data = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "iran.csv"))
att_primary = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "ATTRIBUTE_PRIMARY.csv"))
att_strategy = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "ATTRIBUTE_STRATEGY.csv"))
strategy_code_base = "BASE"

## Remueve algunas variables de ssp 
#ssp_data = ssp_data.drop(columns = ['yf_agrc_vegetables_and_vines_tonne_ha', 'totalvalue_enfu_fuel_consumed_inen_fuel_furnace_gas'])

## Instanciamos un objeto de la clase CostBenefits 
cb = CostBenefits(ssp_data, att_primary, att_strategy, strategy_code_base)

## El método export_db_to_excel guarda la configuración inicial de las tablas de costos a un archivo excel. 
### Cada pestaña representa una tabla en la base de datos del programa de costos y beneficios.
CB_DEFAULT_DEFINITION_FILE_PATH = os.path.join(CB_DEFAULT_DEFINITION_PATH, "cb_config_params.xlsx")

cb.export_db_to_excel(CB_DEFAULT_DEFINITION_FILE_PATH)

## Una vez actualizado el archivo excel, podemos cargarlo y actualizar la base de datos del programa
cb.load_cb_parameters(CB_DEFAULT_DEFINITION_FILE_PATH)

## Analizaremos estrategia por estrategia, y transformación por transformación los resultados de costos y beneficios para identificar 
## los problemas asociados
## La estrategia es analizar cada cb_var_group para detectar dónde están los problemas
df_cost_factors = pd.read_sql(cb.session.query(CostFactor).statement, cb.session.bind)

## Get all system cost variable for a specific cb_var_group
cb_var_group = "wali_sanitation_cost_factors"
strategy_tx = 'WHIRLPOOL:TX:IPPU:DEC_DEMAND'

all_cb_var_group = df_cost_factors.query(f"cb_var_group=='{cb_var_group}'")["output_variable_name"]

#------ System Costs
"""
results_system = pd.concat(
    [
        cb.compute_cost_benefit_from_variable(cb_var_name = cb_var_system_cost, strategy_code_tx = strategy_tx)
        for cb_var_system_cost in all_cb_var_group
    ],
    ignore_index = True
)

results_system = cb.compute_system_cost_for_strategy(strategy_tx)
"""
results_system = cb.compute_system_cost_for_all_strategies()

# Podemos modifical el dataframe y pasarlo como argumento al método compute_system_cost_for_all_strategies
# el cual actualizará la tabla cost_factors en la base de datos y realizará la ejecución con la tabla actualizada
#results_tx = cb.compute_technical_cost_for_strategy(strategy_code_tx = strategy_tx)
results_tx = cb.compute_technical_cost_for_all_strategies()

# Combina resultados
results_all = pd.concat([results_system, results_tx], ignore_index = True)

#-------------POST PROCESS SIMULATION RESULTS---------------
# Post process interactions among strategies that affect the same variables
results_all_pp = cb.cb_process_interactions(results_all)

# SHIFT any stray costs incurred from 2015 to 2025 to 2025 and 2035
results_all_pp_shifted = cb.cb_shift_costs(results_all_pp)

# Guardamos las salidas
WHIRLPOOL_OUTPUT_CB_FILE_PATH = os.path.join(OUTPUT_WHIRLPOOL_QA_PATH, "cost_benefit_results_whirlpool.csv")

results_all_pp_shifted.to_csv(WHIRLPOOL_OUTPUT_CB_FILE_PATH, index = False)

### Replicamos el archiivo whirlpool_plot_data_QA_QC.csv

## Load edgar cw gases for Iran
data = pd.read_csv("whirlpool_edgar_cw_iran_gases.csv")

#now add cost & benefits 
cb_data = results_all_pp_shifted.copy()
#cb_data = cb_data.query("variable!='cb:agrc:crop_value:crops_produced:vegetables'").reset_index(drop = True)
cb_chars = pd.DataFrame([i for i in cb_data.variable.apply(lambda x : x.split(":"))], columns=("name","sector","cb_type","item_1","item_2"))
cb_data = pd.concat([cb_data, cb_chars], axis = 1)

cb_data["value"] /= 1e9 #making all BUSD

# aggregate
cdata = cb_data.groupby(["sector", "cb_type", "strategy_code"]).agg({"value" : "sum"}).reset_index()

## Remueve algunas categorías que están ocasionando problemas
### inen en sector_specific
### agrc en crop_value
### wali en human_health y technical_cost

#cdata = cdata.query("not(sector=='agrc' and cb_type=='crop_value')").reset_index(drop=True)
#cdata = cdata.query("not(sector=='inen' and cb_type=='sector_specific')").reset_index(drop=True)
#cdata = cdata.query("not(sector=='wali' and (cb_type=='human_health' or cb_type=='technical_cost') )").reset_index(drop=True)

id_vars = ["strategy","strategy_id","primary_id","region","strategy_code"]
fvars = ["emission_co2e_total_diff","emission_co2e_ch4_total_diff"]
data = data[id_vars + fvars]

#add cb categories  
data_by_cb_type = cdata.groupby(["strategy_code", "cb_type"]).agg({"value" : "sum"})\
                        .reset_index().pivot(index='strategy_code', 
                                            columns='cb_type', 
                                            values='value')\
                        .replace(np.nan, 0.0)\
                        .reset_index()


data = data.merge(right=data_by_cb_type, on = "strategy_code")
data = data.drop(columns=["emission_co2e_ch4_total_diff"])
data["strategy_code"] = data["strategy_code"].apply(lambda x : x.replace("TRWW", "WALI"))
data["strategy"] = data["strategy"].apply(lambda x : x.replace("TRWW", "WALI"))
data["sector"] = data["strategy"].apply(lambda x : x.split(":")[1])

#now create columns with marginal values  
cb_cats = cdata["cb_type"].unique()
data[[f"{i}_mi_CO2e"for i in cb_cats]] = (data[cb_cats]/abs(data["emission_co2e_total_diff"].to_numpy()[:,np.newaxis]))*1000

#create net benefits 
data["net_benefit"] = data[cb_cats].sum(axis = 1)
data["net_benefit_mi_CO2e"] = (data["net_benefit"]/abs(data["emission_co2e_total_diff"]))*1000

#create additional benefits 
data["additional_benefits"] = data[[i for i in cb_cats if i != "technical_cost"]].sum(axis = 1)

#create total transformation cost 
data["total_transformation_costs"] = data[ ["technical_cost","technical_savings","fuel_cost"]].sum(axis = 1)
data["total_transformation_costs_mi_CO2e"] = (data["total_transformation_costs"]/abs(data["emission_co2e_total_diff"]))*1000

#read strategy names
STRATEGY_NAMES_FILE_PATH = os.path.join(INPUT_WHIRLPOOL_QA_PATH, "strategy_names.csv")
strategy_names = pd.read_csv(STRATEGY_NAMES_FILE_PATH)
strategy_names["strategy_code"] = strategy_names["strategy_code"].apply(lambda x: x.replace("TX:",""))

data.strategy_code = data.strategy_code.apply(lambda x : x.replace("WHIRLPOOL:TX:", "").replace("_LOWER", "").replace("_HIGHER", "").replace("_HIGHEST",""))


data = data.merge(right = strategy_names, on = "strategy_code")

WHIRLPOOL_PLOT_DATA_QA_FILE_PATH = os.path.join(OUTPUT_WHIRLPOOL_QA_PATH, "whirlpool_plot_data_QA_QC_nuevo.csv")

data.to_csv(WHIRLPOOL_PLOT_DATA_QA_FILE_PATH, index = False)


