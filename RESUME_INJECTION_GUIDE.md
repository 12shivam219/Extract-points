# Resume Template Injection Feature - Setup Guide

## Overview
This feature allows you to inject extracted points from your structured text directly into your resume template while preserving all original formatting (fonts, colors, spacing, bullets).

## How It Works

1. **Resume Template with Bookmarks**: Your resume must have Word bookmarks that mark where points should be injected
2. **Extracted Points**: Processing your structured text extracts points organized by company/heading
3. **Smart Injection**: The system matches extracted sections to resume bookmarks and adds points while keeping existing content

## Setup Steps

### Step 1: Prepare Your Resume Template

Your resume needs **Word bookmarks** as injection points. These are hidden markers where new points will be added.

#### Option A: Use the Pre-Made Template
A template file has been created: `Lead Engineer_with_bookmarks.docx`
- Already has bookmarks for all companies
- Ready to use immediately
- Keep this as your template for future use

#### Option B: Add Bookmarks to Your Own Resume
Add bookmarks manually for each company section:

**Steps:**
1. Open your resume in Microsoft Word
2. For each company's "Responsibilities" section:
   - Click at the end of the last responsibility point
   - Go to **Insert → Bookmark**
   - Name it according to your company (examples below)
   - Click Add

**Bookmark Naming Conventions:**
- `KPMG_Responsibilities` - for KPMG section
- `CVS_Responsibilities` - for CVS section
- `Harland_Responsibilities` - for Harland section
- `FirstCitizensBank_Responsibilities` - for First Citizens Bank section

Or create your own names for other companies:
- `[CompanyName]_Responsibilities` format

**Example bookmark location:**
```
Client - KPMG – Aug 2023 – Present
Lead Software Engineer
Responsibilities:
• Existing Point 1
• Existing Point 2
[BOOKMARK GOES HERE] ← Click here before adding bookmark
```

### Step 2: Extract Points from Structured Text

Use the **"Single File Processing"** tab to process your structured text:

1. Enter or paste structured text:
   ```
   Heading 1
   • Point 1
   • Point 2
   
   Heading 2
   • Item A
   • Item B
   ```

2. Set number of points per cycle
3. Click "Process Text"
4. Copy the processed output

### Step 3: Use Resume Template Injection Tab

1. **Upload Resume Template** - Select your resume with bookmarks
2. **Provide Extracted Points** - Either paste the processed text or upload a file
3. **Inject Points** - Click "Inject Points into Resume"
4. **Download** - Get your updated resume with new points added

## Matching Headings to Bookmarks

The system uses intelligent matching:

**extracted Heading** → **Resume Bookmark**
- "KPMG" → `KPMG_Responsibilities`
- "CVS" → `CVS_Responsibilities`  
- "Harland" → `Harland_Responsibilities`
- "First Citizen" → `FirstCitizensBank_Responsibilities`

**Note:** Matching is case-insensitive and flexible. "KPMG", "kpmg", "Kpmg" all match.

## Formatting Preservation

✅ **What's Preserved:**
- Font names and sizes
- Font colors and styles (bold, italic)
- Bullet point styles
- Paragraph spacing
- Document layout

✅ **What's Added:**
- New bullet points with "•" symbol
- Points are inserted right after the bookmark

## Example Workflow

### Input:
```
KPMG
• Led modernization projects
• Built distributed applications
• Designed database schemas

CVS
• Managed enterprise portals  
• Enhanced performance
```

### Process:
1. Upload resume template (with bookmarks)
2. Paste the text above
3. Click "Inject Points"

### Output:
Your resume now has:
- All existing points unchanged
- New 3 points added under KPMG Responsibilities
- New 2 points added under CVS Responsibilities
- Same fonts and formatting as original

## Troubleshooting

### "No matching sections found"
- Check that heading names match your bookmark names
- Confirm bookmarks exist in the resume template
- Use tab 1 to process text first, then copy output

### "Invalid DOCX file"
- Ensure the resume is a valid Word document (.docx)
- Try saving it again in Word format
- Use the pre-made template if issues persist

### Formatting changed after injection
- This is rare; verify your original resume has proper formatting
- Try using the pre-made template
- Contact support if issues continue

## Tips & Best Practices

1. **Always keep a backup** of your original resume
2. **Test with 1-2 points first** before doing bulk additions
3. **Use consistent naming** for headings in your structured text
4. **Process through Tab 1 first** to ensure proper point formatting
5. **Use the template file** provided as reference for bookmark placement

## File Locations

- Template with bookmarks: `Lead Engineer_with_bookmarks.docx`
- Latest version of template: `Lead Engineer.docx` (original)

## Need Help?

- Check format guide in the application
- Ensure structured text follows the required format
- Verify bookmarks are properly named
- Try the sample template provided
