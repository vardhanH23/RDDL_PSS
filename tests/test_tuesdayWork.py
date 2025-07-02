import os

def test_env_token():
    assert os.getenv("RDDL_API_TOKEN") is not None, "RDDL_API_TOKEN must be set"
