# Simplified Testing Instructions for Greta

**Author:** Manus AI  
**Date:** December 7, 2025  
**Version:** 1.0 - Testing Only

## 1.0 Overview

These instructions are for implementing a **simplified testing workflow** for the "Start Your Audiobook Journey" form. This version focuses on testing the file upload and processing workflow **without implementing the full user/admin backend**.

### What This Version Does

- Collects email, name, and book file from a form
- Sends data to webhook server for processing
- Returns a link to view the processed folder structure
- No user accounts, no database, no email notifications

### What This Version Does NOT Do

- Create user accounts
- Store data in database
- Send email notifications
- Manage credits or subscriptions
- Implement admin panel

## 2.0 Form Implementation

### 2.1 Form Fields (Minimum Required)

Create a simple form on audiobooksmith.com with these three fields:

| Field | Type | Required | Validation |
|---|---|---|---|
| **Email** | Text input | Yes | Valid email format |
| **Name** | Text input | Yes | Not empty |
| **Book File** | File upload | Yes | Max 100MB, allowed formats: .pdf, .epub, .mobi, .txt, .docx, .doc |

### 2.2 Optional Fields (Can Be Ignored)

If your form has these fields, you can include them in the submission, but the webhook server will ignore them for now:

- Book Title
- Plan/Tier Selection
- Voice Selection
- Chapter Settings
- Any other advanced options

### 2.3 Frontend Code Example

```typescript
// client/src/components/SimplifiedAudiobookForm.tsx

import { useState } from 'react';

interface FormData {
  email: string;
  name: string;
  bookFile: File | null;
}

export const SimplifiedAudiobookForm = () => {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    name: '',
    bookFile: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Validate file size
      if (file.size > 100 * 1024 * 1024) {
        alert('File size must be less than 100MB');
        return;
      }
      
      // Validate file type
      const allowedTypes = ['.pdf', '.epub', '.mobi', '.txt', '.docx', '.doc'];
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowedTypes.includes(fileExt)) {
        alert('Please upload a PDF, ePub, MOBI, TXT, or Word document');
        return;
      }
      
      setFormData(prev => ({ ...prev, bookFile: file }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.email || !formData.name || !formData.bookFile) {
      alert('Please fill in all fields');
      return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      alert('Please enter a valid email address');
      return;
    }
    
    setIsSubmitting(true);
    setResult(null);
    
    try {
      // Create FormData for multipart upload
      const uploadData = new FormData();
      uploadData.append('email', formData.email);
      uploadData.append('name', formData.name);
      uploadData.append('bookFile', formData.bookFile);
      
      // Send to webhook server
      const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
        method: 'POST',
        body: uploadData
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data);
        
        // Reset form
        setFormData({
          email: '',
          name: '',
          bookFile: null
        });
        
        // Clear file input
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      } else {
        alert(data.message || 'An error occurred');
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Failed to submit form. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-3xl font-bold mb-6">Start Your Audiobook Journey</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-2">
            Email Address *
          </label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="your@email.com"
            required
          />
        </div>
        
        {/* Name Field */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-2">
            Your Name *
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="John Doe"
            required
          />
        </div>
        
        {/* File Upload */}
        <div>
          <label htmlFor="bookFile" className="block text-sm font-medium mb-2">
            Upload Your Book *
          </label>
          <input
            type="file"
            id="bookFile"
            onChange={handleFileChange}
            accept=".pdf,.epub,.mobi,.txt,.doc,.docx"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            required
          />
          <p className="text-sm text-gray-500 mt-2">
            Supported formats: PDF, ePub, MOBI, TXT, Word (max 100MB)
          </p>
          {formData.bookFile && (
            <p className="text-sm text-green-600 mt-2">
              ✓ {formData.bookFile.name} ({(formData.bookFile.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>
        
        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Processing...' : 'Upload and Process'}
        </button>
      </form>
      
      {/* Success Result */}
      {result && result.success && (
        <div className="mt-8 p-6 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-xl font-bold text-green-800 mb-4">
            ✅ {result.message}
          </h3>
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              <strong>Project ID:</strong> {result.projectId}
            </p>
            <p className="text-sm text-gray-700">
              <strong>Email:</strong> {result.metadata.email}
            </p>
            <p className="text-sm text-gray-700">
              <strong>Name:</strong> {result.metadata.name}
            </p>
            <p className="text-sm text-gray-700">
              <strong>Uploaded File:</strong> {result.metadata.uploadedFile}
            </p>
            <a
              href={result.folderUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-4 bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700"
            >
              📁 View Processed Files
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
```

## 3.0 Webhook Integration

### 3.1 Endpoint

