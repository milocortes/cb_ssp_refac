from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker # Imports the sessionmaker class.

#engine = create_engine('sqlite:///:memory:')
engine = create_engine('sqlite:///cb_data.db')

Session = sessionmaker(bind=engine) # Defines a Session class with the bind configuration supplied by sessionmaker.

session = Session() 

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, Numeric, String, DateTime,
                        ForeignKey, Float, Boolean, BigInteger)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref


Base = declarative_base()


class TXTable(Base):
    __tablename__ = 'tx_table'

    output_variable_name = Column(String(), primary_key=True)
    output_display_name = Column(String())
    internal_notes = Column(String())
    display_notes = Column(String())
    cost_type = Column(String())

    def __repr__(self): 
        return "TX_table(output_variable_name='{self.output_variable_name}', " \
                       "output_display_name='{self.output_display_name}', " \
                       "internal_notes='{self.internal_notes}', " \
                       "display_notes={self.display_notes}, " \
                       "cost_type={self.cost_type})".format(self=self)


class TransformationCost(Base):
    __tablename__ = 'transformation_costs'

    output_variable_name = Column(String(), ForeignKey('tx_table.output_variable_name'), primary_key=True)
    transformation_code = Column(String(), ForeignKey('attribute_transformation_code.transformation_code'))
    include = Column(Boolean())
    include_variant = Column(Integer())
    test_id_variant_suffix = Column(String())
    comparison_id_variant = Column(String())
    cb_function = Column(String())
    difference_variable = Column(String())
    multiplier = Column(Float())
    multiplier_unit = Column(String())
    annual_change = Column(Float())
    arg1 = Column(String())
    arg2  = Column(Integer())
    sum = Column(Boolean())
    natural_multiplier_units = Column(String())


    tx_table =  relationship("TXTable", backref=backref('transformation_costs', order_by=output_variable_name))

    def __repr__(self):
        return "TransformationCost(output_variable_name={self.output_variable_name}, " \
                      "transformation_code={self.transformation_code})".format(self=self)


class StrategyInteraction(Base):
    __tablename__ = 'strategy_interactions'

    variable = Column(String(), ForeignKey('tx_table.output_variable_name'), primary_key=True)
    interaction_name = Column(String())
    transformation_code = Column(String(), ForeignKey('attribute_transformation_code.transformation_code'))
    relative_effect = Column(Float())
    scale_variable = Column(Boolean())

    def __repr__(self):
        return "StrategyInteraction(variable='{self.variable}', " \
                     "interaction_name='{self.interaction_name}', " \
                     "transformation_code='{self.transformation_code}', " \
                     "relative_effect='{self.relative_effect}')" \
                     "scale_variable='{self.scale_variable}')".format(self=self)


class CostFactor(Base):
    __tablename__ = 'cost_factors'

    output_variable_name = Column(String(), ForeignKey('tx_table.output_variable_name'), primary_key=True)
    difference_variable = Column(String())
    multiplier = Column(Float())
    multiplier_unit = Column(String())
    annual_change = Column(Float())
    output_display_name = Column(String())
    sum = Column(Boolean())
    natural_multiplier_units = Column(String())
    display_notes = Column(String())
    internal_notes = Column(String())
    cb_function = Column(String())
    cb_var_group = Column(String())



    tx_table =  relationship("TXTable", backref=backref('cost_factors', order_by=output_variable_name))

    def __repr__(self):
        return "CostFactor(output_variable_name={self.output_variable_name}, " \
                      "difference_variable={self.difference_variable})".format(self=self)


class CountriesISO(Base):
    __tablename__ = "countries_by_iso"

    iso_code3 = Column(String(), primary_key=True)  
    category_name = Column(String())          
    region = Column(String())  
    fao_area_code = Column(String())    
    world_bank_global_region = Column(String())


class AttDimTimePeriod(Base):
    __tablename__ = "attribute_dim_time_period"

    time_period = Column(BigInteger(), primary_key=True)
    year = Column(BigInteger())

class AttTransformationCode(Base):
    __tablename__ = "attribute_transformation_code"

    transformation_code = Column(String(), primary_key=True)
    transformation = Column(String())
    transformation_id = Column(String())
    sector = Column(String(), nullable=True)
    description = Column(String(), nullable=True)


