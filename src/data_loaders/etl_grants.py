"""
ETL Module for IMF and World Bank Grant Data Standardization

This module processes raw IMF and World Bank CSV/Excel files and converts them
into a unified standardized format for analysis.
"""

import pandas as pd
import os
import glob
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import (
    IMF_DIR, WORLDBANK_DIR, STANDARDIZED_DIR, GRANT_SCHEMA, COUNTRY_CODE_MAP
)


def parse_imf_csv(file_path):
    """
    Parse IMF grant files (tab-delimited text)
    
    Actual IMF format:
    - Member (country name)
    - Description (program type)
    - Transaction Value Date
    - Amount
    """
    try:
        # IMF .xls file is actually tab-delimited text
        # Skip header lines (first 1 line is metadata)
        df = pd.read_csv(file_path, sep='\t', skiprows=1, encoding='utf-8')
        print(f"DEBUG: IMF Raw Shape: {df.shape}")
        print(f"DEBUG: IMF Columns: {df.columns.tolist()}")
        
        # Map IMF country names to our standard names
        imf_country_map = {
            'Argentina': 'Argentina',
            'Colombia': 'Colombia',
            'Egypt': 'Egypt',
            'Ghana': 'Ghana',
            'Pakistan': 'Pakistan',
            'Sri Lanka': 'Sri Lanka',
            'Türkiye, Republic of': 'Turkey',
            'Turkey': 'Turkey'
        }
        
        records = []
        for _, row in df.iterrows():
            try:
                # Get country
                imf_member = str(row.get('Member', '')).strip()
                country_name = imf_country_map.get(imf_member, imf_member)
                country_code = COUNTRY_CODE_MAP.get(country_name, '')
                
                if not country_code:
                    continue
                
                # Get date
                date_str = str(row.get('Transaction Value Date', ''))
                if not date_str or date_str == 'nan':
                    continue
                
                try:
                    parsed_date = pd.to_datetime(date_str).strftime('%Y-%m-%d')
                except:
                    continue
                
                # Get amount
                amount_str = str(row.get('Amount', '0')).replace(',', '')
                try:
                    amount = float(amount_str)
                except:
                    amount = 0.0
                
                if amount <= 0:
                    continue
                
                # Get program description
                program = str(row.get('Description', 'General Support'))
                
                records.append({
                    'country_code': country_code,
                    'country_name': country_name,
                    'disbursement_date': parsed_date,
                    'amount_usd': amount,
                    'grant_type': program,
                    'source': 'IMF',
                    'program_name': program,
                })
            except Exception as e:
                continue
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error parsing IMF file {file_path}: {e}")
        return pd.DataFrame()


def parse_worldbank_csv(file_path):
    """
    Parse World Bank grant Excel files
    
    Actual columns from World Bank data:
    - Country
    - Board Approval Date
    - Grant Amount $US or IBRD Commitment $US
    - Project Name
    """
    try:
        # World Bank files have a header row, skip it
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path, skiprows=1)
        else:
            df = pd.read_csv(file_path, encoding='utf-8', skiprows=1)
        
        # Map country names from WB format to our standard names
        wb_country_map = {
            'Republic of Turkiye': 'Turkey',
            'Republic of Colombia': 'Colombia',
            'Democratic Socialist Republic of Sri Lanka': 'Sri Lanka',
            'Islamic Republic of Pakistan': 'Pakistan',
            'Argentine Republic': 'Argentina',
            'Republic of Ghana': 'Ghana',
            'Arab Republic of Egypt': 'Egypt',
            'Lebanese Republic': 'Lebanon'
        }
        
        records = []
        for _, row in df.iterrows():
            try:
                # Get country
                wb_country = str(row.get('Country', '')).strip()
                country_name = wb_country_map.get(wb_country, wb_country)
                country_code = COUNTRY_CODE_MAP.get(country_name, '')
                
                if not country_code:
                    continue
                
                # Get date - use Board Approval Date
                date_val = row.get('Board Approval Date')
                if pd.isna(date_val):
                    continue
                
                try:
                    parsed_date = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                except:
                    continue
                
                # Get amount - check multiple columns
                amount = row.get('Grant Amount $US', 0)
                if pd.isna(amount) or amount == 0:
                    amount = row.get('IBRD Commitment $US', 0)
                if pd.isna(amount) or amount == 0:
                    amount = row.get('IDA Commitment $US', 0)  # Added IDA
                if pd.isna(amount) or amount == 0:
                    amount = row.get('Total IBRD, IDA and GRANT Commitment $US', 0)
                
                try:
                    amount = float(amount)
                except:
                    amount = 0.0
                
                if amount <= 0:
                    continue
                
                # Get project name
                project = str(row.get('Project Name', 'Development Support'))
                
                records.append({
                    'country_code': country_code,
                    'country_name': country_name,
                    'disbursement_date': parsed_date,
                    'amount_usd': amount,
                    'grant_type': project,
                    'source': 'World Bank',
                    'program_name': project,
                })
            except Exception as e:
                continue
        
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"Error parsing World Bank file {file_path}: {e}")
        return pd.DataFrame()



