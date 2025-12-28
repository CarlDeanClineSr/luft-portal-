# Read CSV, handling multi-row format
try: 
    df = pd.read_csv(args.input, 
                     parse_dates=['timestamp_utc'],
                     on_bad_lines='skip',  # Skip malformed lines
                     engine='python')  # Use Python engine for flexibility
except Exception as e: 
    print(f"Error reading CSV: {e}")
    print("Attempting alternate parsing...")
    # Fallback: read without date parsing
    df = pd.read_csv(args.input, on_bad_lines='skip', engine='python')
    if 'timestamp_utc' in df. columns:
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')

# Remove rows with NaN chi_amplitude (continuation rows)
df = df[df['chi_amplitude'].notna()]
