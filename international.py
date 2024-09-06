import glob
import numpy as np
import os
import pandas as pd
import re

from utils import *

def international_table(table):
    directory_path = './raw/csv/international'

    # Get list of CSV files
    pattern = '{}/**/*_{}.csv'.format(directory_path, table)
    csv_files = glob.glob(pattern, recursive=True)

    # Read CSV files into a single dataframe
    dataframes = []
    for csv_file in csv_files:
        df = csv_to_dataframe(csv_file, date_parsing=False)
        if df is not None:
            dataframes.append(df)

    # Cleanup columns
    combined_df = pd.concat(dataframes)
    if table == '4':
        combined_df = combined_df.iloc[:, :9]
    combined_df = combined_df[~combined_df.map(lambda x: isinstance(x, str) and "NAME OF THE AIRLINE" in x)]
    combined_df = combined_df[~combined_df.map(lambda x: isinstance(x, str) and "FROM INDIA" in x)]
    combined_df = combined_df[~combined_df.map(lambda x: isinstance(x, str) and "FROM CITY" in x)]
    combined_df = combined_df.dropna()
    combined_df.drop(columns=combined_df.columns[0], axis=1, inplace=True)

    # Assign columns based on table type
    if table == '1':
        combined_df.columns = ['Airline', 'PaxToIndia', 'PaxFromIndia', 'FreightToIndia', 'FreightFromIndia', 'Year', 'Quarter']
        combined_df.sort_values(by=['Airline', 'Year', 'Quarter'], inplace=True)
        filename = 'carrier_quarterly'
    if table == '2':
        combined_df.columns = ['Airline', 'PaxToIndiaM1', 'PaxFromIndiaM1', 'FreightToIndiaM1', 'FreightFromIndiaM1', 'PaxToIndiaM2', 'PaxFromIndiaM2', 'FreightToIndiaM2', 'FreightFromIndiaM2', 'PaxToIndiaM3', 'PaxFromIndiaM3', 'FreightToIndiaM3', 'FreightFromIndiaM3', 'Year', 'Quarter']
        combined_df.sort_values(by=['Airline', 'Year', 'Quarter'], inplace=True)
        filename = 'carrier'
    if table == '3':
        combined_df.columns = ['Country', 'PaxToIndia', 'PaxFromIndia', 'FreightToIndia', 'FreightFromIndia', 'Year', 'Quarter']
        combined_df.sort_values(by=['Country', 'Year', 'Quarter'], inplace=True)
        filename = 'country'
    if table == '4':
        combined_df.columns = ['City1', 'City2', 'PaxToCity2', 'PaxFromCity2', 'FreightToCity2', 'FreightFromCity2', 'Year', 'Quarter']
        combined_df.sort_values(by=['City1', 'City2', 'Year', 'Quarter'], inplace=True)
        filename = 'city'

    # Truncate floats to 2 decimal points for 'Freight' columns
    cols_to_convert = combined_df.columns[combined_df.columns.str.contains('Freight')]
    for col in cols_to_convert:
        combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
    float_format = '{:.2f}'.format

    columns = list(combined_df.columns)

    columns.remove('Year')
    columns.insert(0, 'Year')

    columns.remove('Quarter')
    columns.insert(1, 'Quarter')

    combined_df = combined_df.reindex(columns=columns)

    combined_df.to_csv('aggregated/international/{}.csv'.format(filename), index=False, float_format=float_format)
