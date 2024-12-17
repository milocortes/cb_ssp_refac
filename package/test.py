from costs_benefits_ssp.cb_calculate import CostBenefits
import pandas as pd 
import os 

SSP_RESULTS_PATH = "/home/milo/Documents/egtp/SISEPUEDE/COST_BENEFITS/refactorizacion/remote/cb_ssp_refac/package"

ssp_data = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "iran.csv"))
att_primary = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "ATTRIBUTE_PRIMARY.csv"))
att_strategy = pd.read_csv(os.path.join(SSP_RESULTS_PATH, "ATTRIBUTE_STRATEGY.csv"))


cb = CostBenefits(ssp_data, att_primary, att_strategy)

cb.compute_cost_benefit_from_variable("cb:trns:air_pollution:X:diesel", 'TORNADO:AGRC:DEC_CH4_RICE', 'BASE')
cb.compute_cost_benefit_from_variable("cb:inen:technical_cost:fuel_switch:lo_heat", 'TORNADO:INEN:SHIFT_FUEL_HEAT', 'BASE')
cb.compute_cost_benefit_from_variable("cb:trns:technical_cost:fuel_switch:maritime", 'TORNADO:TRNS:SHIFT_FUEL_MARITIME', 'BASE')
cb.compute_cost_benefit_from_variable('cb:trns:technical_cost:efficiency:non_electric', 'TORNADO:TRNS:INC_EFFICIENCY_NON_ELECTRIC', 'BASE')
cb.compute_cost_benefit_from_variable('cb:entc:technical_cost:loss_reduction:electricity', 'TORNADO:ENTC:DEC_LOSSES', 'BASE')
cb.compute_cost_benefit_from_variable('cb:ippu:technical_savings:clinker:X', 'TORNADO:IPPU:DEC_CLINKER', 'BASE')
#cb.compute_cost_benefit_from_variable('cb:ippu:technical_cost:abating_N2O_and_F_Gases:X', 'TORNADO:IPPU:BUNDLE_DEC_FGAS', 'BASE')
cb.compute_cost_benefit_from_variable('cb:fgtv:technical_cost:flaring:X', 'TORNADO:FGTV:INC_FLARE', 'BASE')
cb.compute_cost_benefit_from_variable('cb:waso:technical_cost:consumer_food_waste:X', 'TORNADO:WASO:DEC_CONSUMER_FOOD_WASTE_HIGHEST', 'BASE')
cb.compute_cost_benefit_from_variable('cb:lvst:technical_cost:ent_ferm_mgmt:X', 'TORNADO:LVST:DEC_ENTERIC_FERMENTATION', 'BASE')
cb.compute_cost_benefit_from_variable('cb:agrc:technical_cost:rice_mgmt:X', 'TORNADO:AGRC:DEC_CH4_RICE', 'BASE')
cb.compute_cost_benefit_from_variable('cb:agrc:technical_cost:increase_productivity:X', 'TORNADO:AGRC:INC_PRODUCTIVITY', 'BASE')
cb.compute_cost_benefit_from_variable('cb:pflo:human_health:better_diets:X', 'TORNADO:PFLO:INC_HEALTHIER_DIETS', 'BASE')
cb.compute_cost_benefit_from_variable('cb:ippu:technical_cost:industrial_ccs:X', 'TORNADO:PFLO:INC_IND_CCS', 'BASE')
cb.compute_cost_benefit_from_variable('cb:lsmm:technical_cost:manure_management', 'TORNADO:LSMM:INC_MANAGEMENT_CATTLE_PIGS', 'BASE')




{'cb:inen:technical_cost:fuel_switch:lo_heat': ('TX:INEN:SHIFT_FUEL_HEAT','cb_difference_between_two_strategies'),
 'cb:trns:technical_cost:fuel_switch:maritime': ('TX:TRNS:SHIFT_FUEL_MARITIME','cb_scale_variable_in_strategy'),
 'cb:trns:technical_cost:efficiency:non_electric': ('TX:TRNS:INC_EFFICIENCY_NON_ELECTRIC','cb_fraction_change'),
 'cb:entc:technical_cost:loss_reduction:electricity': ('TX:ENTC:DEC_LOSSES','cb_entc_reduce_losses'),
 'cb:ippu:technical_savings:clinker:X': ('TX:IPPU:DEC_CLINKER','cb_ippu_clinker'),
 'cb:ippu:technical_cost:abating_N2O_and_F_Gases:X': ('TX:IPPU:BUNDLE_DEC_FGAS','cb_ippu_florinated_gases'),
 'cb:fgtv:technical_cost:flaring:X': ('TX:FGTV:INC_FLARE','cb_fgtv_abatement_costs'),
 'cb:waso:technical_cost:consumer_food_waste:X': ('TX:WASO:DEC_CONSUMER_FOOD_WASTE','cb_waso_reduce_consumer_facing_food_waste'),
 'cb:lvst:technical_cost:ent_ferm_mgmt:X': ('TX:LVST:DEC_ENTERIC_FERMENTATION','cb_lvst_enteric'),
 'cb:agrc:technical_cost:rice_mgmt:X': ('TX:AGRC:DEC_CH4_RICE','cb_agrc_rice_mgmt'),
 'cb:agrc:technical_cost:increase_productivity:X': ('TX:AGRC:INC_PRODUCTIVITY','cb_agrc_lvst_productivity'),
 'cb:pflo:human_health:better_diets:X': ('TX:PFLO:INC_HEALTHIER_DIETS','cb_pflo_healthier_diets'),
 'cb:ippu:technical_cost:industrial_ccs:X': ('TX:PFLO:INC_IND_CCS','cb_ippu_inen_ccs'),
 'cb:lsmm:technical_cost:manure_management': ('TX:LSMM:INC_MANAGEMENT_CATTLE_PIGS','cb_manure_management_cost')}

#cb.compute_cost_benefit_from_variable("cb:scoe:technical_cost:efficiency:appliance")

