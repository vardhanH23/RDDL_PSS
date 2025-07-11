"""
Anomaly Detection Script for CI/CD Log Analysis

- Parses logs exported from Infineon Data Lake using existing RDDL automation.
- Cleans and normalizes data, handles missing values, segments into sequences.
- Implements statistical and rule-based anomaly detection.
- Designed for extensibility (future ML models, advanced analytics).
"""
import os
import re
import pandas as pd
import numpy as np

LOG_DIR = "data/logs/"
ANOMALY_REPORT = "data/anomaly_report.csv"

# exporting logs using existing automation (placeholder)
def export_logs():
    os.makedirs(LOG_DIR, exist_ok=True)
    # Download logs from the data lake uploader output if needed
    # also copy logs from the current directory if present
    for fname in os.listdir('.'):
        if fname.endswith('.log'):
            dest = os.path.join(LOG_DIR, fname)
            if not os.path.exists(dest):
                try:
                    with open(fname, 'rb') as src, open(dest, 'wb') as dst:
                        dst.write(src.read())
                except Exception as e:
                    print(f"[WARNING] Could not copy {fname} to {LOG_DIR}: {e}")

# parsing logs into structured DataFrame
def parse_logs(log_dir):
    records = []
    # Updated regex: allow spaces in value, allow missing commas in vectors
    log_line_re = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+):(?P<test>[^:]+):(?P<level>[^:]+): (?P<key>\w+) = (?P<value>.+)$")
    for fname in os.listdir(log_dir):
        if fname.endswith(".log"):
            with open(os.path.join(log_dir, fname), 'r') as f:
                for line in f:
                    match = log_line_re.match(line.strip())
                    if match:
                        rec = match.groupdict()
                        rec['file'] = fname  # Overwrite with log filename
                        val = rec['value'].strip()
                        # Handle vectors with or without commas
                        if val.startswith('{') and val.endswith('}'):  # vector
                            val = val.strip('{} ').replace(' ', '')
                            # Accept both comma and space separated
                            vals = [float(x) for x in re.split(r'[ ,]+', val) if x]
                            rec['value'] = vals
                        else:
                            try:
                                rec['value'] = int(val)
                            except ValueError:
                                try:
                                    rec['value'] = float(val)
                                except ValueError:
                                    rec['value'] = val
                        records.append(rec)
    if not records:
        print("[WARNING] No log lines matched the expected format. Check your log files or update the regex in parse_logs().")
        return pd.DataFrame()
    df = pd.DataFrame(records)
    return df

# basic anomaly detection (statistical + rule-based)
def detect_anomalies(df):
    anomalies = []
    # Example: flag numeric 'output', 'input', or 'saturated' outliers
    for key in ['output', 'input']:
        sub = df[df['key'] == key]
        if not sub.empty and sub['value'].apply(lambda v: isinstance(v, (int, float))).all():
            vals = sub['value'].astype(float)
            mean = vals.mean()
            std = vals.std()
            threshold = mean + 3 * std
            for idx, row in sub.iterrows():
                if abs(row['value']) > threshold:
                    anomalies.append(row.name)
    # Flag 'saturated' if not 0 or 1
    sub = df[df['key'] == 'saturated']
    for idx, row in sub.iterrows():
        if row['value'] not in [0, 1]:
            anomalies.append(row.name)
    return df.loc[anomalies]

# saving anomaly report
def save_report(anomalies):
    os.makedirs(os.path.dirname(ANOMALY_REPORT), exist_ok=True)
    anomalies.to_csv(ANOMALY_REPORT, index=False)
    print(f"Anomaly report saved to {ANOMALY_REPORT}")

if __name__ == "__main__":
    export_logs()
    df = parse_logs(LOG_DIR)
    print(f"Parsed {len(df)} log entries.")
    if df.empty:
        print("No valid log entries found. Exiting without anomaly detection.")
    else:
        anomalies = detect_anomalies(df)
        print(f"Detected {len(anomalies)} anomalies.")
        save_report(anomalies)