class AgrcLVSTProductivityCostGDP(Base):
    __tablename__ = "agrc_lvst_productivity_cost_gdp"

    iso_code3 = Column(String(), ForeignKey('countries_by_iso.iso_code3'), primary_key=True)
    cost_of_productivity_improvements_pct_gdp = Column(Float())
    cost_of_productivity_improvements_pct_gdp_orig = Column(Float())

class AgrcRiceMGMTTX(Base):
    __tablename__ = "agrc_rice_mgmt_tx"

    time_period = Column(BigInteger(), ForeignKey('attribute_dim_time_period.time_period'), primary_key=True)
    ef_agrc_anaerobicdom_rice_kg_ch4_ha = Column(Float())

class ENTCReduceLosses(Base):
    __tablename__ = "entc_reduce_losses_cost_file"

    iso_code3 = Column(String(), ForeignKey('countries_by_iso.iso_code3'), primary_key=True)
    annual_investment_USD = Column(BigInteger())

class IPPUCCSCostFactor(Base):
    __tablename__ = "ippu_ccs_cost_factors"

    variable = Column(String(), primary_key = True)
    multiplier = Column(BigInteger())
    multiplier_unit = Column(String())
    annual_change  = Column(Float())
    output_variable_name = Column(String())
    output_display_name = Column(String())
    sum = Column(Integer())
    natural_multiplier_units = Column(String())
    display_notes = Column(String())
    internal_notes = Column(String())

class IPPUFgasDesignation(Base):
    __tablename__ = "ippu_fgas_designations"

    gas = Column(String(), primary_key = True)
    gas_suffix = Column(String())
    name = Column(String())
    flourinated_compound_designation = Column(String())


class LNDUSoilCarbonFraction(Base):
    __tablename__ = "LNDU_soil_carbon_fractions"

    iso_code3 = Column(String(), ForeignKey('countries_by_iso.iso_code3'), primary_key=True)
    start_val = Column(Float())
    end_val = Column(Float())


class LVSTEntericFermentationTX(Base):
    __tablename__ = "LVST_enteric_fermentation_tx"

    variable =  Column(String(), primary_key = True)
    application = Column(Float())
    decrease_per_head = Column(Float())


class LVSTTLUConversion(Base):
    __tablename__ = "lvst_tlu_conversions"

    variable = Column(String(), primary_key = True)
    tlu = Column(Float())


class PFLOTransitionNewDiets(Base):
    __tablename__ = "pflo_transition_to_new_diets"

    time_period = Column(BigInteger(), ForeignKey('attribute_dim_time_period.time_period'), primary_key=True)
    frac_gnrl_w_original_diet = Column(Float())

class WALISanitationClassificationSP(Base):
    __tablename__ = "wali_sanitation_classification_strategy_specific_function"


    variable = Column(String(), primary_key = True)
    difference_variable = Column(String())
    population_variable = Column(String())


Base.metadata.create_all(engine)

#### Poblamos la base de datos
import pandas as pd 


###### SSP Attributes tables
directory_ssp_attr_tables = "ssp_attribute_tables"

##### Poblamos countries_by_iso.csv

