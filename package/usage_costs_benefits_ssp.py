## Cargamos paqueterías
from costs_benefits_ssp.cb_calculate import CostBenefits
import pandas as pd 
import os 

## Definimos directorio donde están los datos
SSP_RESULTS_PATH = "/home/milo/Documents/egtp/SISEPUEDE/CB/cb_ssp_refac/package"

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
cb.load_cb_parameters("/home/milo/Documents/egtp/SISEPUEDE/CB/cb_ssp_refac/package/cb_config_params.xlsx")

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
results_all_pp_shifted.to_csv("/home/milo/Documents/egtp/SISEPUEDE/CB/cb_ssp_refac/cost_benefit_results_tornado.csv", index = False)

### Algunas funcionalidades del programa
## El método get_cb_var_fields nos permite obtener información de la variable de costo
cb.get_cb_var_fields(cb_var_name = "cb:trns:air_pollution:X:diesel")
cb.get_cb_var_fields(cb_var_name = "cb:lvst:lvst_value:livestock_produced:chickens")

## El método compute_cost_benefit_from_variable calcula los costos o beneficios de una variable de costos para alguna de las estrategias.
## Este método toma por default la estrategia base definida al instanciar la clase CostBenefits. Podemos modificar la estrategia de comparación al
## agregar en el argumento strategy_code_base la nueva estrategia baseline 
cb.compute_cost_benefit_from_variable(cb_var_name = 'cb:trns:technical_cost:efficiency:non_electric', 
                                      strategy_code_tx = 'TORNADO:TRNS:INC_EFFICIENCY_NON_ELECTRIC')

cb.compute_cost_benefit_from_variable(cb_var_name = 'cb:trns:technical_cost:efficiency:non_electric', 
                                      strategy_code_tx = 'TORNADO:TRNS:INC_EFFICIENCY_NON_ELECTRIC',
                                      strategy_code_base = 'TORNADO:WALI:INC_TREATMENT_INDUSTRIAL')

## El método compute_technical_cost_for_strategy calcula todos los technical cost para una estrategia
cb.compute_technical_cost_for_strategy(strategy_code_tx = 'TORNADO:AGRC:DEC_CH4_RICE')
cb.compute_system_cost_for_strategy(strategy_code_tx = 'TORNADO:AGRC:DEC_CH4_RICE')
