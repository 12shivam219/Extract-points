# 🚀 RESUME AUTOMATION WORKFLOW - COMPLETE GUIDE

## Overview

Automate your resume application process:
1. **Input:** Job description, Job title, Points per technology, Recruiter email
2. **System:** Auto-selects best resume, generates points, injects into resume
3. **Output:** Preview resume, send to recruiter with personalized message

---

## 🔧 QUICK START (5 minutes)

### Step 1: Prepare Your Resumes

Create a folder structure:
```
Extract-points/
├── resumes/
│   ├── Arjun_Python_Django_PostgreSQL.docx
│   ├── Arjun_React_Node_MongoDB.docx
│   └── Arjun_Java_Spring_AWS.docx
└── automation_workflow.py
```

**Filename Format:** `PersonName_Technology1_Technology2_Technology3.docx`

### Step 2: Setup Resume Catalog

```bash
python setup_resumes.py
```

This will:
- Scan `./resumes/` folder
- Extract technologies from filenames  
- Create `resume_catalog.json`
- Detect bookmarks in each resume

### Step 3: Run Automation

```bash
python automation_workflow.py
```

The script will guide you through:
1. Job Title
2. Job Description (paste text)
3. Points per Technology (1-10)
4. Recruiter Email
5. Personalized Message
6. Gmail setup (optional - for sending)
7. Resume Selection
8. Execute & Download

---

## 📋 DETAILED SETUP

### A. Resume Template Preparation

#### Create Bookmarks in Word

Each resume needs bookmarks for injection points:

1. Open resume in Microsoft Word
2. For each section where you want to inject points:
   - Select the text/area
   - Insert → Bookmark
   - Enter bookmark name (e.g., `TechExperience`, `KeyProjects`)
   - Click Add

**Recommended Bookmark Names:**
- `TechExperience` - Technical experience section
- `KeyProjects` - Project highlights
- `Skills` - Skills section
- `Experience` - Professional experience

3. Save the resume with these bookmarks

#### Example Folder Structure

```
resumes/
├── Arjun_Python_FastAPI_PostgreSQL.docx   ✅ Ready
├── Arjun_React_TypeScript_Node.docx       ✅ Ready
├── Arjun_Java_Spring_Kubernetes.docx      ✅ Ready
└── NoTechs.docx                            ❌ Won't work (needs format)
```

### B. Resume Catalog Management

#### Auto-Registration

Run setup to auto-register all resumes:

```bash
python setup_resumes.py
```

Output:
```
📋 RESUME CATALOG SETUP
🔍 Scanning ./resumes/ folder...
  ✅ Arjun_Python_FastAPI_PostgreSQL.docx
  ✅ Arjun_React_TypeScript_Node.docx
  ✅ Arjun_Java_Spring_Kubernetes.docx

📊 Catalog Summary:
  Total Resumes: 3
  Local: 3
  Google Drive: 0
  Technologies Found: Python, FastAPI, PostgreSQL, React, TypeScript, Node, Java, Spring, Kubernetes

✅ Setup complete!
```

#### Catalog File Structure

After registration, check `resume_catalog.json`:

```json
{
  "resumes": [
    {
      "name": "Arjun_Python_FastAPI_PostgreSQL.docx",
      "path": "./resumes/Arjun_Python_FastAPI_PostgreSQL.docx",
      "source": "local",
      "file_id": null,
      "person_name": "Arjun",
      "technologies": ["Python", "FastAPI", "PostgreSQL"],
      "job_roles": [],
      "bookmarks": ["TechExperience", "Experience"],
      "added_date": "C:\\Users\\12shi\\..."
    }
  ]
}
```

---

## 🔄 WORKFLOW EXECUTION

### Start Automation

```bash
python automation_workflow.py
```

### Interactive Steps

#### Step 1: Resume Catalog Display
```
📋 Step 1: Resume Catalog Setup
Local resumes folder: C:\...\Extract-points\resumes

📊 Catalog Summary:
  Total resumes: 3
  Local: 3, Google Drive: 0
  Technologies: Python, FastAPI, PostgreSQL, React, TypeScript, Node...
```

#### Step 2: Job Details Input
```
📝 Step 2: Job Details

Job Title: Senior Python Backend Developer

Job Description (paste below, then press Enter twice when done):
[Paste full job description]

Points per Technology (1-10): 3

Recruiter Email: recruiter@company.com

Personalized Email Message (for recruiter):
Hi [Recruiter],

I am interested in the Senior Python Backend Developer position...
```

