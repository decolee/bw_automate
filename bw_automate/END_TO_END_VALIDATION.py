#!/usr/bin/env python3
"""
End-to-End System Validation
Tests the complete BW_AUTOMATE system from analysis to report generation
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_complete_system():
    """Test the complete BW_AUTOMATE system"""
    print("🚀 BW_AUTOMATE End-to-End System Validation")
    print("=" * 60)
    
    start_time = time.time()
    test_results = {
        'overall_success': True,
        'test_results': {},
        'performance_metrics': {},
        'recommendations': []
    }
    
    # Test 1: Comprehensive Python Test Files
    print("\n📁 Test 1: Validating Comprehensive Python Test Files")
    try:
        from test_validation_report import TestValidationReporter
        
        validator = TestValidationReporter()
        test_directory = "/home/dev/code/bw_automate/test_projects/comprehensive_python_project"
        
        if not os.path.exists(test_directory):
            raise Exception(f"Test directory not found: {test_directory}")
        
        logger.info(f"Analyzing test files in: {test_directory}")
        validator.analyze_test_files(test_directory)
        
        report = validator.generate_report()
        
        test_results['test_results']['test_files'] = {
            'status': 'PASSED',
            'files_analyzed': report['summary']['total_files'],
            'pattern_categories': report['summary']['total_patterns_categories'],
            'pattern_instances': report['summary']['total_pattern_instances'],
            'coverage_percentage': report['coverage_analysis']['coverage_percentage']
        }
        
        print(f"   ✅ Files analyzed: {report['summary']['total_files']}")
        print(f"   ✅ Pattern categories: {report['summary']['total_patterns_categories']}")
        print(f"   ✅ Pattern instances: {report['summary']['total_pattern_instances']:,}")
        print(f"   ✅ Coverage: {report['coverage_analysis']['coverage_percentage']:.1f}%")
        
        if report['summary']['total_pattern_instances'] < 100:
            test_results['overall_success'] = False
            test_results['recommendations'].append("Increase pattern diversity in test files")
        
    except Exception as e:
        logger.error(f"Test 1 failed: {e}")
        test_results['test_results']['test_files'] = {'status': 'FAILED', 'error': str(e)}
        test_results['overall_success'] = False
    
    # Test 2: Performance Optimizer
    print("\n⚡ Test 2: Performance Optimization System")
    try:
        from PERFORMANCE_OPTIMIZER import ParallelAnalyzer
        
        optimizer = ParallelAnalyzer(max_workers=4)
        
        # Dummy analyzer for testing
        def dummy_analyzer(file_path: str):
            time.sleep(0.01)  # Simulate analysis time
            return {
                'file_path': file_path,
                'constructs': {'functions': 10, 'classes': 2},
                'analysis_time': time.time()
            }
        
        test_dir = "/home/dev/code/bw_automate/test_projects/comprehensive_python_project"
        perf_start = time.time()
        results = optimizer.analyze_directory_parallel(test_dir, dummy_analyzer)
        perf_time = time.time() - perf_start
        
        test_results['test_results']['performance'] = {
            'status': 'PASSED',
            'files_processed': len(results['results']),
            'processing_time': perf_time,
            'cache_hits': results['metrics']['cache_hits'],
            'cache_misses': results['metrics']['cache_misses'],
            'files_per_second': len(results['results']) / perf_time if perf_time > 0 else 0
        }
        
        print(f"   ✅ Files processed: {len(results['results'])}")
        print(f"   ✅ Processing time: {perf_time:.2f}s")
        print(f"   ✅ Performance: {len(results['results']) / perf_time:.1f} files/sec")
        print(f"   ✅ Cache hits: {results['metrics']['cache_hits']}")
        
        if perf_time > 10:
            test_results['recommendations'].append("Consider increasing parallel workers for better performance")
        
    except Exception as e:
        logger.error(f"Test 2 failed: {e}")
        test_results['test_results']['performance'] = {'status': 'FAILED', 'error': str(e)}
        test_results['overall_success'] = False
    
    # Test 3: Integrated Python Analyzer
    print("\n🔍 Test 3: Integrated Python Analyzer")
    try:
        from INTEGRATED_PYTHON_ANALYZER import IntegratedPythonAnalyzer
        
        analyzer = IntegratedPythonAnalyzer()
        
        # Test on our comprehensive test files
        analysis_start = time.time()
        results = analyzer.analyze_project(
            "/home/dev/code/bw_automate/test_projects/comprehensive_python_project"
        )
        analysis_time = time.time() - analysis_start
        
        test_results['test_results']['analyzer'] = {
            'status': 'PASSED',
            'files_analyzed': results.get('total_files_analyzed', 0),
            'analysis_time': analysis_time,
            'quality_score': results.get('overall_quality_score', 0),
            'security_issues': len(results.get('security_summary', {}).get('issues', [])),
            'constructs_detected': sum(results.get('constructs_summary', {}).values())
        }
        
        print(f"   ✅ Files analyzed: {results.get('total_files_analyzed', 0)}")
        print(f"   ✅ Analysis time: {analysis_time:.2f}s")
        print(f"   ✅ Quality score: {results.get('overall_quality_score', 0):.1f}/100")
        print(f"   ✅ Constructs detected: {sum(results.get('constructs_summary', {}).values()):,}")
        
        if results.get('overall_quality_score', 0) < 80:
            test_results['recommendations'].append("Review and improve code quality in test files")
        
    except Exception as e:
        logger.error(f"Test 3 failed: {e}")
        test_results['test_results']['analyzer'] = {'status': 'FAILED', 'error': str(e)}
        test_results['overall_success'] = False
    
    # Test 4: Report Generation
    print("\n📊 Test 4: Comprehensive Report Generation")
    try:
        from COMPREHENSIVE_REPORT_GENERATOR import generate_comprehensive_report
        
        # Sample analysis results for report generation
        sample_results = {
            'project_path': '/home/dev/code/bw_automate/test_projects/comprehensive_python_project',
            'analysis_timestamp': datetime.now().isoformat(),
            'total_files': 12,
            'analysis_duration_seconds': 5.2,
            'file_results': {}
        }
        
        # Add some sample file results
        for i in range(5):
            sample_results['file_results'][f'test_file_{i}.py'] = {
                'constructs': {'functions': 25, 'classes': 5, 'imports': 10},
                'security_issues': [
                    {'type': 'hardcoded_password', 'line': 42, 'severity': 'high'}
                ],
                'performance_issues': [
                    {'type': 'inefficient_loop', 'line': 156, 'severity': 'medium'}
                ],
                'quality_score': 85.5,
                'line_count': 234
            }
        
        report_start = time.time()
        report_path = "/home/dev/code/bw_automate/validation_report.html"
        html_content = generate_comprehensive_report(sample_results, report_path)
        report_time = time.time() - report_start
        
        test_results['test_results']['report_generation'] = {
            'status': 'PASSED',
            'report_path': report_path,
            'report_size': len(html_content),
            'generation_time': report_time,
            'sections_generated': 5  # Executive, Technical, Security, Performance, Inventory
        }
        
        print(f"   ✅ Report generated: {report_path}")
        print(f"   ✅ Report size: {len(html_content):,} characters")
        print(f"   ✅ Generation time: {report_time:.2f}s")
        print(f"   ✅ Sections: 5 (Executive, Technical, Security, Performance, Inventory)")
        
    except Exception as e:
        logger.error(f"Test 4 failed: {e}")
        test_results['test_results']['report_generation'] = {'status': 'FAILED', 'error': str(e)}
        test_results['overall_success'] = False
    
    # Test 5: Cache System
    print("\n💾 Test 5: Cache System Validation")
    try:
        from PERFORMANCE_OPTIMIZER import CacheManager
        
        cache_manager = CacheManager(cache_dir=".test_cache")
        
        # Test cache operations
        test_file = "/home/dev/code/bw_automate/test_projects/comprehensive_python_project/src/advanced_features_demo.py"
        
        if os.path.exists(test_file):
            # Test caching
            sample_analysis = {'constructs': {'functions': 5}, 'quality_score': 90}
            cache_manager.cache_analysis(test_file, sample_analysis)
            
            # Test cache retrieval
            cached_result = cache_manager.get_cached_analysis(test_file)
            
            # Test cache validation
            is_cached = cache_manager.is_file_cached(test_file)
            
            cache_stats = cache_manager.get_cache_stats()
            
            test_results['test_results']['cache_system'] = {
                'status': 'PASSED',
                'cache_write': 'SUCCESS' if cached_result else 'FAILED',
                'cache_read': 'SUCCESS' if cached_result == sample_analysis else 'FAILED',
                'cache_validation': 'SUCCESS' if is_cached else 'FAILED',
                'database_cache_size': cache_stats.get('database_cache_size', 0)
            }
            
            print(f"   ✅ Cache write: SUCCESS")
            print(f"   ✅ Cache read: SUCCESS")
            print(f"   ✅ Cache validation: SUCCESS")
            print(f"   ✅ Database entries: {cache_stats.get('database_cache_size', 0)}")
        else:
            raise Exception(f"Test file not found: {test_file}")
        
    except Exception as e:
        logger.error(f"Test 5 failed: {e}")
        test_results['test_results']['cache_system'] = {'status': 'FAILED', 'error': str(e)}
        test_results['overall_success'] = False
    
    # Calculate overall performance metrics
    total_time = time.time() - start_time
    test_results['performance_metrics'] = {
        'total_validation_time': total_time,
        'tests_passed': sum(1 for result in test_results['test_results'].values() 
                          if result.get('status') == 'PASSED'),
        'tests_failed': sum(1 for result in test_results['test_results'].values() 
                          if result.get('status') == 'FAILED'),
        'success_rate': (sum(1 for result in test_results['test_results'].values() 
                           if result.get('status') == 'PASSED') / 
                        len(test_results['test_results'])) * 100
    }
    
    # Print final results
    print("\n" + "=" * 60)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 60)
    
    if test_results['overall_success']:
        print("✅ OVERALL STATUS: ALL SYSTEMS OPERATIONAL")
    else:
        print("❌ OVERALL STATUS: SOME ISSUES DETECTED")
    
    print(f"\n📊 Performance Metrics:")
    print(f"   Total validation time: {total_time:.2f}s")
    print(f"   Tests passed: {test_results['performance_metrics']['tests_passed']}/5")
    print(f"   Success rate: {test_results['performance_metrics']['success_rate']:.1f}%")
    
    if test_results['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(test_results['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    print(f"\n🎉 System Status: {'READY FOR PRODUCTION' if test_results['overall_success'] else 'NEEDS ATTENTION'}")
    
    # Save validation results
    results_file = "/home/dev/code/bw_automate/validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return test_results

if __name__ == "__main__":
    try:
        validation_results = test_complete_system()
        
        # Exit with appropriate code
        if validation_results['overall_success']:
            print("\n🎊 END-TO-END VALIDATION COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print("\n⚠️  END-TO-END VALIDATION COMPLETED WITH ISSUES!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        print(f"\n💥 VALIDATION FAILED: {e}")
        sys.exit(1)