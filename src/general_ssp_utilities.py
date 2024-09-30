import pandas as pd 

def ssp_merge_run_attributes(primary_filename : str, 
                            attribute_filename : str) -> pd.DataFrame:

  primary_attributes = pd.read_csv(primary_filename)
  strategy_attributes = pd.read_csv(attribute_filename)

  merged_attributes = primary_attributes.merge(right = strategy_attributes, on = "strategy_id")
  
  return merged_attributes
