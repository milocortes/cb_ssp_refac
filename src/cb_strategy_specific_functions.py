from typing import Dict, List
from cb_config import *
import pandas as pd
import numpy as np
import re



#---------------Support Functions-----------------

#Get a column of data from a wide data table and return it as long for a single strategy
def cb_get_data_from_wide_to_long(data : pd.DataFrame, 
                                  strategy_code : str, 
                                  variables : List[str]
                                  ) -> pd.DataFrame:

    #global SSP_GLOBAL_LOG_VARIABLE_SEARCH

    #if SSP_GLOBAL_LOG_VARIABLE_SEARCH:
    #    SSP_GLOBAL_LOG_OF_SEARCHED_VARS = SSP_GLOBAL_LOG_OF_SEARCHED_VARS.append(variables)
    
    if not isinstance(variables, list):
        variables = [variables]

    data_wide = data[data["strategy_code"].isin([strategy_code])][SSP_GLOBAL_SIMULATION_IDENTIFIERS + variables].reset_index(drop = True)
    
    data_long = data_wide.melt(id_vars=SSP_GLOBAL_SIMULATION_IDENTIFIERS)
  

    return data_long  



#-------2. Loop Through Variables--------
def cb_wrapper(func):
    def inner1(args_container_to_function_param : dict):
        
        #print("before Execution")
        #print("Update args on dict")

        result_tmp = []

        final_arg_container = {
          "data" : args_container_to_function_param["data"],
          "strategy_code_tx" : args_container_to_function_param["strategy_code"],
          "strategy_code_base" : args_container_to_function_param["comparison_code"],
          "output_var_name" : args_container_to_function_param["output_variable_name"],
          "output_mults" : args_container_to_function_param["multiplier"],
          "change_in_multiplier" : args_container_to_function_param["annual change"],
          "list_of_variables" : args_container_to_function_param["list_of_variables_in_dataset"],
        }

        final_arg_container.update(args_container_to_function_param)

        ## Get all variable matches on difference_variable
        diff_var = args_container_to_function_param["difference_variable"].replace("*", ".*")
        diff_var_list = [string for string in final_arg_container["list_of_variables"] if  re.match(re.compile(diff_var), string)]

        if not diff_var_list:
          print(f'ERROR IN CB_WRAPPER: No variables match : {diff_var}')
          return None 

        sum_results = args_container_to_function_param["sum"]

        # For each variable that matches the substring, calculate the costs and benefits
        for diff_var_param in diff_var_list:
          print(f"                       {diff_var_param}")
          final_arg_container["diff_var"] = diff_var_param
          result = func(**final_arg_container)
          result["strategy_code"] = final_arg_container["strategy_code_tx"]
          result["difference_variable"] = diff_var_param
          result_tmp.append(result)
        #print(pd.concat(result_tmp, ignore_index = True))
        # If flagged, sum up the variables in value and difference_value columns
        #Create a new output data frame and append it to the existing list
        #Note that the difference variable may be garbage if we are summing across different comparison variables
        if sum_results == 1:          
          #create one long dataset
          result_tmp = pd.concat(result_tmp, ignore_index = True)
          results_summarized = result_tmp.groupby(["region", "time_period", "strategy_code", "future_id"]).agg({"value" : sum, "difference_value" : sum}).reset_index()
          results_summarized["difference_variable"] = diff_var
          results_summarized["variable"] = final_arg_container["output_var_name"]

          #print(results_summarized)
          return results_summarized.sort_values(["difference_variable", "time_period"])
          
        else:
          appended_results = pd.concat(result_tmp, ignore_index = True)
          print(appended_results)
          return appended_results.sort_values(["difference_variable", "time_period"])
          
    return inner1

#---------------Manure Management
@cb_wrapper
def cb_manure_management_cost(  data : pd.DataFrame, 
                                strategy_code_tx : str, 
                                strategy_code_base : str, 
                                diff_var : str, 
                                output_vars : str, 
                                output_mults : float, 
                                change_in_multiplier : float, 
                                list_of_variables : list,
                                **additional_args : dict,
                                ) -> pd.DataFrame:

  #time_period = range(SSP_GLOBAL_TIME_PERIODS)
  implementation = [0]*11 + list(np.linspace(0, 0.95, SSP_GLOBAL_TIME_PERIODS - 11))

  manure_imp = pd.DataFrame({"implementation" : implementation})

  tlus = cb_get_data_from_wide_to_long(data, strategy_code_tx, diff_var)
  tlus = pd.concat([tlus, manure_imp], axis = 1)
  tlus["difference_variable"] = diff_var
  tlus["difference_value"] = tlus["value"]*tlus["implementation"]
  tlus["value"] = tlus["difference_value"] * output_mults
  tlus["variable"] = output_vars
  tlus = tlus[SSP_GLOBAL_COLNAMES_OF_RESULTS]

  return tlus

