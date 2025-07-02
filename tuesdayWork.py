import os
import requests
import logging
from rddl_client import DataLakeClient
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Set the actual server URL and RDDL project key
server_url = "https://mtb-webserver.icp.infineon.com/pext/library/mtb-pext-pctrl/develop/Latest/deploy/test/uut/"
rddl_project_key = "PWRLIB72"

BASE_URL = os.getenv("BASE_URL", "https://rd-datalake.icp.infineon.com")
RDDL_API_TOKEN = os.getenv("RDDL_API_TOKEN")

if not RDDL_API_TOKEN:
    logging.error("Bearer token (RDDL_API_TOKEN) is not set. Please set it in your environment.")
    exit(1)

try:
    # Initialize Data Lake Client
    logging.info("Initializing Data Lake Client with Bearer token authentication...")
    auth_credentials = {"token": RDDL_API_TOKEN}
    clnt = DataLakeClient(
        project_key=rddl_project_key,
        base_url=BASE_URL,
        auth_credentials=auth_credentials
    )
    clnt.check_platform()
    logging.info("Platform connection successful.")

    # Step 1: Get directory listing
    logging.info(f"Fetching directory listing from {server_url} ...")
    response = requests.get(server_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    file_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(('.log', '.xml'))]

    if not file_links:
        logging.warning("No log or xml files found in the directory.")
        exit(0)

    for file_link in file_links:
        # Use urljoin to build the correct file URL
        file_url = urljoin(server_url, file_link)
        local_file = os.path.basename(file_link)
        logging.info(f"Downloading {file_url} ...")
        file_resp = requests.get(file_url)
        file_resp.raise_for_status()
        with open(local_file, "wb") as f:
            f.write(file_resp.content)
        logging.info(f"Downloaded {local_file}.")

        artifact_metadata = {
            "name": local_file,
            "description": f"Auto-uploaded log file {local_file}",
            "tags": ["ci", "automation", "logs"]
        }
        logging.info(f"Uploading {local_file} to R&D Data Lake ...")
        clnt.upload_artifact(local_file, artifact_metadata)
        logging.info(f"Uploaded {local_file} successfully.")
        os.remove(local_file)
        logging.info(f"Removed local file {local_file}.")

except requests.exceptions.RequestException as req_err:
    logging.error(f"Request error occurred: {req_err}")
    exit(1)
except Exception as e:
    logging.error(f"An error occurred: {e}")
    exit(1)

logging.info("Pipeline process completed successfully.")
