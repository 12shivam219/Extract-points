# 📧 Email Setup Guide - Send Resumes Without Office Laptop Login

Your application is now ready to send resumes via email without needing to login to your office email on the office laptop!

## Quick Setup (5 minutes)

### Option 1: Gmail (Recommended - Easiest)

**Why Gmail?**
- ✅ Works from office laptop without login
- ✅ Free and doesn't require additional account
- ✅ Can use your personal Gmail if you prefer
- ✅ No login window appears on office laptop

**Step-by-Step:**

1. **Open Gmail Account (on your personal computer):**
   - Go to [myaccount.google.com](https://myaccount.google.com)
   - Sign in with your Gmail account

2. **Enable 2-Factor Authentication:**
   - Click **Security** in the left sidebar
   - Find **2-Step Verification**
   - Follow the prompts (you'll need your phone)
   - Confirm it's enabled

3. **Create App Password:**
   - Go back to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Select **Mail** 
   - Select **Windows Computer** (or your OS)
   - Google shows a **16-character password**
   - **Copy this password** (e.g., `abcd efgh ijkl mnop`)

4. **In the Streamlit App:**
   - Go to Tab 6: "📧 Send Resumes via Email"
   - Step 2: Select **"🔵 Gmail (App Password)"**
   - Paste your Gmail address in **Gmail Address**
   - Paste the 16-character password in **Gmail App Password**
   - Click **Send Emails**

✅ **Done!** No login window, no office email required!

---

### Option 2: Outlook/Office 365

**When to use:**
- You have Office 365 at work
- You prefer official channels

**Setup:**

1. Get your password:
   - If 2FA is enabled: Get App Password from [account.microsoft.com/apppasswords](https://account.microsoft.com/apppasswords)
   - Otherwise: Use your regular Office 365 password

2. In the Streamlit App:
   - Go to Tab 6: "📧 Send Resumes via Email"
   - Step 2: Select **"📧 Outlook/Office 365"**
   - Enter your office email address
   - Enter your password or App Password
   - Click **Send Emails**

---

### Option 3: SendGrid (Professional + Tracking)

**When to use:**
- You want professional email tracking
- You need advanced features

**Setup:**

1. Create free SendGrid account:
   - Go to [sendgrid.com](https://sendgrid.com)
   - Sign up (free tier available)

2. Create API Key:
   - Log in to SendGrid dashboard
   - Go to **Settings → API Keys**
   - Click **Create API Key**
   - Copy the key (looks like `SG.xxxxxxxxxxx...`)

3. In the Streamlit App:
   - Go to Tab 6: "📧 Send Resumes via Email"
   - Step 2: Select **"📧 SendGrid API"**
   - Paste your API key
   - Click **Send Emails**

---

## Cloud Storage Setup

### OneDrive (Windows Computer)

**Already Synced?**
- If your OneDrive is already syncing on your office laptop, the app automatically finds it!
- Just create a **"Resumes"** folder in OneDrive
- Move your resumes there
- Click **"Load Resumes from Cloud"** in the app

**Manual Setup:**
1. Go to [onedrive.live.com](https://onedrive.live.com)
2. Create folder called **"Resumes"**
3. Upload your resume files there
4. Keep OneDrive syncing on your office laptop while using the app

---

### Google Drive

**Setup:**

1. Go to [drive.google.com](https://drive.google.com)
2. Create a folder called **"Resumes"**
3. Upload your resume files
4. On your office laptop:
   - Install [Google Drive for Desktop](https://support.google.com/drive/answer/7329379)
   - Let it sync
   - Or: Use the app directly (it will ask for permission once)

---

### Dropbox

**Setup:**

1. Go to [dropbox.com](https://dropbox.com)
2. Create a folder called **"Resumes"**
3. Upload your resume files
4. On your office laptop:
   - Install [Dropbox app](https://www.dropbox.com/install)
   - Let it sync
   - Or: Set `DROPBOX_ACCESS_TOKEN` environment variable

---

## Step-by-Step Example: Send Resume to 3 People

1. **Tab 6 → Step 1: Load Resumes**
   - Select "☁️ OneDrive"
   - Click "🔄 Load Resumes from Cloud"
   - ✅ See your resumes listed

2. **Tab 6 → Step 2: Email Provider**
   - Select "🔵 Gmail (App Password)"
   - Enter Gmail address and 16-char password

3. **Tab 6 → Step 3: Add Recipients**
   ```
   john.doe@company.com
   jane.smith@company.com
   hiring@company.com
   ```

4. **Tab 6 → Step 4: Email Content**
   - Subject: "Application for Senior Developer Role"
   - Resume: "MyResume_2024.docx"
   - Message: Your cover letter text

5. **Tab 6 → Step 5: Send**
   - Click "🚀 Send Emails"
   - Watch the progress bar
   - ✅ See success message
   - 📧 Check your email history

---

## Troubleshooting

### "Failed to connect to Gmail"
- ❌ Wrong App Password? Copy again from [apppasswords](https://myaccount.google.com/apppasswords)
- ❌ 2FA not enabled? Enable it first
- ❌ Capitalization matters? Try without spaces

### "OneDrive not found"
- ✅ Make sure OneDrive is syncing on your laptop
- ✅ Create a **"Resumes"** folder (exact name)
- ✅ Put resume files in it
- ✅ Wait for sync to complete before sending

### "Gmail says 2FA not enabled"
- Go to [Security](https://myaccount.google.com/security)
- Look for **"2-Step Verification"**
- Click **Enable** if you see the button
- Follow the steps (need your phone)
- Then try App Passwords again

### "Office email says incorrect password"
- Get a new **App Password** from [account.microsoft.com/apppasswords](https://account.microsoft.com/apppasswords)
- Don't use your regular password
- If you don't see "App passwords", enable 2FA first

---

## Environment Variables (Optional)

Instead of entering credentials in the app each time, you can set them once:

**Windows (Command Prompt as Admin):**
```cmd
setx GMAIL_EMAIL "your.email@gmail.com"
setx GMAIL_PASSWORD "16-character-app-password"
setx OUTLOOK_EMAIL "your.email@company.com"
setx OUTLOOK_PASSWORD "your-password"
setx SENDGRID_API_KEY "SG.xxxxxxxxxxxx"
```

**Then restart the app** - credentials will auto-load!

---

## Security Notes

✅ **Safe Because:**
- Credentials only stored in your local computer memory
- Nothing saved to internet
- Gmail App Password can be deleted anytime
- Outlook App Password can be deleted anytime
- SendGrid API Key can be revoked anytime

❌ **Never:**
- Share your passwords with anyone
- Commit credentials to git
- Store passwords in plain text files

---

## Common Questions

**Q: Do I need multiple email accounts?**
- A: No, use one account and send to many recipients

**Q: Can I send to 1000 people?**
- A: Gmail: Yes (free account limit is 500/day)
- A: Outlook: Yes (depends on company policy)
- A: SendGrid: Yes (generous free tier)

**Q: What resume formats work?**
- A: .docx (Word), .pdf, .doc (legacy Word)

**Q: Can I schedule emails for later?**
- A: Not in current version, but you can use the app anytime

**Q: Is my resume safe?**
- A: Yes, it's never stored on internet, only sent directly

---

## Next Steps

1. ✅ Complete setup for your email provider
2. ✅ Upload resumes to cloud storage
3. ✅ Restart the Streamlit app
4. ✅ Go to Tab 6 and try sending one test email
5. ✅ Check that the email was received
6. ✅ Start sending to real recipients!

---

## Support

If something doesn't work:
1. Check the **Setup Instructions** in Tab 6
2. Read the **Troubleshooting** section above
3. Check your internet connection
4. Restart the Streamlit app
5. Check email in spam/junk folder

**Happy Sending! 📧**
