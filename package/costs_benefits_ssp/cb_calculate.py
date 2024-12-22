from typing import List, Union, Dict, Callable
from sqlalchemy.orm import Session
import pandas as pd 
#import polars as pl 

import warnings

import logging

import numpy as np 
import re

import os 

from multiprocessing import Pool

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import load_only
from sqlalchemy.orm import declarative_base

from costs_benefits_ssp.utils.utils import build_path,get_tx_prefix
from costs_benefits_ssp.model.cb_data_model import TXTable,CostFactor,TransformationCost,StrategyInteraction
from costs_benefits_ssp.decorators.cb_wrappers import cb_wrapper 
from costs_benefits_ssp.config.cb_config import * 

from costs_benefits_ssp.model.cb_data_model import CountriesISO,AttDimTimePeriod,AttTransformationCode

from costs_benefits_ssp.model.cb_data_model import (AgrcLVSTProductivityCostGDP,AgrcRiceMGMTTX,ENTCReduceLosses,
                                                    IPPUCCSCostFactor,IPPUFgasDesignation,LNDUSoilCarbonFraction,
                                                    LVSTEntericFermentationTX,LVSTTLUConversion,PFLOTransitionNewDiets,
                                                    WALISanitationClassificationSP)

from costs_benefits_ssp.model.cb_update_data_model import update_db_schema