#--------------IPPU: CCS ------------------
@cb_wrapper
def cb_ippu_inen_ccs(   data : pd.DataFrame, 
                        strategy_code_tx : str, 
                        strategy_code_base : str, 
                        diff_var : str, 
                        output_vars : str, 
                        output_mults : float, 
                        change_in_multiplier : float, 
                        list_of_variables : list,
                        **additional_args : dict,
                        ) -> pd.DataFrame:
    
    #get the fraction reductions in CO2
    ccs_fraction_vars = [i for i in list_of_variables if i.startswith("frac_ippu_production_with_co2_capture_")]
    ccs_fractions = cb_get_data_from_wide_to_long(data, strategy_code_tx, ccs_fraction_vars)

    #given the global capture rate, update the application fraction
    ccs_fractions["application_rate"] = ccs_fractions["value"]

    #get the quantities of production for those variables
    production_vars = [i.replace("frac_ippu_production_with_co2_capture_", "prod_ippu_") + "_tonne" for i in ccs_fraction_vars]
    ccs_fractions["variable"] = ccs_fractions["variable"].apply(lambda x : x.replace("frac_ippu_production_with_co2_capture_", "prod_ippu_") + "_tonne")
    prod_qty = cb_get_data_from_wide_to_long(data, strategy_code_tx, production_vars)

    #merge the two datasets
    by_merge_vars = ['region', 'strategy_code', 'time_period', 'variable']
    tx_suffix = "ccs"
    base_suffix = ""

    data_merged = ccs_fractions.merge(right = prod_qty, on =  by_merge_vars, suffixes=(tx_suffix, base_suffix))

    #multiply the production quantity by the fractions
    data_merged["difference_value"] = data_merged["application_rate"] * data_merged["value"]
    data_merged["difference_variable"] = data_merged["variable"]

    #read the cost definitions
    ccs_cost_factor = additional_args["cb_data"].StrategySpecificCBData["ippu_ccs_cost_factors"]

    data_merged = data_merged.merge(right = ccs_cost_factor, on = 'variable')

    data_merged["value"] = data_merged["difference_value"] * data_merged["multiplier"]
    data_merged["variable"] = data_merged["output_variable_name"]
  
    data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
    
    return data_merged

