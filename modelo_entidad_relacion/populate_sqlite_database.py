from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker # Imports the sessionmaker class.

#engine = create_engine('sqlite:///:memory:')
engine = create_engine('sqlite:///cb_data.db')

Session = sessionmaker(bind=engine) # Defines a Session class with the bind configuration supplied by sessionmaker.

session = Session() 

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, Numeric, String, DateTime,
                        ForeignKey, Float, Boolean)

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
    transformation_code = Column(String())
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
    transformation_code = Column(String())
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


Base.metadata.create_all(engine)

#### Poblamos la base de datos
import pandas as pd 

tx_table = pd.read_csv("tx_table.csv")
transformation_costs = pd.read_csv("transformation_cost.csv")
strategy_interactions = pd.read_csv("strategy_interaction_definitions.csv")
cost_factors = pd.read_csv("cb_cost_factors.csv")


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
        return session.query(CostFactor).filter(CostFactor.output_variable_name == cb_var_name).first() 
    
    elif tx_query.cost_type == "transformation_cost":
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

