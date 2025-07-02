import os
import requests
import logging
from rddl_client import DataLakeClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Environment Variables
PROJECT_KEY = os.getenv("PROJECT_KEY", "PWRLIB72")
BASE_URL = os.getenv("BASE_URL", "https://rd-datalake.icp.infineon.com")
DATA_SOURCE_URL = os.getenv("DATA_SOURCE_URL", "https://mtb-webserver.icp.infineon.com/pext/library/mtb-pext-pctrl/develop/Latest/deploy/test/uut/")
TEMP_FILE_PATH = "temp_data_file"

# IMPORTANT: Set your RDDL_API_TOKEN as an environment variable before running this script.
# Example (PowerShell): $env:RDDL_API_TOKEN="your_actual_token_here"
RDDL_API_TOKEN = os.getenv("RDDL_API_TOKEN")

ARTIFACT_METADATA = {
    "name": "ci_logs",
    "description": "Logs uploaded by CI pipeline",
    "tags": ["ci", "automation", "logs"]
}

if not RDDL_API_TOKEN:
    logging.error("Bearer token (RDDL_API_TOKEN) is not set. Please set it in your environment.")
    exit(1)

try:
    # Initialize Data Lake Client
    logging.info("Initializing Data Lake Client with Bearer token authentication...")
    auth_credentials = {"token": RDDL_API_TOKEN}
    clnt = DataLakeClient(
        project_key=PROJECT_KEY,
        base_url=BASE_URL,
        auth_credentials=auth_credentials
    )
    clnt.check_platform()
    logging.info("Platform connection successful.")

    # Download the data from the source URL
    logging.info(f"Downloading data from {DATA_SOURCE_URL}...")
    response = requests.get(DATA_SOURCE_URL)
    response.raise_for_status()
    with open(TEMP_FILE_PATH, "wb") as temp_file:
        temp_file.write(response.content)
    logging.info(f"Data downloaded successfully to {TEMP_FILE_PATH}.")

    # Upload the artifact to the R&D Data Lake
    logging.info("Uploading artifact to the R&D Data Lake...")
    clnt.upload_artifact(TEMP_FILE_PATH, ARTIFACT_METADATA)
    logging.info("Artifact uploaded successfully.")

except requests.exceptions.RequestException as req_err:
    logging.error(f"Request error occurred: {req_err}")
    exit(1)
except Exception as e:
    logging.error(f"An error occurred: {e}")
    exit(1)
finally:
    if os.path.exists(TEMP_FILE_PATH):
        os.remove(TEMP_FILE_PATH)
        logging.info("Temporary file removed.")

logging.info("Pipeline process completed successfully.")