#### Step 3: Email Configuration (Optional)
```
📧 Step 3: Email Configuration

Do you want to send resume via email? (y/n): y

Your Gmail address: your.email@gmail.com
Gmail App Password (16 chars): xxxx xxxx xxxx xxxx
```

**Note:** To get Gmail App Password:
1. Go to myaccount.google.com
2. Enable 2-Factor Authentication
3. Create App Password
4. Copy the 16-character password

#### Step 4: Resume Selection
```
🔍 Step 4: Resume Selection

✅ Best match found!
Resume: Arjun_Python_FastAPI_PostgreSQL.docx
Match Score: 92.5%
Person: Arjun
Matching Technologies: Python, FastAPI, PostgreSQL, Docker
Missing Technologies: Kubernetes, AWS

📌 Available alternatives:
  1. Arjun_Python_FastAPI_PostgreSQL.docx (92.5%)
  2. Arjun_Java_Spring_Kubernetes.docx (45.0%)
  3. Arjun_React_TypeScript_Node.docx (30.0%)

Use different resume? (number or press Enter for default): [Press Enter or type number]
```

#### Step 5: Automation Runs

```
🚀 Step 5: Running Automation...

[Input Validation] SUCCESS: All inputs validated
[Resume Matching] SUCCESS: Match score: 92.5%
[Points Generation] SUCCESS: Generated 2850 characters of content
[Resume Injection] SUCCESS: Points successfully injected into resume
[Resume Saving] SUCCESS: Saved to: ./automation_output/Senior_Python_Backend_Developer_Arjun_20240115_143022.docx
[Email Sending] SUCCESS: Email sent to recruiter@company.com
[Workflow] Complete
```

#### Step 6: Results

```
============================================================
📊 WORKFLOW RESULTS
============================================================

✅ SUCCESS!

Selected Resume: Arjun_Python_FastAPI_PostgreSQL.docx
Email Sent: ✅ Yes
Resume File: ./automation_output/Senior_Python_Backend_Developer_Arjun_20240115_143022.docx
Log File: ./automation_output/workflow_log_Senior_Python_Backend_Developer_20240115_143022.json

============================================================
```

---

## 📂 OUTPUT FILES

All output files are saved in `./automation_output/`:

```
automation_output/
├── Senior_Python_Backend_Developer_Arjun_20240115_143022.docx
├── workflow_log_Senior_Python_Backend_Developer_20240115_143022.json
└── [More files from previous runs...]
```

### Updated Resume
- **File:** `{JobTitle}_{PersonName}_{datetime}.docx`
- **Contains:** Injected resume points from job description
- **Ready to:** Download & review before sending

### Workflow Log
- **File:** `workflow_log_{JobTitle}_{datetime}.json`
- **Contains:** All step-by-step execution details
- **Use for:** Debugging & reference

---

## 🔍 RESUME MATCHING ALGORITHM

### How It Works

1. **Extract Technologies** from job description using Groq AI
2. **Score Each Resume** based on tech match:
   - Exact match: +100 points
   - Partial match (sub-string): +50 points
3. **Calculate Score:** (matched_points / total_points) × 100%
4. **Rank & Select:** Top resume with alternatives available

### Example

**Job Description Technologies:**
```
Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS
```

**Available Resumes:**
```
Resume A: [Python, FastAPI, PostgreSQL, Docker]        → 80% match ⭐ Best
Resume B: [Java, Spring, MongoDB]                      → 0% match
Resume C: [Python, Django, MySQL]                      → 50% match
```

### Override Resume Selection

You can manually select a different resume if you prefer:
```
📌 Available alternatives:
  1. Arjun_Python_FastAPI_PostgreSQL.docx (80.0%)
  2. Arjun_Python_Django_PostgreSQL.docx (50.0%)
  3. Arjun_Java_Spring_MongoDB.docx (0.0%)

Use different resume? (number or press Enter for default): 2
```

---

## 📧 EMAIL INTEGRATION

### Gmail Setup

#### Get Gmail App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Select "Security" in left menu
3. Enable 2-Step Verification (if not already enabled)
4. Click "App passwords" at bottom
5. Select "Mail" and "Windows Computer"
6. Copy the 16-character password

### Sending Resume

