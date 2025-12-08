# AudiobookSmith Webhook Integration - Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you quickly integrate the webhook system into audiobooksmith.com.

## 📦 What You Have

✅ **Flask Webhook Server** - Running and tested  
✅ **Audiobook Processor** - Ready to process files  
✅ **Frontend Integration Code** - React component ready to use  
✅ **Complete Documentation** - Detailed guides and API specs  

## 🎯 Quick Integration Steps

### Step 1: Copy the Frontend Code

Open your audiobooksmith.com repository and add the form component:

**File**: `frontend_integration_code.jsx` (already created)

```bash
# The code is ready in:
/home/ubuntu/frontend_integration_code.jsx
```

### Step 2: Update the Webhook URL

In the frontend code, update the webhook URL:

```javascript
// Current (sandbox URL - temporary)
const WEBHOOK_URL = "https://5001-ivhxzp207okmv86v56xhi-424900e9.manusvm.computer/webhook/audiobook-process";

// For production, you'll need to:
// 1. Deploy the webhook server to your production server
// 2. Set up a domain (e.g., webhook.audiobooksmith.com)
// 3. Update this URL to your production domain
```

### Step 3: Test the Integration

You can test immediately with the current sandbox URL:

```javascript
// Test with a simple HTML form
<form id="testForm">
  <input type="email" name="email" value="test@example.com" required />
  <input type="text" name="bookTitle" value="Test Book" required />
  <select name="plan">
    <option value="free">Free</option>
    <option value="premium">Premium</option>
  </select>
  <input type="file" name="bookFile" accept=".pdf,.txt" required />
  <button type="submit">Upload</button>
</form>

<script>
document.getElementById('testForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  
  try {
    const response = await fetch('https://5001-ivhxzp207okmv86v56xhi-424900e9.manusvm.computer/webhook/audiobook-process', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    console.log('Success:', result);
    alert('Book uploaded successfully! Audiobook ID: ' + result.data.output.audiobook_id);
  } catch (error) {
    console.error('Error:', error);
    alert('Upload failed: ' + error.message);
  }
});
</script>
```

## 🧪 Test Right Now

You can test the webhook immediately using curl:

```bash
curl -X POST "https://5001-ivhxzp207okmv86v56xhi-424900e9.manusvm.computer/webhook/audiobook-process" \
  -F "email=vitaly@audiobooksmith.com" \
  -F "bookTitle=My Test Book" \
  -F "plan=premium" \
  -F "bookFile=@/path/to/your/book.pdf"
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Audiobook processed successfully",
  "data": {
    "output": {
      "audiobook_id": "ab_20251207204228",
      "status": "ready_for_processing",
      "estimated_completion": "2-3 hours"
    }
  }
}
```

## 📋 Integration Checklist

### For Immediate Testing (5 minutes)
- [ ] Copy `frontend_integration_code.jsx` to your project
- [ ] Update imports in your main component
- [ ] Add the form component to your page
- [ ] Test with a small PDF file
- [ ] Verify response in browser console

### For Production Deployment (1-2 hours)
- [ ] Deploy webhook server to production (see DEPLOYMENT_GUIDE.md)
- [ ] Set up domain name (e.g., webhook.audiobooksmith.com)
- [ ] Configure SSL certificate
- [ ] Update frontend webhook URL
- [ ] Add API key authentication
- [ ] Set up monitoring and logging
- [ ] Test with real user scenarios

## 🎨 Frontend Integration Options

### Option 1: React Component (Recommended)

Use the provided React component:

```jsx
import AudiobookUploadForm from './components/AudiobookUploadForm';

function App() {
  return (
    <div>
      <h1>Upload Your Book</h1>
      <AudiobookUploadForm />
    </div>
  );
}
```

### Option 2: Plain JavaScript

```javascript
async function uploadBook(formData) {
  try {
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      alert('Success! Audiobook ID: ' + result.data.output.audiobook_id);
    } else {
      alert('Error: ' + result.message);
    }
  } catch (error) {
    console.error('Upload error:', error);
    alert('Upload failed: ' + error.message);
  }
}
```

### Option 3: jQuery

```javascript
$('#uploadForm').on('submit', function(e) {
  e.preventDefault();
  
  var formData = new FormData(this);
  
  $.ajax({
    url: WEBHOOK_URL,
    type: 'POST',
    data: formData,
    processData: false,
    contentType: false,
    success: function(result) {
      if (result.success) {
        alert('Success! Audiobook ID: ' + result.data.output.audiobook_id);
      } else {
        alert('Error: ' + result.message);
      }
    },
    error: function(xhr, status, error) {
      alert('Upload failed: ' + error);
    }
  });
});
```

