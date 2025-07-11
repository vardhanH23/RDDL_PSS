"""
RDDL Data Downloader

- Authenticates with RDDL using API token
- Lists all artifacts for a given project
- Downloads each artifact and saves it in a folder by type (logs, images, xml, etc.)
- Easily extendable for new data types
"""
import os
import sys
import requests
import mimetypes

# User config
PROJECT_KEY = os.getenv("RDDL_PROJECT_KEY", "PWRLIB72")
BASE_URL = os.getenv("RDDL_BASE_URL", "https://rd-datalake.icp.infineon.com")
RDDL_API_TOKEN = os.getenv("RDDL_API_TOKEN")

if not RDDL_API_TOKEN:
    print("[ERROR] RDDL_API_TOKEN not set in environment.")
    sys.exit(1)

# Correct endpoint for listing artifacts with metadata (add /api)
ARTIFACTS_URL = f"{BASE_URL}/api/v1/projects/{PROJECT_KEY}/artifacts/metadata"
HEADERS = {
    "Authorization": f"Bearer {RDDL_API_TOKEN}",
}
DATA_DIR = "data/rddl_downloads"
os.makedirs(DATA_DIR, exist_ok=True)

def get_artifacts():
    resp = requests.get(ARTIFACTS_URL, headers=HEADERS, timeout=30)
    print(f"[DEBUG] Status code: {resp.status_code}")
    print(f"[DEBUG] Response headers: {resp.headers}")
    if 'application/json' not in resp.headers.get('Content-Type', ''):
        print("[ERROR] Response is not JSON. Response text:")
        print(resp.text)
        resp.raise_for_status()
    try:
        data = resp.json()
    except Exception as e:
        print("[ERROR] Could not decode JSON. Response text:")
        print(resp.text)
        raise
    return data.get("artifacts", [])

def download_artifact(artifact):
    artifact_id = artifact.get("id")
    name = artifact.get("filename", f"artifact_{artifact_id}")
    type_hint = artifact.get("contentType") or mimetypes.guess_type(name)[0] or "other"
    # Organize by type
    if "image" in type_hint:
        subdir = "images"
    elif name.endswith(".log"):
        subdir = "logs"
    elif name.endswith(".csv"):
        subdir = "csv"
    elif name.endswith(".xml"):
        subdir = "xml"
    else:
        subdir = "other"
    save_dir = os.path.join(DATA_DIR, subdir)
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, name)
    # Download file
    url = f"{BASE_URL}/api/v1/artifacts/{artifact_id}/download"
    print(f"Downloading {name} to {save_path} ...")
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(resp.content)
    print(f"Saved {name} to {save_path}")

def main():
    print(f"Listing artifacts for project {PROJECT_KEY} ...")
    artifacts = get_artifacts()
    print(f"Found {len(artifacts)} artifacts.")
    for artifact in artifacts:
        try:
            download_artifact(artifact)
        except Exception as e:
            print(f"[WARNING] Failed to download {artifact.get('filename')}: {e}")
    print("All downloads complete.")

if __name__ == "__main__":
    main()
