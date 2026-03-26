# Resume Template Injection - Quick Reference

## 🚀 Quick Start (5 Minutes)

### Step 1: Open Application
```bash
streamlit run main.py
```

### Step 2: Extract Points (Tab 1)
```
Input your text:
Heading 1
• Point 1
• Point 2

Click "Process Text"
Copy the output
```

### Step 3: Inject into Resume (Tab 3)
```
1. Upload: Lead Engineer_with_bookmarks.docx
2. Paste: Your processed text
3. Click: ✨ Inject Points
4. Download: Resume_Updated.docx
```

---

## 📝 Input/Output Example

### INPUT (Structured Text):
```
KPMG
• Led modernization projects migrating Monolithic applications to Microservices
• Built distributed enterprise applications using J2EE and Servlets

CVS
• Managed enterprise portals using enterprise web applications
• Enhanced performance using AJAX and jQuery
```

### AFTER PROCESSING (Tab 1):
```
Cycle 1:
KPMG
• Led modernization projects migrating Monolithic applications to Microservices
CVS
• Managed enterprise portals using enterprise web applications

Cycle 2:
KPMG
• Built distributed enterprise applications using J2EE and Servlets
CVS
• Enhanced performance using AJAX and jQuery
```

### AFTER INJECTION:
Your resume now has these new points added:
- KPMG Responsibilities: + 2 points
- CVS Responsibilities: + 2 points
- (All existing points still there!)

---

## 🎯 Key Points

| Feature | Details |
|---------|---------|
| **Add Mode** | Appends to existing, doesn't replace |
| **Format** | All styling preserved |
| **Companies Supported** | KPMG, CVS, Harland, First Citizens Bank |
| **Bookmarks** | Automatically detected |
| **Custom Companies** | Add your own bookmarks |

---

## 🔗 Workflow Diagram

```
┌─────────────────────────┐
│  Structured Text Input  │
│ (Headings + Points)     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Tab 1: Process Text    │
│  (Extract & Reorganize) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Processed Output       │
│  (Points by Cycle)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Tab 3: Resume Inject   │
│  (Upload resume + text) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  RESUME UPDATED ✅      │
│  (New points added)     │
└─────────────────────────┘
```

---

## 📋 Heading to Bookmark Mapping

```
Input Text         →    Resume Bookmark
─────────────────────────────────────────
KPMG              →    KPMG_Responsibilities
CVS               →    CVS_Responsibilities
Harland           →    Harland_Responsibilities
First Citizen     →    FirstCitizensBank_Responsibilities
```

**Case-insensitive matching** ✓
Works with: "KPMG", "kpmg", "Kpmg", "kpmg " (with spaces)

---

## ⚡ Common Actions

### Add Points Only to KPMG:
```
KPMG
• Point 1
• Point 2
```
✓ Only KPMG section updated
✓ Other sections untouched

### Add to Multiple Companies:
```
KPMG
• Point 1

CVS
• Point 2

Harland
• Point 3
```
✓ All three sections updated
✓ Each gets their points

### Process Before Injecting:
```
Text → Tab 1 (Process) → Copy Output → Tab 3 (Inject)
```
Recommended for best results

---

## ✅ Checklist Before Injecting

- [ ] Resume template uploaded (DOCX file)
- [ ] Template has bookmarks (or use provided one)
- [ ] Structured text with headings and points
- [ ] Heading names match bookmark names
- [ ] Points start with • or -
- [ ] Processed through Tab 1 (recommended)

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No matching sections" | Check heading names match bookmarks |
| "Invalid DOCX" | Use Lead Engineer_with_bookmarks.docx |
| Points not showing | Ensure points start with • or - |
| Wrong section updated | Verify heading spelling |
| Formatting changed | Try the provided template |

---

## 📞 Support Resources

1. **RESUME_INJECTION_GUIDE.md** - Detailed setup guide
2. **README.md** - Feature overview
3. **In-app help** - Available in Tab 3
4. **create_resume_bookmarks.py** - Create bookmarks for custom resume

---

## 💾 Files You Need

| File | Purpose |
|------|---------|
| `main.py` | Run the app |
| `Lead Engineer_with_bookmarks.docx` | Use as template |
| `RESUME_INJECTION_GUIDE.md` | Read setup guide |

---

## 🎓 Tips & Tricks

1. **Always backup** your original resume before injecting
2. **Test with 1-2 points** first before bulk additions
3. **Use Tab 1 first** to process and verify text
4. **Copy the whole output** from Tab 1 for best results
5. **Keep the template file** for future use

---

**Ready to use!** Start with Tab 1 → Copy output → Go to Tab 3 → Select template → Inject → Download! ✨
