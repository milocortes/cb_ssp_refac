## Cargamos paqueterías
from costs_benefits_ssp.cb_calculate import CostBenefits
import pandas as pd 
import os 

## Definimos directorio donde están los datos
SSP_RESULTS_PATH = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/package"

## Cargamos los datos
ssp_data = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "iran.zip"))
att_primary = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "ATTRIBUTE_PRIMARY.csv"))
att_strategy = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "ATTRIBUTE_STRATEGY.csv"))
strategy_code_base = "BASE"

## Instanciamos un objeto de la clase CostBenefits 
cb = CostBenefits(ssp_data, att_primary, att_strategy, strategy_code_base)

## Exportamos las tablas de costos a un archivo excel. Cada pestaña representa una tabla en la base de datos del programa
## de costos y beneficios.
## El archivo excel será guardado con el nombre cb_config_params.xlsx en la ruta donde actualmente está la sesión de python
cb.export_db_to_excel()

## Una vez actualizado el archivo excel, podemos cargarlo y para actualizar la base de datos del programa
cb.load_cb_parameters("/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/package/cb_config_params.xlsx")

## Con la base de datos de los factores de costos actualizada, calculamos:

# System Costs
results_system = cb.compute_system_cost_for_all_strategies()

# Technical Costs
results_tx = cb.compute_technical_cost_for_all_strategies()

# Combina resultados
results_all = pd.concat([results_system, results_tx], ignore_index = True)

#-------------POST PROCESS SIMULATION RESULTS---------------
# Post process interactions among strategies that affect the same variables
results_all_pp = cb.cb_process_interactions(results_all)

# SHIFT any stray costs incurred from 2015 to 2025 to 2025 and 2035
results_all_pp_shifted = cb.cb_shift_costs(results_all_pp)

# Guardamos resultados
results_all_pp_shifted.to_csv("/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/package/cost_benefit_results_tornado.csv", index = False)


### Replicamos el archiivo tornado_plot_data_QA_QC.csv

#filter subsector totals
ids = ["primary_id", "region", "time_period"]
subsector_totals = [i for i in ssp_data.columns if "co2e_subsector_total" in i]

#create ch4 totals  
subsector_totals_ch4 = ["emission_co2e_ch4_agrc",
                           "emission_co2e_ch4_ccsq",
                          "emission_co2e_ch4_entc",
                          "emission_co2e_ch4_fgtv",
                          "emission_co2e_ch4_frst",
                          "emission_co2e_ch4_inen",
                          "emission_co2e_ch4_ippu",
                          "emission_co2e_ch4_lsmm",
                          "emission_co2e_ch4_lvst",
                          "emission_co2e_ch4_scoe",
                          "emission_co2e_ch4_trns",
                          "emission_co2e_ch4_trww",
                          "emission_co2e_ch4_waso"]

ch4 = {i:i.split("_")[-1] for i in subsector_totals_ch4}

#read mapping  
te_all = pd.read_csv("emission_targets.csv")
target_country = "IRN"
te_all = te_all[["Subsector","Gas","Vars","Edgar_Class",target_country]].rename(columns = {target_country : "tvalue"})

data = ssp_data[ids + subsector_totals]

for ch_subsector, subsector in ch4.items():
    edgar_vars = te_all.query(f"Subsector == '{subsector}' and Gas=='ch4'")["Vars"].values[0].split(":")
    data[ch_subsector] = ssp_data[edgar_vars].sum(axis = 1)

#estimate totals emissions
data["emission_co2e_total"] = data[subsector_totals].sum(axis = 1)
data["emission_co2e_ch4_total"] = data[subsector_totals_ch4].sum(axis = 1)

# estimate cumulative emissions 
data = data.drop(columns="time_period").groupby(["primary_id", "region"]).sum().reset_index()

#add reference 
data_0 = data.query("primary_id == 0").drop(columns=["primary_id", "region"])
data_diff = data.set_index(["primary_id", "region"]) - data_0.to_numpy()
data_diff.columns = [f"{i}_diff" for i in data_diff.columns ]

data = pd.concat([data.set_index(["primary_id", "region"]), data_diff], axis = 1).reset_index()

data = data.merge(right = att_primary, on="primary_id").merge(right = att_strategy, on = "strategy_id")

#now add cost & benefits 
cb_data = results_all_pp_shifted.copy()
cb_chars = pd.DataFrame([i for i in cb_data.variable.apply(lambda x : x.split(":"))], columns=("name","sector","cb_type","item_1","item_2"))
cb_data = pd.concat([cb_data, cb_chars], axis = 1)

cb_data["value"] /= 1e9 #making all BUSD

# aggregate
cdata = cb_data.groupby(["sector", "cb_type", "strategy_code"]).agg({"value" : "sum"}).reset_index()

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
data["total_transformation_costs"] = data[["technical_cost","technical_savings","fuel_cost"]].sum(axis = 1)
data["total_transformation_costs_mi_CO2e"] = (data["total_transformation_costs"]/abs(data["emission_co2e_total_diff"]))*1000


#read strategy names
data["strategy_code"] = data["strategy_code"].apply(lambda x : x.replace("TORNADO:",""))
data["strategy_code"] = data["strategy_code"].apply(lambda x : x.replace("_HIGHEST","" ))


strategy_names = pd.read_csv("strategy_names.csv")

strategy_names["strategy_code"] = strategy_names["strategy_code"].apply(lambda x: x.replace("TX:",""))


data = data.merge(right = strategy_names, on = "strategy_code")

data.to_csv("tornado_plot_data_QA_QC_nuevo.csv", index = False)

