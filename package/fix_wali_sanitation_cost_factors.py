from costs_benefits_ssp.model.cb_data_model import (AgrcLVSTProductivityCostGDP,AgrcRiceMGMTTX,ENTCReduceLosses,
                                                    IPPUCCSCostFactor,IPPUFgasDesignation,LNDUSoilCarbonFraction,
                                                    LVSTEntericFermentationTX,LVSTTLUConversion,PFLOTransitionNewDiets,
                                                    WALISanitationClassificationSP)


#Calculate the number of people in each sanitation pathway by merging the data with the sanitation classification
#and with the population data and keepign onyl rows where the population_variable matches the variable.pop
#then multiply the fraction by the population
#There was concern that we need to account for differences in ww production between urban and rural
#But we don't since the pathway fractions for them are mutually exclusive! Hooray!

sanitation_classification = pd.read_sql(cb.session.query(WALISanitationClassificationSP).statement, cb.session.bind)

data = ssp_data.merge(right=att_primary, on = "primary_id").merge(att_strategy, on = "strategy_id")


all_tx_on_ssp_data = list(data.strategy_code.unique())
all_tx_on_ssp_data.remove(cb.strategy_code_base)


data_strategy = cb.cb_get_data_from_wide_to_long(data, all_tx_on_ssp_data, sanitation_classification["variable"].to_list())
data_strategy = data_strategy.merge(right = sanitation_classification, on='variable')


population = cb.cb_get_data_from_wide_to_long(data, all_tx_on_ssp_data, ['population_gnrl_rural', 'population_gnrl_urban'])
population = population.rename(columns = {"variable" : "population_variable"})


data_strategy = data_strategy.merge(right = population[ ["strategy_code", "region", "time_period", "future_id", "population_variable", "value"]], on = ["strategy_code", "region", "time_period", "future_id", "population_variable"], suffixes = ["", ".pop"])
data_strategy = data_strategy[data_strategy["population_variable"].isin(data_strategy["population_variable"])].reset_index(drop=True)
data_strategy["pop_in_pathway"] = data_strategy["value"]*data_strategy["value.pop"]


#Do the same thing with the baseline strategy
data_base = cb.cb_get_data_from_wide_to_long(data, cb.strategy_code_base, sanitation_classification["variable"].to_list())
data_base = data_base.merge(right = sanitation_classification, on = 'variable')


population_base = cb.cb_get_data_from_wide_to_long(data, cb.strategy_code_base, ['population_gnrl_rural', 'population_gnrl_urban'])
population_base = population_base.rename(columns = {"variable" : "population_variable"})

data_base = data_base.merge(right = population_base[['region', 'time_period', 'future_id', "population_variable", "value"]], on = ['region', 'time_period', 'future_id', "population_variable"], suffixes = ["", ".pop"])

data_base = data_base[data_base["population_variable"].isin(data_base["population_variable"])].reset_index(drop = True)
data_base["pop_in_pathway"] = data_base["value"]*data_base["value.pop"]


data_strategy.merge(right=data_base[['region', 'time_period', 'future_id', 'pop_in_pathway']],  on = ['region', 'time_period', 'future_id'], suffixes = ["", "_base_strat"])



data_new = pd.concat([data_strategy, data_base], ignore_index = True)

#reduce it by the sanitation category

gp_vars = ["primary_id", "region", "time_period", "strategy_code", "future_id", "difference_variable"]

data_new_summarized = data_new.groupby(gp_vars).agg({"pop_in_pathway" : "sum"}).rename(columns = {"pop_in_pathway" : "value"}).reset_index()
data_new_summarized = data_new_summarized.rename(columns = {"difference_variable" : "variable"})

new_list_of_variables = data_new_summarized["variable"].unique()  

pivot_index_vars = [i for i in data_new_summarized.columns if i not in ["variable", "value"]]
data_new_summarized_wide = data_new_summarized.pivot(index = pivot_index_vars, columns="variable", values="value").reset_index()  


base_wali = data_new_summarized_wide.query("strategy_code=='BASE'").set_index(['primary_id', 'region', 'time_period', 'strategy_code', 'future_id']).mean()

tx_wali = data_new_summarized_wide.query("strategy_code!='BASE'").set_index(['primary_id', 'region', 'time_period', 'strategy_code', 'future_id']).mean()

(base_wali - tx_wali).astype(int)
