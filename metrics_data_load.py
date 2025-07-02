import pandas as pd
import pyodbc

# CSV file path
csv_file = 'financial_application_logs.csv'

# SQL Server connection details
server = 'YOUR_SERVER_NAME'  # e.g., 'localhost\\SQLEXPRESS'
database = 'YOUR_DATABASE'
username = 'YOUR_USERNAME'
password = 'YOUR_PASSWORD'
table = 'FinancialAppLogs'

# Read CSV to DataFrame
df = pd.read_csv(csv_file)

# Convert time columns to proper formats if needed
df['date'] = pd.to_datetime(df['date']).dt.date
df['time_stamp'] = pd.to_datetime(df['time_stamp'], format='%H:%M:%S').dt.time

# Connect to SQL Server
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Insert data
for idx, row in df.iterrows():
    cursor.execute(f"""
        INSERT INTO {table} (
            application_name, date, time_stamp, log_level,
            servernames, severity, detailed_stack_trace, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row['application_name'], row['date'], row['time_stamp'], row['log_level'],
        row['servernames'], row['severity'],
        row['detailed_stack_trace'], row['error_message']
    ))
    if idx % 100 == 0:
        conn.commit()  # Commit every 100 records for performance

conn.commit()
print("All records inserted successfully.")
cursor.close()
conn.close()
