import glob
import numpy as np
import os
import pandas as pd
import re

from dateutil.parser import parse

month_mapping = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
    "SEP": "09", "SEPT": "09", "OCT": "10", "NOV": "11", "DEC": "12",
    "JANUARY": "01", "FEBRUARY": "02", "MARCH": "03", "APRIL": "04",
    "MAY": "05", "JUNE": "06", "JULY": "07", "AUGUST": "08",
    "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11", "DECEMBER": "12",
    "FEBURUARY": "02"
}
pattern = r'(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|FEBURUARY)[\s,]*()\d{4}\b'

def map_string_to_date(string):
    match = re.search(pattern, string.upper())
    if match:
        match_string = match.group().strip().replace(",", "")

        year = ''.join([char for char in match_string if char.isdigit()]).lstrip().rstrip()

        month = ''.join([char for char in match_string if not char.isdigit()]).lstrip().rstrip()
        month = month.replace(month, month_mapping[month], 1)

        parsed_date = parse("{}/{}".format(year, month), fuzzy=True)

        return parsed_date.strftime("%y/%m")

def csv_to_dataframe(csv_file, date_parsing):
    try:
        df = pd.read_csv(csv_file, header=None)
        filename = csv_file.split("/")[-1].replace(".csv", "").replace("%20", "")

        if date_parsing:
            date = map_string_to_date(filename)
            year = "20{}".format(date.split("/")[0])
            month = date.split("/")[1]

            # Edge case for August 2015
            if year == '2015' and month == '08':
                df.columns = [int(col) + 1 for col in df.columns[0:4]]
                df.insert(0, 0, 1, True)
                df = df.iloc[2:]

            df['Year'] = year
            df['Month'] = month
        else:
            year = filename[0:2]
            quarter = filename[3]

            df['Year'] = year
            df['Quarter'] = quarter

        return df

    except Exception as e:
        print(f"Error parsing {csv_file}: {e}")
        return None
