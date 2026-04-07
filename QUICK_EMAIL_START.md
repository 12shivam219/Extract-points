# 🚀 Quick Start: Send Resumes Without Office Laptop Login

## Your Situation
- ✅ Resumes on your personal OneDrive/Google Drive/Dropbox
- ✅ Office laptop (no login to personal email)
- ✅ Need to send resumes to recruiters/companies

## Solution in 3 Steps

### Step 1️⃣: Prepare Your Resumes (Do This at Home)
1. Go to your cloud storage (OneDrive/Google Drive/Dropbox)
2. Create a folder called **"Resumes"**
3. Upload all your resume files there
4. Make sure files sync

### Step 2️⃣: Setup Email (Do This at Home - Once)
**Choose ONE of these:**

**🔵 GMAIL (Easiest):**
```
1. Go to myaccount.google.com → Security
2. Enable 2-Step Verification (if not done)
3. Go to myaccount.google.com/apppasswords
4. Select Mail + Windows
5. Copy the 16-char password
```

**📧 OUTLOOK:**
```
1. Go to account.microsoft.com → Security
2. Get App Password (if 2FA enabled)
3. Or just use your office password
```

**📤 SENDGRID:**
```
1. Create account at sendgrid.com
2. Create API Key
3. Copy the key
```

### Step 3️⃣: Use at Office
1. Start your Streamlit app: `streamlit run main.py`
2. Go to **Tab 6: "📧 Send Resumes via Email"**
3. Follow the 5 steps in the app
4. Done! 🎉

---

## What You Can Do Now

✅ Send resumes to unlimited people
✅ Track who you sent to (email history)
✅ No need to login to office email
✅ No login windows on office laptop
✅ Send multiple files in seconds
✅ Personalize each email message

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or individual install
pip install streamlit python-docx reportlab google-api-python-client dropbox sendgrid pandas
```

---

**Want detailed instructions?** → Read [EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md)

**Ready to send?** → Run the app and go to Tab 6! 🚀
