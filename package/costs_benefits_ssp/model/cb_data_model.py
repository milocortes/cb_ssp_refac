from sqlalchemy import (Column, Integer, Numeric, String, DateTime,ForeignKey, Float, Boolean)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref


Base = declarative_base()

"""
++++++++++++++++++++++++++++++++
++++++ Cost Factor Tables  +++++
++++++++++++++++++++++++++++++++
"""

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
    include_variant = Column(Float())
    test_id_variant_suffix = Column(String())
    comparison_id_variant = Column(String())
    cb_function = Column(String())
    difference_variable = Column(String())
    multiplier = Column(Float())
    multiplier_unit = Column(String())
    annual_change = Column(Float())
    arg1 = Column(String())
    arg2  = Column(Float())
    sum = Column(Boolean())
    natural_multiplier_units = Column(String())


    tx_table =  relationship("TXTable", backref=backref('transformation_costs', order_by=output_variable_name))

    def __repr__(self):
        return "TransformationCost(\n\t\toutput_variable_name = {self.output_variable_name}," \
                        "\n\t\ttransformation_code = {self.transformation_code},"\
                        "\n\t\tinclude = {self.include},"\
                        "\n\t\tinclude_variant = {self.include_variant},"\
                        "\n\t\ttest_id_variant_suffix = {self.test_id_variant_suffix},"\
                        "\n\t\tcomparison_id_variant = {self.comparison_id_variant},"\
                        "\n\t\tcb_function = {self.cb_function},"\
                        "\n\t\tdifference_variable = {self.difference_variable},"\
                        "\n\t\tmultiplier = {self.multiplier},"\
                        "\n\t\tmultiplier_unit = {self.multiplier_unit},"\
                        "\n\t\tannual_change = {self.annual_change},"\
                        "\n\t\targ1 = {self.arg1},"\
                        "\n\t\targ2 = {self.arg2},"\
                        "\n\t\tsum = {self.sum},"\
                        "\n\t\tnatural_multiplier_units = {self.natural_multiplier_units}) ".format(self=self)


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
        return "CostFactor(\n\t\toutput_variable_name = {self.output_variable_name}," \
                      "\n\t\tdifference_variable = {self.difference_variable},"\
                      "\n\t\tmultiplier = {self.multiplier},"\
                      "\n\t\tmultiplier_unit = {self.multiplier_unit},"\
                      "\n\t\tannual_change = {self.annual_change},"\
                      "\n\t\toutput_display_name = {self.output_display_name},"\
                      "\n\t\tsum = {self.sum},"\
                      "\n\t\tnatural_multiplier_units = {self.natural_multiplier_units},"\
                      "\n\t\tdisplay_notes = {self.display_notes},"\
                      "\n\t\tinternal_notes = {self.internal_notes},"\
                      "\n\t\tcb_function = {self.cb_function},"\
                      "\n\t\tcb_var_group = {self.cb_var_group}) ".format(self=self)

"""
++++++++++++++++++++++++++++++++
++++++ SSP Attributes Tables  ++
++++++++++++++++++++++++++++++++
"""

class CountriesISO(Base):
    __tablename__ = "countries_by_iso"

    iso_code3 = Column(String(), primary_key=True)  
    category_name = Column(String())          
    region = Column(String())  
    fao_area_code = Column(String())    
    world_bank_global_region = Column(String())


class AttDimTimePeriod(Base):
    __tablename__ = "attribute_dim_time_period"

    time_period = Column(Float(), primary_key=True)
    year = Column(Float())

class AttTransformationCode(Base):
    __tablename__ = "attribute_transformation_code"

    transformation_code = Column(String(), primary_key=True)
    transformation = Column(String())
    transformation_id = Column(String())
    sector = Column(String(), nullable=True)
    description = Column(String(), nullable=True)

"""
++++++++++++++++++++++++++++++++++++
++++++ Strategy Specific CB Files ++
++++++++++++++++++++++++++++++++++++
"""

class AgrcLVSTProductivityCostGDP(Base):
    __tablename__ = "agrc_lvst_productivity_costgdp"

    iso_code3 = Column(String(), ForeignKey('countries_by_iso.iso_code3'), primary_key=True)
    cost_of_productivity_improvements_pct_gdp = Column(Float())
    cost_of_productivity_improvements_pct_gdp_orig = Column(Float())

class AgrcRiceMGMTTX(Base):
    __tablename__ = "agrc_rice_mgmt_tx"

    time_period = Column(Float(), ForeignKey('attribute_dim_time_period.time_period'), primary_key=True)
    ef_agrc_anaerobicdom_rice_kg_ch4_ha = Column(Float())

class ENTCReduceLosses(Base):
    __tablename__ = "entc_reduce_losses_cost_file"

    iso_code3 = Column(String(), ForeignKey('countries_by_iso.iso_code3'), primary_key=True)
    annual_investment_USD = Column(Float())

class IPPUCCSCostFactor(Base):
    __tablename__ = "ippu_ccs_cost_factors"

    variable = Column(String(), primary_key = True)
    multiplier = Column(Float())
    multiplier_unit = Column(String())
    annual_change  = Column(Float())
    output_variable_name = Column(String())
    output_display_name = Column(String())
    sum = Column(Float())
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

    time_period = Column(Float(), ForeignKey('attribute_dim_time_period.time_period'), primary_key=True)
    frac_gnrl_w_original_diet = Column(Float())

class WALISanitationClassificationSP(Base):
    __tablename__ = "wali_sanitation_classification"


    variable = Column(String(), primary_key = True)
    difference_variable = Column(String())
    population_variable = Column(String())
