"""
Script to extract features from log files for ML analysis.
"""
import re
import sys

def extract_features_from_log(log_path):
    features = []
    with open(log_path, 'r') as f:
        for line in f:
            # Example: extract timestamp, input, output values from lines like:
            # 2025-07-02 23:36:56,167 - INFO - input=1.23 output=4.56
            match = re.search(r'(\d{4}-\d{2}-\d{2} [\d:,]+).*input=([\d.]+).*output=([\d.]+)', line)
            if match:
                timestamp = match.group(1)
                input_val = float(match.group(2))
                output_val = float(match.group(3))
                features.append({'timestamp': timestamp, 'input': input_val, 'output': output_val})
    return features

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_features.py <logfile>")
        sys.exit(1)
    log_file = sys.argv[1]
    feats = extract_features_from_log(log_file)
    for feat in feats:
        print(feat)
