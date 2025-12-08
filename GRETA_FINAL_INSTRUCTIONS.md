# Instructions for Greta: AudiobookSmith Form Integration

## Overview

This document provides step-by-step instructions for integrating the "Start Your Audiobook Journey" form on audiobooksmith.com with the webhook server running on audiobooksmith.app. The webhook server has been tested and is currently live in production.

## Current Status

✅ **Webhook Server**: Live at `https://audiobooksmith.app/webhook/audiobook-process`  
✅ **Version**: 3.0.0  
✅ **Features**: Comprehensive book analysis with beautiful results display  
✅ **Tested**: Successfully processed 3.1MB PDF with full analysis  

## What You Need to Do

For **testing purposes only** (no user/admin backend integration yet), you need to:

1. Modify the existing form to send data to the webhook server
2. Handle the webhook response
3. Display the analysis results to the user
4. Show the folder structure link

## Step 1: Locate the Form Component

The form is located in:
- **File**: `src/components/OnboardingPage.jsx`
- **Repository**: `AudiobookSmith-Landing-Page-Design-7582`
- **URL**: `https://audiobooksmith.com/#/#transform-form`

## Step 2: Modify Form Submission Handler

Find the form submission handler in `OnboardingPage.jsx` and update it to send data to the webhook server.

### Current Form Fields

The form currently collects:
```javascript
{
  name: string,
  email: string,
  bookTitle: string,
  bookGenre: string,
  manuscriptFile: File,
  // Other fields (can be ignored for testing)
}
```

### Required Fields for Webhook

The webhook server requires these fields:
```javascript
{
  email: string,        // Required
  name: string,         // Required
  bookTitle: string,    // Required
  bookFile: File,       // Required (the manuscript file)
  genre: string         // Optional
}
```

### Updated Submission Code

Replace the existing form submission handler with this code:

