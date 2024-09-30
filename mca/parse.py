import os
from glob import glob
from bs4 import BeautifulSoup
import pandas as pd

from dateutil import parser

def parse_html_type1(soup, html_file):

    daily_data = {}

    # Find div tags with class "airport-col"
    airport_cols = soup.find_all('div', class_='airport-col')

    # Extract date from filename
    try:
        col = airport_cols[0].find_all('h2')[0]
        span = col.find_all('span')[-1]
        text = span.text
        date = parser.parse(text, fuzzy=True).date()
        daily_data["Date"] = str(date)
    except:
        pass
    
    # Extract content from div tags
    for col in airport_cols:
        try:
            category = []
            for h2 in col.find_all('h2'):
                for span in h2.find_all('span'):
                    span.decompose()
                h2_text = h2.get_text()
                category = h2_text.rstrip(" ").lstrip(" ")
        except:
            pass

        list_items = col.find_all('li')

        for item in list_items:

            try:
                span_items = item.find_all('span')
                span_data = [span_items[0].get_text(strip=True).title(), span_items[1].get_text(strip=True)]
                daily_data["{} ({})".format(category, span_data[0])] = span_data[1]
            except:
                pass

    return daily_data

def parse_html_type2(soup, html_file):

    daily_data = {}

    # Find div tags with class "paragraph"
    airport_cols = soup.find_all('div', class_='paragraph')

    # Extract date from filename
    try:
        span_text = soup.find_all('span', class_='date-widget')[0].text
        date = parser.parse(span_text, fuzzy=True).date()
        daily_data["Date"] = str(date)
    except:
        pass
    
    # Extract content from div tags
    for col in airport_cols:
        try:
            try:
                category = col.parent.parent.parent.parent.find_all('span', class_='eng-title')[0].text.rstrip(" ").lstrip(" ")
            except:
                pass

            divs = col.find_all('div')
            for div in divs:
                if 'field--name-field-hintdi-text' in div['class']:
                    divs.remove(div)
            divs_data = [divs[0].get_text(strip=True).title(), divs[1].get_text(strip=True)]
            daily_data["{} ({})".format(category, divs_data[0])] = divs_data[1]
        except:
            pass

    return daily_data

def replace_column_names(df):
    df.columns = df.columns.str.replace("Air Sewa Grievances (by entity)", "Grievances")
    df.columns = df.columns.str.replace("Air Sewa Grievances (by type)", "Grievances")
    df.columns = df.columns.str.replace("Air Sewa Grievances (by volume)", "Grievances")
    df.columns = df.columns.str.replace("Grievances (by entity)", "Grievances")
    df.columns = df.columns.str.replace("Grievances (by type)", "Grievances")
    df.columns = df.columns.str.replace("Grievances (by volume)", "Grievances")
    df.columns = df.columns.str.replace("Domestic Flight", "Domestic")
    df.columns = df.columns.str.replace("Domestic traffic", "Domestic")
    df.columns = df.columns.str.replace("International Flight", "International")
    df.columns = df.columns.str.replace("International traffic", "International")
    df.columns = df.columns.str.replace("Pax Load Factor", "Passenger Load Factor")
    df.columns = df.columns.str.replace("VBM - Air India Group", "Vande Bharat Mission")
    
    return df

def extract_before_space(s):
    split_s = s.split(maxsplit=1)
    return split_s[0] if len(split_s) > 1 else s

def safe_concatenate(df, cols, sep='', new_col='Concatenated'):
    # Convert all columns to string type
    df[cols] = df[cols].astype(str)
    
    # Concatenate the columns
    df[new_col] = df[cols].apply(lambda row: sep.join(row.values), axis=1).replace("nan", "")
    
    return df

def merge_duplicated_columns(df):
    duplicate_cols = df.columns[df.columns.duplicated()].tolist()

    for col in duplicate_cols:
        cols_to_concat = df.columns[df.columns == col].tolist()
        df[col + '_concat'] = df[cols_to_concat].apply(lambda x: ' '.join(x.astype(str)), axis=1)

    df.drop(columns=duplicate_cols, inplace=True)
    df.replace(r'nan', '', regex=True, inplace=True)

    for col in df.columns:
        df[col] = df[col].apply(extract_before_space)

    df.replace(r',', '', regex=True, inplace=True)
    df.replace(r' ', '', regex=True, inplace=True)
    df.columns = df.columns.str.replace('_concat', '')

    return df

