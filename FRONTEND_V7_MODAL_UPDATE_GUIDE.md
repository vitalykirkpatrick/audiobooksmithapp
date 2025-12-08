# AudiobookSmith V7 - Frontend Update Guide for Greta

## 📋 Overview

This guide covers all frontend updates needed to work with the new V7 backend system. The main changes are:

1. **Display results in a modal popup** (instead of redirecting to a new page)
2. **Handle new V7 response format** (with AI-detected metadata and voice recommendations)
3. **Simplify the upload form** (remove title and genre fields)
4. **Add error handling** (for validation failures)

**Estimated Time**: 1-2 hours

---

## 🎯 What's Changing

### Before (Current)
- User fills form with: name, email, title, genre, file
- After upload, redirects to external analysis page
- Shows basic info with "Unknown" for author/genre
- No voice recommendations

### After (V7)
- User fills form with: name, email, file (title/genre removed)
- After upload, shows beautiful modal popup on same page
- Displays AI-detected title, author, genre, all chapters
- Shows 5 voice recommendations with audio players
- User can select voice and close modal

---

## 📦 Part 1: Simplify the Upload Form

### Step 1: Remove Unnecessary Fields

**Remove these fields from your upload form:**
- ❌ `bookTitle` input field
- ❌ `genre` dropdown/select field
- ❌ `plan` field (if it exists)

**Keep only these fields:**
- ✅ `name` - User's name (text input)
- ✅ `email` - User's email (email input)
- ✅ `bookFile` - PDF file upload (file input)
- ✅ `acceptTerms` - Terms checkbox (already added)

### Step 2: Update Form Component

**Example React Component:**

```jsx
import React, { useState } from 'react';

function BookUploadForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    bookFile: null,
    acceptTerms: false
  });
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFormData({ ...formData, bookFile: e.target.files[0] });
    setError(null); // Clear any previous errors
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    
    // Validation
    if (!formData.name || !formData.email || !formData.bookFile) {
      setError('Please fill in all required fields');
      return;
    }
    
    if (!formData.acceptTerms) {
      setError('Please accept the Terms & Conditions');
      return;
    }
    
    // Show loading state
    setIsProcessing(true);
    
    // Create FormData
    const data = new FormData();
    data.append('name', formData.name);
    data.append('email', formData.email);
    data.append('bookFile', formData.bookFile);
    
    try {
      // Send to webhook
      const response = await fetch('https://audiobooksmith.app/webhook/upload', {
        method: 'POST',
        body: data
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Show modal with results
        setAnalysisResult(result.analysis);
        setShowModal(true);
      } else {
        // Handle validation error
        setError(result.message || 'Upload failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        {/* Name Field */}
        <div className="form-group">
          <label htmlFor="name">Your Name *</label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        {/* Email Field */}
        <div className="form-group">
          <label htmlFor="email">Email Address *</label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            required
          />
        </div>

        {/* File Upload */}
        <div className="form-group">
          <label htmlFor="bookFile">Upload Book (PDF) *</label>
          <input
            type="file"
            id="bookFile"
            accept=".pdf"
            onChange={handleFileChange}
            required
          />
        </div>

        {/* Terms Checkbox */}
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={formData.acceptTerms}
              onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
              required
            />
            I accept the{' '}
            <a href="https://audiobooksmith.com/#/terms" target="_blank">Terms & Conditions</a>,{' '}
            <a href="https://audiobooksmith.com/#/privacy" target="_blank">Privacy Policy</a>, and{' '}
            <a href="https://audiobooksmith.com/#/cookies" target="_blank">Cookie Policy</a>
          </label>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message" style={{ color: 'red', marginBottom: '15px' }}>
            ⚠️ {error}
          </div>
        )}

        {/* Submit Button */}
        <button type="submit" disabled={isProcessing}>
          {isProcessing ? 'Processing...' : 'Analyze My Book'}
        </button>
      </form>

      {/* Modal Component */}
      {showModal && analysisResult && (
        <AnalysisModal
          analysis={analysisResult}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}

export default BookUploadForm;
```

---

## 📦 Part 2: Create the Analysis Modal Component

