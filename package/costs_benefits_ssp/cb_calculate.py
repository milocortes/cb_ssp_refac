from typing import List, Union, Dict
from sqlalchemy.orm import Session
import pandas as pd 
import logging

import os 

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from costs_benefits_ssp.utils.utils import build_path,get_tx_prefix
from costs_benefits_ssp.model.cb_data_model import TXTable,CostFactor,TransformationCost,AttTransformationCode

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
                 logger: Union[logging.Logger, None] = None
                 ) -> None:

        self.ssp_data = self.marge_attribute_strategy(ssp_data, att_primary, att_strategy)
        self.session = self.initialize_session()
        self.strategy_to_txs : Dict[str, List[str]] = self.get_strategy_to_txs(att_strategy)
        self.att_strategy = att_strategy
        self.ssp_list_of_vars = list(self.ssp_data)


    ##############################################
	#------ FUNCIONES DE INICIALIZACION	   ------#
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


    def get_cb_var_fields(
                        self,
                        cb_var_name : str,
                        ) -> Union[TransformationCost, CostFactor]:

        # Identificamos qué tipo de factor de costo es
        tx_query = self.session.query(TXTable).filter(TXTable.output_variable_name == cb_var_name).first() 

        if tx_query.cost_type == "system_cost":
            print("La variable se evalúa en System Cost")
            return self.session.query(CostFactor).filter(CostFactor.output_variable_name == cb_var_name).first() 
        
        elif tx_query.cost_type == "transformation_cost":
            print("La variable se evalúa en Transformation Cost")
            return self.session.query(TransformationCost).filter(TransformationCost.output_variable_name == cb_var_name).first() 
        

    def compute_cost_benefit_from_variable(
                        self,
                        cb_var_name : str,
                        ) -> Union[CostFactor,TransformationCost]:

        ## Obteniendo registro de la db
        cb_orm = self.get_cb_var_fields(cb_var_name)

        print("---------Costs for: {cb_orm.output_variable_name}."\
            "\n---------CB function to apply {cb_orm.cb_function}"\
            "\n---------CB multiplier {cb_orm.multiplier}".format(cb_orm=cb_orm))

        return cb_orm



