# Fix localhost:5000 Errors in AudiobookSmith

## 🎯 Problem

Your application is trying to connect to `http://localhost:5000` for various API calls, causing console errors:
- Demo samples
- File uploads  
- Authentication
- Database operations

## ✅ Solution

Replace the `database.js` file with an updated version that:
1. Uses the webhook server for book uploads
2. Gracefully handles missing backend for other features
3. Eliminates console errors

---

## 📋 Step-by-Step Fix

### Step 1: Update database.js

Replace the content of `src/lib/database.js` with the updated version (see `database_fixed.js` attachment).

**Key changes:**
- `baseURL` defaults to empty string (no backend required)
- `webhookURL` points to `https://audiobooksmith.app`
- `uploadFile()` method now uses webhook server
- Other methods return graceful errors instead of trying localhost:5000

### Step 2: Create .env file (Optional)

Create `.env.production` in your project root:

```bash
# Webhook Server URL
REACT_APP_WEBHOOK_URL=https://audiobooksmith.app

# API Backend URL (leave empty for now)
REACT_APP_API_URL=
```

### Step 3: Update TransformForm.jsx

Make sure your form passes all required parameters to `uploadFile()`:

```javascript
// In TransformForm.jsx handleSubmit function
const result = await database.uploadFile(
  file,           // the file object
  email,          // user email
  name,           // user name
  bookTitle,      // book title
  genre           // book genre (optional)
);

// Handle the result
if (result.success) {
  // Option 1: Redirect to webhook analysis page
  window.location.href = `https://audiobooksmith.app${result.folderUrl}`;
  
  // Option 2: Show your own success page
  // setShowSuccess(true);
}
```

### Step 4: Deploy

```bash
# Build your application
npm run build

# Deploy to your hosting (Netlify, Vercel, etc.)
# The build will use the production environment variables
```

---

## 🧪 Testing

### Test 1: Check Console Errors

1. Open https://audiobooksmith.com
2. Open DevTools (F12) → Console tab
3. Reload the page
4. **Expected:** No more localhost:5000 errors
5. **You might see:** Warnings about "backend not configured" - this is normal

### Test 2: Submit Form

1. Fill out the book upload form
2. Upload a PDF/EPUB/DOCX file
3. Submit
4. **Expected:** File uploads successfully to webhook
5. **Result:** Either redirects to analysis page OR shows success message

### Test 3: Verify Upload

On your server, check the logs:

```bash
tail -50 /root/audiobook_webhook/logs/webhook_server.log
```

You should see your book being processed.

---

## 📊 What Each Method Does Now

| Method | Old Behavior | New Behavior |
|--------|-------------|--------------|
| `uploadFile()` | ❌ Tries localhost:5000 | ✅ Uses webhook server |
| `getDemoSample()` | ❌ Tries localhost:5000 | ⚠️ Returns graceful error |
| `uploadDemo()` | ❌ Tries localhost:5000 | ⚠️ Returns graceful error |
| `signUp()` | ❌ Tries localhost:5000 | ⚠️ Returns graceful error |
| `signIn()` | ❌ Tries localhost:5000 | ⚠️ Returns graceful error |
| `upsert()` | ❌ Tries localhost:5000 | ⚠️ Returns graceful error |

---

## 🚀 Future: Adding Backend Features

When you're ready to implement the other features (auth, demos, etc.), you have two options:

### Option A: Build Your Own Backend

1. Create a Node.js/Express backend
2. Deploy it (e.g., on your server or Heroku)
3. Set `REACT_APP_API_URL` to your backend URL
4. Implement the API endpoints in `database.js`

### Option B: Use Existing Services

1. **Authentication:** Use Supabase, Firebase Auth, or Auth0
2. **File Storage:** Use Supabase Storage, AWS S3, or Cloudflare R2
3. **Database:** Use Supabase, Firebase, or direct PostgreSQL
4. **Voice Demos:** Integrate with ElevenLabs or similar API

---

## 🐛 Troubleshooting

### Still seeing localhost:5000 errors?

1. **Clear browser cache** and hard reload (Ctrl+Shift+R)
2. **Rebuild your app:** `npm run build`
3. **Check environment variables:** Make sure `.env.production` is loaded
4. **Verify deployment:** Ensure the new code is deployed

### Form submission not working?

1. **Check console** for detailed error messages
2. **Verify webhook server** is running:
   ```bash
   curl https://audiobooksmith.app/webhook/health
   ```
3. **Check CORS** is enabled on webhook server
4. **Verify form data** is being sent correctly

### Want to see what's happening?

Add this to your TransformForm.jsx:

```javascript
// Before uploadFile call
console.log('Uploading with data:', { email, name, bookTitle, genre });

// After uploadFile call
console.log('Upload result:', result);
```

---

## ✅ Summary

**What's Fixed:**
- ✅ No more localhost:5000 console errors
- ✅ Book upload works via webhook
- ✅ Graceful handling of unavailable features
- ✅ Clean console output

**What's Not Implemented (Yet):**
- ⚠️ User authentication
- ⚠️ Voice demos
- ⚠️ Database operations

**Next Steps:**
1. Update `database.js` with the fixed version
2. Test form submission
3. Verify no console errors
4. (Optional) Implement backend for other features

---

## 📞 Need Help?

If you encounter issues:
1. Check the console for error messages
2. Verify webhook server is running
3. Test with the debugging version of handleSubmit
4. Check server logs for processing errors

The book upload functionality is working - we're just cleaning up the console errors from unimplemented features!