### Step 1: Create Modal Component

**Create a new file: `AnalysisModal.jsx`**

```jsx
import React, { useState } from 'react';
import './AnalysisModal.css';

function AnalysisModal({ analysis, onClose }) {
  const [selectedVoice, setSelectedVoice] = useState(null);

  const handleVoiceSelect = async (voice) => {
    setSelectedVoice(voice.voice_id);
    
    // Save selection to server
    try {
      await fetch('https://audiobooksmith.app/webhook/select-voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: analysis.sessionId,
          projectId: analysis.projectId,
          voiceId: voice.voice_id,
          voiceName: voice.name
        })
      });
      
      // Show success message
      alert(`Voice selected: ${voice.name}`);
    } catch (err) {
      console.error('Error saving voice selection:', err);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Close Button */}
        <button className="modal-close" onClick={onClose}>×</button>
        
        {/* Header */}
        <div className="modal-header">
          <h2>📚 Book Analysis Complete!</h2>
          <span className="badge-success">✓ Processing Successful</span>
        </div>

        {/* Book Information */}
        <div className="modal-section">
          <h3>📖 Book Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Title</span>
              <span className="info-value">{analysis.bookInfo.title}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Author</span>
              <span className="info-value">{analysis.bookInfo.author}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Genre</span>
              <span className="info-value">{analysis.bookInfo.genre}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Word Count</span>
              <span className="info-value">{analysis.metrics.word_count.toLocaleString()}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Pages</span>
              <span className="info-value">{analysis.metrics.page_count}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Audio Length</span>
              <span className="info-value">{analysis.metrics.audio_length}</span>
            </div>
          </div>
        </div>

        {/* Chapters */}
        {analysis.structure && analysis.structure.total_chapters > 0 && (
          <div className="modal-section">
            <h3>📑 Chapters ({analysis.structure.total_chapters})</h3>
            <div className="chapters-list">
              {analysis.structure.chapters.slice(0, 10).map((chapter, index) => (
                <div key={index} className="chapter-item">
                  <span className="chapter-number">Chapter {chapter.number}</span>
                  <span className="chapter-title">{chapter.title}</span>
                </div>
              ))}
              {analysis.structure.total_chapters > 10 && (
                <div className="chapter-item">
                  <span className="chapter-more">
                    ... and {analysis.structure.total_chapters - 10} more chapters
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Voice Recommendations */}
        {analysis.voiceRecommendations && analysis.voiceRecommendations.recommended_voices && (
          <div className="modal-section">
            <h3>🎙️ Select Your Narrator Voice</h3>
            
            {/* Voice Criteria */}
            <div className="voice-criteria">
              <p><strong>Recommended for your book:</strong></p>
              <p>
                {analysis.voiceRecommendations.voice_criteria.gender} • 
                {analysis.voiceRecommendations.voice_criteria.accent} • 
                {analysis.voiceRecommendations.voice_criteria.tone}
              </p>
            </div>

            {/* Voice Grid */}
            <div className="voice-grid">
              {analysis.voiceRecommendations.recommended_voices.map((voice) => (
                <div
                  key={voice.voice_id}
                  className={`voice-card ${selectedVoice === voice.voice_id ? 'selected' : ''}`}
                  onClick={() => handleVoiceSelect(voice)}
                >
                  <div className="voice-header">
                    <span className="voice-name">{voice.name}</span>
                    <span className="match-score">{voice.match_score}% Match</span>
                  </div>
                  
                  <p className="voice-description">{voice.description || 'Professional narrator voice'}</p>
                  
                  {voice.match_reason && (
                    <p className="match-reason">
                      <strong>Why:</strong> {voice.match_reason}
                    </p>
                  )}
                  
                  {/* Audio Player */}
                  {voice.sample_generated && (
                    <div className="voice-player">
                      <audio controls preload="metadata">
                        <source
                          src={`https://audiobooksmith.app/files/voice-sample/${analysis.sessionId}/${voice.voice_id}.mp3`}
                          type="audio/mpeg"
                        />
                        Your browser does not support audio playback.
                      </audio>
                    </div>
                  )}
                  
                  <button className={`select-voice-btn ${selectedVoice === voice.voice_id ? 'selected' : ''}`}>
                    {selectedVoice === voice.voice_id ? '✓ Selected' : 'Select This Voice'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Folder Structure */}
        {analysis.folderStructure && (
          <div className="modal-section">
            <h3>📁 Server Folder Structure</h3>
            <p className="folder-info">
              Session: <strong>{analysis.sessionId}</strong><br />
              Files: <strong>{analysis.folderStructure.file_count}</strong> | 
              Folders: <strong>{analysis.folderStructure.folder_count}</strong> | 
              Size: <strong>{analysis.folderStructure.total_size_formatted}</strong>
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn-primary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

export default AnalysisModal;
```

### Step 2: Create Modal CSS

**Create a new file: `AnalysisModal.css`**

```css
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  overflow-y: auto;
}

/* Modal Content */
.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 1000px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

/* Close Button */
.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 32px;
  cursor: pointer;
  color: #999;
  line-height: 1;
  padding: 0;
  width: 40px;
  height: 40px;
}

