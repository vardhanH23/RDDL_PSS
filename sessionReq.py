import os
import requests
import logging
from rddl_client import DataLakeClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Logs to console (visible in CI logs)
    ]
)

# Environment Variables
PROJECT_KEY = os.getenv("PROJECT_KEY", "PWRLIB72")  # Default to PWRLIB72 
BASE_URL = os.getenv("BASE_URL", "https://rd-datalake.icp.infineon.com")
DATA_SOURCE_URL = os.getenv("DATA_SOURCE_URL", "https://mtb-webserver.icp.infineon.com/pext/library/mtb-pext-pctrl/develop/Latest/deploy/test/uut/")
TEMP_FILE_PATH = "temp_data_file"  # Temporary file path for downloaded data
# RDDL_API_TOKEN = os.getenv("RDDL_API_TOKEN", "eyjhbGciOiJSUzI1NiIsImtpZCI6IjA4XzY0WDFCTVFQZVUwR1BsX0Vhd1dzT3Q3YyIsInBpLmF0bSI6InRkbTUifQ.eyJzY29wZSI6Im9 wZW5pZCBlbWFpbCBwcm9maWxlIiwiY2xpZW50X2mRkbCIsImlzcyI6Imh0dHBzOi8vZmVkZXJhdGUuaW5maW5lb24uY29tIiwiY XVkIjoicmRkbCIsImZpcnN0TmFtZSI6IkpvY2hlbiIsImxhc3ROYW1lIjoiV2VpcyIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJjb3VudHJ 5U2hvcnQiOiJERSIsImRpc3BsYXlOYW1lIjoiV2VpcyBKb2NoZW4gKElGQUcgSVQgUkRJIFJEIFBFIC8gRXh0ZXJuYWwpIiwiY29tcGFue SI6IkFyYUNvbSBJVCBTZXJ2aWNlcyBnJlYWxtIjoiSU5UIiwiZW1haWwiOiJXZWlzLmV4dGVybmFsM0BpbmZpbmVvbi5jb20iLCJ tYWlsRG9tYWluVHlwZSI6Ik9LIiwidXNlcm5hbWUiOiJ3ZWlzamajaCIsImV4cCI6MTY1NjQzMTUxOX0.1N-klQ35uo044kP9EsqBp_l81 iLvvxdckDachSMKb76YdupJ7uPVuejQhR51jQSI6gSrjsnLTt3qdpKzTMTevG9x2qM0hg6i-AVG5GWEJeOg-kYSnn05OReAv_MGUOWEGNJ Hie6n0ntoSvQ0dPIFv3hcHWmpGJ6Lfkk9lEvq8K1UEbk3eB814433Zi7y77Mafwo1Gkrv90vnq43cSPcJe2uZ32avAwXL5GTu_bTvBVSXx 9dIJ8itje3S9RnTtb5oZZSI5BqKvGZYvNyOzGSuFsgnqc5S73QS4mc7eV-tu6yRQE0HhiJnPw_sXR735lc4uFyNQxO0Jgwyoo2qcwrN1A")  # Replace with your token
RDDL_API_TOKEN = os.getenv("RDDL_API_TOKEN")



# Metadata for uploading the artifact
ARTIFACT_METADATA = {
    "name": "ci_logs",  # Name of the artifact
    "description": "Logs uploaded by CI pipeline",  # Optional description
    "tags": ["ci", "automation", "logs"]  # Optional tags
}

# Ensure the token is available
if not RDDL_API_TOKEN:
    logging.error("Bearer token (RDDL_API_TOKEN) is not set. Please set it in your environment.")
    exit(1)

try:
    # Step 1: Initialize the Data Lake Client with Bearer Token authentication
    logging.info("Initializing Data Lake Client with Bearer token authentication...")
    auth_credentials = {"token": RDDL_API_TOKEN}
    clnt = DataLakeClient(
        project_key=PROJECT_KEY,
        base_url=BASE_URL,
        auth_credentials=auth_credentials
    )
    clnt.check_platform()
    logging.info("Platform connection successful.")

    # Step 2: Create access policy
    logging.info("Creating access policy...")
    access_policy_url = f"{BASE_URL}/api/v1/projects/{PROJECT_KEY}/access-policies"
    access_policy_data = {
  "name": "AllowWriteCalculationnew1",
  "resource": "artifacts",
  "permissions": [
    "read",
    "write"
  ],
  "roleOp": "AND",
  "roles": [
    "calculator"
  ],
  "conditions": [
    {
      "type": "label",
      "label": "calculation"
    }
  ]
}
    
    # {
    #     "name": "AllowWriteCalculation4",
    #     "resource": "artifacts",
    #     "permissions": [
    #         "read",
    #         "write"
    #     ],
    #     "roleOp": "AND",
    #     "roles": [
    #         "calculator"
    #     ],
    #     "conditions": [
    #         {
    #             "type": "label",
    #             "label": "calculation"
    #         }
    #     ]
    # }
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {RDDL_API_TOKEN}",
        "Content-Type": "application/json"
    })
    response = session.post(access_policy_url, json=access_policy_data)
    response.raise_for_status()  # Raise an exception for HTTP errors
    logging.info("Access policy created successfully.")

    # Step 3: Fetch available projects
    logging.info("Fetching available projects...")
    projects = clnt.get_projects()
    if projects and projects.get("data"):
        logging.info(f"Projects available: {projects['data']}")
    else:
        logging.warning("No projects assigned to your user account.")

    # Step 4: Download the data from the source URL
    logging.info(f"Downloading data from {DATA_SOURCE_URL}...")
    response = requests.get(DATA_SOURCE_URL)
    response.raise_for_status()  # Raise an exception for HTTP errors
    with open(TEMP_FILE_PATH, "wb") as temp_file:
        temp_file.write(response.content)
    logging.info(f"Data downloaded successfully to {TEMP_FILE_PATH}.")

    # Step 5: Upload the artifact to the R&D Data Lake
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
    # Step 6: Clean up temporary file
    if os.path.exists(TEMP_FILE_PATH):
        os.remove(TEMP_FILE_PATH)
        logging.info("Temporary file removed.")

logging.info("CI pipeline process completed successfully.")
