from dataclasses import dataclass
from enum import Enum 
from typing import List, Union, Dict
import pandas as pd 
import logging

import os 

@dataclass
class CBFileDataMixin:
    file_name : str
    extension : str

@dataclass 
class CBDirectoryPathDataMixin:
    directory_name : str

class StrategySpecificCBFile(CBFileDataMixin, Enum):
    """
    Enum que define los archivos con los factores de costos específicos a cada estrategia.
    """
    IPPU_CCS_COST_FACTORS = ("ippu_ccs_cost_factors", "csv")
    LVST_ENTERIC_FERMENTATION_TX = ("LVST_enteric_fermentation_tx", "csv")
    PFLO_TRANSITION_TO_NEW_DIETS = ("PFLO_transition_to_new_diets", "csv")
    AGRC_LVST_PRODUCTIVITY_COST_GDP = ("AGRC_LVST_productivity_cost_gdp", "csv")
    AGRC_RICE_MGMT_TX = ("AGRC_rice_mgmt_tx", "csv")
    ENTC_REDUCE_LOSSES_COST_FILE = ("ENTC_REDUCE_LOSSES_cost_file", "xlsx")

class DefinitionCBFile(CBFileDataMixin, Enum):
    """
    Enum que define los archivos de definición del módulo de costos y beneficios.
    """

    STRATEGY2TX = ("attribute_strategy_code", "csv") #This file tells us which transformation in is in each strategy
    STRATEGY_COST_INSTRUCTIONS = ("strategy_cost_instructions", "csv") #tells us which strategies to evaluate costs and benefit if for
    COST_FACTOR_NAMES = ("system_cost_factors_list", "csv") #the list of all the cost factor files in the system, and the functions they should be evaluated with
    TRANSFORMATION_COST_DEFINITIONS = ("transformation_cost_definitions", "csv") #defines how each transformation is evaluated, including difference variables, cost multipliers, etc.

class CostFactorCBFile(CBFileDataMixin, Enum):
    """
    Enum que define los archivos con los factores de costos.
    """

    AFOLU_CROP_LIVESTOCK_PRODUCTION_COST_FACTORS = ("afolu_crop_livestock_production_cost_factors", "csv")
    AFOLU_ECOSYSTEM_SERVICES_COST_FACTORS = ("afolu_ecosystem_services_cost_factors", "csv")
    ENFU_FUEL_COST_FACTORS = ("enfu_fuel_cost_factors", "csv")
    ENFU_FUEL_COST_FACTORS_DETAIL = ("enfu_fuel_cost_factors_detail", "csv")
    ENFU_SECTOR_FUEL_COST_FACTORS = ("enfu_sector_fuel_cost_factors", "csv")
    ENTC_AIR_POLLUTION_COST_FACTORS = ("entc_air_pollution_cost_factors", "csv")
    ENTC_PRODUCTION_COST_FACTORS = ("entc_production_cost_factors", "csv")
    ENTC_SECTOR_ELECTRICITY_COST_FACTORS = ("entc_sector_electricity_cost_factors", "csv")
    GHG_EFFECTS_FACTORS = ("ghg_effects_factors", "csv")
    INEN_AIR_POLLUTION_COST_FACTORS = ("inen_air_pollution_cost_factors", "csv")
    IPPU_AVOIDED_AIR_POLLUTION_CEMENT_COST_FACTORS = ("ippu_avoided_air_pollution_cement_cost_factors", "csv")
    IPPU_AVOIDED_PRODUCTION_COST_FACTORS = ("ippu_avoided_production_cost_factors", "csv")
    LSMM_WASTE_TO_ENERGY_COST_FACTORS = ("lsmm_waste_to_energy_cost_factors", "csv")
    SOIL_NITROGEN_AND_LIME_COST_FACTORS = ("soil_nitrogen_and_lime_cost_factors", "csv")
    TRNS_AIR_POLLUTION_COST_FACTORS = ("trns_air_pollution_cost_factors", "csv")
    TRNS_CONGESTION_COST_FACTORS = ("trns_congestion_cost_factors", "csv")
    TRNS_FREIGHT_TRANSPORT_COST_FACTORS = ("trns_freight_transport_cost_factors", "csv")
    TRNS_PASSENGER_TRANSPORT_COST_FACTORS = ("trns_passenger_transport_cost_factors", "csv")
    TRNS_ROAD_SAFETY_COST_FACTORS = ("trns_road_safety_cost_factors", "csv")
    TRWW_TREATMENT_COST_FACTORS = ("trww_treatment_cost_factors", "csv")
    TRWW_TREATMENT_WATER_POLLUTION_COST_FACTORS = ("trww_treatment_water_pollution_cost_factors", "csv")
    TRWW_WASTE_TO_ENERGY_COST_FACTORS = ("trww_waste_to_energy_cost_factors", "csv")
    WALI_BENEFIT_OF_SANITATION_COST_FACTORS = ("wali_benefit_of_sanitation_cost_factors", "csv")
    WALI_SANITATION_COST_FACTORS = ("wali_sanitation_cost_factors", "csv")
    WASO_POLLUTION_COST_FACTORS = ("waso_pollution_cost_factors", "csv")
    WASO_WASTE_COLLECTION_COST_FACTORS = ("waso_waste_collection_cost_factors", "csv")
    WASO_WASTE_MANAGEMENT_COST_FACTORS = ("waso_waste_management_cost_factors", "csv")
    WASO_WASTE_TO_ENERGY_COST_FACTORS = ("waso_waste_to_energy_cost_factors", "csv")


