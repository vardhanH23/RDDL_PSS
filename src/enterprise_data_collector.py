"""
Enterprise Data Collector - Unified RDDL System

Single comprehensive tool for collecting data from all RDDL applications:
- RDDL projects (already working)
- JIRA projects (on RDDL)
- Other enterprise applications (on RDDL)

Based on user insights: All systems are on RDDL, just different application names/URLs.
"""
import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class EnterpriseDataCollector:
    def __init__(self):
        self.token = os.getenv('RDDL_API_TOKEN')
        if not self.token:
            raise ValueError("RDDL_API_TOKEN environment variable required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })
        
        # Base configuration
        self.base_url = "https://rd-datalake.icp.infineon.com/api/v1"
        self.data_dir = Path("data/enterprise_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Start with confirmed working project, discover others later
        self.known_working_projects = ['PWRLIB72']
        
        # All potential projects to test (for discovery mode)
        self.potential_projects = [
            # RDDL projects
            'DEMOVID', 'IMAGIMOB', 'LAILA', 'RDDLDEMO', 'TTI-9',
            # JIRA-related projects  
            'DBSDEC', 'VR00330757', 'VR00473862', 'ANPR', 'VR00458351', 'WSTLTJ',
            # Other application projects
            'VR00196400', 'VR00196396', 'VR00473879', 'ACT', 'VR00466059'
        ]
    
    def test_project_access(self, project_key):
        """Test if we can access a specific project"""
        url = f"{self.base_url}/projects/{project_key}/artifacts/metadata"
        try:
            response = self.session.get(url, params={'pageSize': 1})
            return {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'error': None if response.status_code == 200 else response.text[:200]
            }
        except Exception as e:
            return {'accessible': False, 'status_code': None, 'error': str(e)}
    
    def fetch_project_artifacts(self, project_key, max_artifacts=100):
        """Fetch artifacts from a project with pagination"""
        url = f"{self.base_url}/projects/{project_key}/artifacts/metadata"
        all_artifacts = []
        page = 0
        
        while len(all_artifacts) < max_artifacts:
            params = {
                'pageSize': min(25, max_artifacts - len(all_artifacts)),
                'page': page
            }
            
            try:
                response = self.session.get(url, params=params)
                if response.status_code != 200:
                    logging.warning(f"Error fetching {project_key} page {page}: {response.status_code}")
                    break
                
                data = response.json()
                artifacts = data.get('data', [])
                
                if not artifacts:
                    break
                
                all_artifacts.extend(artifacts)
                page += 1
                
                logging.info(f"{project_key}: Fetched page {page}, total artifacts: {len(all_artifacts)}")
                
            except Exception as e:
                logging.error(f"Error fetching {project_key}: {e}")
                break
        
        return all_artifacts
    
    def quick_collect_known_projects(self):
        """Quickly collect from known working projects, then discover new ones"""
        logging.info("� Quick collection from confirmed working projects...")
        
        results = {
            'collection_timestamp': datetime.now().isoformat(),
            'working_projects': {},
            'newly_discovered': {},
            'summary': {'total_artifacts': 0, 'working_projects': 0}
        }
        
        # Collect from known working projects first
        for project_key in self.known_working_projects:
            logging.info(f"📥 Collecting from {project_key} (confirmed working)...")
            
            try:
                artifacts = self.fetch_project_artifacts(project_key, max_artifacts=100)
                results['working_projects'][project_key] = {
                    'artifact_count': len(artifacts),
                    'sample_artifacts': artifacts[:5] if artifacts else [],
                    'status': 'confirmed_working'
                }
                results['summary']['total_artifacts'] += len(artifacts)
                results['summary']['working_projects'] += 1
                
                logging.info(f"✅ {project_key}: {len(artifacts)} artifacts collected")
                
            except Exception as e:
                logging.error(f"❌ {project_key}: {e}")
                results['working_projects'][project_key] = {'error': str(e)}
        
        # Test a small sample of potential projects to discover new accessible ones
        logging.info("\n🔍 Testing sample of potential projects for new discoveries...")
        test_sample = self.potential_projects[:10]  # Test first 10 only
        
        for project_key in test_sample:
            access_test = self.test_project_access(project_key)
            if access_test['accessible']:
                logging.info(f"🎉 NEW DISCOVERY: {project_key} is accessible!")
                artifacts = self.fetch_project_artifacts(project_key, max_artifacts=25)
                results['newly_discovered'][project_key] = {
                    'artifact_count': len(artifacts),
                    'sample_artifacts': artifacts[:3] if artifacts else []
                }
                results['summary']['total_artifacts'] += len(artifacts)
                results['summary']['working_projects'] += 1
        
        return results
    
    def collect_from_accessible_projects(self, max_artifacts_per_project=100):
        """Collect data from accessible projects efficiently"""
        logging.info("📥 Starting focused data collection...")
        
        # Use the quick collection method
        collection_results = self.quick_collect_known_projects()
        
        # Save collection results
        collection_file = self.data_dir / f"enterprise_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(collection_file, 'w', encoding='utf-8') as f:
            json.dump(collection_results, f, indent=2, ensure_ascii=False)
        
        logging.info(f"📁 Results saved: {collection_file}")
        return collection_results
    
    def run_comprehensive_enterprise_scan(self):
        """Run the complete enterprise data collection"""
        logging.info("🚀 ENTERPRISE DATA COLLECTION - FOCUSED APPROACH")
        logging.info("=" * 60)
        logging.info("Collecting from confirmed working projects + testing for new discoveries...")
        
        try:
            results = self.collect_from_accessible_projects()
            
            if results and results['summary']['total_artifacts'] > 0:
                self.print_final_summary(results)
                return results
            else:
                logging.error("Data collection failed!")
                return None
                
        except Exception as e:
            logging.error(f"Enterprise collection error: {e}")
            return None
    
    def print_final_summary(self, results):
        """Print final summary of data collection"""
        print("\n" + "=" * 70)
        print("🎯 ENTERPRISE DATA COLLECTION SUMMARY")
        print("=" * 70)
        
        summary = results['summary']
        print(f"📊 Working Projects: {summary['working_projects']}")
        print(f"📦 Total Artifacts: {summary['total_artifacts']}")
        
        # Show working projects
        if results['working_projects']:
            print(f"\n✅ CONFIRMED WORKING PROJECTS:")
            for project, data in results['working_projects'].items():
                if 'artifact_count' in data:
                    print(f"   {project:15} {data['artifact_count']:>6} artifacts")
        
        # Show newly discovered projects
        if results['newly_discovered']:
            print(f"\n� NEWLY DISCOVERED PROJECTS:")
            for project, data in results['newly_discovered'].items():
                print(f"   {project:15} {data['artifact_count']:>6} artifacts")
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Focus on PWRLIB72 for comprehensive software improvement analysis")
        print(f"   This project has {results['working_projects'].get('PWRLIB72', {}).get('artifact_count', 0)} artifacts with high-value data types")

def main():
    """Main execution function"""
    print("🔍 ENTERPRISE DATA COLLECTOR")
    print("=" * 40)
    print("Unified tool for all RDDL enterprise applications")
    print("(RDDL projects, JIRA projects, and other enterprise apps)")
    print()
    
    try:
        collector = EnterpriseDataCollector()
        results = collector.run_comprehensive_enterprise_scan()
        
        if results:
            print("\n🚀 Enterprise data collection completed successfully!")
            print("📁 Check the data/enterprise_data/ folder for detailed results")
        else:
            print("\n❌ Enterprise data collection failed - check logs for details")
            
    except ValueError as e:
        print(f"\n❌ Setup Error: {e}")
        print("\n🔧 Required Setup:")
        print("1. Connect to Infineon VPN")
        print("2. Set RDDL_API_TOKEN environment variable")
        print("   Get token: https://rd-datalake.icp.infineon.com (Profile -> API Tokens)")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()
