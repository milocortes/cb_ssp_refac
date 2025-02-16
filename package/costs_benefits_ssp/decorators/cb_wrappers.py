import functools
import pandas as pd
import re 
from typing import Union,Dict

def cb_wrapper(func): 
    @functools.wraps(func)
    def wrapper_decorator(self,
                          cb_orm = None,
                          cb_var_name : Union[str, None] = None,
                          strategy_code_tx : Union[str, None] = None,
                          data_baseline : Union[pd.DataFrame, None] = None,
                          data_tx :  Union[pd.DataFrame, None] = None,
                          cb_var_fields : Union[Dict[str, Union[float,int,str]], None] = None   
                          ):
        
        if cb_var_name:
          ## Obteniendo registro de la db
          cb_orm = self.get_cb_var_fields(cb_var_name)

          ## Agregamos como atributo la estrategia a comparar
          if strategy_code_tx : cb_orm.strategy_code_tx = strategy_code_tx

          cb_orm.strategy_code_base = self.strategy_code_base

          print("---------Costs for: {cb_orm.output_variable_name}.".format(cb_orm=cb_orm))

          if cb_orm.tx_table.cost_type == "system_cost":
              print("La variable se evalúa en System Cost")

              if cb_orm.cb_var_group == 'wali_sanitation_cost_factors' or cb_orm.cb_var_group == 'wali_benefit_of_sanitation_cost_factors':
                cb_orm.cb_function = 'cb_difference_between_two_strategies'
              
              if cb_orm.cb_function=="cb:enfu:fuel_cost:X:X":

                cb_orm.cb_function = 'cb_difference_between_two_strategies'
              

          elif cb_orm.tx_table.cost_type == "transformation_cost":
              
              print("La variable se evalúa en Transformation Cost")
              
              if not(self.tx_in_strategy(cb_orm.transformation_code, cb_orm.strategy_code_tx)):

                print("La TX no se encuentra en la estrategia")
                return pd.DataFrame()

        ## Actualizamos los campos del registro si recibimos el diccionario cb_var_fields
        if isinstance(cb_var_fields, dict):
            self.update_cost_factor_register(cb_var_name = cb_var_name, 
                                        cb_var_fields = cb_var_fields)

        ## Get all variable matches on difference_variable
        diff_var = cb_orm.difference_variable.replace("*", ".*")
        diff_var_list = [string for string in self.ssp_list_of_vars if  re.match(re.compile(diff_var), string)]

        if not diff_var_list:
          print(f'ERROR IN CB_WRAPPER: No variables match : {diff_var}')
          return None 
         
        # For each variable that matches the substring, calculate the costs and benefits and acumulate the results
        result_tmp = []

        for diff_var_param in diff_var_list:
            cb_orm.diff_var = diff_var_param
            
            if isinstance(data_baseline, pd.DataFrame) and isinstance(data_tx, pd.DataFrame):
              result = func(self, cb_orm = cb_orm, data_baseline = data_baseline, data_tx = data_tx)
            else: 
              result = func(self, cb_orm = cb_orm)
            result_tmp.append(result)

        # If flagged, sum up the variables in value and difference_value columns
        #Create a new output data frame and append it to the existing list
        #Note that the difference variable may be garbage if we are summing across different comparison variables

        if cb_orm.sum == 1:          
          result_tmp = pd.concat(result_tmp, ignore_index = True)
          llaves_gb = ["region", "time_period", "strategy_code", "future_id"]

          results_summarized = result_tmp.groupby(llaves_gb).agg({"value" : "sum", 
                                                                  "difference_value" : "sum",
                                                                  "variable_value_baseline" : "sum",
                                                                  "variable_value_pathway" : "sum"}).reset_index()
                                                                  
          results_summarized["difference_variable"] = cb_orm.diff_var
          results_summarized["variable"] = cb_orm.output_variable_name

          return results_summarized.sort_values(["difference_variable", "time_period"])
          
        else:
          if not all(elem is None for elem in result_tmp):
            appended_results = pd.concat(result_tmp, ignore_index = True)
            return appended_results.sort_values(["difference_variable", "time_period"])
          else:
            return None

    return wrapper_decorator 