class CBDirectoryPath(CBDirectoryPathDataMixin, Enum):
    """
    Enum que define el directorio específico a cada grupo de archivos.
    """
    StrategySpecificCBFile = "strategy_specific_cb_files"
    DefinitionCBFile = "definition_files"
    CostFactorCBFile = "cost_factors"

class CBFilesReader:
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
            data_file_path : str, 
            logger: Union[logging.Logger, None] = None
        ):
        
        #------ Inicializamos el Reader con los datos en cada Enum

        # Load Strategy Specific Files
        self.StrategySpecificCBData = self.read_files_on_enum(StrategySpecificCBFile, 
                                           [
                                            data_file_path,
                                            CBDirectoryPath.StrategySpecificCBFile.directory_name
                                           ],
                                           logger)

        # Load Definition Files
        self.DefinitionCBFile = self.read_files_on_enum(DefinitionCBFile, 
                                           [
                                            data_file_path,
                                            CBDirectoryPath.DefinitionCBFile.directory_name
                                           ],
                                           logger)
                                           
        # Load Cost Factor Files
        self.CostFactorCBFile = self.read_files_on_enum(CostFactorCBFile, 
                                           [
                                            data_file_path,
                                            CBDirectoryPath.CostFactorCBFile.directory_name
                                           ],
                                           logger)


    ##############################################
	#------ FUNCIONES DE INICIALIZACION	   ------#
	##############################################

    def read_files_on_enum(self, 
            cb_file_enum : Enum, 
            data_files_path : List[str], 
            logger: Union[logging.Logger, None] = None
        ) -> Dict[str, pd.DataFrame]:
        
        """
        La función read_files_on_enum carga los archivos definidos en el Enum que pasa como argumento
        """

        cb_data_enum : Dict[str, pd.DataFrame] = {}

        for cb_file in cb_file_enum:
            
            # Construye nombre de archivo
            FILE_NAME = f"{cb_file.file_name}.{cb_file.extension}"

            # Construye ruta de archivo
            DATA_FILE_PATH = os.path.join(*data_files_path, f"{FILE_NAME}")

            # Verifica si el archivo se encuentra en la ruta definida
            if os.path.isfile(DATA_FILE_PATH):
                if logger:
                    logger.info(f"El archivo {FILE_NAME} EXISTE")
                try:
                    if cb_file.extension == "csv":
                        # Cargamos archivo en formato csv
                        cb_data_enum[cb_file.file_name] = pd.read_csv(
                            DATA_FILE_PATH,
                            encoding="latin"
                        )

                    elif cb_file.extension == "xlsx":
                        # Cargamos archivo en formato excel
                        cb_data_enum[cb_file.file_name] = pd.read_excel(
                            DATA_FILE_PATH
                        )

                    if logger:
                        logger.warning(f"El archivo {FILE_NAME} se cargó correctamente")
                except:
                    if logger:
                        logger.warning(f"No fue posible cargar el archivo {FILE_NAME}")
                        #raise Exception(f"No fue posible cargar el archivo {FILE_NAME}") 

            else:
                if logger:
                    logger.warning(f"El archivo {DATA_FILE_PATH} NO EXISTE")


        return  cb_data_enum