.modal-close:hover {
  color: #333;
}

/* Modal Header */
.modal-header {
  text-align: center;
  margin-bottom: 30px;
}

.modal-header h2 {
  font-size: 28px;
  color: #333;
  margin-bottom: 10px;
}

.badge-success {
  display: inline-block;
  background: #10b981;
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

/* Modal Sections */
.modal-section {
  margin-bottom: 30px;
}

.modal-section h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.info-item {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.info-label {
  display: block;
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 5px;
}

.info-value {
  display: block;
  font-size: 18px;
  color: #333;
  font-weight: 600;
}

/* Chapters List */
.chapters-list {
  max-height: 300px;
  overflow-y: auto;
}

.chapter-item {
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  gap: 15px;
}

.chapter-number {
  font-weight: 600;
  color: #667eea;
  min-width: 100px;
}

.chapter-title {
  color: #333;
}

.chapter-more {
  color: #999;
  font-style: italic;
}

/* Voice Criteria */
.voice-criteria {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.voice-criteria p {
  margin: 5px 0;
  color: #856404;
}

/* Voice Grid */
.voice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

/* Voice Card */
.voice-card {
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.voice-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.voice-card.selected {
  border-color: #10b981;
  background: #f0fdf4;
}

.voice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.voice-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.match-score {
  background: #667eea;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.voice-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
  line-height: 1.5;
}

.match-reason {
  background: #e0f2fe;
  border-left: 3px solid #0284c7;
  padding: 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #0c4a6e;
  margin-bottom: 15px;
}

/* Voice Player */
.voice-player {
  background: white;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 15px;
}

.voice-player audio {
  width: 100%;
  height: 40px;
}

/* Select Voice Button */
.select-voice-btn {
  width: 100%;
  padding: 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease;
}

.select-voice-btn:hover {
  background: #5568d3;
}

.select-voice-btn.selected {
  background: #10b981;
}

/* Folder Info */
.folder-info {
  color: #666;
  line-height: 1.8;
}

/* Modal Footer */
.modal-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 2px solid #f0f0f0;
}

.btn-primary {
  padding: 12px 40px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease;
}

.btn-primary:hover {
  background: #5568d3;
}

/* Responsive */
@media (max-width: 768px) {
  .modal-content {
    padding: 20px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .voice-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 📦 Part 3: Handle Validation Errors

### Update Error Handling in Form

When the backend rejects a document (e.g., template, guide), it returns:

```json
{
  "success": false,
  "error": "validation_failed",
  "message": "This appears to be a template document, not a book...",
  "suggestions": [
    "Upload an actual book, short story, or sample chapter",
    "Not suitable: templates, forms, proposals, guides"
  ]
}
```

**Update your form's error handling:**

```jsx
const handleSubmit = async (e) => {
  e.preventDefault();
  setError(null);
  setIsProcessing(true);
  
  const data = new FormData();
  data.append('name', formData.name);
  data.append('email', formData.email);
  data.append('bookFile', formData.bookFile);
  
  try {
    const response = await fetch('https://audiobooksmith.app/webhook/upload', {
      method: 'POST',
      body: data
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Show modal with results
      setAnalysisResult(result.analysis);
      setShowModal(true);
    } else {
      // Show error message
      let errorMsg = result.message || 'Upload failed';
      
      // Add suggestions if available
      if (result.suggestions && result.suggestions.length > 0) {
        errorMsg += '\n\nSuggestions:\n' + result.suggestions.join('\n');
      }
      
      setError(errorMsg);
    }
  } catch (err) {
    setError('Network error. Please try again.');
  } finally {
    setIsProcessing(false);
  }
};
```

---

## 📦 Part 4: Testing Checklist

After implementing the changes, test these scenarios:

### ✅ Valid Book Upload
1. Upload a real book PDF (e.g., Vitaly book)
2. Verify modal appears (no redirect)
3. Check that title, author, genre are displayed (not "Unknown")
4. Verify all chapters are listed
5. Check that 5 voices appear with audio players
6. Test playing a voice sample
7. Test selecting a voice
8. Close modal and verify you're still on the same page

### ✅ Invalid Document Upload
1. Upload a technical guide or template
2. Verify error message appears (not modal)
3. Check that error message is clear and helpful
4. Verify suggestions are displayed

### ✅ Form Validation
1. Try submitting without name → should show error
2. Try submitting without email → should show error
3. Try submitting without file → should show error
4. Try submitting without accepting terms → should show error

### ✅ Responsive Design
1. Test modal on desktop
2. Test modal on tablet
3. Test modal on mobile
4. Verify audio players work on all devices

---

## 📊 V7 Response Format Reference

The V7 backend returns this JSON structure:

```json
{
  "success": true,
  "message": "Book processed successfully",
  "projectId": "user_20251208_123456",
  "sessionId": "2025-12-08T12-34-56",
  "folderUrl": "https://audiobooksmith.app/files/view/2025-12-08T12-34-56",
  "analysis": {
    "projectId": "user_20251208_123456",
    "sessionId": "2025-12-08T12-34-56",
    "userEmail": "user@example.com",
    "timestamp": "2025-12-08T12:34:56",
    "bookInfo": {
      "title": "VITALY The MisAdventures of a Ukrainian Orphan",
      "author": "Vitaly Magidov",
      "genre": "Memoir",
      "type": "Memoir",
      "language": "English"
    },
    "metrics": {
      "word_count": 109940,
      "page_count": 439,
      "reading_time": "549m",
      "audio_length": "732m"
    },
    "structure": {
      "total_chapters": 46,
      "chapters": [
        {"number": 1, "title": "The Beginning"},
        {"number": 2, "title": "Early Memories"},
        ...
      ]
    },
    "voiceRecommendations": {
      "voice_criteria": {
        "gender": "male",
        "age_range": "middle-aged",
        "accent": "American",
        "tone": "warm, empathetic",
        "reasoning": "..."
      },
      "recommended_voices": [
        {
          "voice_id": "abc123",
          "name": "Adam",
          "description": "Deep, warm male voice",
          "match_score": 95,
          "match_reason": "Perfect for memoir narration",
          "sample_generated": true,
          "sample_path": "/path/to/sample.mp3"
        },
        ...
      ]
    },
    "folderStructure": {
      "session_id": "2025-12-08T12-34-56",
      "file_count": 15,
      "folder_count": 19,
      "total_size_formatted": "2.5 MB"
    }
  }
}
```

---

## 🎯 Summary

### What You Need to Do:

1. **Remove** `title` and `genre` fields from the form
2. **Keep** only `name`, `email`, `bookFile`, `acceptTerms`
3. **Create** the `AnalysisModal` component
4. **Create** the `AnalysisModal.css` stylesheet
5. **Update** form submission to show modal instead of redirecting
6. **Add** error handling for validation failures
7. **Test** with both valid books and invalid documents

### Expected Result:

- Users stay on your website (no redirect)
- Beautiful modal shows all analysis results
- Voice players work and users can select voices
- Clear error messages for invalid uploads
- Professional, seamless user experience

---

**Estimated Time**: 1-2 hours

**Questions?** Check the V7 response format reference above or test with the deployed V7 backend.

Good luck! 🚀
