"""
RDDL Data Analysis Tool

Analyzes the downloaded RDDL artifacts to understand:
1. What types of data we have
2. Content patterns and insights
3. Redundancy analysis
4. Potential value for software improvement
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RDDLDataAnalyzer:
    def __init__(self):
        self.rddl_dir = Path("data/rddl_downloads/PWRLIB72")
        self.analysis_dir = Path("data/rddl_analysis")
        self.analysis_dir.mkdir(exist_ok=True)
        
    def analyze_file_content(self, file_path):
        """Analyze content of a single file"""
        try:
            # Read file content
            if file_path.suffix.lower() in ['.log', '.txt']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    # Try to decode if it looks like text
                    try:
                        content = content.decode('utf-8', errors='ignore')
                    except:
                        content = f"<Binary file: {len(content)} bytes>"
            
            # Generate content hash for duplicate detection
            content_hash = hashlib.md5(str(content).encode()).hexdigest()
            
            analysis = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'content_hash': content_hash,
                'content_preview': content[:500] if len(str(content)) > 500 else content,
                'line_count': len(str(content).split('\n')) if isinstance(content, str) else 0,
                'contains_test_data': any(keyword in str(content).lower() for keyword in 
                                        ['test', 'pass', 'fail', 'error', 'warning']),
                'contains_performance_data': any(keyword in str(content).lower() for keyword in 
                                               ['time', 'duration', 'performance', 'speed', 'memory']),
                'contains_coverage_data': any(keyword in str(content).lower() for keyword in 
                                            ['coverage', 'gcov', 'percent', '%']),
                'file_type_analysis': self.analyze_file_type(file_path, content)
            }
            
            return analysis
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': str(e),
                'file_size': file_path.stat().st_size if file_path.exists() else 0
            }
    
    def analyze_file_type(self, file_path, content):
        """Analyze what type of data this file contains"""
        content_str = str(content).lower()
        
        analysis = {
            'primary_type': 'unknown',
            'data_insights': [],
            'sw_improvement_potential': 'low'
        }
        
        if file_path.name.startswith('test_'):
            analysis['primary_type'] = 'unit_test_log'
            if 'pass' in content_str or 'fail' in content_str:
                analysis['data_insights'].append('Contains test results')
                analysis['sw_improvement_potential'] = 'high'
        
        elif 'ceedling' in file_path.name:
            analysis['primary_type'] = 'build_system_log'
            analysis['data_insights'].append('Ceedling C testing framework output')
            analysis['sw_improvement_potential'] = 'medium'
        
        elif 'gcovr' in file_path.name:
            analysis['primary_type'] = 'code_coverage_report'
            analysis['data_insights'].append('Code coverage analysis')
            analysis['sw_improvement_potential'] = 'very_high'
        
        elif file_path.suffix == '.xml':
            analysis['primary_type'] = 'test_report_xml'
            analysis['data_insights'].append('Structured test report')
            analysis['sw_improvement_potential'] = 'high'
        
        elif 'temp_data' in file_path.name:
            analysis['primary_type'] = 'sensor_data'
            analysis['data_insights'].append('Sensor/measurement data')
            analysis['sw_improvement_potential'] = 'medium'
        
        # Add specific insights based on content
        if 'filter' in content_str:
            analysis['data_insights'].append('Contains filter testing data')
        if 'regulator' in content_str:
            analysis['data_insights'].append('Contains regulator testing data')
        if 'coverage' in content_str:
            analysis['data_insights'].append('Contains code coverage metrics')
        
        return analysis
    
    def find_duplicates(self, file_analyses):
        """Find duplicate files based on content hash"""
        hash_groups = {}
        for analysis in file_analyses:
            if 'content_hash' in analysis:
                hash_val = analysis['content_hash']
                if hash_val not in hash_groups:
                    hash_groups[hash_val] = []
                hash_groups[hash_val].append(analysis)
        
        duplicates = {hash_val: files for hash_val, files in hash_groups.items() if len(files) > 1}
        return duplicates
    
    def analyze_sw_improvement_potential(self, file_analyses):
        """Analyze potential for software improvement based on data types"""
        potential_analysis = {
            'high_value_data': [],
            'medium_value_data': [],
            'low_value_data': [],
            'recommendations': []
        }
        
        for analysis in file_analyses:
            if 'file_type_analysis' not in analysis:
                continue
                
            file_type = analysis['file_type_analysis']
            potential = file_type.get('sw_improvement_potential', 'low')
            
            file_info = {
                'file': analysis['file_name'],
                'type': file_type['primary_type'],
                'insights': file_type['data_insights']
            }
            
            if potential == 'very_high':
                potential_analysis['high_value_data'].append(file_info)
            elif potential == 'high':
                potential_analysis['high_value_data'].append(file_info)
            elif potential == 'medium':
                potential_analysis['medium_value_data'].append(file_info)
            else:
                potential_analysis['low_value_data'].append(file_info)
        
        # Generate recommendations
        if any('code_coverage' in str(item) for item in potential_analysis['high_value_data']):
            potential_analysis['recommendations'].append(
                "Code coverage data can identify untested code paths and improve test quality"
            )
        
        if any('test_log' in str(item) for item in potential_analysis['high_value_data']):
            potential_analysis['recommendations'].append(
                "Test logs can reveal failure patterns and help optimize test suites"
            )
        
        if any('build_system' in str(item) for item in potential_analysis['medium_value_data']):
            potential_analysis['recommendations'].append(
                "Build logs can help optimize compilation times and identify bottlenecks"
            )
        
        return potential_analysis
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis of all RDDL data"""
        logging.info("🔍 Starting comprehensive RDDL data analysis...")
        
        if not self.rddl_dir.exists():
            logging.error("No RDDL data found to analyze")
            return None
        
        # Analyze all files
        file_analyses = []
        
        for file_path in self.rddl_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.endswith('.json'):
                logging.info(f"Analyzing: {file_path.name}")
                analysis = self.analyze_file_content(file_path)
                file_analyses.append(analysis)
        
        # Find duplicates
        duplicates = self.find_duplicates(file_analyses)
        
        # Analyze SW improvement potential
        sw_potential = self.analyze_sw_improvement_potential(file_analyses)
        
        # Create comprehensive report
        comprehensive_analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_files_analyzed': len(file_analyses),
            'file_analyses': file_analyses,
            'duplicate_analysis': {
                'duplicate_groups': len(duplicates),
                'duplicates': duplicates,
                'total_duplicate_files': sum(len(files) for files in duplicates.values())
            },
            'sw_improvement_potential': sw_potential,
            'summary': {
                'total_size_bytes': sum(a.get('file_size', 0) for a in file_analyses),
                'file_types': self.get_file_type_summary(file_analyses),
                'data_value_assessment': self.assess_overall_value(sw_potential)
            }
        }
        
        # Save analysis
        analysis_file = self.analysis_dir / f"rddl_comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_analysis, f, indent=2, ensure_ascii=False)
        
        logging.info(f"📊 Analysis saved to: {analysis_file}")
        
        # Print summary
        self.print_analysis_summary(comprehensive_analysis)
        
        return comprehensive_analysis
    
    def get_file_type_summary(self, file_analyses):
        """Get summary of file types"""
        type_counts = {}
        for analysis in file_analyses:
            if 'file_type_analysis' in analysis:
                file_type = analysis['file_type_analysis']['primary_type']
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
        return type_counts
    
    def assess_overall_value(self, sw_potential):
        """Assess overall value of the dataset"""
        high_value_count = len(sw_potential['high_value_data'])
        medium_value_count = len(sw_potential['medium_value_data'])
        
        if high_value_count >= 3:
            return "Very High - Rich dataset for SW improvement"
        elif high_value_count >= 1:
            return "High - Good potential for SW insights"
        elif medium_value_count >= 3:
            return "Medium - Some useful data available"
        else:
            return "Low - Limited SW improvement potential"
    
    def print_analysis_summary(self, analysis):
        """Print analysis summary"""
        print("\n" + "="*70)
        print("🔍 RDDL DATA ANALYSIS SUMMARY")
        print("="*70)
        
        print(f"📁 Total Files Analyzed: {analysis['total_files_analyzed']}")
        print(f"💾 Total Data Size: {analysis['summary']['total_size_bytes']:,} bytes")
        print(f"🔄 Duplicate Files: {analysis['duplicate_analysis']['total_duplicate_files']}")
        print(f"📊 Overall Value: {analysis['summary']['data_value_assessment']}")
        
        print("\n📋 FILE TYPES FOUND:")
        for file_type, count in analysis['summary']['file_types'].items():
            print(f"   {file_type:25} {count:>3} files")
        
        print(f"\n🎯 SOFTWARE IMPROVEMENT POTENTIAL:")
        sw_potential = analysis['sw_improvement_potential']
        print(f"   High Value Data:   {len(sw_potential['high_value_data'])} files")
        print(f"   Medium Value Data: {len(sw_potential['medium_value_data'])} files")
        print(f"   Low Value Data:    {len(sw_potential['low_value_data'])} files")
        
        if sw_potential['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(sw_potential['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        if analysis['duplicate_analysis']['duplicate_groups'] > 0:
            print(f"\n⚠️  REDUNDANCY ANALYSIS:")
            print(f"   Found {analysis['duplicate_analysis']['duplicate_groups']} groups of duplicate files")
            print(f"   Total redundant files: {analysis['duplicate_analysis']['total_duplicate_files']}")

def main():
    """Main execution function"""
    print("🔍 RDDL DATA ANALYZER")
    print("====================")
    print("Analyzing downloaded RDDL data for software improvement insights...")
    print()
    
    analyzer = RDDLDataAnalyzer()
    analysis = analyzer.run_comprehensive_analysis()
    
    if analysis:
        print(f"\n📊 Detailed analysis saved to: data/rddl_analysis/")
        print("\n🚀 This analysis will help identify valuable data for software improvement!")

if __name__ == "__main__":
    main()