countries_by_iso = pd.read_csv(f"{directory_ssp_attr_tables}/countries_by_iso.csv")
data_fields = ['iso_code3', 'category_name', 'region', 'fao_area_code', 'world_bank_global_region']
session.bulk_save_objects(
	[CountriesISO(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in countries_by_iso.to_records(index = False) ]
)
##### Poblamos attribute_dim_time_period.csv

attribute_dim_time_period = pd.read_csv(f"{directory_ssp_attr_tables}/attribute_dim_time_period.csv")
data_fields = ['time_period', 'year']
session.bulk_save_objects(
	[AttDimTimePeriod(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in attribute_dim_time_period.to_records(index = False) ]
)

##### Poblamos attribute_transformer_code.csv

attribute_transformer_code = pd.read_csv(f"{directory_ssp_attr_tables}/attribute_transformer_code.csv")
data_fields = ['transformation_code', 'transformation', 'transformation_id', 'sector', 'description']
session.bulk_save_objects(
	[AttTransformationCode(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in attribute_transformer_code.to_records(index = False) ]
)


###### COST FACTORS
directory_cost_factors = "cost_factors"
tx_table = pd.read_csv(f"{directory_cost_factors}/tx_table.csv")
transformation_costs = pd.read_csv(f"{directory_cost_factors}/transformation_cost.csv")
strategy_interactions = pd.read_csv(f"{directory_cost_factors}/strategy_interaction_definitions.csv")
cost_factors = pd.read_csv(f"{directory_cost_factors}/cb_cost_factors.csv")


##### Poblamos tx_table
tx_table_fields = ["output_variable_name", "output_display_name", "internal_notes", "display_notes", "cost_type"]

session.bulk_save_objects(
[TXTable(**{tb_fields : record_fields for tb_fields,record_fields in zip(tx_table_fields, record)}) for record in tx_table.to_records(index = False) ]
)

##### Poblamos strategy_interactions
strategy_interactions_fields = ['variable', 'interaction_name', 'transformation_code',
       'relative_effect', 'scale_variable']

session.bulk_save_objects(
[StrategyInteraction(**{tb_fields : record_fields for tb_fields,record_fields in zip(strategy_interactions_fields, record)}) for record in strategy_interactions.to_records(index = False) ]
)

##### Poblamos transformation_costs
transformation_costs_fields = ['output_variable_name', 'transformation_code', 'include',
       'include_variant', 'test_id_variant_suffix', 'comparison_id_variant',
       'cb_function', 'difference_variable', 'multiplier', 'multiplier_unit',
       'annual_change', 'arg1', 'arg2', 'sum', 'natural_multiplier_units']

session.bulk_save_objects(
[TransformationCost(**{tb_fields : record_fields for tb_fields,record_fields in zip(transformation_costs_fields, record)}) for record in transformation_costs.to_records(index = False) ]
)

##### Poblamos cost_factors
cost_factors_fields = ['output_variable_name', 'difference_variable', 'multiplier',
       'multiplier_unit', 'annual_change', 'output_display_name', 'sum',
       'natural_multiplier_units', 'display_notes', 'internal_notes',
       'cb_function', 'cb_var_group']

session.bulk_save_objects(
[CostFactor(**{tb_fields : record_fields for tb_fields,record_fields in zip(cost_factors_fields, record)}) for record in cost_factors.to_records(index = False) ]
)

###### Strategy Specific CB Files
directory_strat_specific_cb_files = "strategy_specific_cb_files"

##### Poblamos AGRC_rice_mgmt_tx.csv

AGRC_rice_mgmt_tx = pd.read_csv(f"{directory_strat_specific_cb_files}/AGRC_rice_mgmt_tx.csv")
data_fields = ['time_period', 'ef_agrc_anaerobicdom_rice_kg_ch4_ha']
session.bulk_save_objects(
	[AgrcRiceMGMTTX(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in AGRC_rice_mgmt_tx.to_records(index = False) ]
)

##### Poblamos ENTC_REDUCE_LOSSES_cost_file.csv

ENTC_REDUCE_LOSSES_cost_file = pd.read_csv(f"{directory_strat_specific_cb_files}/ENTC_REDUCE_LOSSES_cost_file.csv")
data_fields = ['iso_code3', 'annual_investment_USD']
session.bulk_save_objects(
	[ENTCReduceLosses(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in ENTC_REDUCE_LOSSES_cost_file.to_records(index = False) ]
)

##### Poblamos WALI_sanitation_classification_strategy_specific_function.csv

WALI_sanitation_classification_strategy_specific_function = pd.read_csv(f"{directory_strat_specific_cb_files}/WALI_sanitation_classification_strategy_specific_function.csv")
data_fields = ['variable', 'difference_variable', 'population_variable']
session.bulk_save_objects(
	[WALISanitationClassificationSP(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in WALI_sanitation_classification_strategy_specific_function.to_records(index = False) ]
)

##### Poblamos LVST_enteric_fermentation_tx.csv

LVST_enteric_fermentation_tx = pd.read_csv(f"{directory_strat_specific_cb_files}/LVST_enteric_fermentation_tx.csv")
data_fields = ['variable', 'application', 'decrease_per_head']
session.bulk_save_objects(
	[LVSTEntericFermentationTX(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in LVST_enteric_fermentation_tx.to_records(index = False) ]
)

##### Poblamos ippu_ccs_cost_factors.csv

ippu_ccs_cost_factors = pd.read_csv(f"{directory_strat_specific_cb_files}/ippu_ccs_cost_factors.csv")
data_fields = ['variable', 'multiplier', 'multiplier_unit', 'annual_change', 'output_variable_name', 'output_display_name', 'sum', 'natural_multiplier_units', 'display_notes', 'internal_notes']
session.bulk_save_objects(
	[IPPUCCSCostFactor(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in ippu_ccs_cost_factors.to_records(index = False) ]
)

##### Poblamos lvst_tlu_conversions.csv

lvst_tlu_conversions = pd.read_csv(f"{directory_strat_specific_cb_files}/lvst_tlu_conversions.csv")
data_fields = ['variable', 'tlu']
session.bulk_save_objects(
	[LVSTTLUConversion(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in lvst_tlu_conversions.to_records(index = False) ]
)

##### Poblamos ippu_fgas_designations.csv

ippu_fgas_designations = pd.read_csv(f"{directory_strat_specific_cb_files}/ippu_fgas_designations.csv")
data_fields = ['gas', 'gas_suffix', 'name', 'flourinated_compound_designation']
session.bulk_save_objects(
	[IPPUFgasDesignation(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in ippu_fgas_designations.to_records(index = False) ]
)

##### Poblamos LNDU_soil_carbon_fractions.csv

LNDU_soil_carbon_fractions = pd.read_csv(f"{directory_strat_specific_cb_files}/LNDU_soil_carbon_fractions.csv")
data_fields = ['iso_code3', 'start_val', 'end_val']
session.bulk_save_objects(
	[LNDUSoilCarbonFraction(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in LNDU_soil_carbon_fractions.to_records(index = False) ]
)

##### Poblamos AGRC_LVST_productivity_cost_gdp.csv

AGRC_LVST_productivity_cost_gdp = pd.read_csv(f"{directory_strat_specific_cb_files}/AGRC_LVST_productivity_cost_gdp.csv")
data_fields = ['iso_code3', 'cost_of_productivity_improvements_pct_gdp', 'cost_of_productivity_improvements_pct_gdp_orig']
session.bulk_save_objects(
	[AgrcLVSTProductivityCostGDP(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in AGRC_LVST_productivity_cost_gdp.to_records(index = False) ]
)

##### Poblamos PFLO_transition_to_new_diets.csv

PFLO_transition_to_new_diets = pd.read_csv(f"{directory_strat_specific_cb_files}/PFLO_transition_to_new_diets.csv")
data_fields = ['time_period', 'frac_gnrl_w_original_diet']
session.bulk_save_objects(
	[PFLOTransitionNewDiets(**{tb_fields : record_fields for tb_fields,record_fields in zip(data_fields, record)}) for record in PFLO_transition_to_new_diets.to_records(index = False) ]
)

#### COMMIT
session.commit()



####
cookies = session.query(TXTable).all() 
print(cookies)



tx_query = session.query(TXTable).filter(TXTable.output_variable_name == "cb:scoe:technical_cost:efficiency:appliance").all() 
print(tx_query)

tx_query = session.query(TXTable).filter(TXTable.output_variable_name == "cb:scoe:technical_cost:efficiency:appliance").first() 
print(tx_query)

tx_cost_query = session.query(TransformationCost).filter(TransformationCost.output_variable_name == "cb:scoe:technical_cost:efficiency:appliance").all() 


#####
from typing import Union

def get_cb_var_fields(cb_var_name : str,
                      session : Session
                      ) -> Union[TransformationCost, CostFactor]:

    # Identificamos qué tipo de factor de costo es
    tx_query = session.query(TXTable).filter(TXTable.output_variable_name == cb_var_name).first() 

    if tx_query.cost_type == "system_cost":
        print("La variable se evalúa en System Cost")
        return session.query(CostFactor).filter(CostFactor.output_variable_name == cb_var_name).first() 
    
    elif tx_query.cost_type == "transformation_cost":
        print("La variable se evalúa en ")
        return session.query(TransformationCost).filter(TransformationCost.output_variable_name == cb_var_name).first() 
    

def compute_cost_benefit_from_variable(
                    cb_var_name : str,
                    session : Session
                    ) -> None:

    ## Obteniendo registro de la db
    cb_orm = get_cb_var_fields(cb_var_name, session)

    print("---------Costs for: {cb_orm.output_variable_name}."\
          "\n---------CB function to apply {cb_orm.cb_function}"\
          "\n---------CB multiplier {cb_orm.multiplier}".format(cb_orm=cb_orm))