#--------------FGTV: ALL COSTS ------------
#This function calculates the cost of abating fugitive emissions.
#(1) calculates the "fugitive emissions intensity" as the fugitive emissions per unit of energy consumed in each time period in the baseline
#(2) calculates the "expected fugitive emissions" in a transformed future by multiplying that intensity by the energy consumed in the transformed future
#(3) calculates "fugitive emissions abated"  as difference between "expected fugitive emissions" and actual emissions
#(4) calculates "cost of abatement" as quantity abated * cost of abatement
@cb_wrapper
def cb_fgtv_abatement_costs(data : pd.DataFrame, 
                            strategy_code_tx : str, 
                            strategy_code_base : str, 
                            diff_var : str, 
                            output_vars : str, 
                            output_mults : float, 
                            change_in_multiplier : float, 
                            list_of_variables : list,
                            **additional_args : dict,
                            ) -> pd.DataFrame:
    
    #(1) FUGITIVE EMISSIONS INTENSITY
    energy_vars = ['energy_demand_enfu_total_fuel_coal', 'energy_demand_enfu_total_fuel_oil', 'energy_demand_enfu_total_fuel_natural_gas']
    fgtv_vars = [string for string in list_of_variables if  re.match(re.compile('emission_co2e_.*_fgtv_fuel_.*'), string)]

    #1. Get the fugitive emissions per PJ of coal and oil together in the baseline
    energy = cb_get_data_from_wide_to_long(data, strategy_code_base, energy_vars)
    energy["fuel"] = energy["variable"].apply(lambda x : x.replace('energy_demand_enfu_total_', ''))
    fgtv = cb_get_data_from_wide_to_long(data, strategy_code_base, fgtv_vars)
    fgtv["fuel"] = fgtv["variable"].apply(lambda x : x.split("_fgtv_")[-1])

    #1.a summarize the emissions by fuel
    vars_to_groupby = ["primary_id", "region", "time_period", "strategy_code", "fuel"]
    fgtv = fgtv.groupby(vars_to_groupby).agg({"value" : sum}).reset_index()

    data_merged_base = energy.merge(right = fgtv, on = vars_to_groupby, suffixes=('.en_base', '.fg_base'))

    #2. Get the fugitive emissions per PJ of coal and oil together in the transformed future
    energy_tx = cb_get_data_from_wide_to_long(data, strategy_code_tx, energy_vars)
    energy_tx["fuel"] = energy_tx["variable"].apply(lambda x : x.replace('energy_demand_enfu_total_', ''))
    fgtv_tx = cb_get_data_from_wide_to_long(data, strategy_code_tx, fgtv_vars)
    fgtv_tx["fuel"] = fgtv_tx["variable"].apply(lambda x : x.split("_fgtv_")[-1])

    #2.b summarize the emissions by fuel
    fgtv_tx = fgtv_tx.groupby(vars_to_groupby).agg({"value" : sum}).reset_index()

    data_merged_tx = energy_tx.merge(right = fgtv_tx, on = vars_to_groupby, suffixes=('.en_tx', '.fg_tx'))

    #3. Merge the two together
    data_merged = data_merged_tx.merge(right = data_merged_base, on = ['region', 'time_period', 'fuel'], suffixes=['.tx', '.base'])
    #(2/3) FUGITIVE EMISSIONS INTENSITY and EXPECTED FUGITIVE EMISSIONS
    #4. Calculate the fugitive emissions per unit demand in the baseline and apply it to the transformed future
    data_merged["fgtv_co2e_per_demand_base"] = data_merged["value.fg_base"]/data_merged["value.en_base"]
    data_merged["fgtv_co2e_expected_per_demand"] = data_merged["value.en_tx"]*data_merged["fgtv_co2e_per_demand_base"]
  
    #5. Calculate the difference between observed and expected demand
    data_merged["difference_value"] = data_merged["value.fg_tx"] - data_merged["fgtv_co2e_expected_per_demand"]
    data_merged["difference_variable"] = data_merged["variable.tx"]

    #6. Apply the multiplier
    data_merged["value"] = data_merged["difference_value"]*output_mults
    data_merged["variable"] = output_vars

    #7. Get columns
    data_merged["strategy_code"] = data_merged["strategy_code.tx"]
    data_merged["future_id"]= data_merged["future_id.tx"]
    data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]

    #8. If tehre are NANs or NAs in the value, replace them with 0.
    data_merged.replace(np.nan, 0.0)

    return data_merged

#--------------LNDU: SOIL CARBON/CONSERVATION AGRICULTURE------------
@cb_wrapper
def cb_lndu_soil_carbon(data : pd.DataFrame, 
                            strategy_code_tx : str, 
                            strategy_code_base : str, 
                            diff_var : str, 
                            output_vars : str, 
                            output_mults : float, 
                            change_in_multiplier : float, 
                            list_of_variables : list,
                            **additional_args : dict,
                            ) -> pd.DataFrame:

    #get the beginning and ending fractions of acres under soil conservation
    #create transformations as time series per country
    ca_fracs = additional_args["cb_data"].StrategySpecificCBData["LNDU_soil_carbon_fractions"]
    
    time_period = pd.DataFrame({"time_period" : range(SSP_GLOBAL_TIME_PERIODS)})
    
    a = ca_fracs[["region"]].merge(right = time_period, how = "cross")

    ca_fracs = ca_fracs.merge(right=a, on = "region")
    

    ca_fracs["gains_in_ca"] = ca_fracs["end_val"] - ca_fracs["start_val"]
    ca_fracs["frac_in_year"] = ca_fracs["gains_in_ca"]/(SSP_GLOBAL_TIME_PERIODS - SSP_GLOBAL_TIME_PERIOD_TX_START +1) * (ca_fracs["time_period"] - SSP_GLOBAL_TIME_PERIOD_TX_START+1)
    ca_fracs.loc[(ca_fracs["time_period"] >=0) & (ca_fracs["time_period"]<=SSP_GLOBAL_TIME_PERIOD_TX_START-1), "frac_in_year"] = 0
    ca_fracs["frac_in_year"] = ca_fracs["frac_in_year"]+ca_fracs["start_val"]

    #calculate the number of acres under CA in the transformation and in baseline
    ca_data_tx = cb_get_data_from_wide_to_long(data, strategy_code_tx, diff_var)
  
    ca_data_tx = ca_data_tx.merge(right = ca_fracs, on =['region', 'time_period'])
    ca_data_tx["acres_ca"] = ca_data_tx["value"]*ca_data_tx["frac_in_year"]

    ca_data_base = cb_get_data_from_wide_to_long(data, strategy_code_base, diff_var)
    ca_data_base = ca_data_base.merge(right = ca_fracs, on = ['region', 'time_period'])
    ca_data_base["acres_ca"] = ca_data_base["value"]*ca_data_base["start_val"]
    

    ca_data_merged = ca_data_tx.merge(right = ca_data_base, on = ['region', 'time_period'], suffixes = ['', '.base'])
    ca_data_merged["difference_variable"] = 'diff_additional_acres_under_soil_management'
    ca_data_merged["difference_value"] = ca_data_merged["acres_ca"]-ca_data_merged["acres_ca.base"]
    ca_data_merged["zeros"] = 0
    ca_data_merged["difference_value"] = np.maximum(ca_data_merged["difference_value"], ca_data_merged["zeros"])
  
    #for any extra acreage, apply multipliers
    #apply multipliers to those acres
    ca_data_merged["value"] = ca_data_merged["difference_value"]*output_mults
    ca_data_merged["variable"] = output_vars

    #get the relevant columns
    ca_data_merged = ca_data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
    
    return ca_data_merged

