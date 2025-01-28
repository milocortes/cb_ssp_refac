
def retrieve_data(
    self,
    cb_orm_strat : Union[CostFactor,TransformationCost],
)

    # Obtenemos datos de las salidas de ssp
    data = self.ssp_data.copy()

    #get the data tables and merge them
    datap_base = data[data["strategy_code"]==cb_orm_strat.strategy_code_base][SSP_GLOBAL_SIMULATION_IDENTIFIERS + [cb_orm.diff_var]].reset_index(drop = True)
    datap_tx   = data[data["strategy_code"]==cb_orm_strat.strategy_code_tx][SSP_GLOBAL_SIMULATION_IDENTIFIERS + [cb_orm.diff_var]].reset_index(drop = True)
    
    datap_base = datap_base.drop(columns=["primary_id", "strategy_code"])

    cb_orm_out = cb_orm_strat.
    
    return datap_base, cb_orm_out



@cb_wrapper
def cb_difference_between_two_strategies(
                    self,
                    datap_base: pd.DataFrame,
                    datap_tx: pd.DataFrame,
                    cb_orm : Union[CostFactor,TransformationCost],
                    ) -> pd.DataFrame:
    
    #
    #   CAN cb_orm STORE UNITS INFORMATION?
    #
    #  use SISEPUEDE units system to make sure everything is in the right units
    #


    tx_suffix = '_tx'
    base_suffix = '_base'

    data_merged = datap_tx.merge(right = datap_base, on =  ['time_period'], suffixes=(tx_suffix, base_suffix))

    #Calculate the difference in variables and then apply the multiplier, which may change over time
    #Assume cost change only begins in 2023

    data_merged["difference_variable"] = cb_orm.diff_var

    data_merged["difference_value"] = data_merged[f"{cb_orm.diff_var}{tx_suffix}"] - data_merged[f"{cb_orm.diff_var}{base_suffix}"]

    data_merged["time_period_for_multiplier_change"] = np.maximum(0, data_merged["time_period"] - SSP_GLOBAL_TIME_PERIOD_2023)

    data_merged["variable"] = cb_orm.output_variable_name

    data_merged["value"] = data_merged["difference_value"]*cb_orm.multiplier*cb_orm.annual_change**data_merged["time_period_for_multiplier_change"]

    data_merged = data_merged[SSP_GLOBAL_COLNAMES_OF_RESULTS]
    

    return data_merged



# by strategy
def wrapper_function(self,
    cb_orm_strat
):

        # retrieve data
        data_base, data_tx, cb_norm = self.retrieve_data(
            region,
            future,
            cb_orm_strat,
        )


        self.cb_difference_between_two_strategies(
            data_base,
            data_tx,
            cb_norm,
        )



def loop_over_region(self, region, ):
     
    # get dat by region

    for future in futures:
        
        self.wrapper_func(...)