"""
Module to download log/xml files from a remote server and upload them to R&D Data Lake.
"""
import os
import sys
import logging
import mimetypes
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuration
SERVER_URL = "https://mtb-webserver.icp.infineon.com/pext/library/mtb-pext-pctrl/develop/Latest/deploy/test/uut/"
PROJECT_KEY = "PWRLIB72"
BASE_URL = os.getenv("BASE_URL", "https://rd-datalake.icp.infineon.com")
RDDL_API_TOKEN = os.getenv("RDDL_API_TOKEN")

if not RDDL_API_TOKEN:
    logging.error("Bearer token (RDDL_API_TOKEN) is not set. Please set it in your environment.")
    sys.exit(1)

ARTIFACT_UPLOAD_URL = f"{BASE_URL}/api/v1/projects/{PROJECT_KEY}/artifacts"
HEADERS = {
    "Authorization": f"Bearer {RDDL_API_TOKEN}",
}

LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def guess_content_type(filename):
    """Guess the MIME type for a file."""
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"

def upload_file(local_file, headers, upload_url):
    """Upload a file to the R&D Data Lake."""
    with open(local_file, "rb") as f:
        file_data = f.read()
    response = requests.post(
        upload_url,
        headers=headers,
        data=file_data,
        timeout=60
    )
    return response

def main():
    try:
        logging.info("Fetching directory listing from %s ...", SERVER_URL)
        response = requests.get(SERVER_URL, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        file_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(('.log', '.xml'))]

        if not file_links:
            logging.warning("No log or xml files found in the directory.")
            sys.exit(0)

        for file_link in file_links:
            file_url = urljoin(SERVER_URL, file_link)
            local_file = os.path.basename(file_link)
            log_path = os.path.join(LOGS_DIR, local_file)
            logging.info("Downloading %s ...", file_url)
            file_resp = requests.get(file_url, timeout=30)
            file_resp.raise_for_status()
            with open(log_path, "wb") as f:
                f.write(file_resp.content)
            logging.info("Downloaded %s.", log_path)

            content_type = guess_content_type(local_file)
            upload_headers = {
                "Authorization": f"Bearer {RDDL_API_TOKEN}",
                "Filename": local_file,
                "Metadata": f'{{"description": "Auto-uploaded log file {local_file}", "tags": ["ci", "automation", "logs"]}}',
                "ContentType": content_type,
                "content-type": content_type,
                "Content-Type": content_type
            }
            logging.debug("Upload headers: %s", upload_headers)  # Uncomment for troubleshooting
            logging.info("Uploading %s to R&D Data Lake ...", local_file)
            upload_resp = upload_file(log_path, upload_headers, ARTIFACT_UPLOAD_URL)
            if upload_resp.status_code == 201:
                logging.info("Uploaded %s successfully.", local_file)
            else:
                logging.error("Failed to upload %s. Status: %s, Response: %s", local_file, upload_resp.status_code, upload_resp.text)
        # Print files left in logs dir
        remaining = os.listdir(LOGS_DIR)
        logging.info("Files remaining in %s: %s", LOGS_DIR, remaining)

    except requests.exceptions.RequestException as req_err:
        logging.error("Request error occurred: %s", req_err)
        sys.exit(1)
    except Exception as e:
        logging.error("An error occurred: %s", e)
        sys.exit(1)

    logging.info("Pipeline process completed successfully.")

if __name__ == "__main__":
    main()
