# ⚡ AUTOMATION QUICK START (3 minutes)

## What It Does

1. **You input:** Job description + Job title + Points per tech + Recruiter email
2. **System auto-selects** best resume from your collection
3. **Generates** resume points matching the job
4. **Injects** points into your resume template
5. **Shows preview** and sends to recruiter

---

## 🚀 START NOW

### 1. Prepare Resumes (2 minutes)

Create a folder: `Extract-points/resumes/`

Add resume files with this naming:
```
PersonName_Technology1_Technology2.docx
```

**Examples:**
- `Arjun_Python_FastAPI_PostgreSQL.docx`
- `Arjun_React_Node_MongoDB.docx`

**Important:** Each resume must have **Word bookmarks** in sections (Insert → Bookmark)

### 2. Register Resumes (1 minute)

```bash
python setup_resumes.py
```

This scans your folder and creates `resume_catalog.json`

### 3. Run Automation (1 minute)

```bash
python automation_workflow.py
```

Answer the prompts:
- Job Title: ___
- Job Description: [paste]
- Points per Technology: 3
- Recruiter Email: recruiter@company.com
- Your Message: Hi, I'm interested in...
- Gmail setup: Yes/No (for sending)

**That's it!** ✅

---

## 📂 Folder Structure

```
Extract-points/
├── resumes/                          ← Add your resumes here
│   ├── Arjun_Python_FastAPI_PG.docx
│   ├── Arjun_React_Node_MongoDB.docx
│   └── README.md
├── utils/
│   ├── resume_catalog.py             ← Manages resumes
│   ├── resume_matcher.py              ← Finds best resume
│   └── [other files]
├── automation_workflow.py            ← Main script
├── setup_resumes.py                  ← Initialize
├── resume_catalog.json               ← Generated
└── automation_output/                ← Results saved here
    ├── Updated_Resume.docx
    └── workflow_log.json
```

---

## 🎯 How Matching Works

**Job says:** Python, FastAPI, PostgreSQL, Kubernetes

**Your Resumes:**
- Resume A: Python, FastAPI, PostgreSQL, Docker → **92% match** ⭐
- Resume B: React, Node, MongoDB → 0% match
- Resume C: Python, Django, MySQL → 50% match

**System picks:** Resume A (highest match)

**You can override:** Select different resume if preferred

---

## 📧 Email Sending (Optional)

To auto-send resumes to recruiter:

1. Enable 2-Factor Auth on Gmail
2. Create App Password (myaccount.google.com → App passwords)
3. Select "Yes" when script asks
4. Enter your Gmail + 16-char App Password

Resume will be sent automatically!

---

## 💡 Key Points

✅ **Auto-matches** resume based on job requirements
✅ **Generates** custom resume points
✅ **Injects** into your template (preserves formatting)
✅ **Preview & Download** before sending
✅ **Optional email** sending to recruiter
✅ **Logs everything** for reference

---

## ⚠️ Requirements

- Resumes with Word bookmarks
- Job description (text)
- Groq API key in `.env` (already set up)
- Gmail account (optional, for sending)

---

## 📌 File Naming Guide

```
Good ✅:
- Arjun_Python_FastAPI_PostgreSQL.docx
- Priya_React_TypeScript_Node.docx
- Rahul_Java_Spring_Kubernetes.docx

Bad ❌:
- Resume.docx
- Arjun_Resume_Updated.docx
- Backend_Engineer.docx
```

**Format:** `FirstName_Tech1_Tech2_Tech3.docx` (no spaces)

---

## 🔗 Full Documentation

See `AUTOMATION_GUIDE.md` for:
- Detailed setup
- Troubleshooting
- Advanced features
- Best practices

---

## ❓ Common Questions

**Q: What if best resume doesn't match?**
A: Script shows alternatives - you can pick different one

**Q: Can I customize the email?**
A: Yes, you type personalized message during setup

**Q: Where are results saved?**
A: `./automation_output/` with timestamps

**Q: Do I need to create bookmarks?**
A: Yes, each resume needs Word bookmarks for injection

**Q: How long does it take?**
A: ~3-5 minutes per job application

---

## ✅ Ready?

1. `python setup_resumes.py`
2. `python automation_workflow.py`
3. Follow the interactive prompts!

That's all! Good luck applying 🚀
