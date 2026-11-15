import pandas as pd
import statsmodels.api as sm
import json

def regress(df):
    
    outcome_variable = df[df.columns[-1]]
    predictor_variables = sm.add_constant(df[df.columns[:-1]])

    return sm.OLS(outcome_variable, predictor_variables).fit()


def get_coef_table(lin_reg):

    coef_df = pd.DataFrame({
        'coef': lin_reg.params.values,
        'pvalue': lin_reg.pvalues.round(4),
        'ci_lower': lin_reg.conf_int()[0],
        'ci_upper': lin_reg.conf_int()[1]
    }, index=lin_reg.params.index)
    
    return coef_df.sort_values(by=["coef"]).drop(["const"])


def create_coefficient_dataframe(res):

    df = pd.DataFrame(index = list(res.params.to_dict().keys())[1:])

    df["coef"] = res.params
    df["ci_low"], df["ci high"] = res.conf_int()[0], res.conf_int()[1]

    df["err_left"], df["err_right"] = df["coef"] - df["ci_low"], df["ci high"] - df["coef"]
    df["pval"] = res.pvalues

    return df.sort_values(by=["coef"], ascending = False)



def save_regression(df, fname):

    df.to_csv(f"data/{fname}.csv")
    df.to_parquet(f"data/{fname}.parquet")



def save_regression_summary(regression_results, file_name):

    with open(f"data/{file_name}.txt", "w") as f:
        f.write(regression_results.summary().as_text())


def save_my_json(my_dict, f_name):

    with open(f"data/{f_name}.json", "w", encoding= "utf-8") as f:
        json.dump(my_dict, f, ensure_ascii=False, indent=4)


def run_regressions_for_r_squared():

    rsquared_and_predictors = {}

    for data_set in ["9.index_with_hood"]:

        df_myData = pd.read_parquet(f"data/{data_set}.parquet")

        outcome_variable = df_myData[df_myData.columns[-1]]
        predictor_variables = sm.add_constant(df_myData[df_myData.columns[:-1]])
        sm.OLS(outcome_variable, predictor_variables).fit().rsquared
        rsquared_and_predictors["all"] = float(sm.OLS(outcome_variable, predictor_variables).fit().rsquared)

        for column in df_myData.columns[:-1]:

            predictor_variables = sm.add_constant(df_myData[df_myData.columns[:-1]]).drop([column], axis = 1)
            sm.OLS(outcome_variable, predictor_variables).fit().rsquared
            rsquared_and_predictors[column] = float(abs(((sm.OLS(outcome_variable, predictor_variables).fit().rsquared - rsquared_and_predictors["all"])/rsquared_and_predictors["all"])*100))


  
    print(rsquared_and_predictors)
    save_my_json(rsquared_and_predictors, "11.r_squared_changes")




def run_regressions():

    for data_set in ["9.index_with_hood"]:
        df_myData = pd.read_parquet(f"data/{data_set}.parquet")
        regression_results = regress(df_myData)
        print(regression_results.summary())
        save_regression_summary(regression_results, "10.regression_summary")
        #save_regression(get_coef_table(regression_results), "10.regression_results")
        save_regression(create_coefficient_dataframe(regression_results), "10.regression_results")
        


def main():

    run_regressions()
    run_regressions_for_r_squared()

main()