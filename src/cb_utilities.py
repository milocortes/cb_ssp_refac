from data_reader import CBFilesReader
from cb_strategy_specific_functions import mapping_strategy_specific_functions
from typing import List
from cb_config import *
import pickle
import pandas as pd 
import numpy as np
import copy
import re

from cb_strategy_specific_functions import cb_difference_between_two_strategies,cb_get_data_from_wide_to_long

global SSP_GLOBAL_list_of_variables 

#------------------1. Loop Through Cost Definitions -------
#This function loops through the strategies and applies system costs 
#which are defined in the cost factors
def cb_calculate_system_costs(data : pd.DataFrame, # SSP data output
                              strategy_cost_definitions_param : pd.DataFrame, # tells us which strategies to evaluate costs and benefit iffor 
                              system_cost_definitions : pd.DataFrame, # the list of all the cost factor files in the system, and the functions they should be evaluated with
                              cb_data : CBFilesReader, # data container
                              list_of_variables : List[str],
                              SSP_GLOBAL_list_of_strategies : List[str]
                              ) -> pd.DataFrame:
    
    # Get list of all variables in the SSP data output
    #list_of_variables = SSP_GLOBAL_list_of_variables

    #cut the list of strategies to evaluate to those that are marked to be evaluated, and that are in the data
    strategy_cost_definitions = strategy_cost_definitions_param.copy()
    strategy_cost_definitions = strategy_cost_definitions[(strategy_cost_definitions["evaluate_system_costs"] == 1) & (strategy_cost_definitions["strategy_code"].isin(SSP_GLOBAL_list_of_strategies))]
    strategy_code_comparison_mapping  = strategy_cost_definitions[["strategy_code", "comparison_code"]].to_records(index = False)
                                    
    strategy_cost_definitions  = strategy_cost_definitions.set_index("strategy_code")
    
    
    #cut the list of system cost definitions to those that are marked to be evaluated
    system_cost_definitions = system_cost_definitions[system_cost_definitions["include"]==1]    
    cost_factor_defined_mapping = {system_cost.split(".")[0] : cb_function for system_cost,cb_function in system_cost_definitions[["system_cost_filename", "cb_function"]].to_records(index = False)}

    # Obtenemos el diccionario de los factores de costos
    cost_factors_mapping = {system_cost : (system_cost_data, cost_factor_defined_mapping[system_cost]) for system_cost,system_cost_data in cb_data.CostFactorCBFile.items() if system_cost in cost_factor_defined_mapping}

    # Lista que va a acumular los resultados de cada ejecución
    results = []

    for strategy_code,comparison_code in strategy_code_comparison_mapping:
        if SSP_PRINT_STRATEGIES:
            # AQUÍ PONDREMOS UN MESSAGE
            print(f'============Evaluating system costs for {strategy_code} =================')

        for cost_factor, (cost_factor_data, cost_factor_function) in cost_factors_mapping.items():
            # AQUÍ PONDREMOS OTRO MESSAGE
            print(f"Cost Factor Loop: {strategy_code} vs {comparison_code} for cost factor {cost_factor} and cost factor function {cost_factor_function}")

            # Define argument container
            args_container = {
                  "data" : data,
                  "strategy_code" : strategy_code,
                  "cost_factor" : cost_factor,
                  "cost_factor_data" : cost_factor_data,
                  "cost_factor_function" : cost_factor_function,
                  "list_of_variables_in_dataset" :  list_of_variables,                 
            }

            args_container.update(
              strategy_cost_definitions.loc[strategy_code].to_dict()
            )

            if cost_factor_function=='cb_apply_cost_factors' or cost_factor_function=="cb_system_fuel_costs":
              results.append(
                cb_apply_cost_factors(args_container)
              )
            elif cost_factor_function=='cb_wali_sanitation_costs':


              sanitation_classification = cb_data.StrategySpecificCBData['WALI_sanitation_classification_strategy_specific_function']

              #Calculate the number of people in each sanitation pathway by merging the data with the sanitation classification
              #and with the population data and keepign onyl rows where the population_variable matches the variable.pop
              #then multiply the fraction by the population
              #There was concern that we need to account for differences in ww production between urban and rural
              #But we don't since the pathway fractions for them are mutually exclusive! Hooray!

              data_strategy = cb_get_data_from_wide_to_long(data, strategy_code, sanitation_classification["variable"].to_list())
              data_strategy = data_strategy.merge(right = sanitation_classification, on='variable')


              population = cb_get_data_from_wide_to_long(data, strategy_code, ['population_gnrl_rural', 'population_gnrl_urban'])
              data_strategy = data_strategy.merge(right = population, on = ['region', 'time_period', 'future_id'], suffixes = ["", ".pop"])
              data_strategy = data_strategy[data_strategy["population_variable"].isin(data_strategy["variable.pop"])].reset_index()
              data_strategy["pop_in_pathway"] = data_strategy["value"]*data_strategy["value.pop"]


              #Do the same thing with the baseline strategy
              data_base = cb_get_data_from_wide_to_long(data, comparison_code, sanitation_classification["variable"].to_list())
              data_base = data_base.merge(right = sanitation_classification, on = 'variable')

            
              population_base = cb_get_data_from_wide_to_long(data, comparison_code, ['population_gnrl_rural', 'population_gnrl_urban'])
            
              data_base = data_base.merge(right = population_base, on = ['region', 'time_period', 'future_id'], suffixes = ["", ".pop"])

              data_base = data_base[data_base["population_variable"].isin(data_base["variable.pop"])].reset_index(drop = True)
              data_base["pop_in_pathway"] = data_base["value"]*data_base["value.pop"]
            
              data_new = pd.concat([data_strategy, data_base], ignore_index = True)
            
              #reduce it by the sanitation category

              gp_vars = ["primary_id", "region", "time_period", "strategy_code", "future_id", "difference_variable"]

              data_new_summarized = data_new.groupby(gp_vars).agg({"pop_in_pathway" : "sum"}).rename(columns = {"pop_in_pathway" : "value"}).reset_index()
              data_new_summarized = data_new_summarized.rename(columns = {"difference_variable" : "variable"})
            
              new_list_of_variables = data_new_summarized["variable"].unique()  
              
              pivot_index_vars = [i for i in data_new_summarized.columns if i not in ["variable", "value"]]
              data_new_summarized_wide = data_new_summarized.pivot(index = pivot_index_vars, columns="variable", values="value").reset_index()  

              args_container["data"] = data.merge(right=data_new_summarized_wide, on = ['primary_id', 'region', 'time_period', 'future_id', 'strategy_code'])
              args_container["list_of_variables_in_dataset"] += ["pop_unimproved_rural", "pop_improved_rural", "pop_safelymanaged_rural", "pop_unimproved_urban", "pop_improved_urban", "pop_safelymanaged_urban", "pop_omit_rural"]
              results.append(
                #mapping_strategy_specific_functions["cb_wali_sanitation_costs"](args_container)
                cb_apply_cost_factors(args_container)
              )



    cb_results = pd.concat(results, ignore_index = True)
    return cb_results