class CostBenefits:
    """
    Clase que carga los archivos definidos en los Enum.

    Argumentos de inicialización
    -----------------------------

    - data_file_path : directorio donde se encuentran los datos a cargar
    
    
    Argumentos opcionales
    -----------------------------
    - logger : objeto logger opcional para dar seguimiento a los eventos de lectura de archivos

    """
    def __init__(self, 
                 ssp_data : pd.DataFrame,
                 att_primary : pd.DataFrame,
                 att_strategy : pd.DataFrame,
                 strategy_code_base : str,
                 logger: Union[logging.Logger, None] = None
                 ) -> None:

        self.session = self.initialize_session()
        self.strategy_to_txs : Dict[str, List[str]] = self.get_strategy_to_txs(att_strategy)
        self.att_strategy = att_strategy
        self.strategy_code_base = strategy_code_base
        self.ssp_data = self.marge_attribute_strategy(ssp_data, att_primary, att_strategy)
        self.ssp_list_of_vars = list(self.ssp_data) 
        self.ssp_data = self.add_additional_columns()
        self.ssp_list_of_vars = list(self.ssp_data) 
        #self.pl_ssp_data = pl.from_pandas(self.ssp_data)


    ##############################################
	#------ METODOS DE INICIALIZACION	   ------#
	##############################################

    def marge_attribute_strategy(
                 self,
                 ssp_data : pd.DataFrame,
                 att_primary : pd.DataFrame,
                 att_strategy : pd.DataFrame,      
                ) -> pd.DataFrame:
        
        merged_attributes = att_primary.merge(right = att_strategy, on = "strategy_id")
        return merged_attributes[['primary_id', 'strategy_code', 'future_id']].merge(right = ssp_data, on='primary_id')

        

    def initialize_session(
                self
                ) -> Session:
        
        FILE_PATH = os.path.dirname(os.path.abspath(__file__))
        DB_FILE_PATH = build_path([FILE_PATH, "database", "cb_data.db"])

        engine = create_engine(f"sqlite:///{DB_FILE_PATH}")
        Session = sessionmaker(bind=engine)

        return Session()


    def get_strategy_to_txs(
                self,
                att_strategy : pd.DataFrame,
        ) -> Dict[str, List[str]]:

        # Obtenemos lista de transformaciones de SSP
        ssp_txs = [i.transformation_code for i in self.session.query(AttTransformationCode).all()]

        original_strategy_to_txs = att_strategy[["strategy_code", "transformation_specification"]].to_records(index = False)
        
        strategy_to_txs = {strategy : [get_tx_prefix(transformation, ssp_txs) for transformation in transformations.split("|")] 
        for strategy,transformations in original_strategy_to_txs}

        return strategy_to_txs

    def add_additional_columns(
                self,
                ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #add calculation of total TLUs to data
        tlu_conversions = pd.read_sql(self.session.query(LVSTTLUConversion).statement, self.session.bind)


        pop_livestock = data[SSP_GLOBAL_SIMULATION_IDENTIFIERS + [i for i in self.ssp_list_of_vars if "pop_lvst" in i]]
        pop_livestock = pop_livestock.melt(id_vars=['primary_id', 'time_period', 'region', 'strategy_code', 'future_id'])
        pop_livestock = pop_livestock.merge(right=tlu_conversions, on = "variable")

        pop_livestock["total_tlu"] = pop_livestock["value"] * pop_livestock["tlu"]

        pop_livestock_summarized = pop_livestock.groupby(SSP_GLOBAL_SIMULATION_IDENTIFIERS).\
                                                    agg({"total_tlu" : sum}).\
                                                    rename(columns={"total_tlu":"lvst_total_tlu"}).\
                                                    reset_index()

        data = data.merge(right = pop_livestock_summarized, on = SSP_GLOBAL_SIMULATION_IDENTIFIERS)

       
        #Calculate the number of people in each sanitation pathway by merging the data with the sanitation classification
        #and with the population data and keepign onyl rows where the population_variable matches the variable.pop
        #then multiply the fraction by the population
        #There was concern that we need to account for differences in ww production between urban and rural
        #But we don't since the pathway fractions for them are mutually exclusive! Hooray!

        sanitation_classification = pd.read_sql(self.session.query(WALISanitationClassificationSP).statement, self.session.bind)

        all_tx_on_ssp_data = list(data.strategy_code.unique())
        all_tx_on_ssp_data.remove(self.strategy_code_base)

        data_strategy = self.cb_get_data_from_wide_to_long(data, all_tx_on_ssp_data, sanitation_classification["variable"].to_list())
        data_strategy = data_strategy.merge(right = sanitation_classification, on='variable')


        population = self.cb_get_data_from_wide_to_long(data, all_tx_on_ssp_data, ['population_gnrl_rural', 'population_gnrl_urban'])
        data_strategy = data_strategy.merge(right = population, on = ['region', 'time_period', 'future_id'], suffixes = ["", ".pop"])
        data_strategy = data_strategy[data_strategy["population_variable"].isin(data_strategy["variable.pop"])].reset_index()
        data_strategy["pop_in_pathway"] = data_strategy["value"]*data_strategy["value.pop"]


        #Do the same thing with the baseline strategy
        data_base = self.cb_get_data_from_wide_to_long(data, self.strategy_code_base, sanitation_classification["variable"].to_list())
        data_base = data_base.merge(right = sanitation_classification, on = 'variable')

    
        population_base = self.cb_get_data_from_wide_to_long(data, self.strategy_code_base, ['population_gnrl_rural', 'population_gnrl_urban'])
    
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
        
        data = data.merge(right=data_new_summarized_wide, on = ['primary_id', 'region', 'time_period', 'future_id', 'strategy_code'])

        return data

    ##############################################
	#------------- UTILITIES   ------------#
	##############################################


    def tx_in_strategy(
                self,
                tx : str,
                strategy_code : str
        ) -> bool:

        return tx in self.strategy_to_txs[strategy_code]

    #Get a column of data from a wide data table and return it as long for a single strategy
    def cb_get_data_from_wide_to_long(
                self,
                data : pd.DataFrame, 
                strategy_code : List[str], 
                variables : List[str]
        ) -> pd.DataFrame:

        if not isinstance(variables, list):
            variables = [variables]

        if not isinstance(strategy_code, list):
            strategy_code = [strategy_code]

        data_wide = data[data["strategy_code"].isin(strategy_code)][SSP_GLOBAL_SIMULATION_IDENTIFIERS + variables].reset_index(drop = True)
        
        data_long = data_wide.melt(id_vars=SSP_GLOBAL_SIMULATION_IDENTIFIERS)
    

        return data_long  

    def mapping_strategy_specific_functions(
                        self,
                        cb_function : str,
                        cb_orm : Union[TransformationCost, CostFactor]
        ) -> Callable:
        
        match cb_function:
            #case 'cb_lndu_soil_carbon':
            #    return self.cb_lndu_soil_carbon(cb_orm)
            case 'cb_difference_between_two_strategies' | 'cb_apply_cost_factors': 
                return self.cb_difference_between_two_strategies(cb_orm)
            case 'cb_scale_variable_in_strategy' : 
                return self.cb_scale_variable_in_strategy(cb_orm)
            case 'cb_fraction_change' : 
                return self.cb_fraction_change(cb_orm)
            case 'cb_entc_reduce_losses' : 
                return self.cb_entc_reduce_losses(cb_orm)
            case 'cb_ippu_clinker' : 
                return self.cb_ippu_clinker(cb_orm)
            case 'cb_ippu_florinated_gases':
                return self.cb_ippu_florinated_gases(cb_orm)
            case 'cb_fgtv_abatement_costs' : 
                return self.cb_fgtv_abatement_costs(cb_orm)
            case 'cb_waso_reduce_consumer_facing_food_waste' : 
                return self.cb_waso_reduce_consumer_facing_food_waste(cb_orm)
            case 'cb_lvst_enteric' : 
                return self.cb_lvst_enteric(cb_orm)
            case 'cb_agrc_rice_mgmt' : 
                return self.cb_agrc_rice_mgmt(cb_orm)
            case 'cb_agrc_lvst_productivity' : 
                return self.cb_agrc_lvst_productivity(cb_orm)
            case 'cb_pflo_healthier_diets' : 
                return self.cb_pflo_healthier_diets(cb_orm)
            case 'cb_ippu_inen_ccs' : 
                return self.cb_ippu_inen_ccs(cb_orm)
            case 'cb_manure_management_cost' : 
                return self.cb_manure_management_cost(cb_orm)

    def get_all_strategies_on_data(
                        self
        ) -> List[str]:
        
        all_strategies = list(self.ssp_data.strategy_code.unique())
        all_strategies.remove(self.strategy_code_base)

        return all_strategies


    ##############################################
	#------ METHODS	   ------#
	##############################################
    
    def get_cb_var_fields(
                        self,
                        cb_var_name : str,
                        ) -> Union[TransformationCost, CostFactor]:

        # Identificamos qué tipo de factor de costo es
        tx_query = self.session.query(TXTable).filter(TXTable.output_variable_name == cb_var_name).first() 

        if tx_query.cost_type == "system_cost":
            
            return self.session.query(CostFactor).filter(CostFactor.output_variable_name == cb_var_name).first() 
        
        elif tx_query.cost_type == "transformation_cost":
            return self.session.query(TransformationCost).filter(TransformationCost.output_variable_name == cb_var_name).first() 
        

    def compute_cost_benefit_from_variable(
                        self,
                        cb_var_name : str,
                        strategy_code_tx : str,
                        strategy_code_base : Union[str,None] = None,
                        verbose : bool = True,
                        dec_original_multiplier_value : float = 1.0
                        ) -> pd.DataFrame:

        ## Obteniendo registro de la db
        cb_orm = self.get_cb_var_fields(cb_var_name)

        ## Agregamos como atributo la estrategia a comparar
        if strategy_code_tx : cb_orm.strategy_code_tx = strategy_code_tx

        ## Agregamos como atributo la estrategia baseline
        if strategy_code_base : 
            cb_orm.strategy_code_base = strategy_code_base
        else:
            cb_orm.strategy_code_base = self.strategy_code_base 

        if verbose:
            print("---------Costs for: {cb_orm.output_variable_name}.".format(cb_orm=cb_orm))


        if cb_orm.tx_table.cost_type == "system_cost":
            if verbose:
                print("La variable se evalúa en System Cost")
                #print(f"                       {cb_orm.diff_var}")

            
            if cb_orm.cb_var_group == 'wali_sanitation_cost_factors' or cb_orm.cb_var_group == 'wali_benefit_of_sanitation_cost_factors':
                cb_orm.cb_function = 'cb_difference_between_two_strategies'
            
            if cb_orm.cb_function=="cb:enfu:fuel_cost:X:X":
                cb_orm.cb_function = 'cb_difference_between_two_strategies'

            # Actualizamos multiplicador
            cb_orm.multiplier *= dec_original_multiplier_value

            # Aplicamos la función de costo
            df_cb_results_var = self.mapping_strategy_specific_functions(cb_orm.cb_function,cb_orm)
            
            return df_cb_results_var
        elif cb_orm.tx_table.cost_type == "transformation_cost":
            
            print("La variable se evalúa en Transformation Cost")
            
            if self.tx_in_strategy(cb_orm.transformation_code, cb_orm.strategy_code_tx):
                # Actualizamos multiplicador
                cb_orm.multiplier *= dec_original_multiplier_value

                # Aplicamos la función de costo
                df_cb_results_var = self.mapping_strategy_specific_functions(cb_orm.cb_function,cb_orm)
            
                return df_cb_results_var
            else:
                print("La TX no se encuentra en la estrategia")
                return pd.DataFrame()

    ##############################################
	#------ SYSTEM COSTS METHODS	   ------#
	##############################################
    
    def compute_system_cost_for_strategy(
                        self,
                        strategy_code_tx : str,
                        strategy_code_base : Union[str,None] = None,
                        verbose : bool = True
                        ) -> pd.DataFrame:
        ## Get cb variables that will be evaluated on system cost
        system_cost_cb_vars = self.session.query(TXTable).filter(TXTable.cost_type == "system_cost").options(load_only(TXTable.output_variable_name)).all()

        accumulate_system_costs = []

        for cb_var in system_cost_cb_vars:
            accumulate_system_costs.append(
                self.compute_cost_benefit_from_variable(cb_var.output_variable_name, strategy_code_tx, verbose = verbose)
           )

        return pd.concat(accumulate_system_costs, ignore_index = True)
    
    def compute_system_cost_for_all_strategies(
                        self,
                        strategy_code_base : Union[str,None] = None,
                        verbose : bool = True
                        ) -> pd.DataFrame:
        
        all_strategies = self.get_all_strategies_on_data()
        accumulate_system_costs_all_strat = []
        total_strategies = len(all_strategies)

        for id_strat, strategy in enumerate(all_strategies):
            print(f"\n************************************\n*Strategy : {strategy} ({id_strat}/{total_strategies})\n************************************\n")
            accumulate_system_costs_all_strat.append(
                self.compute_system_cost_for_strategy(strategy,verbose = verbose)
            )
        
        return pd.concat(accumulate_system_costs_all_strat, ignore_index = True)

    ##############################################
	#------ TECHNICAL COSTS METHODS	   ------#
	##############################################

    def compute_technical_cost_for_strategy(
                        self,
                        strategy_code_tx : str,
                        strategy_code_base : Union[str,None] = None,
                        verbose : bool = True
                        ) -> pd.DataFrame:
        ## Get cb variables that will be evaluated on system cost
        technical_cost_cb = self.session.query(TransformationCost).all()
        
        ## Get mapping between cb_var by technical cost and transformation 
        cb_tech_cost_mapping_to_tx = pd.read_sql(self.session.query(TransformationCost).statement, self.session.bind) 
        cb_tech_cost_mapping_to_tx = dict(cb_tech_cost_mapping_to_tx[["output_variable_name", "transformation_code"]].to_records(index = False))
        
        ## Get all transformations in technical cost
        all_tx_in_technical_cost = [i.transformation_code for i in technical_cost_cb]

        ## Get transformation inside on strategy_code_tx
        tx_technical_cost_in_strategy = list(set(all_tx_in_technical_cost).intersection(self.strategy_to_txs[strategy_code_tx]))

        if tx_technical_cost_in_strategy:

            accumulate_technical_costs = []

            for cb_var,tx_associated in cb_tech_cost_mapping_to_tx.items():
                if tx_associated in tx_technical_cost_in_strategy:
                    accumulate_technical_costs.append(
                        self.compute_cost_benefit_from_variable(cb_var, strategy_code_tx, verbose = verbose)
                )

            return pd.concat(accumulate_technical_costs, ignore_index = True)
        else:
            print(f"The Strategy {strategy_code_tx} hasn't technical costs")
            return pd.DataFrame()

    def compute_technical_cost_for_all_strategies(
                        self,
                        strategy_code_base : Union[str,None] = None,
                        verbose : bool = True
                        ) -> pd.DataFrame:
        
        all_strategies = self.get_all_strategies_on_data()
        accumulate_technical_costs_all_strat = []
        total_strategies = len(all_strategies)

        for id_strat, strategy in enumerate(all_strategies):
            print(f"\n************************************\n*Strategy : {strategy} ({id_strat}/{total_strategies})\n************************************\n")
            accumulate_technical_costs_all_strat.append(
                self.compute_technical_cost_for_strategy(strategy,verbose = verbose)
            )
        
        return pd.concat(accumulate_technical_costs_all_strat, ignore_index = True)

    ##############################################
	#----- METHOD FOR COMPUTING INTERACTIONS ----#
	##############################################

    def cb_process_interactions(
                        self,
                        res : pd.DataFrame,
        ) -> pd.DataFrame:

        # Get interaction table
        interactions = pd.read_sql(self.session.query(StrategyInteraction).statement, self.session.bind)

        #get the list of interactions
        list_of_interactions = interactions["interaction_name"].unique()

        #get the strategies in the results file
        strategies = res["strategy_code"].unique()


        for strategy_code in strategies:
            # Get transformations in the strategy definition
            tx_in_strategy = self.strategy_to_txs[strategy_code]
            
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

    ##############################################
	#---------- SHIFT COSTS METHOD  -------------#
	##############################################
    
    def cb_shift_costs(
                        self,
                        res : pd.DataFrame,
        ) -> pd.DataFrame:

        #SHIFT any stray costs incurred from 2015 to 2025 to 2025 and 2035
        res_pre2025 = res.query(f"time_period<{SSP_GLOBAL_TIME_PERIOD_TX_START}")#get the subset of early costs
        res_pre2025["variable"] = res_pre2025["variable"] + "_shifted" + (res_pre2025["time_period"]+SSP_GLOBAL_TIME_PERIOD_0).astype(str)#create a new variable so they can be recognized as shifted costs
        res_pre2025["time_period"] = res_pre2025["time_period"]+SSP_GLOBAL_TIME_PERIOD_TX_START #shift the time period

        results_all_pp_shift = pd.concat([res, res_pre2025], ignore_index = True) #paste the results

        results_all_pp_shift.loc[results_all_pp_shift["time_period"]<SSP_GLOBAL_TIME_PERIOD_TX_START,'value'] = 0 #set pre-2025 costs to 0

        return results_all_pp_shift

    ##############################################
	#-- DB EXPORT AND LOAD METHODS   ------------#
	##############################################

    def export_db_to_excel(
                        self,
                        PATH : str = None
        ) -> None:

        list_of_tables = [TXTable,CostFactor,TransformationCost,StrategyInteraction,AgrcLVSTProductivityCostGDP,AgrcRiceMGMTTX,ENTCReduceLosses,
                                                    IPPUCCSCostFactor,IPPUFgasDesignation,LNDUSoilCarbonFraction,
                                                    LVSTEntericFermentationTX,LVSTTLUConversion,PFLOTransitionNewDiets,
                                                    WALISanitationClassificationSP,CountriesISO,AttDimTimePeriod,AttTransformationCode]


        # create a excel writer object
        with pd.ExcelWriter("cb_config_params.xlsx") as writer:

            for tb in list_of_tables:
                #print(tb.__tablename__)
                df = pd.read_sql(self.session.query(tb).statement, self.session.bind) 
                # use to_excel function and specify the sheet_name and index 
                # to store the dataframe in specified sheet
                df.to_excel(writer, sheet_name=tb.__tablename__, index=False)


    def load_cb_parameters_(
        self, 
        FP : str
        ) -> None:
        
        # Test if file exists
        if os.path.isfile(FP):
            print("Cargamos configuración de archivo excel")

            ## Diccionario que mapea los nombres de las pestañas con su respectiva tabla en la base de datos
            cb_model_mapping = {"tx_table" : TXTable,
                                "transformation_costs" : TransformationCost,
                                "strategy_interactions" : StrategyInteraction,
                                "cost_factors" : CostFactor,
                                "countries_by_iso" : CountriesISO,
                                "attribute_dim_time_period" : AttDimTimePeriod,
                                "attribute_transformation_code" : AttTransformationCode,
                                "agrc_lvst_productivity_costgdp" : AgrcLVSTProductivityCostGDP,
                                "agrc_rice_mgmt_tx" : AgrcRiceMGMTTX,
                                "entc_reduce_losses_cost_file" : ENTCReduceLosses,
                                "ippu_ccs_cost_factors" : IPPUCCSCostFactor,
                                "ippu_fgas_designations" : IPPUFgasDesignation,
                                "LNDU_soil_carbon_fractions" : LNDUSoilCarbonFraction,
                                "LVST_enteric_fermentation_tx" : LVSTEntericFermentationTX,
                                "lvst_tlu_conversions" : LVSTTLUConversion,
                                "pflo_transition_to_new_diets" : PFLOTransitionNewDiets,
                                "wali_sanitation_classification" : WALISanitationClassificationSP}

            ## Iniciamos una nueva sesión en el objeto 
            engine = create_engine('sqlite:///:memory:')

            Session = sessionmaker(bind=engine)

            self.session = Session()

            Base = declarative_base()

            update_db_schema(Base)

            Base.metadata.create_all(engine)
            
            ## Poblamod cada tabla con los datos del archivo excel

            for sheet_name,tb_model in cb_model_mapping.items():
                df_tb = pd.read_excel(FP, engine = "openpyxl", sheet_name = sheet_name)
                data_fields = df_tb.columns

                self.session.bulk_save_objects(
                    [tb_model(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in df_tb.to_records(index = False) ]
                )

            print("Se actualizó la base de datos")


        else:
            warnings.warn("El archivo de factores de CB no fue encontrado\nSe usará la configuración default")



    #+++++++++++++++++++++++++++++++++++++++++++++    
    ##############################################
	#------ DECORATED METHODS	  ---------------#
    #------ STRATEGY SPECIFIC FUNCTIONS ---------#
    ##############################################
    #+++++++++++++++++++++++++++++++++++++++++++++


    # ---------------------------------------------
    # ------ CB_DIFFERENCE_BETWEEN_TWO_STRATEGIES
    # ---------------------------------------------

    @cb_wrapper
    def cb_difference_between_two_strategies(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #get the data tables and merge them
        datap_base = data[data["strategy_code"]==cb_orm.strategy_code_base][SSP_GLOBAL_SIMULATION_IDENTIFIERS + [cb_orm.diff_var]].reset_index(drop = True)
        datap_tx   = data[data["strategy_code"]==cb_orm.strategy_code_tx][SSP_GLOBAL_SIMULATION_IDENTIFIERS + [cb_orm.diff_var]].reset_index(drop = True)
        
        datap_base = datap_base.drop(columns=["primary_id", "strategy_code"])

        tx_suffix = '_tx'
        base_suffix = '_base'

        data_merged = datap_tx.merge(right = datap_base, on =  ['region', 'time_period', 'future_id'], suffixes=(tx_suffix, base_suffix))

        #Calculate the difference in variables and then apply the multiplier, which may change over time
        #Assume cost change only begins in 2023

        data_merged["difference_variable"] = cb_orm.diff_var

        data_merged["difference_value"] = data_merged[f"{cb_orm.diff_var}{tx_suffix}"] - data_merged[f"{cb_orm.diff_var}{base_suffix}"]

        data_merged["time_period_for_multiplier_change"] = np.maximum(0, data_merged["time_period"] - SSP_GLOBAL_TIME_PERIOD_2023)

        data_merged["variable"] = cb_orm.output_variable_name

        data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier*cb_orm.annual_change**data_merged["time_period_for_multiplier_change"]

        data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
        
        return data_merged

    # ---------------------------------------------
    # ------ CB_SCALE_VARIABLE_IN_STRATEGY 
    # ---------------------------------------------

    #This function calculates costs and benefits as just a scalar applied to a variable within
    # a single strategy. It uses code from cb_difference_between_two_strategies, so the use of
    # data_merged, for example, is holdover from that function.
    @cb_wrapper
    def cb_scale_variable_in_strategy(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:

        print(f"                       {cb_orm.diff_var}")
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        id_vars  = ['region','time_period', 'strategy_code', 'future_id']
        
        datap_tx = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, cb_orm.diff_var)

        #This is code copied over from another function, so data_merged is just datap_tx
        data_merged = datap_tx.copy()
        data_merged["difference"] = data_merged["value"]
        
        data_merged["time_period_for_multiplier_change"] = np.maximum(0,data_merged["time_period"]-SSP_GLOBAL_TIME_PERIOD_2023)
        data_merged["values"] = data_merged["difference"]*cb_orm.multiplier*cb_orm.annual_change**data_merged["time_period_for_multiplier_change"]  

        tmp = data_merged[id_vars]
        tmp["difference_variable"] = cb_orm.diff_var
        tmp["difference_value"] = data_merged["difference"]
        tmp["variable"] = cb_orm.output_variable_name
        tmp["value"] = data_merged["values"]
        output = tmp.copy()
    
        return output 


    # ---------------------------------------------
    # ------ CB_FRACTION_CHANGE 
    # ---------------------------------------------
    #This function calculates the costs adn benefits as a multiplier applied to the
    #difference in a variable between two strategies, where that difference is
    #defined by some change in a factor, e.g., km/l or tons-waste/person. frac_var
    #gives the name of the variable that has the fraction. Invert tells us whether we
    #need to flip the fractions ot make our calculation correct. If our effect variable
    #is already in the denominator of our fraction (e.g., effect in L, fraction is km/L) then
    #we are good. If the effect variable is in the numerator (e.g., effect in T, fraction is 
    #T/person) then we need to flip it.
    #To be specific, let E_tx be the effect we observe (e.g., L of fuel) in the transformation
    #let f_base and f_tx be the fractions of km/L in the base and transformed futures
    #then the distance that has been traveled in the transformation, d_tx = E_tx*f_tx. 
    #traveling that same distance with the old efficiency would have required 
    #E_base = d_tx/f_base L. So, E_tx-E_base = E_tx - d_tx/f_base = E_tx - Etx*f_tx/f_base
    # = E_tx(1-ftx/f_base)
    @cb_wrapper
    def cb_fraction_change(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:

        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()
        invert = cb_orm.arg2
        frac_var = cb_orm.arg1

        #get teh change in fractions
        fraction_tx = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, frac_var)
        fraction_base = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_base, frac_var)
    
        if invert == 1 :
            fraction_tx["value"] = 1/fraction_tx["value"]
            fraction_base["value"] = 1/fraction_base["value"]
        
        data_merged = fraction_tx.merge(right = fraction_base, on = ['time_period', 'region', 'variable'], suffixes = ['.tx_frac', '.ba_frac'])
        data_merged["fraction_change"] = data_merged["value.tx_frac"]/data_merged["value.ba_frac"]
        data_merged["fraction_multiplier"] = (1-data_merged["fraction_change"])
    

        #get the output results
        output_tx = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, cb_orm.diff_var)
        data_merged = data_merged.merge(right = output_tx, on = ['time_period', 'region'], suffixes=['.tx_frac', '.effect'])
        data_merged = data_merged.rename(columns = {"value" : "effect_value"})
    
        #get the avoided value
        data_merged["difference_variable"] = cb_orm.diff_var
        data_merged["difference_value"] = data_merged["effect_value"]*data_merged["fraction_multiplier"]
        data_merged["variable"] = cb_orm.output_variable_name

        data_merged["time_period_for_multiplier_change"] = np.maximum(0,data_merged["time_period"]-SSP_GLOBAL_TIME_PERIOD_2023)
        data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier*cb_orm.annual_change**data_merged["time_period_for_multiplier_change"]    
    
        data_merged_results = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
    
        #any divide-by-zero NAs from our earlier division gets a 0
        data_merged_results = data_merged_results.replace(np.nan, 0.0)
        
        return data_merged_results

    #----------ENTC:REDUCE_LOSSES: Technical cost of maintaining grid ----------
    @cb_wrapper
    def cb_entc_reduce_losses(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:

        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #get the loss file
        cb_transmission_loss_costs = pd.read_sql(self.session.query(ENTCReduceLosses).statement, self.session.bind) 

        #map ISO3 to the reigons
        country_codes = pd.read_sql(self.session.query(CountriesISO).statement, self.session.bind)

        # merge dataframes
        cb_transmission_loss_costs = cb_transmission_loss_costs.merge(right = country_codes, on = "iso_code3")
    
        data_strategy = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, cb_orm.diff_var)
        data_output = data_strategy.merge(right = cb_transmission_loss_costs, on = 'region')
        data_output["variable"] = cb_orm.output_variable_name
        data_output["value"] = data_output["annual_investment_USD"]
        data_output["difference_variable"] = 'N/A (constant annual cost)'
        data_output["difference_value"] = data_output["annual_investment_USD"]
    
        data_output = data_output[SSP_GLOBAL_COLNAMES_OF_RESULTS] 
    
        return data_output

    #----------IPPU:CLINKER------------------}
    @cb_wrapper
    def cb_ippu_clinker(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:

        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #get the clinker fraction data
        diff_clinker = self.mapping_strategy_specific_functions("cb_difference_between_two_strategies",cb_orm)
        

        data_amt_cement = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, 'prod_ippu_cement_tonne')
    
        data_merged = diff_clinker.merge(right = data_amt_cement, on = ['region', 'time_period'], suffixes = ["", ".cement"])
    
        data_merged["difference_value"] = data_merged["value.cement"]/(1-data_merged["difference_value"]) - data_merged["value.cement"]
        data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier
    
        
        data_output = data_merged[diff_clinker.columns.to_list()]
        
        return data_output

    #----------IPPU:FGASES-------------------
    @cb_wrapper
    def cb_ippu_florinated_gases( 
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:

        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #get all the variables with florinated gases
        #use nomenclature "emission_co2e_NAMEOFGAS_ippu_" where name of gas contains an "f"
        emissions_vars = [i for i in self.ssp_list_of_vars if i.startswith('emission_co2e_')]
        fgases = [i for i in emissions_vars if not ("_co2_" in i or "_n2o_" in i or "_ch4_" in i or "_subsector_" in i)]

        #sum up for both strategies
        data_strategy = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, fgases)
    
        data_strategy_summarized = data_strategy.groupby(["region", "time_period", "strategy_code"]).agg({"value" : "sum"}).rename(columns = {"value" : "difference_value"}).reset_index()
        data_strategy_summarized["difference_variable"] = 'emission_co2e_all_fgases_ippu'
        data_strategy_summarized["variable"] = output_vars


        data_strategy_base = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_base, fgases)
        data_strategy_base_summarized = data_strategy_base.groupby(["region", "time_period", "strategy_code"]).agg({"value" : "sum"}).rename(columns = {"value" : "difference_value"}).reset_index()
        data_strategy_base_summarized["difference_variable"] = 'emission_co2e_all_fgases_ippu'
        data_strategy_base_summarized["variable"] = cb_orm.output_variable_name


        #take difference and multiply by cost / CO2e
        data_fgases_merged = data_strategy_summarized.merge(right = data_strategy_base_summarized, on = ['region', 'time_period'], suffixes = ["", ".base"])
        data_fgases_merged["difference_value"] = data_fgases_merged["difference_value"] - data_fgases_merged["difference_value.base"]
        data_fgases_merged["value"] = data_fgases_merged["difference_value"]*cb_orm.multiplier
    
        data_fgases_merged = data_fgases_merged[["region","time_period","strategy_code", "difference_variable", "difference_value","variable","value"]]
    
        #return result
        return data_fgases_merged


    #--------------FGTV: ALL COSTS ------------
    #This function calculates the cost of abating fugitive emissions.
    #(1) calculates the "fugitive emissions intensity" as the fugitive emissions per unit of energy consumed in each time period in the baseline
    #(2) calculates the "expected fugitive emissions" in a transformed future by multiplying that intensity by the energy consumed in the transformed future
    #(3) calculates "fugitive emissions abated"  as difference between "expected fugitive emissions" and actual emissions
    #(4) calculates "cost of abatement" as quantity abated * cost of abatement
    @cb_wrapper
    def cb_fgtv_abatement_costs(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #(1) FUGITIVE EMISSIONS INTENSITY
        energy_vars = ['energy_demand_enfu_total_fuel_coal', 'energy_demand_enfu_total_fuel_oil', 'energy_demand_enfu_total_fuel_natural_gas']
        fgtv_vars = [string for string in self.ssp_list_of_vars if  re.match(re.compile('emission_co2e_.*_fgtv_fuel_.*'), string)]

        #1. Get the fugitive emissions per PJ of coal and oil together in the baseline
        energy = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_base, energy_vars)
        energy["fuel"] = energy["variable"].apply(lambda x : x.replace('energy_demand_enfu_total_', ''))
        fgtv = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_base, fgtv_vars)
        fgtv["fuel"] = fgtv["variable"].apply(lambda x : x.split("_fgtv_")[-1])

        #1.a summarize the emissions by fuel
        vars_to_groupby = ["primary_id", "region", "time_period", "strategy_code", "fuel"]
        fgtv = fgtv.groupby(vars_to_groupby).agg({"value" : "sum"}).reset_index()

        data_merged_base = energy.merge(right = fgtv, on = vars_to_groupby, suffixes=('.en_base', '.fg_base'))

        #2. Get the fugitive emissions per PJ of coal and oil together in the transformed future
        energy_tx = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, energy_vars)
        energy_tx["fuel"] = energy_tx["variable"].apply(lambda x : x.replace('energy_demand_enfu_total_', ''))
        fgtv_tx = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, fgtv_vars)
        fgtv_tx["fuel"] = fgtv_tx["variable"].apply(lambda x : x.split("_fgtv_")[-1])

        #2.b summarize the emissions by fuel
        fgtv_tx = fgtv_tx.groupby(vars_to_groupby).agg({"value" : "sum"}).reset_index()

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
        data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier
        data_merged["variable"] = cb_orm.output_variable_name

        #7. Get columns
        data_merged["strategy_code"] = data_merged["strategy_code.tx"]
        data_merged["future_id"]= data_merged["future_id.tx"]
        data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]

        #8. If tehre are NANs or NAs in the value, replace them with 0.
        data_merged.replace(np.nan, 0.0)

        return data_merged

        
    #----------WASO:WASTE REDUCTION TECHNICAL COSTS------------------

    # This function calculates consumer food waste avoided, which includes everythign after
    #the retailer. From james:
    #  consumer_food_waste_avoided = (qty_waso_total_food_produced_tonne - 
    #qty_agrc_food_produced_lost_sent_to_msw_tonne) * 
    #  (1 - factor_waso_waste_per_capita_scalar_food)/factor_waso_waste_per_capita_scalar_food
    @cb_wrapper
    def cb_waso_reduce_consumer_facing_food_waste(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        
        cols_required = ['qty_waso_total_food_produced_tonne', 'qty_agrc_food_produced_lost_sent_to_msw_tonne','factor_waso_waste_per_capita_scalar_food']

        food_waste_data = data[data["strategy_code"]==cb_orm.strategy_code_tx][SSP_GLOBAL_SIMULATION_IDENTIFIERS + cols_required].reset_index(drop = True)
    
        #Get teh consumer food waste amount
        food_waste_data["consumer_food_waste"] = (food_waste_data["qty_waso_total_food_produced_tonne"]) 
                                            #KLUDGE 07.06/2023
        #UNCOMMENT THIS LINE WHEN JAMES FIXES WHAT 'qty_waso_total_food_produced_tonne' means
                                            #Because of a bug, this is already consumer food waste.
                                        # - food_waste_data$qty_agrc_food_produced_lost_sent_to_msw_tonne)

        #Get how much would have been there
        food_waste_data["consumer_food_waste_counterfactual"] = food_waste_data["consumer_food_waste"]/food_waste_data["factor_waso_waste_per_capita_scalar_food"]


        #get the difference, whic his hte avoided amount
        food_waste_data["consumer_food_waste_avoided"] = food_waste_data["consumer_food_waste"] - food_waste_data["consumer_food_waste_counterfactual"]

        food_waste_data["consumer_food_waste_avoided2"] = (food_waste_data["qty_waso_total_food_produced_tonne"] - food_waste_data["qty_agrc_food_produced_lost_sent_to_msw_tonne"]) *(1-food_waste_data["factor_waso_waste_per_capita_scalar_food"])/ food_waste_data["factor_waso_waste_per_capita_scalar_food"]
    
        food_waste_to_merge = food_waste_data[SSP_GLOBAL_SIMULATION_IDENTIFIERS + ['consumer_food_waste_avoided']]

        outputs = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, 'qty_waso_total_food_produced_tonne')

        merged_data = outputs.merge(right = food_waste_to_merge, on=['strategy_code', 'region', 'time_period'], suffixes=['', '.food'])

        
        merged_data["difference_variable"] = 'qty_consumer_food_waste_avoided'
        merged_data["difference_value"] = merged_data["consumer_food_waste_avoided"]
        merged_data["variable"] = cb_orm.output_variable_name
        merged_data["value"] = merged_data["difference_value"] * cb_orm.multiplier
    
        merged_data = merged_data[SSP_GLOBAL_COLNAMES_OF_RESULTS]

        return merged_data

    #----------LVST: ENTERIC FERMENTATION------------------
    @cb_wrapper
    def cb_lvst_enteric(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #define the strategy as the fractino of livestock receivving this intervention in a particular year
        tx_definition = pd.read_sql(self.session.query(LVSTEntericFermentationTX).statement, self.session.bind)
        affected_livestock = tx_definition[tx_definition["application"]>0]
        timesteps = pd.DataFrame({"time_period" : range(SSP_GLOBAL_TIME_PERIODS)})

        enteric_pop_fracs = affected_livestock.merge(right=timesteps, how = "cross")

        enteric_pop_fracs["application_in_year"] = enteric_pop_fracs["application"]/(SSP_GLOBAL_TIME_PERIODS - SSP_GLOBAL_TIME_PERIOD_TX_START) *(enteric_pop_fracs["time_period"] - SSP_GLOBAL_TIME_PERIOD_TX_START+1)
        enteric_pop_fracs.loc[(enteric_pop_fracs["time_period"] >=0) & (enteric_pop_fracs["time_period"]<=SSP_GLOBAL_TIME_PERIOD_TX_START-1), "application_in_year"] = 0


        #apply that to the data
        data_num_livestock = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, affected_livestock["variable"].to_list())
    
        data_merged = data_num_livestock.merge(right = enteric_pop_fracs, on = ['variable', 'time_period'])
        data_merged["difference_variable"] = data_merged["variable"] 
        data_merged["difference_value"] = data_merged["value"]*data_merged["application_in_year"]
        #data_merged["variable"] = data_merged["variable"].apply(lambda x : f"{cb_orm.output_variable_name[:-1]}{x}")
        data_merged["variable"] = cb_orm.output_variable_name
        data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier
        data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
    
        return data_merged 

    #----------AGRC:RICE------------
    @cb_wrapper
    def cb_agrc_rice_mgmt(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()
        
        #define the transformation as the fraction of acres receiivng better rice management
        tx_definition = pd.read_sql(self.session.query(AgrcRiceMGMTTX).statement, self.session.bind)
        tx_definition["level_of_implementation"] = (1-tx_definition["ef_agrc_anaerobicdom_rice_kg_ch4_ha"])/0.45
        
        rice_management_data = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, cb_orm.diff_var)

        #merge with transformation
        rice_management_data = rice_management_data.merge(right = tx_definition, on = 'time_period')
    
        rice_management_data["difference_variable"] = cb_orm.diff_var #paste0('diff_', diff_var)
        rice_management_data["difference_value"] = rice_management_data["value"]*rice_management_data["level_of_implementation"]
        rice_management_data["variable"] = cb_orm.output_variable_name
        rice_management_data["value"] = rice_management_data["difference_value"]*cb_orm.multiplier
        rice_management_data = rice_management_data[SSP_GLOBAL_COLNAMES_OF_RESULTS]
        
        return rice_management_data

    #----------AGRCLVST:Productivity----------
    #the economic cost of increasing productivity is equal to
    #some percent of GDP defined in file
    @cb_wrapper
    def cb_agrc_lvst_productivity(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #Get the gdp data
        gdp = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, 'gdp_mmm_usd')

        #Get the fractions for each country
        gdp_fracs = pd.read_sql(self.session.query(AgrcLVSTProductivityCostGDP).statement, self.session.bind)
        gdp_fracs = gdp_fracs.rename(columns = {"cost_of_productivity_improvements_pct_gdp" : "cost_frac"})

        #country codes
        country_codes = pd.read_sql(self.session.query(CountriesISO).statement, self.session.bind)

        gdp_fracs = gdp_fracs.merge(right = country_codes, on = "iso_code3")
        gdp_fracs = gdp_fracs.rename(columns = {"REGION" : "region"})
        gdp_fracs = gdp_fracs[['region', 'cost_frac']]

        #merge wiht gdp
        gdp = gdp.merge(right=gdp_fracs, on = "region")
        gdp["difference_variable"] = 'diff_fraction_of_GDP_for_productivity'
        gdp["difference_value"] = gdp["cost_frac"]
        gdp["variable"] = cb_orm.output_variable_name
        gdp["value"] = gdp["value"]*10**9*gdp["cost_frac"]/2*(-1)

        escalar_prod = 1

        if cb_orm.strategy_code_tx == 'PFLO:UNCONSTRAINED':
            escalar_prod = 1.2
        
        gdp["value"] *= escalar_prod

        gdp.loc[gdp["time_period"]<SSP_GLOBAL_TIME_PERIOD_TX_START, "value"] = 0
    
        gdp = gdp[SSP_GLOBAL_COLNAMES_OF_RESULTS]

        return gdp


    #--------------PFLO:BETTER DIETS------------
    #calculate the number of additional people using better diets
    #for each such person, there is a $370 cost savings in groceries and 
    #$1000/yr cost savings in health
    @cb_wrapper
    def cb_pflo_healthier_diets(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #Get the population
        population = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, ['population_gnrl_rural', 'population_gnrl_urban'])
        
        vars_to_groupby = ["primary_id", "region", "time_period", "strategy_code", "future_id"]

        total_pop = population.groupby(vars_to_groupby).agg({"value" : "sum"}).rename(columns = {"value" : "total_pop"}).reset_index()

        #get the file with popualtion fractions  
        diet_frac = pd.read_sql(self.session.query(PFLOTransitionNewDiets).statement, self.session.bind)
        
        data_merged = total_pop.merge(right = diet_frac, on='time_period')
        data_merged["difference_value"] = data_merged["total_pop"]*(1-data_merged["frac_gnrl_w_original_diet"])
        data_merged["difference_variable"] = 'pop_with_better_diet'
        data_merged["variable"] = cb_orm.output_variable_name
        data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier

        data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]

        return data_merged

    #--------------IPPU: CCS ------------------
    @cb_wrapper
    def cb_ippu_inen_ccs(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()
        
        #get the fraction reductions in CO2
        ccs_fraction_vars = [i for i in self.ssp_list_of_vars if i.startswith("frac_ippu_production_with_co2_capture_")]
        ccs_fractions = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, ccs_fraction_vars)

        #given the global capture rate, update the application fraction
        ccs_fractions["application_rate"] = ccs_fractions["value"]

        #get the quantities of production for those variables
        production_vars = [i.replace("frac_ippu_production_with_co2_capture_", "prod_ippu_") + "_tonne" for i in ccs_fraction_vars]
        ccs_fractions["variable"] = ccs_fractions["variable"].apply(lambda x : x.replace("frac_ippu_production_with_co2_capture_", "prod_ippu_") + "_tonne")
        prod_qty = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, production_vars)

        #merge the two datasets
        by_merge_vars = ['region', 'strategy_code', 'time_period', 'variable']
        tx_suffix = "ccs"
        base_suffix = ""

        data_merged = ccs_fractions.merge(right = prod_qty, on =  by_merge_vars, suffixes=(tx_suffix, base_suffix))

        #multiply the production quantity by the fractions
        data_merged["difference_value"] = data_merged["application_rate"] * data_merged["value"]
        data_merged["difference_variable"] = data_merged["variable"]

        #read the cost definitions
        ccs_cost_factor = pd.read_sql(self.session.query(IPPUCCSCostFactor).statement, self.session.bind)
        
        data_merged = data_merged.merge(right = ccs_cost_factor, on = 'variable')

        data_merged["value"] = data_merged["difference_value"] * data_merged["multiplier"]
        data_merged["variable"] = data_merged["output_variable_name"]
    
        data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
        
        return data_merged


    #---------------Manure Management
    @cb_wrapper
    def cb_manure_management_cost(
                        self,
                        cb_orm : Union[CostFactor,TransformationCost]
                        ) -> pd.DataFrame:
        
        # Obtenemos datos de las salidas de ssp
        data = self.ssp_data.copy()

        #time_period = range(SSP_GLOBAL_TIME_PERIODS)
        implementation = [0]*11 + list(np.linspace(0, 0.95, SSP_GLOBAL_TIME_PERIODS - 11))

        manure_imp = pd.DataFrame({"implementation" : implementation})

        tlus = self.cb_get_data_from_wide_to_long(data, cb_orm.strategy_code_tx, cb_orm.diff_var)
        tlus = pd.concat([tlus, manure_imp], axis = 1)
        tlus["difference_variable"] = cb_orm.diff_var
        tlus["difference_value"] = tlus["value"]*tlus["implementation"]
        tlus["value"] = tlus["difference_value"]*cb_orm.multiplier
        tlus["variable"] = cb_orm.output_variable_name
        tlus = tlus[SSP_GLOBAL_COLNAMES_OF_RESULTS]

        return tlus.dropna()


