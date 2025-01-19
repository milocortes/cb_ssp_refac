import functools
import pandas as pd
import re 

def cb_wrapper(func): 
    @functools.wraps(func)
    def wrapper_decorator(self,cb_orm):
        
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
            result = func(self, cb_orm)
            result_tmp.append(result)

        # If flagged, sum up the variables in value and difference_value columns
        #Create a new output data frame and append it to the existing list
        #Note that the difference variable may be garbage if we are summing across different comparison variables

        if cb_orm.sum == 1:          
          result_tmp = pd.concat(result_tmp, ignore_index = True)
          results_summarized = result_tmp.groupby(["region", "time_period", "strategy_code", "future_id"]).agg({"value" : "sum", "difference_value" : "sum"}).reset_index()
          results_summarized["difference_variable"] = cb_orm.diff_var
          results_summarized["variable"] = cb_orm.output_variable_name

          return results_summarized.sort_values(["difference_variable", "time_period"])
          
        else:
          appended_results = pd.concat(result_tmp, ignore_index = True)
          return appended_results.sort_values(["difference_variable", "time_period"])

    return wrapper_decorator 


