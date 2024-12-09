# coding: utf-8
from sqlalchemy import Boolean, Column, DECIMAL, ForeignKey, String, Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


strategy_interaction_definitions = Table(
    'strategy_interaction_definitions', metadata,
    Column('variable', String),
    Column('interaction_name', String),
    Column('transformation_code', String),
    Column('relative_effect', DECIMAL),
    Column('scale_variable', Boolean)
)


class TxTable(Base):
    __tablename__ = 'tx_table'

    output_variable_name = Column(String, primary_key=True)
    output_display_name = Column(String)
    internal_notes = Column(String)
    display_notes = Column(String)
    cost_type = Column(String)


afolu_crop_livestock_production_cost_factors = Table(
    'afolu_crop_livestock_production_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


afolu_ecosystem_services_cost_factors = Table(
    'afolu_ecosystem_services_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


enfu_fuel_cost_factors = Table(
    'enfu_fuel_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


enfu_fuel_cost_factors_detail = Table(
    'enfu_fuel_cost_factors_detail', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


enfu_sector_fuel_cost_factors = Table(
    'enfu_sector_fuel_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


entc_air_pollution_cost_factors = Table(
    'entc_air_pollution_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


entc_production_cost_factors = Table(
    'entc_production_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


entc_sector_electricity_cost_factors = Table(
    'entc_sector_electricity_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


ghg_effects_factors = Table(
    'ghg_effects_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


inen_air_pollution_cost_factors = Table(
    'inen_air_pollution_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


ippu_avoided_air_pollution_cement_cost_factors = Table(
    'ippu_avoided_air_pollution_cement_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


ippu_avoided_production_cost_factors = Table(
    'ippu_avoided_production_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


lsmm_waste_to_energy_cost_factors = Table(
    'lsmm_waste_to_energy_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


soil_nitrogen_and_lime_cost_factors = Table(
    'soil_nitrogen_and_lime_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


transformation_cost = Table(
    'transformation_cost', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('transformation_code', String),
    Column('include', Boolean),
    Column('include_variant', DECIMAL),
    Column('test_id_variant_suffix', String),
    Column('comparison_id_variant', String),
    Column('cb_function', String),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', DECIMAL),
    Column('arg1', String),
    Column('arg2', DECIMAL),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String)
)


trns_air_pollution_cost_factors = Table(
    'trns_air_pollution_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trns_congestion_cost_factors = Table(
    'trns_congestion_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trns_freight_transport_cost_factors = Table(
    'trns_freight_transport_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trns_passenger_transport_cost_factors = Table(
    'trns_passenger_transport_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trns_road_safety_cost_factors = Table(
    'trns_road_safety_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trww_treatment_cost_factors = Table(
    'trww_treatment_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trww_treatment_water_pollution_cost_factors = Table(
    'trww_treatment_water_pollution_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


trww_waste_to_energy_cost_factors = Table(
    'trww_waste_to_energy_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


wali_benefit_of_sanitation_cost_factors = Table(
    'wali_benefit_of_sanitation_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


wali_sanitation_cost_factors = Table(
    'wali_sanitation_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


waso_pollution_cost_factors = Table(
    'waso_pollution_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


waso_waste_collection_cost_factors = Table(
    'waso_waste_collection_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


waso_waste_management_cost_factors = Table(
    'waso_waste_management_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)


waso_waste_to_energy_cost_factors = Table(
    'waso_waste_to_energy_cost_factors', metadata,
    Column('output_variable_name', ForeignKey('tx_table.output_variable_name')),
    Column('difference_variable', String),
    Column('multiplier', DECIMAL),
    Column('multiplier_unit', String),
    Column('annual_change', Boolean),
    Column('output_display_name', String),
    Column('sum', Boolean),
    Column('natural_multiplier_units', String),
    Column('display_notes', String),
    Column('internal_notes', String),
    Column('cb_function', String)
)
