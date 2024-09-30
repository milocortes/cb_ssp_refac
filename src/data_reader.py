from enum import Enum 
from typing import List, Union, Dict
import pandas as pd 
import logging

import os 

class StrategySpecificCBFile(Enum):
    """
    Enum que define los archivos con los factores de costos específicos a cada estrategia.
    """
    IPPU_CCS_COST_FACTORS = ("ippu_ccs_cost_factors", "csv")
    LVST_ENTERIC_FERMENTATION_TX = ("LVST_enteric_fermentation_tx", "csv")
    PFLO_TRANSITION_TO_NEW_DIETS = ("PFLO_transition_to_new_diets", "csv")
    AGRC_LVST_PRODUCTIVITY_COST_GDP = ("AGRC_LVST_productivity_cost_gdp", "csv")
    AGRC_RICE_MGMT_TX = ("AGRC_rice_mgmt_tx", "csv")
    ENTC_REDUCE_LOSSES_COST_FILE = ("ENTC_REDUCE_LOSSES_cost_file", "xlsx")

    def __str__(self) -> str:
        return self.name

    def file_name(self) -> str:
        return self.value[0]   

    def extension(self) -> str:
        return self.value[1]

class CBDirectoryPath(Enum):
    """
    Enum que define el directorio específico a cada grupo de archivos.
    """
    StrategySpecificCBFile = "strategy_specific_cb_files"

    def directory_name(self) -> str:
        return self.value   

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
        
        # Inicializamos el Reader con los datos en cada Enum
        self.StrategySpecificCBData = self.read_files_on_enum(StrategySpecificCBFile, 
                                           [
                                            data_file_path,
                                            CBDirectoryPath.StrategySpecificCBFile.directory_name()
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
            FILE_NAME = f"{cb_file.file_name()}.{cb_file.extension()}"

            # Construye ruta de archivo
            DATA_FILE_PATH = os.path.join(*data_files_path, f"{FILE_NAME}")

            # Verifica si el archivo se encuentra en la ruta definida
            if os.path.isfile(DATA_FILE_PATH):
                logger.info(f"El archivo {FILE_NAME} EXISTE")
                try:
                    if cb_file.extension() == "csv":
                        # Cargamos archivo en formato csv
                        cb_data_enum[cb_file.file_name()] = pd.read_csv(
                            DATA_FILE_PATH,
                            encoding="latin"
                        )

                    elif cb_file.extension() == "xlsx":
                        # Cargamos archivo en formato excel
                        cb_data_enum[cb_file.file_name()] = pd.read_excel(
                            DATA_FILE_PATH
                        )

                    logger.warning(f"El archivo {FILE_NAME} se cargó correctamente")
                except:
                    logger.warning(f"No fue posible cargar el archivo {FILE_NAME}")
                    #raise Exception(f"No fue posible cargar el archivo {FILE_NAME}") 

            else:
                logger.warning(f"El archivo {DATA_FILE_PATH} NO EXISTE")


        return  cb_data_enum