def cb_apply_cost_factors(
                          args_container_param : dict,
                        ) -> pd.DataFrame:
    
    cb_results = []
    args_container_to_function = copy.deepcopy(args_container_param)
    df_cost_factor_data = args_container_to_function["cost_factor_data"]


    get_cost_factor_columns = [
                                "difference_variable",
                                "output_variable_name",
                                "multiplier",
                                "annual change",
                                "sum"
    ]

    df_cost_factor_data = df_cost_factor_data[get_cost_factor_columns].reset_index(drop=True)

    for i in range(df_cost_factor_data.shape[0]):
      args_cost_factor_container = df_cost_factor_data.iloc[i].to_dict()

      print(f"---------Costs for: {args_cost_factor_container['output_variable_name']}")

      args_container_to_function.update(
                args_cost_factor_container
      )

      cb_results.append(
          cb_difference_between_two_strategies(
              args_container_to_function
          )
      )

    if not all(elem is None for elem in cb_results):
      cb_results = pd.concat(cb_results, ignore_index = True)

    else:
      cb_results = pd.DataFrame()

    return cb_results


#This function loops through the strategies and creates a cost benefit definition table
#uniqe to each strategy based on the componetn transformations
#It then calls a support function to loop through the strategy definition
def cb_calculate_transformation_costs(
                                      data : pd.DataFrame, # SSP data output
                                      strategy_cost_definitions_param : pd.DataFrame, #tells us which strategies to evaluate costs and benefit sfor
                                      strategy_definitions_table : pd.DataFrame, #This file tells us which transformation in is in each strategy
                                      tx_definitions_table : pd.DataFrame , # defines how each transformation is evaluated, including difference variables, cost multipliers, etc.
                                      cb_data : CBFilesReader, # data container
                                      list_of_variables : List[str],
                                      SSP_GLOBAL_list_of_strategies : List[str],
                                    ) -> pd.DataFrame:

  #cut the list of strategies to evaluate to those that are marked to be evaluated, and that are in the data
  strategy_cost_definitions = strategy_cost_definitions_param.copy()
  strategy_cost_definitions = strategy_cost_definitions[(strategy_cost_definitions["evaluate_transformation_costs"] == 1) & (strategy_cost_definitions["strategy_code"].isin(SSP_GLOBAL_list_of_strategies))]

  strategy_code_comparison_mapping  = strategy_cost_definitions[["strategy_code", "comparison_code"]].to_records(index = False)

  #For each strategy, create a set of instructions for calculating transformation-specific costs and benefits
  #based on the (a) strategy to transformation mapping and (b) transformation cost table
  #call the instructions and append them to the list.
  #Note: it is possible we could speed this up by creating a list of all instructions and then running the code once
  #And, the function that calls cb_wrapper could probably be integrated into this function

  results = []
  log_tx_missings_in_strat = []

  strategy_definitions_table = strategy_definitions_table.set_index("strategy_code")

  for strategy_code,comparison_code in strategy_code_comparison_mapping:

    strategy_definition = strategy_definitions_table.loc[strategy_code]
    strategy_definition = strategy_definition[strategy_definition !=0]

    transformations_list = list(strategy_definition.index)

    #update the strategy codes in the definition file
    strategy_cb_table = tx_definitions_table[tx_definitions_table["transformation_code"].isin(transformations_list)]
    strategy_cb_table = strategy_cb_table.replace(np.nan, 0.0)

    #------Just a debug section------
    print(f"The following transformations are in strategy: {strategy_code}")
    print('\n'.join('{}: {}'.format(*k) for k in enumerate(transformations_list)))

    if not strategy_cb_table.empty:
      strategy_cb_table["strategy_code"] = strategy_code
      strategy_cb_table["test_id"] = strategy_code
      strategy_cb_table["comparison_id"] = comparison_code
      strategy_cb_table["comparison_id"] = comparison_code
      strategy_cb_table["strategy_cb_table"] = comparison_code

      
      results.append(
            cb_calculate_transformation_costs_in_strategy(data, strategy_cb_table, cb_data, list_of_variables, SSP_GLOBAL_list_of_strategies)
      )
    else:
      for tx_missing in transformations_list:
        log_tx_missings_in_strat.append([strategy_code, tx_missing, "MISSING"])

    if not strategy_cb_table.empty:
          
      for tx_missing in transformations_list:
        log_tx_missings_in_strat.append([strategy_code, tx_missing, "NO-MISSING"])

  results = pd.concat(results, ignore_index = True)
  log_tx_missings_in_strat = pd.DataFrame(log_tx_missings_in_strat, columns = ["strategy_code", "tx", "status"]).query("tx!='TX:LNDU:PLUR'")

  return results,log_tx_missings_in_strat


