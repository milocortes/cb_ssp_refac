import pandas as pd 

#------------------1. Loop Through Cost Definitions -------
#This function loops through the strategies and applies system costs 
#which are defined in the cost factors
def cb_calculate_system_costs(data : pd.DataFrame, # SSP data output
                              strategy_cost_definitions_param : pd.DataFrame, # tells us which strategies to evaluate costs and benefit iffor 
                              system_cost_definitions : pd.DataFrame, # the list of all the cost factor files in the system, and the functions they should be evaluated with
                              cb_data : CBFilesReader, # data container
                              ) -> pd.DataFrame:
    
    # Get list of all variables in the SSP data output
    list_of_variables = SSP_GLOBAL_list_of_variables

    #cut the list of strategies to evaluate to those that are marked to be evaluated, and that are in the data
    strategy_cost_definitions = strategy_cost_definitions_param.copy()
    strategy_cost_definitions = strategy_cost_definitions[strategy_cost_definitions["evaluate_system_costs"] == 1 
                                    & strategy_cost_definitions["strategy_code"].isin(SSP_GLOBAL_list_of_strategies)]
    
    
    #cut the list of system cost definitions to those that are marked to be evaluated
    system_cost_definitions = system_cost_definitions[system_cost_definitions["include"]==1]    
    cost_factor_defined_mapping = {system_cost.split(".")[0] : cb_function for system_cost,cb_function in system_cost_definitions[["system_cost_filename", "cb_function"]].to_records(index = False)}

    # Obtenemos el diccionario de los factores de costos
    cost_factors_mapping = {system_cost : (system_cost_data, cost_factor_defined_mapping[system_cost]) for system_cost,system_cost_data in cb_data.CostFactorCBFile.items() if system_cost in cost_factor_defined_mapping}

    # Lista que va a acumular los resultados de cada ejecución
    results = []

    for strategy_code,comparison_code in strategy_cost_definitions[["strategy_code", "comparison_code"]].to_records(index = False):
        if SSP_PRINT_STRATEGIES:
            # AQUÍ PONDREMOS UN MESSAGE
            print(f'============Evaluating system costs for {strategy_code} =================')

        for cost_factor, (cost_factor_data, cost_factor_function) in cost_factors_mapping.items():
            # AQUÍ PONDREMOS OTRO MESSAGE
            print(f"Cost Factor Loop: {strategy_code} vs {comparison_code} for cost factor {cost_factor} and cost factor function {cost_factor_function}")

    """
      do_call_args<-list(data, strategy_cost_definitions[d,], data.frame(cost_factors_list[c]), list_of_variables)
      r<-do.call(system_cost_definitions$cb_function[c], do_call_args)
      results<-append(results, list(r))

  
    #append all the outputs
    cb_results<-do.call("rbind", results)
  
    #boom. done.
    return(cb_results)
    """