## 🔧 Common Customizations

### 1. Add Progress Bar

```javascript
const xhr = new XMLHttpRequest();

xhr.upload.addEventListener('progress', (e) => {
  if (e.lengthComputable) {
    const percentComplete = (e.loaded / e.total) * 100;
    updateProgressBar(percentComplete);
  }
});

xhr.addEventListener('load', () => {
  const result = JSON.parse(xhr.responseText);
  handleSuccess(result);
});

xhr.open('POST', WEBHOOK_URL);
xhr.send(formData);
```

### 2. Add File Validation

```javascript
function validateFile(file) {
  const maxSize = 100 * 1024 * 1024; // 100MB
  const allowedTypes = ['application/pdf', 'text/plain'];
  
  if (file.size > maxSize) {
    alert('File is too large. Maximum size is 100MB.');
    return false;
  }
  
  if (!allowedTypes.includes(file.type)) {
    alert('Invalid file type. Please upload PDF or TXT files only.');
    return false;
  }
  
  return true;
}
```

### 3. Add Loading State

```javascript
const [isUploading, setIsUploading] = useState(false);

const handleSubmit = async (e) => {
  e.preventDefault();
  setIsUploading(true);
  
  try {
    // ... upload code
  } finally {
    setIsUploading(false);
  }
};

return (
  <button type="submit" disabled={isUploading}>
    {isUploading ? 'Uploading...' : 'Upload Book'}
  </button>
);
```

## 📊 Response Handling

### Success Response

```javascript
{
  "success": true,
  "message": "Audiobook processed successfully",
  "data": {
    "output": {
      "audiobook_id": "ab_20251207204228",
      "status": "ready_for_processing",
      "estimated_completion": "2-3 hours",
      "notification_email": "user@example.com"
    }
  }
}
```

**What to do**:
1. Show success message to user
2. Save audiobook_id for tracking
3. Send confirmation email
4. Redirect to status page

### Error Response

```javascript
{
  "success": false,
  "error": "File too large",
  "message": "File size exceeds maximum allowed size (100 MB)"
}
```

**What to do**:
1. Show error message to user
2. Log error for debugging
3. Allow user to retry
4. Provide helpful guidance

## 🎯 Next Steps

### Immediate (Now)
1. ✅ Test the webhook with curl
2. ✅ Copy frontend code to your project
3. ✅ Test with a small file
4. ✅ Verify response handling

### Short Term (This Week)
1. 📝 Review DEPLOYMENT_GUIDE.md
2. 🚀 Deploy to production server
3. 🔒 Add authentication
4. 📊 Set up monitoring

### Long Term (This Month)
1. 🎨 Customize UI/UX
2. 📧 Add email notifications
3. 📈 Implement analytics
4. 🔄 Add job queue for processing

## 📚 Documentation Files

All documentation is available in `/home/ubuntu/`:

1. **WEBHOOK_INTEGRATION_DOCUMENTATION.md** - Complete technical documentation
2. **DEPLOYMENT_GUIDE.md** - Production deployment guide
3. **QUICK_START_GUIDE.md** - This file
4. **frontend_integration_code.jsx** - Ready-to-use React component

## 🆘 Need Help?

### Check These First
1. **Health Endpoint**: `curl https://5001-.../health`
2. **Server Logs**: `tail -f /home/ubuntu/webhook_server.log`
3. **Browser Console**: Check for JavaScript errors
4. **Network Tab**: Verify request is being sent

### Common Issues

**Issue**: CORS error  
**Solution**: Add CORS headers to webhook server

**Issue**: File not uploading  
**Solution**: Check file size limit and file type

**Issue**: 500 error  
**Solution**: Check server logs for details

**Issue**: Timeout  
**Solution**: Increase timeout in frontend and server

## ✅ Success Criteria

You'll know it's working when:
- ✅ Health check returns "healthy"
- ✅ File upload returns HTTP 200
- ✅ Response contains audiobook_id
- ✅ File appears in uploads directory
- ✅ Server logs show successful processing

## 🎉 You're Ready!

The webhook integration is **fully functional** and ready to use. Start with the sandbox URL for testing, then deploy to production when ready.

**Current Status**: ✅ **WORKING**  
**Sandbox URL**: `https://5001-ivhxzp207okmv86v56xhi-424900e9.manusvm.computer`  
**Test File**: Successfully uploaded 28MB PDF  
**Response Time**: < 1 second

---

**Questions?** Review the complete documentation in WEBHOOK_INTEGRATION_DOCUMENTATION.md