#This function loops through a strategy-specific cost benefit definition created by the 
#cb_calculate_transformation_costs function and calls cb_wrapper on each and returns the results
def cb_calculate_transformation_costs_in_strategy(
                                                  data : pd.DataFrame, 
                                                  strategy_specific_definitions_param : pd.DataFrame,
                                                  cb_data : CBFilesReader, # data container
                                                  list_of_variables : List[str],
                                                  SSP_GLOBAL_list_of_strategies : List[str],
                                                ) -> pd.DataFrame:
    
    #cut the list of strategies to evaluate to those that are marked to be evaluated, and that are in the data
    strategy_specific_definitions = strategy_specific_definitions_param.copy()
    strategy_specific_definitions = strategy_specific_definitions[(strategy_specific_definitions["include"] == 1) & (strategy_specific_definitions["strategy_code"].isin(SSP_GLOBAL_list_of_strategies))]
    strategy_specific_definitions = strategy_specific_definitions.reset_index(drop = True)

    strategy_specific_code_comparison_mapping  = strategy_specific_definitions[["strategy_code", "test_id", "comparison_id", "output_variable_name"]].to_records(index = False)

    for strategy_code, test_id, comparison_id,output_variable_name in strategy_specific_code_comparison_mapping:
      print(f"Evaluating transformation costs for {strategy_code} which is {test_id} vs. {comparison_id} for {output_variable_name}")

    results = []

    nstrat = strategy_specific_definitions.shape[0]

    for id_strat in range(nstrat):
      args_container = strategy_specific_definitions.iloc[[id_strat]].to_dict()
      args_container = {i:j[id_strat] for i,j in args_container.items()}

      print(f"============Evaluating transformation costs for {args_container['strategy_code']}-{args_container['output_variable_name']}")
      args_container["data"] = data
      args_container["list_of_variables_in_dataset"] = list_of_variables
      args_container["annual change"] = args_container['annual.change']
      args_container["cb_data"] = cb_data
      args_container["comparison_code"] = args_container["comparison_id"]
      args_container["output_vars"] = args_container["output_variable_name"]

      cb_function = args_container["cb_function"]

      #print(f"Usaremos la función específica a la estrategia {mapping_strategy_specific_functions[cb_function]}")
      print(f"Usaremos la función específica a la estrategia {cb_function}")
      ctcs_resultado = mapping_strategy_specific_functions[cb_function](args_container)
      
      results.append(
        ctcs_resultado
      )

    results = pd.concat(results, ignore_index = True)

    return results