def merge_columns(df, columns, column_name):

    # Check if all specified columns exist in the DataFrame
    if not all(col in df.columns for col in columns):
        raise ValueError(f"The DataFrame does not contain all specified columns: {columns}")

    # Save all columns as String type
    df[columns] = df[columns].astype(str)
    # Merge columns into a new temporary column
    df['temp'] = df[columns].sum(1)
    # Drop original merged columns
    df = df.drop(columns, axis=1)
    # Rename temporary column
    df = df.rename(columns={'temp': column_name})
    # Remove NaN string occurrences
    df[column_name] = df[column_name].str.replace("nan", "")

    return df

def retain_last_row(df, column):

    # Drop duplicates keeping last occurrence
    df = df.drop_duplicates(subset=column, keep='last')
    
    return df

def is_blank_column(col):
    return col.isnull().all()

def generate_dataframe():
    # Initialize an empty list to store extracted data
    extracted_data = []

    # Find all HTML files recursively
    for html_file in glob(os.path.join(html_dir, "**/*.html"), recursive=True):
        
        print("Parsing {}".format(html_file))

        # Open the HTML file
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
        except:
            continue

        # Parse the HTML file
        daily_data = {}
        if len(daily_data.keys()) < 3:
            daily_data = parse_html_type1(soup, html_file)
        if len(daily_data.keys()) < 3:
            daily_data = parse_html_type2(soup, html_file)

        # Save the HTML contents
        if len(daily_data.keys()) < 3:
            pass
        else:
            extracted_data.append(daily_data)

    # Convert the list to a pandas DataFrame
    df = pd.DataFrame(extracted_data)

    return df

