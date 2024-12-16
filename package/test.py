from costs_benefits_ssp.cb_calculate import CostBenefits
import pandas as pd 

ssp_data = pd.read_csv("/home/milo/Documents/egtp/SISEPUEDE/CB/cb_ssp_refac/data/ssp_model_results/iran_tornado/iran.csv")
att_primary = pd.read_csv("/home/milo/Documents/egtp/SISEPUEDE/CB/cb_ssp_refac/data/ssp_model_results/iran_tornado/ATTRIBUTE_PRIMARY.csv")
att_strategy = pd.read_csv("/home/milo/Documents/egtp/SISEPUEDE/CB/cb_ssp_refac/data/ssp_model_results/iran_tornado/ATTRIBUTE_STRATEGY.csv")


cb = CostBenefits(ssp_data, att_primary, att_strategy)
cb.compute_cost_benefit_from_variable("cb:scoe:technical_cost:efficiency:appliance")
