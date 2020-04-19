import os
import pandas as pd
import tabula

def read_budgets(directory):
    budgets = []
    for filename in os.listdir(directory):
        budget_tables = tabula.read_pdf(
            f"{directory}/{filename}",
            multiple_tables=True
        )
        budgets.append(budget_tables)

    return budgets


# this takes a while
budgets = read_budgets("SY1819_School_Budgets")
def generate_basic_information_table(df):
    '''Series representing the "basic information" table.'''


    if df.shape[1] == 3:
        df = df.iloc[1:, 1:]
        df = df.reset_index(drop=True)
        df = df.T.reset_index(drop=True).T




    df.loc[4] = ["Economically Disadvantaged Rate", df.loc[6, 1]]
    df = df.loc[1:4, :]
    return pd.Series(list(df[1]), index=list(df[0]), name='basic_information')

def generate_enrollment_table(df):
    '''returns a series representing the "enrollment" table'''
    # nothing too crazy here
    df = df.T.loc[1:, :]
    df_to_series = pd.Series(list(df[1]), index=list(df[0]), name="enrollment")
    return df_to_series.str.replace(',', '').astype(float)

generate_enrollment_table(enrollment)

def generate_allotments_table(df, code, fund):
    '''Multiindex DF of org code, fund, and budget category by budget year'''
    df.columns = df.iloc[0]
    df = df.drop(0)
    df = df.set_index(['Position/Expenditure'])
    df = (df.apply(lambda x: x.str.replace('$', '').str.replace(',', ''))
            .astype(float)
          )
    df.name = fund + "ed_allotments"

    df_index_arrays = [
        [code] * len(df),
        [fund] * len(df),
        list(df.index),
    ]

    df.index = pd.MultiIndex.from_arrays(
        df_index_arrays,
        names=("org_code", "fund", "allotment")
    )
    df.columns = [column[:4] for column in df.columns]

    return df

def generate_all_tables(list_of_df):
    basic_information = generate_basic_information_table(list_of_df[0])
    enrollment = generate_enrollment_table(list_of_df[1])

    operating_funded_allotments = generate_allotments_table(
        list_of_df[2],
        basic_information['Organization Code'],
        'operating_fund'
    )
    grant_funded_allotments = generate_allotments_table(
        list_of_df[3],
        basic_information['Organization Code'],
        'grant_fund'
    )
    operating_and_grant_funded_allotments = pd.concat(
        [operating_funded_allotments, grant_funded_allotments]
    )

    return basic_information, enrollment, operating_and_grant_funded_allotments

basic_information, enrollment, operating_and_grant_funded_allotments =
generate_all_tables(sample_budget)

def generate_row(budget_year, basic_information, allotments, enrollment):
    '''School budget series for fiscal year.'''
 	# budget_year should be FY14, FY18, or FY19

    flattened_allotments = pd.DataFrame(allotments.to_records())
    flattened_allotments.index = flattened_allotments['fund'] +": " + flattened_allotments['allotment']
    flattened_allotments = flattened_allotments.drop(
        ['fund','allotment'], axis=1
    )
    budget_allotments = flattened_allotments[budget_year]

    enrollment_label = budget_year + ' Projected' if budget_year == "FY19" else budget_year
    enrollment_index = 'projected_enrollment' if budget_year == "FY19" else 'enrollment'
    enrollment_row = pd.Series(
        enrollment[enrollment_label], index=[enrollment_index]
    )

    return pd.concat(
            [basic_information,budget_allotments,enrollment_row],
            axis=0
           )

generate_row("FY18", basic_information,
             operating_and_grant_funded_allotments, enrollment)

def generate_tabular_budget(budget_year, budgets):
    '''generate a tabular budget summary for a budget year. Budget year must be FY14,
    FY18, or FY19. Enrollemnt values for budget year 2019 are projected.'''
    school_budget_series = []
    for budget_tables in budgets:
        basic_information, enrollment, operating_and_grant_funded_allotments = generate_all_tables(
            budget_tables
        )
        budget_row = generate_row(
            budget_year, basic_information, operating_and_grant_funded_allotments, enrollment
        )
        budget_row = budget_row
        school_budget_series.append(budget_row)

    return pd.DataFrame(school_budget_series)


fy14 = generate_tabular_budget('FY14', budgets)
fy14['budget_year'] = "FY14"
fy14.to_csv("output/combined_fy14.excel")

fy18 = generate_tabular_budget('FY18', budgets)
fy18['budget_year'] = "FY18"
fy18.to_csv("output/combined_fy18.excel")

fy19 = generate_tabular_budget('FY19', budgets)
fy19['budget_year'] = "FY19"
fy19.to_csv("output/combined_fy19.excel")


combined_tabular_budgets = pd.concat([fy14, fy18, fy19])
combined_tabular_budgets.to_csv("output/all_budgets_tabular.excel")

def generate_hierarchical_budget(budgets):
    school_budgets_dfs = []
    for budget_tables in budgets:
        school_budgets_dfs.append(operating_and_grant_funded_allotments)
    return pd.concat(school_budgets_dfs)

hierarchical_budget = generate_hierarchical_budget(budgets)
hierarchical_budget.to_csv("output/all_budgets_hierarchical.csv")

hierarchical_budget