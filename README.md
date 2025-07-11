# RDDL PIP Automation Task

Automates downloading log/xml files, uploading to R&D Data Lake, and cleaning up.

## Setup

1. Clone the repo:
   ```sh
   git clone https://gitlab.intra.infineon.com/ifx/innersource/icw-iot-testdev/rddl_pip_automationtask.git
   cd rddl_pip_automationtask/AfterAuth
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set environment variables:
   - `RDDL_API_TOKEN` (required)
   - `BASE_URL` (optional, default provided)

## Usage

Run the main script:
```sh
python src/data_lake_uploader.py
```

## Testing

```sh
pytest
```

## Anomaly Detection for CI/CD Logs

This project provides an AI-powered anomaly detection and remediation system for CI/CD pipelines in an industrial/enterprise setting (Infineon, PSS division).

### Features
- **Log Export & Parsing:** Uses RDDL automation to collect and parse logs from Infineon Data Lake.
- **Data Cleaning:** Handles missing values, normalizes, and segments log data.
- **Anomaly Detection:** Implements both rule-based and statistical anomaly detection as a baseline.
- **Extensible:** Designed for future ML-based anomaly detection and root cause analysis.

### Usage

1. **Export Logs:**
   - Ensure logs are available in `data/logs/` (or use the RDDL automation to download).
2. **Run Anomaly Detection:**
   ```bash
   python src/anomaly_detection.py
   ```
3. **View Results:**
   - Anomaly report is saved to `data/anomaly_report.csv`.

### File Structure

- `src/data_lake_uploader.py` – Existing log export/parse utilities
- `src/anomaly_detection.py` – New anomaly detection script
- `data/logs/` – Directory for raw log files
- `data/anomaly_report.csv` – Output anomaly report
- `tests/` – Unit tests

### Next Steps
- Add advanced ML-based anomaly detection (LogBERT, LogGPT, etc.)
- Integrate with Data Lake uploader for end-to-end automation
- Add more robust tests and CI integration

### References
- LogSage (2024), LogBERT (2021), LogGPT (2023), Informer (2021)

### Report

#### Approach
- Used rule-based and statistical methods for initial anomaly detection.
- Focused on error codes, status, and outlier durations.

#### Challenges
- Log format variability
- Handling missing or inconsistent data
- Threshold selection for statistical anomalies

---
For questions, contact the project maintainer.