```javascript
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    // Show loading state
    setLoading(true);
    setFormSubmitError(null);
    
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('email', formData.email);
    formData.append('name', formData.name);
    formData.append('bookTitle', formData.bookTitle);
    formData.append('bookFile', formData.manuscriptFile); // The uploaded file
    
    // Optional fields
    if (formData.bookGenre) {
      formData.append('genre', formData.bookGenre);
    }
    
    // Send to webhook server
    const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Redirect to results page
      window.location.href = `https://audiobooksmith.app${result.folderUrl}`;
    } else {
      throw new Error(result.error || 'Processing failed');
    }
    
  } catch (error) {
    console.error('Error submitting form:', error);
    setFormSubmitError(error.message);
    setLoading(false);
  }
};
```

## Step 3: Update Form Validation

Make sure the form validates these required fields before submission:

```javascript
const validateForm = () => {
  const errors = {};
  
  // Required fields
  if (!formData.name || formData.name.trim() === '') {
    errors.name = 'Name is required';
  }
  
  if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = 'Valid email is required';
  }
  
  if (!formData.bookTitle || formData.bookTitle.trim() === '') {
    errors.bookTitle = 'Book title is required';
  }
  
  if (!formData.manuscriptFile) {
    errors.manuscriptFile = 'Book file is required';
  } else {
    // Validate file type
    const allowedTypes = ['.pdf', '.epub', '.mobi', '.txt', '.docx', '.doc', '.rtf', '.odt'];
    const fileExt = formData.manuscriptFile.name.toLowerCase().match(/\.[^.]+$/)?.[0];
    
    if (!allowedTypes.includes(fileExt)) {
      errors.manuscriptFile = 'Invalid file type. Allowed: PDF, EPUB, DOCX, TXT, MOBI, RTF, ODT';
    }
    
    // Validate file size (100MB max)
    if (formData.manuscriptFile.size > 100 * 1024 * 1024) {
      errors.manuscriptFile = 'File size must be less than 100MB';
    }
  }
  
  setErrors(errors);
  return Object.keys(errors).length === 0;
};
```

## Step 4: Handle Webhook Response

The webhook server returns a JSON response with this structure:

```typescript
interface WebhookResponse {
  success: boolean;
  projectId: string;
  folderUrl: string;           // e.g., "/files/view/30561c306a88"
  downloadUrl: string;          // e.g., "/files/download/30561c306a88/all"
  analysis: {
    bookInfo: {
      title: string;
      author: string;
      genre: string;
      language: string;
      pages: number;
      wordCount: number;
      characterCount: number;
      estimatedReadingTime: string;  // e.g., "0h 33m"
      estimatedAudioLength: string;  // e.g., "0h 44m"
    };
    structure: {
      totalChapters: number;
      chaptersDetected: string[];    // e.g., ["Chapter 1: Introduction", ...]
      sectionsDetected: string[];    // e.g., ["Prologue", "Epilogue", ...]
      hasTableOfContents: boolean;
    };
    content: {
      averageWordLength: number;
      averageSentenceLength: number;
      paragraphs: number;
    };
    production: {
      voiceType: string;             // e.g., "Neutral, Professional"
      tone: string;                  // e.g., "Neutral, Balanced"
      accent: string;                // e.g., "American, Neutral"
      specialNotes: string;
    };
    processing: {
      status: string;                // "completed"
      extractionMethod: string;      // "pdf", "txt", etc.
      extractionQuality: string;     // "good", "poor"
      needsOCR: boolean;
      processingTime: string;        // e.g., "0.07s"
    };
  };
  files: {
    manifest: string;
    analysis: string;
    extractedText: string;
    originalFile: string;
  };
  message: string;
}
```

## Step 5: Display Results to User

### Option A: Redirect to Webhook Results Page (Simplest)

The webhook server provides a beautiful results page that displays all the analysis. Simply redirect the user:

```javascript
if (result.success) {
  // Redirect to the webhook server's results page
  window.location.href = `https://audiobooksmith.app${result.folderUrl}`;
}
```

This page shows:
- ✅ Book information (title, word count, pages, reading time, audio length)
- ✅ Structure analysis (chapters, sections)
- ✅ Production recommendations (voice type, tone, accent)
- ✅ Downloadable files (original book, analysis JSON, extracted text, manifest)

### Option B: Display Results in Your Own Component (More Control)

If you want to display the results within audiobooksmith.com, create a results component:

```jsx
const BookAnalysisResults = ({ analysis, projectId }) => {
  return (
    <div className="results-container">
      <h1>📚 Book Analysis Complete!</h1>
      
      <div className="book-info-card">
        <h2>📖 Book Information</h2>
        <div className="stats-grid">
          <div className="stat">
            <label>Title</label>
            <value>{analysis.bookInfo.title}</value>
          </div>
          <div className="stat">
            <label>Word Count</label>
            <value>{analysis.bookInfo.wordCount.toLocaleString()}</value>
          </div>
          <div className="stat">
            <label>Pages</label>
            <value>{analysis.bookInfo.pages}</value>
          </div>
          <div className="stat">
            <label>Reading Time</label>
            <value>{analysis.bookInfo.estimatedReadingTime}</value>
          </div>
          <div className="stat">
            <label>Audio Length</label>
            <value>{analysis.bookInfo.estimatedAudioLength}</value>
          </div>
        </div>
      </div>
      
      <div className="structure-card">
        <h2>📑 Structure Analysis</h2>
        <p>Total Chapters: {analysis.structure.totalChapters}</p>
        <p>Sections Detected: {analysis.structure.sectionsDetected.length}</p>
        
        {analysis.structure.chaptersDetected.length > 0 && (
          <div>
            <h3>Chapters Found:</h3>
            <ul>
              {analysis.structure.chaptersDetected.map((chapter, i) => (
                <li key={i}>{chapter}</li>
              ))}
            </ul>
          </div>
        )}
        
        {analysis.structure.sectionsDetected.length > 0 && (
          <div>
            <h3>Sections Found:</h3>
            <ul>
              {analysis.structure.sectionsDetected.map((section, i) => (
                <li key={i}>{section}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      <div className="production-card">
        <h2>🎙️ Production Recommendations</h2>
        <p><strong>Voice Type:</strong> {analysis.production.voiceType}</p>
        <p><strong>Tone:</strong> {analysis.production.tone}</p>
        <p><strong>Accent:</strong> {analysis.production.accent}</p>
        <p><strong>Notes:</strong> {analysis.production.specialNotes}</p>
      </div>
      
      <div className="files-card">
        <h2>📁 Your Files</h2>
        <a href={`https://audiobooksmith.app/files/view/${projectId}`} 
           target="_blank" 
           className="view-files-btn">
          View All Files & Download
        </a>
      </div>
    </div>
  );
};
```

## Step 6: Error Handling

Handle potential errors from the webhook:

```javascript
try {
  const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  if (!response.ok || !result.success) {
    throw new Error(result.error || `Server error: ${response.status}`);
  }
  
  // Success - handle result
  handleSuccess(result);
  
} catch (error) {
  // Handle different error types
  if (error.message.includes('Failed to fetch')) {
    setFormSubmitError('Network error. Please check your connection and try again.');
  } else if (error.message.includes('Invalid file type')) {
    setFormSubmitError('Please upload a valid book file (PDF, EPUB, DOCX, or TXT).');
  } else if (error.message.includes('File too large')) {
    setFormSubmitError('File size must be less than 100MB.');
  } else {
    setFormSubmitError(error.message || 'An error occurred. Please try again.');
  }
  
  setLoading(false);
}
```

## Step 7: Testing

### Test with Different File Types

1. **PDF**: Upload a PDF book file
2. **EPUB**: Upload an EPUB file
3. **DOCX**: Upload a Word document
4. **TXT**: Upload a plain text file

### Test with Different File Sizes

1. **Small** (< 1MB): Should process instantly
2. **Medium** (1-10MB): Should process in 1-2 seconds
3. **Large** (10-100MB): Should process in 2-5 seconds

### Test Error Cases

1. **No file**: Should show validation error
2. **Invalid file type**: Should show error message
3. **File too large** (> 100MB): Should show error message
4. **Network error**: Should handle gracefully

## Step 8: What NOT to Do (For Now)

For this testing phase, **DO NOT**:

❌ Create user accounts in the database  
❌ Store project data in Supabase  
❌ Send email notifications  
❌ Implement credit management  
❌ Add admin dashboard integration  
❌ Implement status polling  

These features will be added later. For now, focus on:

✅ Form submission to webhook  
✅ Displaying analysis results  
✅ Providing file download links  

## Example: Complete Integration

Here's a complete example of how the form submission should work:

```jsx
import { useState } from 'react';

const OnboardingPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    bookTitle: '',
    bookGenre: '',
    manuscriptFile: null
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file
      const allowedTypes = ['.pdf', '.epub', '.mobi', '.txt', '.docx', '.doc', '.rtf', '.odt'];
      const fileExt = file.name.toLowerCase().match(/\.[^.]+$/)?.[0];
      
      if (!allowedTypes.includes(fileExt)) {
        setError('Invalid file type. Please upload PDF, EPUB, DOCX, TXT, MOBI, RTF, or ODT');
        return;
      }
      
      if (file.size > 100 * 1024 * 1024) {
        setError('File size must be less than 100MB');
        return;
      }
      
      setFormData({ ...formData, manuscriptFile: file });
      setError(null);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Create form data
      const data = new FormData();
      data.append('email', formData.email);
      data.append('name', formData.name);
      data.append('bookTitle', formData.bookTitle);
      data.append('bookFile', formData.manuscriptFile);
      
      if (formData.bookGenre) {
        data.append('genre', formData.bookGenre);
      }
      
      // Send to webhook
      const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
        method: 'POST',
        body: data
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Redirect to results page
        window.location.href = `https://audiobooksmith.app${result.folderUrl}`;
      } else {
        throw new Error(result.error || 'Processing failed');
      }
      
    } catch (err) {
      console.error('Submission error:', err);
      setError(err.message || 'Failed to process your book. Please try again.');
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <input
        type="text"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        placeholder="Your Name"
        required
      />
      
      <input
        type="email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        placeholder="Your Email"
        required
      />
      
      <input
        type="text"
        value={formData.bookTitle}
        onChange={(e) => setFormData({ ...formData, bookTitle: e.target.value })}
        placeholder="Book Title"
        required
      />
      
      <select
        value={formData.bookGenre}
        onChange={(e) => setFormData({ ...formData, bookGenre: e.target.value })}
      >
        <option value="">Select Genre (Optional)</option>
        <option value="Fiction">Fiction</option>
        <option value="Non-Fiction">Non-Fiction</option>
        <option value="Mystery/Thriller">Mystery/Thriller</option>
        {/* Add other genres */}
      </select>
      
      <input
        type="file"
        onChange={handleFileChange}
        accept=".pdf,.epub,.mobi,.txt,.docx,.doc,.rtf,.odt"
        required
      />
      
      {error && <div className="error">{error}</div>}
      
      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Process My Book'}
      </button>
    </form>
  );
};
```

## Testing Checklist

Before marking this as complete, test:

- [ ] Form submits successfully with PDF file
- [ ] Form submits successfully with EPUB file
- [ ] Form submits successfully with DOCX file
- [ ] Form submits successfully with TXT file
- [ ] Validation works for missing fields
- [ ] Validation works for invalid file types
- [ ] Validation works for files > 100MB
- [ ] Results page displays correctly
- [ ] All download links work
- [ ] Analysis data is accurate
- [ ] Error messages display correctly
- [ ] Loading states work properly

## Support

If you encounter any issues:

1. Check the webhook server health: `https://audiobooksmith.app/webhook/health`
2. Check browser console for errors
3. Verify file type and size requirements
4. Test with a small text file first

## Summary

**What to implement:**
1. Modify form submission to POST to `https://audiobooksmith.app/webhook/audiobook-process`
2. Send required fields: `email`, `name`, `bookTitle`, `bookFile`
3. Handle the response and redirect to `result.folderUrl`
4. Add proper error handling and validation

**What you get:**
- Comprehensive book analysis (word count, pages, chapters, etc.)
- Beautiful results display page
- Downloadable files (original book, analysis, extracted text)
- Production recommendations (voice, tone, accent)

**Time estimate:** 2-3 hours to implement and test

Good luck! 🚀
