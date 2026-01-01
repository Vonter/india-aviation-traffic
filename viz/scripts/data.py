#!/usr/bin/env python3
"""
Convert CSV files to optimized JSON files with pre-calculated aggregations for frontend.
"""
import csv
import json
import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
AGGREGATED_DIR = PROJECT_ROOT / "aggregated"
OUTPUT_DIR = PROJECT_ROOT / "viz" / "static" / "data"

# Metrics for airports and airlines
AIRPORT_METRICS = ['paxTotal', 'paxTo', 'paxFrom', 'freightTotal', 'freightTo', 'freightFrom', 'mailTotal', 'mailTo', 'mailFrom']
AIRLINE_METRICS = ['passengerNumber', 'paxTotal', 'paxTo', 'paxFrom', 'freightTotal', 'aircraftNumber', 'aircraftHours', 'passengerLoadFactor']

def ensure_output_dir():
    """Ensure output directory exists"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_date(year: int, month: int) -> str:
    """Convert year and month to ISO date string (first day of month)"""
    return f"{year}-{month:02d}-01"

def parse_quarter_date(year: int, quarter: int) -> str:
    """Convert year and quarter to ISO date string (first day of quarter)"""
    month = (quarter - 1) * 3 + 1
    return f"{year}-{month:02d}-01"

def normalize_year(year: int) -> int:
    """Convert 2-digit years to 4-digit years (15 -> 2015, 20 -> 2020, etc.)"""
    if year < 100:
        return 2000 + year
    return year

def get_year_from_date(date_str: str) -> int:
    """Extract year from date string"""
    try:
        year = int(date_str.split('-')[0])
        return normalize_year(year)
    except:
        return 2000

def date_to_quarter(date_str: str) -> str:
    """Convert a date string to quarterly period (first day of quarter)"""
    try:
        parts = date_str.split('-')
        year = int(parts[0])
        month = int(parts[1])
        # Calculate quarter: Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
        quarter = (month - 1) // 3 + 1
        return parse_quarter_date(year, quarter)
    except:
        return date_str

def convert_domestic_city():
    """Convert domestic city CSV to JSON"""
    csv_path = AGGREGATED_DIR / "domestic" / "city.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return []
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = normalize_year(int(row['Year']))
            month = int(row['Month'])
            city1 = row['City1'].strip()
            city2 = row['City2'].strip()
            
            # Calculate totals
            pax_to = float(row.get('PaxToCity2', 0) or 0)
            pax_from = float(row.get('PaxFromCity2', 0) or 0)
            total_pax = pax_to + pax_from
            
            freight_to = float(row.get('FreightToCity2', 0) or 0)
            freight_from = float(row.get('FreightFromCity2', 0) or 0)
            total_freight = freight_to + freight_from
            
            mail_to = float(row.get('MailToCity2', 0) or 0)
            mail_from = float(row.get('MailFromCity2', 0) or 0)
            total_mail = mail_to + mail_from
            
            data.append({
                'date': parse_date(year, month),
                'airport': city1,
                'destination': city2,
                'paxTo': pax_to,
                'paxFrom': pax_from,
                'paxTotal': total_pax,
                'freightTo': freight_to,
                'freightFrom': freight_from,
                'freightTotal': total_freight,
                'mailTo': mail_to,
                'mailFrom': mail_from,
                'mailTotal': total_mail
            })
    
    return data

def convert_international_city():
    """Convert international city CSV to JSON"""
    csv_path = AGGREGATED_DIR / "international" / "city.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return []
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = normalize_year(int(row['Year']))
            quarter = int(row['Quarter'])
            city1 = row['City1'].strip()
            city2 = row['City2'].strip()
            
            # Calculate totals
            pax_to = float(row.get('PaxToCity2', 0) or 0)
            pax_from = float(row.get('PaxFromCity2', 0) or 0)
            total_pax = pax_to + pax_from
            
            freight_to = float(row.get('FreightToCity2', 0) or 0)
            freight_from = float(row.get('FreightFromCity2', 0) or 0)
            total_freight = freight_to + freight_from
            
            data.append({
                'date': parse_quarter_date(year, quarter),
                'airport': city1,
                'destination': city2,
                'paxTo': pax_to,
                'paxFrom': pax_from,
                'paxTotal': total_pax,
                'freightTo': freight_to,
                'freightFrom': freight_from,
                'freightTotal': total_freight
            })
    
    # Save as JSON
    output_path = OUTPUT_DIR / "international-city.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Converted {len(data)} rows to {output_path}")
    return data

def convert_domestic_carrier():
    """Convert domestic carrier CSV to JSON"""
    csv_path = AGGREGATED_DIR / "domestic" / "carrier.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return []
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = normalize_year(int(row['Year']))
            month = int(row['Month'])
            airline = row['Airline'].strip()
            
            # Skip Total rows and Grand Total
            if airline in ['Total Domestic', 'Total International', 'Grand Total']:
                continue
            
            data.append({
                'date': parse_date(year, month),
                'airline': airline,
                'aircraftNumber': float(row.get('Aircraft Number', 0) or 0),
                'aircraftHours': float(row.get('Aircraft Hours', 0) or 0),
                'aircraftKilometres': float(row.get('Aircraft Kilometres', 0) or 0),
                'passengerNumber': float(row.get('Passenger Number', 0) or 0),
                'passengerKilometers': float(row.get('Passenger Kilometers', 0) or 0),
                'seatKilometers': float(row.get('Seat Kilometers', 0) or 0),
                'passengerLoadFactor': float(row.get('Passenger Load Factor', 0) or 0),
                'freight': float(row.get('Freight', 0) or 0),
                'mail': float(row.get('Mail', 0) or 0),
                'totalCargo': float(row.get('Total Cargo', 0) or 0),
                'paxTotal': float(row.get('Passenger Number', 0) or 0),
                'freightTotal': float(row.get('Freight', 0) or 0)
            })
    
    # Save as JSON
    output_path = OUTPUT_DIR / "domestic-carrier.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Converted {len(data)} rows to {output_path}")
    return data

def convert_international_carrier():
    """Convert international carrier CSV to JSON"""
    csv_path = AGGREGATED_DIR / "international" / "carrier.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return []
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = normalize_year(int(row['Year']))
            quarter = int(row['Quarter'])
            airline = row['Airline'].strip()
            
            # Skip Total rows and Grand Total
            if airline in ['Total Domestic', 'Total International', 'Grand Total']:
                continue
            
            # Sum across all months in quarter
            pax_to = sum(float(row.get(f'PaxToIndiaM{i}', 0) or 0) for i in [1, 2, 3])
            pax_from = sum(float(row.get(f'PaxFromIndiaM{i}', 0) or 0) for i in [1, 2, 3])
            freight_to = sum(float(row.get(f'FreightToIndiaM{i}', 0) or 0) for i in [1, 2, 3])
            freight_from = sum(float(row.get(f'FreightFromIndiaM{i}', 0) or 0) for i in [1, 2, 3])
            
            data.append({
                'date': parse_quarter_date(year, quarter),
                'airline': airline,
                'paxTo': pax_to,
                'paxFrom': pax_from,
                'paxTotal': pax_to + pax_from,
                'freightTo': freight_to,
                'freightFrom': freight_from,
                'freightTotal': freight_to + freight_from
            })
    
    # Save as JSON
    output_path = OUTPUT_DIR / "international-carrier.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Converted {len(data)} rows to {output_path}")
    return data

def convert_daily():
    """Convert daily CSV to JSON"""
    csv_path = AGGREGATED_DIR / "daily.csv"
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return []
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row['Date']
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                date_iso = date_obj.strftime('%Y-%m-%d')
            except:
                continue
            
            def safe_float(val):
                try:
                    return float(val) if val and val.strip() else 0.0
                except:
                    return 0.0
            
            record = {'date': date_iso}
            for key, value in row.items():
                if key != 'Date':
                    record[key] = safe_float(value) if value else 0.0
            
            data.append(record)
    
    # Save as JSON
    output_path = OUTPUT_DIR / "daily.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Converted {len(data)} rows to {output_path}")
    return data

def precalculate_airport_aggregations(domestic_data, international_data):
    """Pre-calculate airport aggregations by type, metric, and date"""
    print("Pre-calculating airport aggregations...")
    
    # Normalize airport names to uppercase and strip special characters for comparison
    def normalize_name(name):
        if not name:
            return None
        # Convert to uppercase, strip whitespace, and remove special characters (keep only alphanumeric and spaces)
        normalized = re.sub(r'[^A-Z0-9\s]', '', name.upper().strip())
        # Collapse multiple spaces to single space and strip again
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized if normalized else None
    
    # Note: We use normalized (uppercase) names directly for all outputs
    
    # Get unique airports normalized, and track which appear in domestic vs international
    # Use normalized names for comparison, but store original names
    airports_with_data = set()
    airports_as_destinations = set()
    years = set()
    domestic_airports_norm = set()  # Normalized names
    international_airports_norm = set()  # Normalized names
    
    for point in domestic_data:
        if point.get('airport'):
            norm_name = normalize_name(point['airport'])
            if norm_name:
                airports_with_data.add(norm_name)
                domestic_airports_norm.add(norm_name)
        if point.get('destination'):
            norm_name = normalize_name(point['destination'])
            if norm_name:
                airports_as_destinations.add(norm_name)
        if point.get('date'):
            years.add(get_year_from_date(point['date']))
    
    for point in international_data:
        if point.get('airport'):
            norm_name = normalize_name(point['airport'])
            if norm_name:
                airports_with_data.add(norm_name)
                international_airports_norm.add(norm_name)
        if point.get('destination'):
            norm_name = normalize_name(point['destination'])
            if norm_name:
                airports_as_destinations.add(norm_name)
        if point.get('date'):
            years.add(get_year_from_date(point['date']))
    
    # Exclude international-only airports (airports that only appear in international data)
    airports_to_include = airports_with_data - (international_airports_norm - domestic_airports_norm)
    
    # Use normalized (uppercase) names for output
    airports = sorted(airports_to_include)
    years = sorted(years)
    
    print(f"Found {len(airports_with_data)} airports with data ({len(domestic_airports_norm)} domestic, {len(international_airports_norm)} international)")
    print(f"Excluding {len(international_airports_norm - domestic_airports_norm)} international-only airports")
    print(f"Final airport list: {len(airports)} airports")
    
    # Bidirectional metrics
    bidirectional_metrics = {'paxTotal', 'freightTotal'}
    
    # Pre-aggregate by type, metric, date, and airport - optimized
    aggregations = {
        'domestic': {},
        'international': {},
        'all': {}
    }
    
    # Pre-index data by type for faster filtering (using normalized names)
    domestic_by_date_airport = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    international_by_date_airport = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    all_by_date_airport = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    # Single pass through data to build all aggregations
    # Convert domestic monthly data to quarterly for consistent periodicity
    for point in domestic_data:
        date = point.get('date')
        # Convert monthly date to quarterly period
        quarter_date = date_to_quarter(date) if date else None
        airport = normalize_name(point.get('airport'))
        destination = normalize_name(point.get('destination'))
        if quarter_date and airport:
            for metric in AIRPORT_METRICS:
                value = point.get(metric, 0) or 0
                if value:
                    # For bidirectional metrics, count traffic in both directions
                    if metric in bidirectional_metrics and destination:
                        # Count for origin airport
                        domestic_by_date_airport[metric][quarter_date][airport] += value
                        all_by_date_airport[metric][quarter_date][airport] += value
                        # Count for destination airport (bidirectional)
                        if destination in airports_to_include:
                            domestic_by_date_airport[metric][quarter_date][destination] += value
                            all_by_date_airport[metric][quarter_date][destination] += value
                    else:
                        # For directional metrics, only count for origin
                        domestic_by_date_airport[metric][quarter_date][airport] += value
                        all_by_date_airport[metric][quarter_date][airport] += value
    
    for point in international_data:
        date = point.get('date')
        # International data is already quarterly, but ensure it's in the correct format
        quarter_date = date_to_quarter(date) if date else None
        airport = normalize_name(point.get('airport'))
        destination = normalize_name(point.get('destination'))
        if quarter_date and airport:
            for metric in AIRPORT_METRICS:
                value = point.get(metric, 0) or 0
                if value:
                    # For bidirectional metrics, count traffic in both directions
                    if metric in bidirectional_metrics and destination:
                        # Count for origin airport
                        international_by_date_airport[metric][quarter_date][airport] += value
                        all_by_date_airport[metric][quarter_date][airport] += value
                        # Count for destination airport (bidirectional)
                        if destination in airports_to_include:
                            international_by_date_airport[metric][quarter_date][destination] += value
                            all_by_date_airport[metric][quarter_date][destination] += value
                    else:
                        # For directional metrics, only count for origin
                        international_by_date_airport[metric][quarter_date][airport] += value
                        all_by_date_airport[metric][quarter_date][airport] += value
    
    # Convert to final format (using normalized uppercase names, only including airports in airports_to_include)
    for metric in AIRPORT_METRICS:
        aggregations['domestic'][metric] = []
        aggregations['international'][metric] = []
        aggregations['all'][metric] = []
        
        # Domestic
        for date in sorted(domestic_by_date_airport[metric].keys()):
            for airport_norm, value in domestic_by_date_airport[metric][date].items():
                if airport_norm in airports_to_include:
                    aggregations['domestic'][metric].append({
                        'period': date,
                        'name': airport_norm,
                        'value': value,
                        'avgRidership': value
                    })
        
        # International
        for date in sorted(international_by_date_airport[metric].keys()):
            for airport_norm, value in international_by_date_airport[metric][date].items():
                if airport_norm in airports_to_include:
                    aggregations['international'][metric].append({
                        'period': date,
                        'name': airport_norm,
                        'value': value,
                        'avgRidership': value
                    })
        
        # All
        for date in sorted(all_by_date_airport[metric].keys()):
            for airport_norm, value in all_by_date_airport[metric][date].items():
                if airport_norm in airports_to_include:
                    aggregations['all'][metric].append({
                        'period': date,
                        'name': airport_norm,
                        'value': value,
                        'avgRidership': value
                    })
        
        # Sort by date
        aggregations['domestic'][metric].sort(key=lambda x: x['period'])
        aggregations['international'][metric].sort(key=lambda x: x['period'])
        aggregations['all'][metric].sort(key=lambda x: x['period'])
    
    # Save aggregations (no indent for smaller file size)
    output_path = OUTPUT_DIR / "airport-aggregations.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregations, f, separators=(',', ':'))
    print(f"Saved airport aggregations to {output_path}")
    
    # Pre-calculate sorted lists by metric totals
    # Only include airports that are in airports_to_include (exclude international-only)
    sorted_lists = {}
    for metric in AIRPORT_METRICS:
        totals = defaultdict(float)
        bidirectional = metric in bidirectional_metrics
        
        # Process domestic data
        for point in domestic_data:
            airport_norm = normalize_name(point.get('airport'))
            destination_norm = normalize_name(point.get('destination'))
            value = point.get(metric, 0) or 0
            
            if airport_norm and airport_norm in airports_to_include:
                # Count for origin airport
                totals[airport_norm] += value
                
                # For bidirectional metrics, also count for destination
                if bidirectional and destination_norm and destination_norm in airports_to_include:
                    totals[destination_norm] += value
        
        # Process international data
        for point in international_data:
            airport_norm = normalize_name(point.get('airport'))
            destination_norm = normalize_name(point.get('destination'))
            value = point.get(metric, 0) or 0
            
            if airport_norm and airport_norm in airports_to_include:
                # Count for origin airport
                totals[airport_norm] += value
                
                # For bidirectional metrics, also count for destination
                if bidirectional and destination_norm and destination_norm in airports_to_include:
                    totals[destination_norm] += value
        
        sorted_list = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        # Use normalized (uppercase) names directly
        sorted_lists[metric] = [{'name': name, 'value': value} for name, value in sorted_list]
    
    output_path = OUTPUT_DIR / "airport-sorted.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_lists, f, separators=(',', ':'))
    print(f"Saved airport sorted lists to {output_path}")
    
    # Pre-calculate destination breakdowns - optimized
    destinations = {}
    
    # Pre-index by airport, year, type, metric, and destination (using normalized names)
    dest_index = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(float)))))
    
    # Single pass through data (using normalized names)
    for point in domestic_data:
        airport_norm = normalize_name(point.get('airport'))
        destination_norm = normalize_name(point.get('destination'))
        year = get_year_from_date(point.get('date', ''))
        if airport_norm and destination_norm and year and airport_norm in airports_to_include:
            for metric in AIRPORT_METRICS:
                value = point.get(metric, 0) or 0
                if value:
                    # For bidirectional metrics, count both directions
                    if metric in bidirectional_metrics:
                        # Count A->B for airport A
                        dest_index[airport_norm][year]['domestic'][metric][destination_norm] += value
                        dest_index[airport_norm][year]['all'][metric][destination_norm] += value
                        # Count B->A for airport B (reverse direction) - only if destination is in airports_to_include
                        if destination_norm in airports_to_include:
                            dest_index[destination_norm][year]['domestic'][metric][airport_norm] += value
                            dest_index[destination_norm][year]['all'][metric][airport_norm] += value
                    else:
                        # For directional metrics, only count one direction
                        dest_index[airport_norm][year]['domestic'][metric][destination_norm] += value
                        dest_index[airport_norm][year]['all'][metric][destination_norm] += value
    
    for point in international_data:
        # International data: airport field is City1 (could be international city), destination is City2 (could be Indian city)
        # We need to handle both directions and only include routes FROM Indian airports
        city1_norm = normalize_name(point.get('airport'))  # City1 from CSV
        city2_norm = normalize_name(point.get('destination'))  # City2 from CSV
        year = get_year_from_date(point.get('date', ''))
        
        if not (city1_norm and city2_norm and year):
            continue
            
        # Determine which city is the Indian airport (the one in airports_to_include)
        # and which is the destination (could be international city or another Indian airport)
        indian_airport_norm = None
        destination_norm = None
        
        if city1_norm in airports_to_include:
            # City1 is Indian airport, City2 is destination
            indian_airport_norm = city1_norm
            destination_norm = city2_norm
        elif city2_norm in airports_to_include:
            # City2 is Indian airport, City1 is destination (reverse the route)
            indian_airport_norm = city2_norm
            destination_norm = city1_norm
        else:
            # Neither city is in airports_to_include, skip this route
            continue
        
        # Now process the route from Indian airport to destination
        for metric in AIRPORT_METRICS:
            value = point.get(metric, 0) or 0
            if value:
                # For bidirectional metrics, count both directions
                if metric in bidirectional_metrics:
                    # Count Indian->Destination
                    dest_index[indian_airport_norm][year]['international'][metric][destination_norm] += value
                    dest_index[indian_airport_norm][year]['all'][metric][destination_norm] += value
                    # Count Destination->Indian (reverse) - only if destination is also an Indian airport
                    if destination_norm in airports_to_include:
                        dest_index[destination_norm][year]['international'][metric][indian_airport_norm] += value
                        dest_index[destination_norm][year]['all'][metric][indian_airport_norm] += value
                else:
                    # For directional metrics, only count one direction (from Indian airport)
                    dest_index[indian_airport_norm][year]['international'][metric][destination_norm] += value
                    dest_index[indian_airport_norm][year]['all'][metric][destination_norm] += value
    
    # Convert to final format (using normalized uppercase names, only for airports in airports_to_include)
    for airport_norm in airports:
        if airport_norm not in airports_to_include:
            continue
        destinations[airport_norm] = {}
        for year in years:
            destinations[airport_norm][year] = {}
            for data_type in ['domestic', 'international', 'all']:
                destinations[airport_norm][year][data_type] = {}
                for metric in AIRPORT_METRICS:
                    if airport_norm in dest_index and year in dest_index[airport_norm] and data_type in dest_index[airport_norm][year] and metric in dest_index[airport_norm][year][data_type]:
                        totals = dest_index[airport_norm][year][data_type][metric]
                        result = sorted(totals.items(), key=lambda x: x[1], reverse=True)
                        # Use normalized (uppercase) destination names directly
                        destinations[airport_norm][year][data_type][metric] = [
                            {'destination': dest_norm, 'value': val} for dest_norm, val in result
                        ]
                    else:
                        destinations[airport_norm][year][data_type][metric] = []
    
    output_path = OUTPUT_DIR / "airport-destinations.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(destinations, f, separators=(',', ':'))
    print(f"Saved airport destinations to {output_path}")
    
    # Collect all unique destinations (including international cities) for treemap dropdown
    all_destinations = set()
    for airport_norm in airports:
        if airport_norm not in airports_to_include:
            continue
        for year in years:
            for data_type in ['domestic', 'international', 'all']:
                for metric in AIRPORT_METRICS:
                    if airport_norm in dest_index and year in dest_index[airport_norm] and data_type in dest_index[airport_norm][year] and metric in dest_index[airport_norm][year][data_type]:
                        for dest_norm in dest_index[airport_norm][year][data_type][metric].keys():
                            # Use normalized (uppercase) destination names directly
                            all_destinations.add(dest_norm)
    
    # Save metadata - only airports with data, plus all destinations
    metadata = {
        'airports': airports,  # Only airports that have data
        'destinations': sorted(list(all_destinations)),  # All destinations including international cities
        'years': years,
        'metrics': AIRPORT_METRICS
    }
    output_path = OUTPUT_DIR / "airport-metadata.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, separators=(',', ':'))
    print(f"Saved airport metadata to {output_path} ({len(airports)} airports with data, {len(all_destinations)} destinations)")

def precalculate_airline_aggregations(domestic_data, international_data):
    """Pre-calculate airline aggregations by type, metric, and date"""
    print("Pre-calculating airline aggregations...")
    
    # Normalize airline names to uppercase and strip special characters for comparison
    def normalize_name(name):
        if not name:
            return None
        # Convert to uppercase, strip whitespace, and remove special characters (keep only alphanumeric and spaces)
        normalized = re.sub(r'[^A-Z0-9\s]', '', name.upper().strip())
        # Collapse multiple spaces to single space and strip again
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized if normalized else None
    
    # Combine data
    all_data = domestic_data + international_data
    
    # Get unique airlines normalized, using normalized names (all uppercase)
    airlines_norm = set()
    for point in all_data:
        if point.get('airline'):
            norm_name = normalize_name(point['airline'])
            if norm_name:
                airlines_norm.add(norm_name)
    
    # Use normalized (uppercase) names for output
    airlines = sorted(airlines_norm)
    
    # Pre-aggregate by type, metric, date, and airline
    aggregations = {
        'domestic': {},
        'international': {},
        'all': {}
    }
    
    for metric in AIRLINE_METRICS:
        for data_type in ['domestic', 'international', 'all']:
            aggregations[data_type][metric] = {}
            
            # Filter data by type
            if data_type == 'domestic':
                filtered_data = [p for p in domestic_data if 'aircraftNumber' in p]
            elif data_type == 'international':
                filtered_data = [p for p in international_data if 'aircraftNumber' not in p]
            else:
                filtered_data = all_data
            
            # Group by quarterly period and airline (convert to quarterly for consistent periodicity)
            grouped = defaultdict(lambda: defaultdict(float))
            
            for point in filtered_data:
                date = point.get('date')
                # Convert to quarterly period for consistent aggregation
                quarter_date = date_to_quarter(date) if date else None
                airline_norm = normalize_name(point.get('airline'))
                # Get value, treating None/empty as 0 but preserving actual 0 values
                # Map passengerNumber to paxTotal for international data (which doesn't have passengerNumber)
                if metric == 'passengerNumber' and metric not in point:
                    raw_value = point.get('paxTotal')
                else:
                    raw_value = point.get(metric)
                if raw_value is None or raw_value == '':
                    value = 0.0
                else:
                    try:
                        value = float(raw_value)
                        if value < 0:  # Handle negative values
                            value = 0.0
                    except (ValueError, TypeError):
                        value = 0.0
                
                # Include all valid entries (date and airline present), even if value is 0
                if quarter_date and airline_norm:
                    grouped[quarter_date][airline_norm] += value
            
            # Convert to array format
            result = []
            for date in sorted(grouped.keys()):
                for airline_norm, value in grouped[date].items():
                    # Use normalized (uppercase) name directly
                    result.append({
                        'period': date,
                        'name': airline_norm,
                        'value': value,
                        'avgRidership': value
                    })
            
            aggregations[data_type][metric] = result
    
    # Save aggregations (no indent for smaller file size)
    output_path = OUTPUT_DIR / "airline-aggregations.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(aggregations, f, separators=(',', ':'))
    print(f"Saved airline aggregations to {output_path}")
    
    # Pre-calculate sorted lists by metric totals
    sorted_lists = {}
    for metric in AIRLINE_METRICS:
        totals = defaultdict(float)
        for point in all_data:
            airline_norm = normalize_name(point.get('airline'))
            value = point.get(metric, 0) or 0
            if airline_norm:
                totals[airline_norm] += value
        
        sorted_list = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        # Use normalized (uppercase) names directly
        sorted_lists[metric] = [{'name': name, 'value': value} for name, value in sorted_list]
    
    output_path = OUTPUT_DIR / "airline-sorted.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_lists, f, separators=(',', ':'))
    print(f"Saved airline sorted lists to {output_path}")
    
    # Save metadata
    metadata = {
        'airlines': airlines,
        'metrics': AIRLINE_METRICS
    }
    output_path = OUTPUT_DIR / "airline-metadata.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, separators=(',', ':'))
    print(f"Saved airline metadata to {output_path}")

def main():
    """Main conversion function"""
    print("Converting CSV files to JSON with pre-calculations...")
    ensure_output_dir()
    
    # Convert base data
    domestic_city = convert_domestic_city()
    international_city = convert_international_city()
    domestic_carrier = convert_domestic_carrier()
    international_carrier = convert_international_carrier()
    daily_data = convert_daily()
    
    # Pre-calculate aggregations
    if domestic_city and international_city:
        precalculate_airport_aggregations(domestic_city, international_city)
    
    if domestic_carrier and international_carrier:
        precalculate_airline_aggregations(domestic_carrier, international_carrier)
    
    print("Conversion complete!")

if __name__ == "__main__":
    main()

