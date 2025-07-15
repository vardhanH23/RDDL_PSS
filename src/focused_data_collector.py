"""
Focused Data Collector

Based on enterprise scan results: PWRLIB72 is the main accessible project.
This tool efficiently downloads all artifacts from accessible projects.
Uses the proven working logic from data_lake_uploader.py and rddl_data_downloader.py.
"""
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FocusedDataCollector:
    def __init__(self):
        self.token = os.getenv('RDDL_API_TOKEN')
        if not self.token:
            raise ValueError("RDDL_API_TOKEN environment variable required")
        
        # Use the proven working configuration
        self.base_url = "https://rd-datalake.icp.infineon.com"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Data organization
        self.data_root = Path("data/focused_collection")
        self.data_root.mkdir(exist_ok=True)
        
        # Known working projects (from enterprise scan)
        self.working_projects = ['PWRLIB72']
    
    def get_artifact_type(self, artifact):
        """Determine folder type for artifact organization"""
        name = artifact.get("filename", "")
        content_type = artifact.get("contentType", "")
        
        # Check content type first
        if "xml" in content_type or name.lower().endswith(".xml"):
            return "xml"
        elif "text/plain" in content_type or name.lower().endswith((".log", ".txt")):
            return "logs"
        elif "image" in content_type or name.lower().endswith((".png", ".jpg", ".jpeg")):
            return "images"
        elif "csv" in content_type or name.lower().endswith(".csv"):
            return "csv"
        else:
            return "other"
    
    def get_artifacts_metadata(self, project_key):
        """Get all artifacts metadata for a project using proven API pattern"""
        url = f"{self.base_url}/api/v1/projects/{project_key}/artifacts/metadata"
        all_artifacts = []
        page_number = 1
        
        while True:
            params = {"pageSize": 25, "pageNumber": page_number}
            logging.info(f"Fetching {project_key} page {page_number}...")
            
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if resp.status_code == 200:
                    data = resp.json()
                    artifacts = data.get("data", [])
                    
                    if not artifacts:
                        break
                    
                    # Standardize artifact format
                    for artifact in artifacts:
                        if "artifactID" in artifact:
                            standardized = {
                                "id": artifact["artifactID"],
                                "filename": artifact.get("rawDataFile", {}).get("fileName", "unknown"),
                                "contentType": artifact.get("rawDataFile", {}).get("contentType", ""),
                                "fileSize": artifact.get("rawDataFile", {}).get("fileSize", 0),
                                "dateCreated": artifact.get("dateCreated", ""),
                                "description": artifact.get("description", "")
                            }
                            all_artifacts.append(standardized)
                    
                    if len(artifacts) < 25:
                        break
                    page_number += 1
                else:
                    logging.error(f"Error fetching {project_key}: {resp.status_code}")
                    break
                    
            except Exception as e:
                logging.error(f"Request error for {project_key}: {e}")
                break
        
        logging.info(f"Found {len(all_artifacts)} artifacts in {project_key}")
        return all_artifacts
    
    def download_artifact(self, project_key, artifact):
        """Download single artifact using proven API pattern"""
        artifact_id = artifact.get("id")
        if not artifact_id:
            return False, "No artifact ID"
        
        name = artifact.get("filename", f"artifact_{artifact_id}")
        artifact_type = self.get_artifact_type(artifact)
        
        # Create organized directory structure
        project_dir = self.data_root / project_key
        type_dir = project_dir / artifact_type
        type_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = type_dir / name
        
        # Use proven download API endpoint
        download_url = f"{self.base_url}/api/v1/projects/{project_key}/artifacts/{artifact_id}"
        
        try:
            logging.info(f"Downloading {name} ({artifact_type})...")
            
            resp = requests.get(download_url, headers=self.headers, timeout=120)
            resp.raise_for_status()
            
            # Save file
            with open(save_path, "wb") as f:
                f.write(resp.content)
            
            file_size = len(resp.content) / 1024  # KB
            logging.info(f"✅ Saved {name} ({file_size:.1f} KB) to {save_path}")
            
            return True, str(save_path)
            
        except Exception as e:
            logging.error(f"❌ Failed to download {name}: {e}")
            return False, str(e)
    
    def collect_project_data(self, project_key):
        """Collect all data from a project"""
        logging.info(f"\n=== COLLECTING DATA FROM {project_key} ===")
        
        # Get all artifacts metadata
        artifacts = self.get_artifacts_metadata(project_key)
        
        if not artifacts:
            logging.warning(f"No artifacts found in {project_key}")
            return None
        
        # Create project directory
        project_dir = self.data_root / project_key
        project_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            "project_key": project_key,
            "collection_date": datetime.now().isoformat(),
            "total_artifacts": len(artifacts),
            "artifacts": artifacts
        }
        
        metadata_path = project_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Download all artifacts
        results = {
            'project_key': project_key,
            'total_artifacts': len(artifacts),
            'successful_downloads': 0,
            'failed_downloads': 0,
            'downloads': [],
            'file_types': {}
        }
        
        for i, artifact in enumerate(artifacts, 1):
            logging.info(f"[{i}/{len(artifacts)}] Processing {artifact.get('filename', 'unnamed')}")
            
            success, result = self.download_artifact(project_key, artifact)
            
            artifact_type = self.get_artifact_type(artifact)
            results['file_types'][artifact_type] = results['file_types'].get(artifact_type, 0) + 1
            
            if success:
                results['successful_downloads'] += 1
                results['downloads'].append({
                    'filename': artifact.get('filename'),
                    'type': artifact_type,
                    'path': result,
                    'size': artifact.get('fileSize', 0)
                })
            else:
                results['failed_downloads'] += 1
                logging.error(f"Failed: {artifact.get('filename')} - {result}")
        
        # Save results summary
        results_path = project_dir / "collection_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logging.info(f"\n📊 {project_key} Collection Complete:")
        logging.info(f"   ✅ Downloaded: {results['successful_downloads']}/{results['total_artifacts']}")
        logging.info(f"   ❌ Failed: {results['failed_downloads']}")
        logging.info(f"   📁 Saved to: {project_dir}")
        
        return results
    
    def run_focused_collection(self):
        """Run focused collection on all accessible projects"""
        logging.info("🎯 FOCUSED DATA COLLECTION")
        logging.info("=" * 50)
        logging.info("Downloading all artifacts from accessible projects...")
        
        collection_summary = {
            'collection_timestamp': datetime.now().isoformat(),
            'projects': {},
            'total_summary': {
                'projects_processed': 0,
                'total_artifacts': 0,
                'total_downloads': 0,
                'total_failures': 0
            }
        }
        
        for project_key in self.working_projects:
            try:
                results = self.collect_project_data(project_key)
                
                if results:
                    collection_summary['projects'][project_key] = results
                    collection_summary['total_summary']['projects_processed'] += 1
                    collection_summary['total_summary']['total_artifacts'] += results['total_artifacts']
                    collection_summary['total_summary']['total_downloads'] += results['successful_downloads']
                    collection_summary['total_summary']['total_failures'] += results['failed_downloads']
                    
            except Exception as e:
                logging.error(f"Error collecting {project_key}: {e}")
                collection_summary['projects'][project_key] = {'error': str(e)}
        
        # Save overall summary
        summary_path = self.data_root / f"collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(collection_summary, f, indent=2, ensure_ascii=False)
        
        self.print_final_summary(collection_summary)
        logging.info(f"📁 Complete summary saved: {summary_path}")
        
        return collection_summary
    
    def print_final_summary(self, summary):
        """Print final collection summary"""
        print("\n" + "=" * 80)
        print("🎯 FOCUSED DATA COLLECTION SUMMARY")
        print("=" * 80)
        
        total = summary['total_summary']
        print(f"📊 Projects Processed: {total['projects_processed']}")
        print(f"📦 Total Artifacts: {total['total_artifacts']}")
        print(f"✅ Successful Downloads: {total['total_downloads']}")
        print(f"❌ Failed Downloads: {total['total_failures']}")
        print(f"📈 Success Rate: {(total['total_downloads']/total['total_artifacts']*100):.1f}%")
        
        print(f"\n📁 PROJECT DETAILS:")
        for project_key, results in summary['projects'].items():
            if 'error' not in results:
                print(f"   {project_key}:")
                print(f"      📦 Artifacts: {results['total_artifacts']}")
                print(f"      ✅ Downloaded: {results['successful_downloads']}")
                
                if results.get('file_types'):
                    print(f"      📂 File Types: {dict(results['file_types'])}")
                
                print(f"      📁 Location: data/focused_collection/{project_key}/")
            else:
                print(f"   {project_key}: ❌ {results['error']}")

def main():
    """Main execution function"""
    print("🎯 FOCUSED ENTERPRISE DATA COLLECTOR")
    print("=" * 50)
    print("Efficiently downloads all artifacts from accessible RDDL projects")
    print("Based on enterprise scan results showing PWRLIB72 as accessible")
    print()
    
    try:
        collector = FocusedDataCollector()
        results = collector.run_focused_collection()
        
        if results and results['total_summary']['total_downloads'] > 0:
            print(f"\n🚀 Collection completed successfully!")
            print(f"📁 All files organized in: data/focused_collection/")
            print(f"🔍 Use rddl_data_analyzer.py to analyze the downloaded data")
        else:
            print(f"\n❌ Collection completed but no files downloaded")
            
    except ValueError as e:
        print(f"\n❌ Setup Error: {e}")
        print("Please set RDDL_API_TOKEN environment variable")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()
