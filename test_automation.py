"""
Test automation workflow with mock data
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path.cwd()))

from automation_workflow import AutomationWorkflow

def test_workflow():
    """Test the complete workflow with sample data."""
    
    print("\n" + "="*60)
    print("[TEST] TESTING AUTOMATION WORKFLOW")
    print("="*60)
    
    workflow = AutomationWorkflow()
    
    # Test 1: Input Validation
    print("\n[TEST 1] Input Validation")
    is_valid, msg = workflow.validate_inputs(
        job_description="Python FastAPI Backend Developer with 5+ years experience. Required: Python, FastAPI, PostgreSQL, Docker, AWS, CI/CD",
        job_title="Senior Backend Developer",
        points_per_tech=2,
        recruiter_email="test@company.com",
        personal_message="Hi, I'm very interested in this position."
    )
    print(f"   Result: {msg}")
    assert is_valid, "Validation failed!"
    
    # Test 2: Catalog & Resume Matching
    print("\n[TEST 2] Resume Catalog")
    summary = workflow.catalog.get_catalog_summary()
    print(f"   Total resumes: {summary['total_resumes']}")
    print(f"   Technologies: {summary['unique_technologies'][:5]}")
    
    if summary['total_resumes'] > 0:
        # Test 3: Resume Matching
        print("\n[TEST 3] Resume Matching")
        success, best_match, msg = workflow.matcher.find_best_resume(
            "Python FastAPI Backend Developer. Required: Python, FastAPI, PostgreSQL, Docker, AWS",
            "Senior Backend Developer"
        )
        print(f"   Result: {msg}")
        
        if success:
            print(f"   Match score: {best_match['score']:.1f}%")
            print(f"   Technologies: {best_match['resume']['technologies']}")
            
            # Test 4: Points Generation
            print("\n[TEST 4] Points Generation")
            try:
                points = workflow.points_generator.generate_points(
                    job_description="Python FastAPI Backend Developer. Required: Python, FastAPI, PostgreSQL, Docker, AWS, CI/CD pipelines",
                    job_title="Senior Backend Developer",
                    tech_stacks=["Python", "FastAPI", "PostgreSQL"],
                    num_points=2
                )
                print(f"   Generated {len(points)} characters of content")
                print(f"   First 100 chars: {points[:100]}...")
                
                # Test 5: Full Workflow
                print("\n[TEST 5] Full Workflow (without email)")
                success, result = workflow.run_workflow(
                    job_description="Python FastAPI Backend Developer. Required: Python, FastAPI, PostgreSQL, Docker, AWS, CI/CD pipelines",
                    job_title="Senior Backend Developer",
                    points_per_tech=2,
                    recruiter_email="test@company.com",
                    personal_message="Hi, I'm very interested in this senior backend developer position.",
                    override_resume=None  # Use best match
                )
                
                if success:
                    print(f"   *** Workflow SUCCESS!")
                    print(f"   Selected resume: {result['selected_resume']['name']}")
                    print(f"   Email sent: {result['email_sent']}")
                    print(f"   Resume file: {result.get('resume_file_path', 'N/A')}")
                    print(f"   Log file: {result.get('log_file', 'N/A')}")
                else:
                    print(f"   *** Workflow FAILED!")
                    for error in result['errors']:
                        print(f"      Error: {error}")
                    
            except Exception as e:
                print(f"   *** Error: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   *** No matching resume found. Adding sample resumes might help.")
    else:
        print("   *** No resumes in catalog. Please add resumes first.")
    
    print("\n" + "="*60)
    print("*** TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_workflow()
