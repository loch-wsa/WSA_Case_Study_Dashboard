import streamlit as st
import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=None)
def process_data(value):
    """Process data values with caching for better performance"""
    try:
        if isinstance(value, str):
            if value.startswith('<'):
                return float(value.strip('<'))
            elif value.startswith('>'):
                value = value.strip('>')
                if value.isdigit():
                    return float(value)
                return 2000
            elif value == 'N/R':
                return 0
            elif value.endswith('LINT'):
                return float(value.split()[0].strip('<'))
            try:
                return float(value)
            except ValueError:
                return 0
        elif value is None:
            return 0
        else:
            return float(value)
    except Exception:
        return 0

@st.cache_data(ttl=3600)
def load_data():
    """Load and process all data files with caching"""
    try:
        # Load all data files from the data directory
        influent_data = pd.read_csv('data/Point Leo Influent Water.csv')
        treated_data = pd.read_csv('data/Point Leo Treated Water.csv')
        influent_ranges = pd.read_csv('data/Brolga Influent Parameters.csv')
        treated_ranges = pd.read_csv('data/Brolga Treated Parameters.csv')
        
        # Check if we need to rename columns in treated data
        if 'Product Water' in treated_data.columns and 'Influent Water' not in treated_data.columns:
            treated_data = treated_data.rename(columns={'Product Water': 'Influent Water'})
        
        # Process numeric columns for both dataframes
        for df in [influent_data, treated_data]:
            for col in df.columns:
                if col not in ['Influent Water', 'Details', 'Pond']:
                    df[col] = df[col].apply(process_data)
                    
        return influent_data, treated_data, influent_ranges, treated_ranges
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        raise e

# Define relevant parameters
RELEVANT_PARAMS = [
    'TURBIDITY',
    'PH',
    'TOC',
    'E COLI(C)',
    'EC',
    'TDS_180',
    'COLIFORM (C)',
    'DOC'
]