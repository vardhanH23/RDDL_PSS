import os
import pandas as pd
import pytest
from src.anomaly_detection import parse_logs, detect_anomalies

def test_parse_logs(tmp_path):
    # Create a fake log file in the real log format
    log_content = """
test_fb_filter_3p3z.c:123:test_Filter3p3z:INFO: input = 10000
test_fb_filter_3p3z.c:124:test_Filter3p3z:INFO: output = 6
test_fb_filter_3p3z.c:125:test_Filter3p3z:INFO: in = { 10000, 0, 0 }
test_fb_filter_3p3z.c:126:test_Filter3p3z:INFO: out = { 456250, 0, 0 }
test_fb_filter_3p3z.c:123:test_Filter3p3z:INFO: input = 10800
test_fb_filter_3p3z.c:124:test_Filter3p3z:INFO: output = 27
test_fb_filter_3p3z.c:125:test_Filter3p3z:INFO: in = { 10800, 10000, 0 }
test_fb_filter_3p3z.c:126:test_Filter3p3z:INFO: out = { 1824457, 456250, 0 }
"""
    log_dir = tmp_path / "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = log_dir / "test.log"
    with open(log_file, "w") as f:
        f.write(log_content.strip())
    df = parse_logs(str(log_dir))
    assert len(df) == 8  # 8 lines in the test log
    # Check that input/output keys are parsed
    assert set(df['key']).issuperset({'input', 'output', 'in', 'out'})
    anomalies = detect_anomalies(df)
    # No anomalies expected in this simple test
    assert isinstance(anomalies, pd.DataFrame)
