import pandas as pd
import pyodbc
import os
import numpy as np
from pathlib import Path

# SQL Server connection parameters
SERVER = 'localhost\\SQL2022'  # e.g., 'localhost' or 'server_name\\instance'
DATABASE = 'nfl'
USERNAME = ''  # Optional: leave empty for Windows Authentication
PASSWORD = ''  # Optional: leave empty for Windows Authentication

# Directory containing CSV files
DATA_DIR = 'rawdata'

def create_connection():
    """Create a connection to SQL Server"""
    try:
        if USERNAME and PASSWORD:
            # SQL Server Authentication
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={SERVER};'
                f'DATABASE={DATABASE};'
                f'UID={USERNAME};'
                f'PWD={PASSWORD}'
            )
        else:
            # Windows Authentication
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={SERVER};'
                f'DATABASE={DATABASE};'
                f'Trusted_Connection=yes;'
            )
        
        conn = pyodbc.connect(conn_str)
        print("Successfully connected to SQL Server")
        return conn
    except Exception as e:
        print(f"Error connecting to SQL Server: {e}")
        return None

def create_staging_table(conn):
    """Create the Coach_Staging table if it doesn't exist"""
    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Coach_Staging')
    BEGIN
        CREATE TABLE Coach_Staging (
            coach NVARCHAR(100),
            Year INT,
            Age INT,
            Tm NVARCHAR(10),
            Lg NVARCHAR(10),
            G INT,
            W INT,
            L INT,
            T INT,
            [W-L%] DECIMAL(5,3),
            SRS DECIMAL(6,2),
            OSRS DECIMAL(6,2),
            DSRS DECIMAL(6,2),
            G_Playoff INT,
            W_Playoff INT,
            L_Playoff INT,
            [W-L%_Playoff] DECIMAL(5,3),
            [Rank] INT,
            Num INT,
            Won INT,
            Notes NVARCHAR(500),
            ImportDate DATETIME DEFAULT GETDATE()
        )
        PRINT 'Coach_Staging table created successfully'
    END
    ELSE
    BEGIN
        PRINT 'Coach_Staging table already exists'
    END
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
        cursor.close()
        print("Table creation check completed")
    except Exception as e:
        print(f"Error creating table: {e}")

def clean_dataframe(df):
    """Clean and prepare the dataframe for import"""
    # Create a copy to avoid modifying original
    df_clean = df.copy()
    
    # Handle empty strings, NaN values, and convert to None for SQL NULL
    import numpy as np
    df_clean = df_clean.replace('', None)
    df_clean = df_clean.replace(np.nan, None)
    
    # Also handle any whitespace-only values
    df_clean = df_clean.replace(r'^\s*$', None, regex=True)
    
    # Handle the column renaming more robustly
    # First, let's standardize the column names
    cols = df_clean.columns.tolist()
    new_columns = []
    
    for col in cols:
        if col == 'coach':
            new_columns.append('coach')
        elif col == 'Year':
            new_columns.append('Year')
        elif col == 'Age':
            new_columns.append('Age')
        elif col == 'Tm':
            new_columns.append('Tm')
        elif col == 'Lg':
            new_columns.append('Lg')
        elif col == 'G' or col == 'G.1':
            # First G is regular season, second is playoffs
            if 'G' not in [c for c in new_columns]:
                new_columns.append('G')
            else:
                new_columns.append('G_Playoff')
        elif col == 'W' or col == 'W.1':
            # First W is regular season, second is playoffs
            if 'W' not in [c for c in new_columns]:
                new_columns.append('W')
            else:
                new_columns.append('W_Playoff')
        elif col == 'L' or col == 'L.1':
            # First L is regular season, second is playoffs
            if 'L' not in [c for c in new_columns]:
                new_columns.append('L')
            else:
                new_columns.append('L_Playoff')
        elif col == 'T':
            new_columns.append('T')
        elif col == 'W-L%' or col == 'W-L%.1':
            # First W-L% is regular season, second is playoffs
            if 'W-L%' not in [c for c in new_columns]:
                new_columns.append('W-L%')
            else:
                new_columns.append('W-L%_Playoff')
        elif col == 'SRS':
            new_columns.append('SRS')
        elif col == 'OSRS':
            new_columns.append('OSRS')
        elif col == 'DSRS':
            new_columns.append('DSRS')
        elif 'G plyf' in col:
            new_columns.append('G_Playoff')
        elif 'W plyf' in col:
            new_columns.append('W_Playoff')
        elif 'L plyf' in col:
            new_columns.append('L_Playoff')
        elif col == 'Rank':
            new_columns.append('Rank')
        elif col == 'Num':
            new_columns.append('Num')
        elif col == 'Won':
            new_columns.append('Won')
        elif col == 'Notes':
            new_columns.append('Notes')
        else:
            new_columns.append(col)
    
    df_clean.columns = new_columns
    
    return df_clean

def import_csv_to_sql(conn, csv_file):
    """Import a single CSV file into SQL Server"""
    try:
        # Read CSV file with better handling of empty values
        df = pd.read_csv(csv_file, keep_default_na=False, na_values=['', 'NA', 'N/A', 'null'])
        print(f"\nProcessing {csv_file}")
        print(f"Rows found: {len(df)}")
        print(f"Columns found: {list(df.columns)}")
        
        # Clean the dataframe
        df_clean = clean_dataframe(df)
        
        # Debug: Print first few rows to see data structure
        print(f"Cleaned columns: {list(df_clean.columns)}")
        print(f"Sample data after cleaning:")
        print(df_clean.head(2).to_string())
        
        # Insert data
        cursor = conn.cursor()
        
        # Build INSERT statement
        columns = df_clean.columns.tolist()
        placeholders = ','.join(['?' for _ in columns])
        column_names = ','.join([f'[{col}]' for col in columns])
        
        insert_sql = f"INSERT INTO Coach_Staging ({column_names}) VALUES ({placeholders})"
        print(f"Insert SQL: {insert_sql}")
        
        # Insert rows
        rows_inserted = 0
        for index, row in df_clean.iterrows():
            # Convert any remaining NaN values to None
            values = []
            for col in columns:
                val = row[col]
                if pd.isna(val):  # Handle NaN, None, etc.
                    values.append(None)
                else:
                    values.append(val)
            values = tuple(values)
            
            if index < 2:  # Debug print for first few rows
                print(f"Row {index}: {values}")
            
            cursor.execute(insert_sql, values)
            rows_inserted += 1
        
        conn.commit()
        cursor.close()
        print(f"Successfully imported {rows_inserted} rows from {os.path.basename(csv_file)}")
        
    except Exception as e:
        print(f"Error importing {csv_file}: {e}")
        conn.rollback()

def main():
    """Main function to process all CSV files"""
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        print(f"Error: Directory '{DATA_DIR}' not found")
        return
    
    # Get all CSV files
    csv_files = list(Path(DATA_DIR).glob('*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in '{DATA_DIR}' directory")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to process")
    
    # Connect to SQL Server
    conn = create_connection()
    if not conn:
        return
    
    try:
        # Create table if it doesn't exist
        create_staging_table(conn)
        
        # Process each CSV file
        for csv_file in csv_files:
            import_csv_to_sql(conn, csv_file)
        
        print("\n=== Import Complete ===")
        
        # Display summary
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Coach_Staging")
        total_rows = cursor.fetchone()[0]
        print(f"Total rows in Coach_Staging: {total_rows}")
        cursor.close()
        
    finally:
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()