**URL:** `https://audiobooksmith.app/webhook/audiobook-process`  
**Method:** POST  
**Content-Type:** multipart/form-data

### 3.2 Request Format

```
POST /webhook/audiobook-process
Content-Type: multipart/form-data

Fields:
- email: string (required)
- name: string (required)
- bookFile: file (required, max 100MB)
```

### 3.3 Success Response

```json
{
  "success": true,
  "message": "Book processed successfully!",
  "projectId": "a1b2c3d4",
  "folderUrl": "https://audiobooksmith.app/files/view/a1b2c3d4",
  "metadata": {
    "email": "user@example.com",
    "name": "John Doe",
    "uploadedFile": "my-book.pdf",
    "originalExtension": ".pdf",
    "processedAt": "2025-12-07T21:30:00.000000Z",
    "projectId": "a1b2c3d4"
  }
}
```

### 3.4 Error Response

```json
{
  "success": false,
  "error": "Invalid file format",
  "message": "Please upload a valid book file (.pdf, .epub, .mobi, .txt, .docx, .doc)"
}
```

## 4.0 File Browser

After processing, users can view their files at:

**URL:** `https://audiobooksmith.app/files/view/{projectId}`

The file browser shows:
- Project metadata (email, name, uploaded file, processed date)
- Folder structure
- All processed files
- Download buttons for each file

### 4.1 File Browser Features

- **Breadcrumb navigation** - Navigate through folders
- **File listing** - View all files and folders
- **Download buttons** - Download any file
- **Metadata display** - Show project information
- **Responsive design** - Works on mobile and desktop

## 5.0 Implementation Steps

### Step 1: Create the Form Component

1. Copy the code example above
2. Add it to your audiobooksmith.com codebase
3. Style it to match your website design
4. Add it to the appropriate page

### Step 2: Test Locally (Optional)

```bash
# Test with curl
curl -X POST https://audiobooksmith.app/webhook/audiobook-process \
  -F "email=test@example.com" \
  -F "name=Test User" \
  -F "bookFile=@/path/to/test-book.pdf"
```

### Step 3: Deploy and Test

1. Deploy your form to audiobooksmith.com
2. Fill out the form with test data
3. Upload a small PDF file (< 5MB for testing)
4. Click submit
5. Verify you receive a success response
6. Click the "View Processed Files" link
7. Verify you can see the file browser

### Step 4: Verify File Browser

1. Check that metadata is displayed correctly
2. Verify uploaded file is shown
3. Test downloading the file
4. Check that folder navigation works (if processor creates folders)

## 6.0 What Happens on the Server

When you submit the form:

1. **Webhook receives request** - Validates email, name, and file
2. **Generates project ID** - Creates unique 8-character ID
3. **Saves file** - Stores uploaded file in `/root/audiobook_webhook/processed/{projectId}/`
4. **Saves metadata** - Creates `metadata.json` with form data
5. **Calls processor** - Runs `audiobook_processor.py` (if exists)
6. **Returns response** - Sends back project ID and folder URL

## 7.0 Troubleshooting

### Form doesn't submit

- Check browser console for errors
- Verify webhook URL is correct
- Check file size (must be < 100MB)
- Verify file format is allowed

### 404 Error on webhook

- Verify webhook server is running
- Check URL: `https://audiobooksmith.app/webhook/audiobook-process`
- Test health endpoint: `https://audiobooksmith.app/health`

### File browser shows "Project not found"

- Verify project ID in URL
- Check that file was uploaded successfully
- Look at server logs: `/root/audiobook_webhook/logs/webhook_server.log`

### Can't download files

- Check file permissions on server
- Verify file exists in project directory
- Check browser console for errors

## 8.0 Next Steps (After Testing)

Once testing is complete and working:

1. Implement user account creation
2. Add database integration
3. Implement email notifications
4. Add status polling for long-running tasks
5. Implement credit management
6. Add admin panel
7. Integrate with payment system

## 9.0 Summary

This simplified testing workflow allows you to:

✅ Test file upload functionality  
✅ Verify webhook integration  
✅ See processed files in browser  
✅ Download processed files  
✅ Test without complex backend  

**No user accounts, no database, no emails - just pure testing!**

---

## Appendix: Quick Reference

### Form Fields
```typescript
{
  email: string,      // Required
  name: string,       // Required
  bookFile: File      // Required, max 100MB
}
```

### Webhook Endpoint
```
POST https://audiobooksmith.app/webhook/audiobook-process
```

### File Browser URL
```
https://audiobooksmith.app/files/view/{projectId}
```

### Server Logs
```
/root/audiobook_webhook/logs/webhook_server.log
```

### Processed Files Location
```
/root/audiobook_webhook/processed/{projectId}/
```