During workflow, the system will:
1. Ask for your Gmail address
2. Ask for Gmail App Password
3. Compose professional email with:
   - Subject: "Resume - {JobTitle} - {PersonName}"
   - Body: Your personalized message + job details
   - Attachment: Updated resume as DOCX
4. Send to recruiter email

### Email Content Example

```
Subject: Resume - Senior Python Backend Developer - Arjun

Body:
Hi [Recruiter],

I am interested in the Senior Python Backend Developer position...

Position: Senior Python Backend Developer
Resume: Arjun
Technologies: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS

Best regards
```

---

## 🐛 TROUBLESHOOTING

### Issue: "No resumes found in catalog"

**Cause:** Resumes not registered

**Solution:**
```bash
# 1. Ensure resumes are in ./resumes/ folder
# 2. Check filename format: PersonName_Tech1_Tech2.docx
# 3. Run setup to register
python setup_resumes.py
```

### Issue: "No technologies found in job description"

**Cause:** Job description too short or format unclear

**Solution:**
- Paste complete job description (min 50 characters)
- Include clear technology mentions (Python, React, etc.)
- Include frameworks and tools

### Issue: "Email send failed"

**Cause:** Invalid Gmail credentials or 2FA not enabled

**Solution:**
1. Verify Gmail address is correct
2. Enable 2-Factor Authentication on Gmail
3. Generate new App Password
4. Try again with new password

### Issue: "Resume file not found"

**Cause:** Local resume file was moved or deleted

**Solution:**
```bash
# Re-register resumes
python setup_resumes.py
```

### Issue: "Points not injected into resume"

**Cause:** Resume doesn't have bookmarks

**Solution:**
1. Open resume in Word
2. Add bookmarks to sections (Insert → Bookmark)
3. Save and re-register

---

## 📊 ADVANCED USAGE

### Batch Processing (Multiple Jobs)

Run automation multiple times:
```bash
# Job 1
python automation_workflow.py

# Job 2
python automation_workflow.py

# Job 3
python automation_workflow.py
```

All results saved with timestamps.

### Update Catalog Metadata

Edit `resume_catalog.json` to add job roles:
```json
{
  "name": "Arjun_Python_FastAPI_PostgreSQL.docx",
  "job_roles": ["Backend Developer", "Senior Backend Engineer", "Python Developer"]
}
```

### Google Drive Integration

To use resumes from Google Drive:
1. Set up Google Drive API credentials
2. During registration, select Google Drive folder
3. System will auto-register files with proper naming

---

## ✅ CHECKLIST

Before running automation:

- [ ] Resumes created with bookmarks
- [ ] Resumes in `./resumes/` folder
- [ ] Resumes named: `PersonName_Tech1_Tech2.docx`
- [ ] Catalog initialized: `python setup_resumes.py`
- [ ] Groq API key in `.env` file (already configured)
- [ ] Gmail setup (optional, for email sending)

---

## 💡 TIPS & BEST PRACTICES

1. **Keep Resumes Updated**
   - Maintain multiple tech-focused resumes
   - Update with latest projects and achievements

2. **Use Specific Technologies in Filenames**
   - Not just "Python" but "Python_FastAPI_PostgreSQL"
   - Helps accurate matching

3. **Add Job Roles to Metadata**
   - Edit `resume_catalog.json`
   - Improves future matching

4. **Review Before Sending**
   - Always review updated resume
   - Check injected points make sense
   - Verify email content

5. **Save Personalized Messages**
   - Create template messages
   - Customize per recruiter
   - Keep tone professional

6. **Monitor Workflow Logs**
   - Check logs for errors
   - Verify all steps completed
   - Use for debugging

---

## 📞 SUPPORT

If you encounter issues:

1. Check workflow logs in `./automation_output/`
2. Review .env file for API configuration
3. Ensure resume files have proper bookmarks
4. Verify email credentials (for sending)

---

## 📝 SUMMARY

**Complete End-to-End Automation:**
1. ✅ Auto-select best resume
2. ✅ Generate relevant resume points
3. ✅ Inject into resume template
4. ✅ Allow manual override
5. ✅ Show preview/download
6. ✅ Send via email
7. ✅ Log all activities

**Time Saved:** ~30 minutes per application → ~3 minutes per application! 🚀

---

## 🎯 NEXT STEPS

1. Create resume templates with bookmarks
2. Add resumes to `./resumes/` folder
3. Run `python setup_resumes.py`
4. Run `python automation_workflow.py`
5. Review and send updated resume!

Good luck with your applications! 🍀
