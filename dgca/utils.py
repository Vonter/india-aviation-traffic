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

    "FEBURUARY": "02",

    "AUG*": "08", "SEP*": "09", "SEPT*": "09", "OCT*": "10", "NOV*": "11", "DEC*": "12",
}

airline_mapping = {
    "Air Asia": "AirAsia India",
    "Air India": "Air India",
    "Airline": "Generic Airline",
    "Flybig": "Flybig",
    "Spicejet": "SpiceJet",
    "TruJet": "TruJet",
    "TrueJet": "TruJet",
    "Trujet": "TruJet",
    "air deccan": "Air Deccan",
    "air heritage": "Air Heritage",
    "air india": "Air India",
    "air india express": "Air India Express",
    "air taxi": "Air Taxi",
    "airasia": "AirAsia India",
    "aircarnival": "Air Carnival",
    "aircosta": "Air Costa",
    "airheritage": "Air Heritage",
    "airindia": "Air India",
    "airindiaexpress": "Air India Express",
    "airodisha": "Air Odisha",
    "airpegasus": "Air Pegasus",
    "aix connect": "AIX Connect",
    "aix connect ": "AIX Connect",
    "akasa air": "Akasa Air",
    "akasa air ": "Akasa Air",
    "alliance": "Alliance Air",
    "alliance air": "Alliance Air",
    "bluedart": "Blue Dart Aviation",
    "deccanair": "Air Deccan",
    "fly": "Fly91",
    "fly ": "Fly91",
    "go air": "Go First",
    "goair": "Go First",
    "india one air": "India One Air",
    "indigo": "IndiGo",
    "jetairways": "Jet Airways",
    "jetlite": "JetLite",
    "pawan hans": "Pawan Hans",
    "pawanhans": "Pawan Hans",
    "quikjetcargo": "QuikJet Cargo",
    "spicejet": "SpiceJet",
    "star air": "Star Air",
    "starair": "Star Air",
    "totaldom": "Total Domestic",
    "totalint": "Total International",
    "trujet": "TruJet",
    "vistara": "Vistara",
    "zoomair": "Zoom Air"
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

def append_columns(df, filename, domestic, table):

    if domestic and table == 'city':
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
    
    if domestic and table == 'carrier':
        year = filename[-2:] 
        df['Year'] = int("20{}".format(year))
        df['Airline'] = filename
        
        masks = []
        patterns = [
            'NON.*SCH.*INTER',
            'SCH.*INTER',
            'NON.*SCH.*DOM',
            'SCH.*DOM'
        ]
        for col in df.columns:
            masks.append(df[col].astype(str).str.contains('|'.join(patterns), na=False, case=False, regex=True))
        matching_indices = df.index[pd.concat(masks, axis=1).any(axis=1)].tolist()
        matching_indices.append(len(df))

        pattern_mapping = {
            r'NON.*SCH.*INTER': "NonScheduledInternational",
            r'SCH.*INTER': "ScheduledInternational",
            r'NON.*SCH.*DOM': "NonScheduledDomestic",
            r'SCH.*DOM': "ScheduledDomestic"
        }
        for index in range(0, len(matching_indices) - 1):
            row = df.loc[matching_indices[index]]
            for pattern, value in pattern_mapping.items():
                if any(re.search(pattern, str(cell), re.IGNORECASE) for cell in row):
                    df.loc[matching_indices[index]:matching_indices[index + 1], 'Type'] = value
                    break

    if not domestic:
        year = filename[0:2]
        quarter = filename[3]
        df['Year'] = year
        df['Quarter'] = quarter

    return df

def csv_to_dataframe(csv_file, domestic, table):
    #try:
    df = pd.read_csv(csv_file, header=None)
    filename = csv_file.split("/")[-1].replace(".csv", "").replace("%20", "")

    df = append_columns(df, filename, domestic, table)

    return df

#    except Exception as e:
#        print(f"Error parsing {csv_file}: {e}")
#        return None