def cb_process_interactions(res : pd.DataFrame,
                            st2tx : pd.DataFrame, 
                            pp_instructions : pd.DataFrame
                            ) -> pd.DataFrame:
    

    interactions = pp_instructions.copy()

    #get the list of interactions
    list_of_interactions = interactions["interaction_name"].unique()

    #get the strategies in the results file
    strategies = res["strategy_code"].unique()

    for strategy_code in strategies:
        #get the list of transformations
        strategy_definition = st2tx.query(f"strategy_code=='{strategy_code}'").reset_index(drop = True).iloc[0]
        
        #update the strategy codes in the definition file
        tx_in_strategy = strategy_definition[strategy_definition==1].index.to_list()

        #for each interaction
        for interaction in list_of_interactions:
            #transformations that interact
            tx_interacting = interactions.query(f"interaction_name=='{interaction}'")
            tx_in_interaction = tx_interacting["transformation_code"].unique()
            tx_in_both = list(set(tx_in_interaction).intersection(tx_in_strategy))

            #only count the transfomrations actully in the strategy
            tx_interacting = tx_interacting[tx_interacting["transformation_code"].isin(tx_in_both)]

            if SSP_PRINT_STRATEGIES: 
                print(f"Resolving Interactions in {interaction} : {', '.join(tx_interacting['transformation_code'].to_list())} ")

            if tx_interacting.shape[0] == 0:
                if SSP_PRINT_STRATEGIES:
                    print(f"No interactions, skipping... {strategy_code}")
                    continue

            # Rescale
            tx_rescale = tx_interacting.groupby("transformation_code")\
                                        .agg({"relative_effect" : "mean"})\
                                        .reset_index()\
                                        .rename(columns = {"relative_effect":"original_scalar"})
            
            new_sum = tx_rescale["original_scalar"].sum()
            tx_rescale["newscalar"] = tx_rescale["original_scalar"]/new_sum

            #update the original scalars in the intracting tx
            tx_interacting = tx_interacting.merge(right=tx_rescale, on = "transformation_code")
            tx_interacting["strategy_code"] = strategy_code

            #apply these scalars to the data
            res_subset = res[(res["strategy_code"] == strategy_code) & (res["variable"].isin(tx_interacting["variable"]))]
            res_subset = res_subset.merge(right=tx_interacting, on = ["strategy_code", "variable"], suffixes=['', '.int'])
            res_subset.loc[res_subset["scale_variable"]==0.0, "newscalar"] = 1.0

            res_subset["value"] = res_subset["value"] * res_subset["newscalar"]
            res_subset["difference_value"] = res_subset["difference_value"] * res_subset["newscalar"]

            #make a replacement dataset
            res_for_replacement = res_subset[SSP_GLOBAL_COLNAMES_OF_RESULTS]

            #remove the other rows from the dataset
            res = res[~((res["strategy_code"] == strategy_code) & (res["variable"].isin(tx_interacting["variable"])))]

            res = pd.concat([res, res_for_replacement], ignore_index = True)

    return res
