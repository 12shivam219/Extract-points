# Tab 7: Complete Resume Automation Workflow

Add this to `main.py` to create a new tab for end-to-end automation:

```python
# In main.py, modify the tabs line from 6 to 7:
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Single File Processing", 
    "Batch Processing", 
    "Resume Template Injection", 
    "Batch Resume Injection", 
    "Auto Points from Job Description", 
    "📧 Send Resumes via Email",
    "🚀 Complete Resume Automation"  # NEW TAB 7
])

# Then add this section at the end of main.py:

with tab7:
    st.markdown("## 🚀 Complete Resume Automation Workflow")
    st.markdown("""
    **One-click automation:**
    1. Upload job description
    2. System auto-selects best resume
    3. Generates job-specific points
    4. Injects into resume
    5. Downloads updated resume
    6. Optionally sends via email
    """)
    
    # Step 1: Initialize workflow
    from automation_workflow import AutomationWorkflow
    
    if 'automation_workflow' not in st.session_state:
        st.session_state.automation_workflow = AutomationWorkflow()
    
    workflow = st.session_state.automation_workflow
    
    # Show catalog
    st.markdown("### 📋 Step 1: Check Resume Catalog")
    summary = workflow.catalog.get_catalog_summary()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Resumes", summary['total_resumes'])
    with col2:
        st.metric("Local", summary['local_resumes'])
    with col3:
        st.metric("Technologies", len(summary['unique_technologies']))
    
    if summary['unique_technologies']:
        st.info(f"Available: {', '.join(summary['unique_technologies'][:10])}")
    
    # Job Details Input
    st.markdown("### 📝 Step 2: Job Details")
    
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job Title", placeholder="e.g., Senior Java Developer")
    
    with col2:
        points_per_tech = st.slider("Points per Technology", 1, 5, 3)
    
    job_description = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste job description here..."
    )
    
    recruiter_email = st.text_input("Recruiter Email", placeholder="recruiter@company.com")
    
    # Optional Message
    st.markdown("### 💬 Step 3: Personalized Message (Optional)")
    personal_message = st.text_area(
        "Leave blank to auto-generate",
        height=100,
        placeholder="Hi, I'm interested in this role because..."
    )
    
    # Email Configuration
    st.markdown("### 📧 Step 4: Email Configuration (Optional)")
    email_enabled = st.checkbox("Send resume via email?")
    
    gmail_address = None
    gmail_password = None
    
    if email_enabled:
        col1, col2 = st.columns(2)
        with col1:
            gmail_address = st.text_input("Gmail Address", type="password", placeholder="your-email@gmail.com")
        with col2:
            gmail_password = st.text_input("Gmail App Password", type="password", placeholder="16-char app password")
    
    # Run Automation
    if st.button("🚀 Run Full Automation", use_container_width=True, key="automation_run_button"):
        if not job_title:
            st.error("❌ Please enter job title")
        elif not job_description or len(job_description) < 50:
            st.error("❌ Job description too short (min 50 characters)")
        elif not recruiter_email or '@' not in recruiter_email:
            st.error("❌ Invalid email address")
        else:
            try:
                with st.spinner("🔄 Running automation..."):
                    # Initialize email if needed
                    if email_enabled and gmail_address and gmail_password:
                        success, msg = workflow.initialize_email(gmail_address, gmail_password)
                        if not success:
                            st.error(f"Email config failed: {msg}")
                    
                    # Run workflow
                    success, result = workflow.run_workflow(
                        job_description=job_description,
                        job_title=job_title,
                        points_per_tech=points_per_tech,
                        recruiter_email=recruiter_email,
                        personal_message=personal_message
                    )
                    
                    # Show results
                    if success:
                        st.success("✅ Automation completed!")
                        st.json({
                            "Selected Resume": result['selected_resume']['name'],
                            "Match Score": result['match_score'],
                            "Points Generated": result['generated_text'][:100] + "...",
                            "Email Sent": result['email_sent'],
                            "File": result.get('resume_file_path', 'N/A')
                        })
                        
                        # Download button
                        with open(result['resume_file_path'], 'rb') as f:
                            st.download_button(
                                label="📥 Download Resume",
                                data=f.read(),
                                file_name=Path(result['resume_file_path']).name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        
                        # Show log
                        with st.expander("📋 Execution Log"):
                            import json
                            if result.get('log_file'):
                                with open(result['log_file'], 'r') as f:
                                    log_data = json.load(f)
                                    st.json(log_data)
                    else:
                        st.error("❌ Automation failed")
                        for error in result['errors']:
                            st.error(f"  - {error}")
                        
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.code(str(e))

```