def standardize_grants():
    """
    Main ETL function to process all IMF and World Bank files
    and create a unified standardized grants database
    
    Returns:
        pd.DataFrame: Standardized grants data
    """
    all_grants = []
    
    # Process IMF files
    print("Processing IMF grant files...")
    imf_files = glob.glob(os.path.join(IMF_DIR, '*.csv'))
    imf_files.extend(glob.glob(os.path.join(IMF_DIR, '*.xls')))
    for file_path in imf_files:
        print(f"  - Processing {os.path.basename(file_path)}")
        df = parse_imf_csv(file_path)
        if not df.empty:
            all_grants.append(df)
    
    # Process World Bank files
    print("Processing World Bank grant files...")
    wb_files = glob.glob(os.path.join(WORLDBANK_DIR, '*.csv'))
    wb_files.extend(glob.glob(os.path.join(WORLDBANK_DIR, '*.xlsx')))
    wb_files.extend(glob.glob(os.path.join(WORLDBANK_DIR, '*.xls')))
    
    for file_path in wb_files:
        print(f"  - Processing {os.path.basename(file_path)}")
        df = parse_worldbank_csv(file_path)
        if not df.empty:
            all_grants.append(df)
    
    # Combine all grants
    if all_grants:
        combined_df = pd.concat(all_grants, ignore_index=True)
        
        # Sort by date
        combined_df['disbursement_date'] = pd.to_datetime(combined_df['disbursement_date'])
        combined_df = combined_df.sort_values('disbursement_date')
        
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(
            subset=['country_code', 'disbursement_date', 'amount_usd'],
            keep='first'
        )
        
        print(f"\nTotal grants standardized: {len(combined_df)}")
        return combined_df
    else:
        print("No grant files found or processed successfully.")
        return pd.DataFrame(columns=GRANT_SCHEMA)


def save_standardized(df):
    """
    Save standardized grants to CSV
    
    Args:
        df: DataFrame with standardized grants
    """
    os.makedirs(STANDARDIZED_DIR, exist_ok=True)
    output_path = os.path.join(STANDARDIZED_DIR, 'grants.csv')
    df.to_csv(output_path, index=False)
    print(f"\nStandardized grants saved to: {output_path}")
    return output_path


def load_standardized_grants():
    """
    Load previously standardized grants from CSV
    
    Returns:
        pd.DataFrame: Standardized grants data
    """
    grants_path = os.path.join(STANDARDIZED_DIR, 'grants.csv')
    if os.path.exists(grants_path):
        df = pd.read_csv(grants_path)
        df['disbursement_date'] = pd.to_datetime(df['disbursement_date'])
        return df
    else:
        return pd.DataFrame(columns=GRANT_SCHEMA)


if __name__ == '__main__':
    # Run ETL process
    print("Starting Grant Data Standardization...")
    grants_df = standardize_grants()
    if not grants_df.empty:
        save_standardized(grants_df)
        print("\nETL Complete!")
    else:
        print("\nNo data to process. Please upload grant files.")
