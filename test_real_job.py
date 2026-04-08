"""
Test automation workflow with real job data provided by user
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from automation_workflow import AutomationWorkflow

def test_with_real_job_data():
    """Test automation with real job data."""
    
    print("\n" + "="*70)
    print("[REAL WORLD TEST] AUTOMATION WORKFLOW WITH USER DATA")
    print("="*70)
    
    # Job data provided by user
    job_title = "Java Developer"
    
    job_description = """
Software Dev Engineer II: 26-00819

Job Description:
Primary Skills: Java(Proficient), Data Structure & Algorithms (Expert), AWS (Proficient), System Design (Proficient), CI/CD pipeline (Proficient)

Job Summary:
We are seeking a Software Development Engineer II to join the team. The ideal candidate will have strong programming expertise in Python and Java, along with experience in designing scalable systems and automation solutions. This role focuses on improving system reliability, enhancing test processes, and supporting high-impact manufacturing operations through innovative engineering solutions.

Key Responsibilities:
- Design and implement automation solutions to improve operational efficiency
- Develop monitoring and diagnostic tools for reliability and early fault detection
- Troubleshoot and resolve complex technical issues
- Collaborate with cross-functional teams to align automation with operational goals
- Lead design and architecture efforts for new and existing systems
- Ensure code quality and follow best practices in software development
- Mentor junior engineers and contribute to team growth

Must-Have Skills:
- 5+ years of professional software development experience (non-internship)
- Strong programming skills in Python.
- Experience in system design, architecture, and scalability

Industry Experience:
Background in high-performance, production-level environments
"""
    
    recruiter_email = "kapil.moorjani@akraya.com"
    
    personalized_message = """Hi Kapil,

Thank you for reaching out about the Software Dev Engineer II position at your client in Redmond, WA.

I have strong experience with Java, system design, and cloud technologies. I would be very interested in discussing how my background aligns with this opportunity.

I'm attaching my resume for your review and would welcome the chance to speak with you further.

Best regards,
Erick
"""
    
    points_per_tech = 2
    
    # Initialize workflow
    workflow = AutomationWorkflow()
    
    # Validate inputs
    print("\n[Step 1] Validating Inputs...")
    is_valid, msg = workflow.validate_inputs(
        job_description, job_title, points_per_tech, recruiter_email, personalized_message
    )
    print(f"  {msg}")
    
    if not is_valid:
        print("[ERROR] Validation failed!")
        return
    
    # Show catalog
    print("\n[Step 2] Resume Catalog Status...")
    summary = workflow.catalog.get_catalog_summary()
    print(f"  Total resumes: {summary['total_resumes']}")
    print(f"  Technologies available: {', '.join(summary['unique_technologies'][:5])}")
    
    if summary['total_resumes'] == 0:
        print("[ERROR] No resumes in catalog!")
        return
    
    # Find best resume
    print("\n[Step 3] Analyzing Job Description...")
    success, best_match, msg = workflow.matcher.find_best_resume(job_description, job_title)
    print(f"  {msg}")
    
    if not success:
        print("[ERROR] Could not find matching resume")
        return
    
    # Show alternatives
    print("\n[Step 4] Checking Alternative Resumes...")
    success, alternatives, alt_msg = workflow.matcher.get_alternative_resumes(job_description, top_n=5)
    
    if alternatives:
        print(f"  Found {len(alternatives)} alternatives:")
        for i, alt in enumerate(alternatives[:3], 1):
            print(f"    {i}. {alt['resume']['name']} ({alt['score']:.1f}%)")
    
    # Run full workflow
    print("\n[Step 5] Running Complete Workflow...")
    print("  Processing: Job analysis -> Points generation -> Resume injection -> Saving")
    
    success, result = workflow.run_workflow(
        job_description=job_description,
        job_title=job_title,
        points_per_tech=points_per_tech,
        recruiter_email=recruiter_email,
        personal_message=personalized_message,
        override_resume=None
    )
    
    # Show results
    print("\n" + "="*70)
    print("[RESULTS] WORKFLOW EXECUTION")
    print("="*70)
    
    if success:
        print("\n[SUCCESS] Workflow completed successfully!\n")
        print(f"  Selected Resume: {result['selected_resume']['name']}")
        print(f"  Person Name: {result['selected_resume']['person_name']}")
        print(f"  Resume Technologies: {', '.join(result['selected_resume']['technologies'])}")
        print(f"\n  Generated Content: {len(result.get('extracted_points', ''))} characters")
        print(f"  Email Sent: {'Yes' if result['email_sent'] else 'No (not configured)'}")
        
        if result.get('resume_file_path'):
            print(f"\n  Updated Resume: {result['resume_file_path']}")
            # Check if file exists and get size
            from pathlib import Path
            resume_path = Path(result['resume_file_path'])
            if resume_path.exists():
                size = resume_path.stat().st_size / 1024  # KB
                print(f"  File Size: {size:.1f} KB")
        
        if result.get('log_file'):
            print(f"  Workflow Log: {result['log_file']}")
        
        # Show first few lines of generated points
        if result.get('extracted_points'):
            points_preview = result['extracted_points'][:300]
            print(f"\n  Sample Generated Content:\n")
            print(f"  {points_preview}...")
    else:
        print("\n[FAILED] Workflow encountered errors!\n")
        for error in result['errors']:
            print(f"  [ERROR] {error}")
    
    print("\n" + "="*70)
    print("[COMPLETE] Real-world test finished")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_with_real_job_data()