def parse_dataframe(df):
    df = df.astype(str)

    # Rename column headers
    df = replace_column_names(df)

    # Merge duplicated columns
    df = merge_duplicated_columns(df)
    df = merge_duplicated_columns(df)
    
    df = merge_columns(df, ['Airports (State Govt./ Private)', 'Airports (State Govt./Private)'], 'Airports (State Govt/Private)')
    df = merge_columns(df, ['Grievances (Air Aisa India)', 'Grievances (Air Asia Behrad)', 'Grievances (Air Asia Berhad (Int.))', 'Grievances (Airasia India)', 'Grievances (Air Asia)', 'Grievances (Air Asia Berhad)', 'Grievances (Air Asia India)'], 'Grievances (Air Asia)')
    df = merge_columns(df, ['Grievances (Air Seychelles)', 'Grievances (Air Sychelles)'], 'Grievances (Air Seychelles)')
    df = merge_columns(df, ['Grievances (Akasa  Air)', 'Grievances (Akasa Air)', 'Grievances (Akasa)', 'Grievances (Akasha Air)'], 'Grievances (Akasa Air)')
    df = merge_columns(df, ['Grievances (Alliance Air)', 'Grievances (Alliance  Air)', 'Grievances (Alliance Air (India))', 'Grievances (Alliance)'], 'Grievances (Alliance Air)')
    df = merge_columns(df, ['Grievances (Delhi Airport)', 'Grievances (Delhi  Airport)', 'Grievances (Delhi)'], 'Grievances (Delhi Airport)')
    df = merge_columns(df, ['Grievances (Egypt Air)', 'Grievances (Egypt)'], 'Grievances (Egypt Air)')
    df = merge_columns(df, ['Grievances (Eminrates Airlines)', 'Grievances (Emirates  Airline)', 'Grievances (Emirates Airline)', 'Grievances (Emirates Airlines)', 'Grievances (Emirates)'], 'Grievances (Eminrates Airlines)')
    df = merge_columns(df, ['Grievances (Ethiopian Airlines)', 'Grievances (Ethiopian)'], 'Grievances (Ethiopian Airlines)')
    df = merge_columns(df, ['Grievances (Etihad Airway)', 'Grievances (Etihad Airways)', 'Grievances (Etihad)'], 'Grievances (Etihad Airways)')
    df = merge_columns(df, ['Grievances (Go Air)', 'Grievances (Go First)', 'Grievances (Goair)', 'Grievances (Gofirst)'], 'Grievances (GoAir)')
    df = merge_columns(df, ['Grievances (Indi Go)', 'Grievances (Indogo)', 'Grievances (Indigo)'], 'Grievances (IndiGo)')
    df = merge_columns(df, ['Grievances (Klm Airlines)', 'Grievances (Klm)'], 'Grievances (KLM Airlines)')
    df = merge_columns(df, ['Grievances (Malda Airport)', 'Grievances (Malda)'], 'Grievances (Malda Airport)')
    df = merge_columns(df, ['Grievances (Malaysia Airlines)', 'Grievances (Malaysia)'], 'Grievances (Malaysia Airlines)')
    df = merge_columns(df, ['Grievances (Malindo  Airways)', 'Grievances (Malindo Airways)'], 'Grievances (Malindo Airways)')
    df = merge_columns(df, ['Grievances (Qatar Airways)', 'Grievances (Qatar Airway)', 'Grievances (Qatar)'], 'Grievances (Qatar Airways)')
    df = merge_columns(df, ['Grievances (Singapore Airline)', 'Grievances (Singapore Airlines)'], 'Grievances (Singapore Airline)')
    df = merge_columns(df, ['Grievances (Srilankan Airlines)', 'Grievances (Srilankan Airways)'], 'Grievances (Srilankan Airlines)')
    df = merge_columns(df, ['Grievances (Swiss Air)', 'Grievances (Swiss Airlines)', 'Grievances (Swiss Airways)'], 'Grievances (Swiss Air)')
    df = merge_columns(df, ['Grievances (Viejet Air)', 'Grievances (Viet Jet Air)', 'Grievances (Viet Jet)', 'Grievances (Vietjet Air)', 'Grievances (Vietjet)', 'Grievances (Vietjetair)'], 'Grievances (Viet Jet)')
    df = merge_columns(df, ['Grievances (Virgin Atlantic)', 'Grievances (Virgin Atlantica)'], 'Grievances (Virgin Atlantic)')
    df = merge_columns(df, ['Grievances (Vistara Airlines)', 'Grievances (Vistara)'], 'Grievances (Vistara)')
        
    df = merge_columns(df, ['Domestic (Arrival Flights)', 'Domestic (Arriving Flights)'], 'Domestic (Arrival Flights)')
    df = merge_columns(df, ['Domestic (Departure Flights)', 'Domestic (Departing Flights)'], 'Domestic (Departure Flights)')
    df = merge_columns(df, ['International (Arrival Flights)', 'International (Arriving Flights)'], 'International (Arrival Flights)')
    df = merge_columns(df, ['International (Departure Flights)', 'International (Departing Flights)'], 'International (Departure Flights)')

    df = merge_columns(df, ['Passenger Load Factor (Go First)', 'Passenger Load Factor (Go First*)'], 'Passenger Load Factor (GoAir)')
    df = merge_columns(df, ['Passenger Load Factor (Air Asia India)', 'Passenger Load Factor (Aix Connect)'], 'Passenger Load Factor (Air Asia India)')

    df = merge_columns(df, ['Krishi UDAN (Others (Mt))', 'Krishi UDAN (Others)'], 'Krishi UDAN (Others)')
    df = merge_columns(df, ['Krishi UDAN (Perishable (Mt))', 'Krishi UDAN (Pershable)'], 'Krishi UDAN (Perishable)')
    df = merge_columns(df, ['Krishi UDAN (Total (Mt))', 'Krishi UDAN (Total)'], 'Krishi UDAN (Total)')

    df = merge_columns(df, ['Skilling by IGRUA (Students Pass Out)', 'Skilling by IGRUA (Students Passout)'], 'Skilling by IGRUA (Students Pass Out)')

    df = merge_columns(df, ['UDAN (RCS) (Subsidy)', 'UDAN (RCS) (Viability Gap Funding)'], 'UDAN (RCS) (Subsidy)')

    df = merge_columns(df, ['On Time Performance (Go First)', 'On Time Performance (Go First*)', 'On Time Performance (Goair)'], 'On Time Performance (GoAir)')
    df = merge_columns(df, ['On Time Performance (Air Asia India)', 'On Time Performance (Aix Connect)'], 'On Time Performance (Air Asia)')

    df = merge_columns(df, ['Drones (Exempted Orgn)', 'Drones (Exempted Projects)'], 'Drones (Exempted Projects)')

    df = merge_columns(df, ['Passenger Load Factor (GoAir)', 'Passenger Load Factor (Goair)'], 'Passenger Load Factor (GoAir)')
    
    # Remove duplicate rows
    df = retain_last_row(df, 'Date')

    # Remove commas
    df = df.apply(lambda x: x.str.replace(',', '') if isinstance(x, str) else x)

    # Convert to integer
    df = df.fillna(0)
    for col in df.columns:
        try:
            df[col] = df[col].str.replace(',', '').astype(int)
        except Exception as e:
            pass

    # Drop blank columns
    blank_columns = df.columns[df.apply(is_blank_column)].tolist()
    df = df.drop(blank_columns, axis=1)
    
    # Re-order columns
    df = df.reindex(columns=['Date', 'Domestic (Aircraft Movements)', 'Domestic (Airport Footfalls)', 'Domestic (Arrival Flights)', 'Domestic (Arriving Pax)', 'Domestic (Departing Pax)', 'Domestic (Departure Flights)', 'International (Aircraft Movements)', 'International (Airport Footfalls)', 'International (Arrival Flights)', 'International (Arriving Pax)', 'International (Departing Pax)', 'International (Departure Flights)', 'Cargo (In MT) (Inbound (Dom))', 'Cargo (In MT) (Inbound (Int))', 'Cargo (In MT) (Outbound (Dom))', 'Cargo (In MT) (Outbound (Int))', 'Cargo (In MT) (Total (Dom))', 'Cargo (In MT) (Total (Int))', 'On Time Performance (Air Asia)', 'On Time Performance (Air India)', 'On Time Performance (Akasa Air)', 'On Time Performance (Alliance Air)', 'On Time Performance (GoAir)', 'On Time Performance (Indigo)', 'On Time Performance (Spicejet)', 'On Time Performance (Vistara)', 'Passenger Load Factor (Air Asia India)', 'Passenger Load Factor (Air India)', 'Passenger Load Factor (Akasa Air)', 'Passenger Load Factor (Alliance Air)', 'Passenger Load Factor (GoAir)', 'Passenger Load Factor (Indigo)', 'Passenger Load Factor (Spicejet)', 'Passenger Load Factor (Vistara)', 'Grievances (Aeroflot)', 'Grievances (Air Arabia)', 'Grievances (Air Asia)', 'Grievances (Air Astana)', 'Grievances (Air Canada)', 'Grievances (Air China)', 'Grievances (Air France)', 'Grievances (Air India Express)', 'Grievances (Air India)', 'Grievances (Air Seychelles)', 'Grievances (Aix Connect)', 'Grievances (Aizwal Airport)', 'Grievances (Akasa Air)', 'Grievances (Alliance Air)', 'Grievances (Baggage)', 'Grievances (Bangkok Airways)', 'Grievances (Bcas)', 'Grievances (British Airways)', 'Grievances (Check-In)', 'Grievances (Chennai Airport)', 'Grievances (Cisf)', 'Grievances (Customs)', 'Grievances (Delhi Airport)', 'Grievances (Delta Airlines)', 'Grievances (Dgca)', 'Grievances (Egypt Air)', 'Grievances (Eminrates Airlines)', 'Grievances (Ethiopian Airlines)', 'Grievances (Etihad Airways)', 'Grievances (Fly Dubai)', 'Grievances (Flybig)', 'Grievances (GoAir)', 'Grievances (Gulf Air)', 'Grievances (Immigration)', 'Grievances (IndiGo)', 'Grievances (KLM Airlines)', 'Grievances (Kenya Airways)', 'Grievances (Kolkata Airport)', 'Grievances (Lucknow)', 'Grievances (Lufthansa)', 'Grievances (Malaysia Airlines)', 'Grievances (Malda Airport)', 'Grievances (Malindo Airways)', 'Grievances (Meals)', 'Grievances (Mumbai Airport)', 'Grievances (Nepal Airlines)', 'Grievances (Others)', 'Grievances (Pawan Hans)', 'Grievances (Pending (D))', 'Grievances (Pending (Till Date))', 'Grievances (Pending (Ytd))', 'Grievances (Pending)', 'Grievances (Qatar Airways)', 'Grievances (Received (D))', 'Grievances (Received (Till Date))', 'Grievances (Received (Ytd))', 'Grievances (Received)', 'Grievances (Refunds)', 'Grievances (Resolved (D))', 'Grievances (Resolved (Till Date))', 'Grievances (Resolved (Ytd))', 'Grievances (Resolved)', 'Grievances (Security Check)', 'Grievances (Security)', 'Grievances (Singapore Airline)', 'Grievances (Spicejet)', 'Grievances (Srilankan Airlines)', 'Grievances (Star Air)', 'Grievances (Swiss Air)', 'Grievances (Thai Airways)', 'Grievances (Trujet)', 'Grievances (Turkish Airlines)', 'Grievances (United Airlines)', 'Grievances (Viet Jet)', 'Grievances (Virgin Atlantic)', 'Grievances (Vistara)', 'Airports (Custom)', 'Airports (Domestic*)', 'Airports (International*)', 'Airports (Joint Venture International)', 'Airports (Operational)', 'Airports (State Govt/Private)', 'Drones (An Issued)', 'Drones (Certified Pilots)', 'Drones (Dan Issued)', 'Drones (Drone Schools)', 'Drones (Exempted Projects)', 'Drones (Models Approved)', 'Drones (Trainers)', 'Drones (Type Certificates)', 'Drones (Uin Issued)', 'Flying Training Organizations (Base Ftos)', 'Flying Training Organizations (Opeational Bases)', 'Flying Training Organizations (Total Ftos)', 'Flying Training Organizations (Upcoming Ftos)', 'Krishi UDAN (Airports*)', 'Krishi UDAN (Others)', 'Krishi UDAN (Perishable)', 'Krishi UDAN (Total)', 'Skilling by AASSC (Assessors Certified)', 'Skilling by AASSC (Candidates Certified)', 'Skilling by AASSC (Job Roles Developed)', 'Skilling by AASSC (Trainers Certified)', 'Skilling by AASSC (Training Centres Accredited)', 'Skilling by AASSC (Training Partners Affiliated)', 'Skilling by IGRUA (Course & Activities)', 'Skilling by IGRUA (Flying Hours)', 'Skilling by IGRUA (Registerd Students)', 'Skilling by IGRUA (Students Pass Out)', 'Skilling by RGNAU (Candidates Who Obtained Jobs)', 'Skilling by RGNAU (Candidates Who Passed Out)', 'Skilling by RGNAU (Number Of Candidates)', 'Skilling by RGNAU (Number Of Courses)', 'UDAN (RCS) (Airports*)', 'UDAN (RCS) (Flights)', 'UDAN (RCS) (Operators)', 'UDAN (RCS) (Passengers)', 'UDAN (RCS) (Routes)', 'UDAN (RCS) (Subsidy)', 'Vande Bharat Mission (Flights Till Date)', 'Vande Bharat Mission (Inbound Flights)', 'Vande Bharat Mission (Inbound Pax)', 'Vande Bharat Mission (Outbound Flights)', 'Vande Bharat Mission (Outbound Pax)', 'Vande Bharat Mission (Passengers Till Date)', 'Vande Bharat Mission - Arrivals (Air India Group)', 'Vande Bharat Mission - Arrivals (By Land)', 'Vande Bharat Mission - Arrivals (Chartered)', 'Vande Bharat Mission - Arrivals (Naval Ships)', 'Vande Bharat Mission - Arrivals (Others)', 'Vande Bharat Mission - Arrivals (Total)'])

    return df

def save_dataframe(df, output_file):
    df.to_csv(output_file, index=False)

# Set up the directory path
html_dir = "raw/civilaviation"

# Generate initial DataFrame
df = generate_dataframe()

# Parse DataFrame
df = parse_dataframe(df)

# Save DataFrame
save_dataframe(df, '../aggregated/daily.csv')
