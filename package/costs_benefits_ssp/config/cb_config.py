#set globally the variables for analaysis
#SSP_GLOBAL_COLNAMES_OF_RESULTS = ['strategy_code', 'future_id', 'region', 'time_period', 'difference_variable', 'difference_value', 'variable', 'value']
SSP_GLOBAL_COLNAMES_OF_RESULTS = ['strategy_code', 'future_id', 'region', 'time_period', 'difference_variable', 'variable_value_baseline', 'variable_value_pathway', 'difference_value', 'variable', 'value']
SSP_GLOBAL_SIMULATION_IDENTIFIERS = ['primary_id', 'strategy_code', 'region', 'time_period', 'future_id']
SSP_GLOBAL_SIMULATION_LONG_COLS = ['primary_id', 'strategy_code', 'region', 'time_period', 'variable', 'value']

SSP_GLOBAL_TIME_PERIOD_0 = 2015
SSP_GLOBAL_TIME_PERIOD_TX_START = 10 #11
SSP_GLOBAL_TIME_PERIODS = 36
SSP_GLOBAL_TIME_PERIOD_2023 = 8 #9
SSP_GLOBAL_COST_YEAR = 4 #cost everything to 2019

SSP_GLOBAL_CCS_CAPTURE_RATE = 0.9

#set globally the variables for output
#0 -- no printing out
#1 -- only transformation names
#2 -- + cost factor or top line variable names
#3 -- + all variables
SSP_PRINT_STRATEGIES = True
SSP_PRINT_TOP_LINE_VARS = True
SSP_PRINT_DETAILED_VARS = True
SSP_PRINT_COST_FACTOR_FILENAMES = True

#Print to a log all the variables searched for
SSP_GLOBAL_LOG_VARIABLE_SEARCH = True
SSP_GLOBAL_LOG_OF_SEARCHED_VARS = []

SSP_GLOBAL_OUTPUT_NAME_CONVENTION = ["prefix",	"sector",	"cost_type",	"specification",	"sub_specification"]