#--------------PFLO:BETTER DIETS------------
#calculate the number of additional people using better diets
#for each such person, there is a $370 cost savings in groceries and 
#$1000/yr cost savings in health
@cb_wrapper
def cb_pflo_healthier_diets(data : pd.DataFrame, 
                            strategy_code_tx : str, 
                            strategy_code_base : str, 
                            diff_var : str, 
                            output_vars : str, 
                            output_mults : float, 
                            change_in_multiplier : float, 
                            list_of_variables : list,
                            **additional_args : dict,
                            ) -> pd.DataFrame:

    #Get the population
    population = cb_get_data_from_wide_to_long(data, strategy_code_tx, ['population_gnrl_rural', 'population_gnrl_urban'])
    
    vars_to_groupby = ["primary_id", "region", "time_period", "strategy_code", "future_id"]

    total_pop = population.groupby(vars_to_groupby).agg({"value" : "sum"}).rename(columns = {"value" : "total_pop"}).reset_index()

    #get the file with popualtion fractions  
    diet_frac = additional_args["cb_data"].StrategySpecificCBData["PFLO_transition_to_new_diets"]

    data_merged = total_pop.merge(right = diet_frac, on='time_period')
    data_merged["difference_value"] = data_merged["total_pop"]*(1-data_merged["frac_gnrl_w_original_diet"])
    data_merged["difference_variable"] = 'pop_with_better_diet'
    data_merged["variable"] = output_vars
    data_merged["value"] = data_merged["difference_value"] * output_mults

    data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]

    return data_merged

#----------AGRCLVST:Productivity----------
#the economic cost of increasing productivity is equal to
#some percent of GDP defined in file
@cb_wrapper
def cb_agrc_lvst_productivity(data : pd.DataFrame, 
                            strategy_code_tx : str, 
                            strategy_code_base : str, 
                            diff_var : str, 
                            output_vars : str, 
                            output_mults : float, 
                            change_in_multiplier : float, 
                            list_of_variables : list,
                            **additional_args : dict,
                            ) -> pd.DataFrame:
    #Get the gdp data
    gdp = cb_get_data_from_wide_to_long(data, strategy_code_tx, 'gdp_mmm_usd')

    #Get the fractions for each country
    gdp_fracs = additional_args["cb_data"].StrategySpecificCBData["AGRC_LVST_productivity_cost_gdp"]
    gdp_fracs = gdp_fracs.rename(columns = {"cost_of_productivity improvements_pct_gdp" : "cost_frac"})

    #country codes
    country_codes = additional_args["cb_data"].StrategySpecificCBData["iso3_all_countries"].rename(columns = {"ISO3" : "iso_code3"})
    gdp_fracs = gdp_fracs.merge(right = country_codes, on = "iso_code3")
    gdp_fracs = gdp_fracs.rename(columns = {"REGION" : "region"})
    gdp_fracs = gdp_fracs[['region', 'cost_frac']]

    #merge wiht gdp
    gdp = gdp.merge(right=gdp_fracs, on = "region")
    gdp["difference_variable"] = 'diff_fraction_of_GDP_for_productivity'
    gdp["difference_value"] = gdp["cost_frac"]
    gdp["variable"] = output_vars
    gdp["value"] = gdp["value"]*10**9*gdp["cost_frac"]/2*(-1)
    gdp.loc[gdp["time_period"]<SSP_GLOBAL_TIME_PERIOD_TX_START, "value"] = 0
  
    gdp = gdp[SSP_GLOBAL_COLNAMES_OF_RESULTS]

    return gdp
  
