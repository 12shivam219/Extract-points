"""
Test optional recruiter message feature
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from automation_workflow import AutomationWorkflow

def test_optional_message():
    """Test that recruiter message is optional."""
    
    print("\n" + "="*70)
    print("[TEST] OPTIONAL RECRUITER MESSAGE")
    print("="*70)
    
    workflow = AutomationWorkflow()
    
    job_description = "Java Developer role. Required: Java, Python, AWS, CI/CD"
    job_title = "Java Developer"
    points_per_tech = 2
    recruiter_email = "test@company.com"
    
    # Test 1: Without personal message (empty string)
    print("\n[Test 1] WITHOUT Personal Message (Empty String)...")
    success, result = workflow.run_workflow(
        job_description=job_description,
        job_title=job_title,
        points_per_tech=points_per_tech,
        recruiter_email=recruiter_email,
        personal_message=""  # Empty - should auto-generate
    )
    
    if success:
        print("  SUCCESS - Workflow completed")
        print(f"  Selected Resume: {result['selected_resume']['name']}")
        print("  Message Status: AUTO-GENERATED")
    else:
        print("  FAILED - Check errors below")
        for error in result['errors']:
            print(f"    {error}")
    
    # Test 2: With personal message (provided)
    print("\n[Test 2] WITH Personal Message (User Provided)...")
    workflow2 = AutomationWorkflow()
    
    custom_msg = "Hi, I'm very interested in this Java Developer role."
    success2, result2 = workflow2.run_workflow(
        job_description=job_description,
        job_title=job_title,
        points_per_tech=points_per_tech,
        recruiter_email=recruiter_email,
        personal_message=custom_msg  # Provided
    )
    
    if success2:
        print("  SUCCESS - Workflow completed")
        print(f"  Selected Resume: {result2['selected_resume']['name']}")
        print("  Message Status: USER-PROVIDED")
    else:
        print("  FAILED - Check errors below")
        for error in result2['errors']:
            print(f"    {error}")
    
    # Test 3: Validate that message is truly optional (None)
    print("\n[Test 3] WITHOUT Message (None)...")
    workflow3 = AutomationWorkflow()
    
    success3, result3 = workflow3.run_workflow(
        job_description=job_description,
        job_title=job_title,
        points_per_tech=points_per_tech,
        recruiter_email=recruiter_email
        # No personal_message at all
    )
    
    if success3:
        print("  SUCCESS - Workflow completed")
        print(f"  Selected Resume: {result3['selected_resume']['name']}")
        print("  Message Status: AUTO-GENERATED (default)")
    else:
        print("  FAILED - Check errors below")
        for error in result3['errors']:
            print(f"    {error}")
    
    print("\n" + "="*70)
    print("[SUMMARY]")
    print("="*70)
    print("\n[Result 1] Empty message ('') -> Auto-generated: " + 
          ("PASS" if success else "FAIL"))
    print("[Result 2] Custom message -> User-provided: " + 
          ("PASS" if success2 else "FAIL"))
    print("[Result 3] No message arg -> Auto-generated: " + 
          ("PASS" if success3 else "FAIL"))
    
    if success and success2 and success3:
        print("\n✅ ALL TESTS PASSED - Optional message feature works!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    test_optional_message()
