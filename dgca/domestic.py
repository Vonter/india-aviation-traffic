import glob
import numpy as np
import os
import pandas as pd
import re

from utils import *

def domestic_table_city():
    directory_path = './raw/csv/domestic'

    pattern = f'{directory_path}/**/*CITYPAIR*.csv'
    csv_files = glob.glob(pattern, recursive=True)

    dataframes = []
    for csv_file in csv_files:
        df = csv_to_dataframe(csv_file, domestic=True, table='city')
        if df is not None:
            dataframes.append(df)

    combined_df = pd.concat(dataframes)

    combined_df = combined_df.iloc[:, :11]
    combined_df = combined_df[~combined_df.map(lambda x: isinstance(x, str) and "NAME OF THE AIRLINE" in x)]
    combined_df = combined_df[~combined_df.map(lambda x: isinstance(x, str) and "TO CITY" in x)]

    fingerprint_columns = combined_df.columns[:4].tolist()
    combined_df = combined_df.dropna(subset=fingerprint_columns, how='any')

    combined_df.drop(columns=combined_df.columns[0], axis=1, inplace=True)

    moved_column = combined_df.pop('Year')
    combined_df['Year'] = moved_column
    moved_column = combined_df.pop('Month')
    combined_df['Month'] = moved_column

    combined_df.columns = ['City1', 'City2', 'PaxToCity2', 'PaxFromCity2', 'FreightToCity2', 'FreightFromCity2', 'MailToCity2', 'MailFromCity2', 'Year', 'Month']

    combined_df['City1'] = combined_df['City1'].str.lstrip()
    combined_df['City2'] = combined_df['City2'].str.lstrip()

    combined_df.sort_values(by=['City1', 'City2', 'Year', 'Month'], inplace=True)

    combined_df = combined_df.map(lambda x: '0' if isinstance(x, str) and x == '-' else x)

    combined_df['PaxToCity2'] = pd.to_numeric(combined_df['PaxToCity2'], errors='coerce')
    combined_df['PaxFromCity2'] = pd.to_numeric(combined_df['PaxFromCity2'], errors='coerce')
    combined_df['FreightToCity2'] = pd.to_numeric(combined_df['FreightToCity2'], errors='coerce')
    combined_df['FreightFromCity2'] = pd.to_numeric(combined_df['FreightFromCity2'], errors='coerce')
    combined_df['MailToCity2'] = pd.to_numeric(combined_df['MailToCity2'], errors='coerce')
    combined_df['MailFromCity2'] = pd.to_numeric(combined_df['MailFromCity2'], errors='coerce')
    float_format = '{:.2f}'.format

    columns = list(combined_df.columns)

    columns.remove('Year')
    columns.insert(0, 'Year')

    columns.remove('Month')
    columns.insert(1, 'Month')

    combined_df = combined_df.reindex(columns=columns)

    combined_df.to_csv('../aggregated/domestic/city.csv', index=False, float_format=float_format)

def domestic_table_carrier():
    directory_path = './raw/csv/domestic'

    all_files = glob.glob(f'{directory_path}/**/*', recursive=True)
    csv_files = [f for f in all_files if "CITYPAIR" not in f]

    dataframes = []
    for csv_file in csv_files:
        df = csv_to_dataframe(csv_file, domestic=True, table='carrier')
        if df is not None:
            dataframes.append(df)

    combined_df = pd.concat(dataframes)

    # Filter rows where the first column contains any month name
    months = ['january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december',
              'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN'
              'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
              'JUNE', 'JULY']
    combined_df = combined_df[combined_df[combined_df.columns[0]].str.contains('|'.join(months), na=False)]

    combined_df = combined_df.iloc[:, :20]
    fingerprint_columns = combined_df.columns[:4].tolist()
    combined_df = combined_df.dropna(subset=fingerprint_columns, how='any')

    combined_df.columns = ['Month', 'Aircraft Number', 'Aircraft Hours', 'Aircraft Kilometres', 'Passenger Number', 'Passenger Kilometers', 'Seat Kilometers', 'Passenger Load Factor', 'Freight', 'Mail', 'Total Cargo', 'Passenger Tonne Kilometer', 'Mail Tonne Kilometer', 'Freight Tonne Kilometer', 'Total Tonne Kilometer', 'Available Tonne Kilometer', 'Weight Load Factor', 'Year', 'Airline', 'Type']

    combined_df['Month'] = combined_df['Month'].str.rstrip()
    combined_df['Month'] = combined_df['Month'].replace(month_mapping)
    combined_df['Airline'] = combined_df['Airline'].str.replace('\d+', '', regex=True)
    combined_df['Airline'] = combined_df['Airline'].replace(airline_mapping)

    combined_df.sort_values(by=['Type', 'Airline', 'Year', 'Month'], inplace=True)
    combined_df = combined_df.map(lambda x: '0' if isinstance(x, str) and x == '-' else x)

    columns = list(combined_df.columns)

    columns.remove('Type')
    columns.insert(0, 'Type')

    columns.remove('Airline')
    columns.insert(1, 'Airline')

    columns.remove('Year')
    columns.insert(2, 'Year')

    columns.remove('Month')
    columns.insert(3, 'Month')

    combined_df = combined_df.reindex(columns=columns)

    float_format = '{:.3f}'.format
    for col in combined_df.columns[4:20]:
        combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')

    print(combined_df)

    combined_df.to_csv('../aggregated/domestic/carrier.csv', index=False, float_format=float_format)