#----------AGRC:RICE------------
@cb_wrapper
def cb_agrc_rice_mgmt(data : pd.DataFrame, 
                            strategy_code_tx : str, 
                            strategy_code_base : str, 
                            diff_var : str, 
                            output_vars : str, 
                            output_mults : float, 
                            change_in_multiplier : float, 
                            list_of_variables : list,
                            **additional_args : dict,
                            ) -> pd.DataFrame:
    
    #define the transformation as the fraction of acres receiivng better rice management
    tx_definition = additional_args["cb_data"].StrategySpecificCBData['AGRC_rice_mgmt_tx']
    tx_definition["level_of_implementation"] = (1-tx_definition["ef_agrc_anaerobicdom_rice_kg_ch4_ha"])/0.45
    
    rice_management_data = cb_get_data_from_wide_to_long(data, strategy_code_tx, diff_var)

    #merge with transformation
    rice_management_data = rice_management_data.merge(right = tx_definition, on = 'time_period')
  
    rice_management_data["difference_variable"] = diff_var #paste0('diff_', diff_var)
    rice_management_data["difference_value"] = rice_management_data["value"]*rice_management_data["level_of_implementation"]
    rice_management_data["variable"] = output_vars
    rice_management_data["value"] = rice_management_data["difference_value"]*output_mults
    rice_management_data = rice_management_data[SSP_GLOBAL_COLNAMES_OF_RESULTS]
    
    return rice_management_data


#----------LVST: ENTERIC FERMENTATION------------------
@cb_wrapper
def cb_lvst_enteric(data : pd.DataFrame, 
                            strategy_code_tx : str, 
                            strategy_code_base : str, 
                            diff_var : str, 
                            output_vars : str, 
                            output_mults : float, 
                            change_in_multiplier : float, 
                            list_of_variables : list,
                            **additional_args : dict,
                            ) -> pd.DataFrame:

    #define the strategy as the fractino of livestock receivving this intervention in a particular year
    tx_definition = additional_args["cb_data"].StrategySpecificCBData['LVST_enteric_fermentation_tx']
    affected_livestock = tx_definition[tx_definition["application"]>0]
    timesteps = pd.DataFrame({"time_period" : range(SSP_GLOBAL_TIME_PERIODS)})

    enteric_pop_fracs = affected_livestock.merge(right=timesteps, how = "cross")

    enteric_pop_fracs["application_in_year"] = enteric_pop_fracs["application"]/(SSP_GLOBAL_TIME_PERIODS - SSP_GLOBAL_TIME_PERIOD_TX_START) *(enteric_pop_fracs["time_period"] - SSP_GLOBAL_TIME_PERIOD_TX_START+1)
    enteric_pop_fracs.loc[(enteric_pop_fracs["time_period"] >=0) & (enteric_pop_fracs["time_period"]<=SSP_GLOBAL_TIME_PERIOD_TX_START-1), "application_in_year"] = 0


    #apply that to the data
    data_num_livestock = cb_get_data_from_wide_to_long(data, strategy_code_tx, affected_livestock["variable"].to_list())
  
    data_merged = data_num_livestock.merge(right = enteric_pop_fracs, on = ['variable', 'time_period'])
    data_merged["difference_variable"] = data_merged["variable"] 
    data_merged["difference_value"] = data_merged["value"]*data_merged["application_in_year"]
    data_merged["variable"] = data_merged["variable"].apply(lambda x : f"{output_vars}{x}")
    data_merged["value"] = data_merged["difference_value"]*output_mults
    data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
  
    return data_merged 


mapping_strategy_specific_functions : Dict[str,str] = {
    'cb_lndu_soil_carbon' : cb_lndu_soil_carbon,
    'cb_difference_between_two_strategies' : 'cb_difference_between_two_strategies',
    'cb_scale_variable_in_strategy' : 'cb_scale_variable_in_strategy',
    'cb_fraction_change' : 'cb_fraction_change',
    'cb_entc_reduce_losses' : 'cb_entc_reduce_losses',
    'cb_ippu_clinker' : 'cb_ippu_clinker',
    'cb_fgtv_abatement_costs' : cb_fgtv_abatement_costs,
    'cb_waso_reduce_consumer_facing_food_waste' : 'cb_waso_reduce_consumer_facing_food_waste',
    'cb_lvst_enteric' : cb_lvst_enteric,
    'cb_agrc_rice_mgmt' : cb_agrc_rice_mgmt,
    'cb_agrc_lvst_productivity' : cb_agrc_lvst_productivity,
    'cb_pflo_healthier_diets' : cb_pflo_healthier_diets,
    'cb_ippu_inen_ccs' : cb_ippu_inen_ccs,
    'cb_manure_management_cost' : cb_manure_management_cost,
}