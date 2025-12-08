// ============================================================================
// WEBHOOK INTEGRATION CODE FOR OnboardingPage.jsx
// ============================================================================
// This code replaces the existing handleSubmit function in OnboardingPage.jsx
// for TESTING PURPOSES ONLY (no database/user account creation)
// ============================================================================

// STEP 1: Add this new validation function (replace existing validateForm)
const validateForm = () => {
  const newErrors = {};
  
  // Required fields for webhook
  if (!formData.name || formData.name.trim() === '') {
    newErrors.name = 'Name is required';
  }
  
  if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    newErrors.email = 'Valid email is required';
  }
  
  if (!formData.bookTitle || formData.bookTitle.trim() === '') {
    newErrors.bookTitle = 'Book title is required';
  }
  
  if (!formData.manuscriptFile) {
    newErrors.manuscriptFile = 'Book file is required';
  } else {
    // Validate file type
    const allowedExtensions = ['.pdf', '.epub', '.mobi', '.txt', '.docx', '.doc', '.rtf', '.odt'];
    const fileName = formData.manuscriptFile.name.toLowerCase();
    const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      newErrors.manuscriptFile = 'Invalid file type. Allowed: PDF, EPUB, DOCX, TXT, MOBI, RTF, ODT';
    }
    
    // Validate file size (100MB max)
    const maxSize = 100 * 1024 * 1024; // 100MB in bytes
    if (formData.manuscriptFile.size > maxSize) {
      newErrors.manuscriptFile = `File size must be less than 100MB (current: ${(formData.manuscriptFile.size / (1024 * 1024)).toFixed(1)}MB)`;
    }
  }
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

// STEP 2: Replace the entire handleSubmit function with this:
const handleSubmit = async (e) => {
  e.preventDefault();
  setFormSubmitError(null);
  
  // Check if upgrade is needed (for free plan word count limits)
  if (requiresUpgrade) {
    handleUpgrade();
    return;
  }
  
  // Validate form
  if (!validateForm()) {
    const firstErrorField = Object.keys(errors)[0];
    const errorElement = document.getElementById(firstErrorField);
    if (errorElement) {
      errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    return;
  }
  
  try {
    setLoading(true);
    
    // Create FormData for multipart/form-data upload
    const webhookData = new FormData();
    
    // Required fields
    webhookData.append('email', formData.email);
    webhookData.append('name', formData.name);
    webhookData.append('bookTitle', formData.bookTitle);
    webhookData.append('bookFile', formData.manuscriptFile);
    
    // Optional fields (only add if they have values)
    if (formData.bookGenre && formData.bookGenre.trim() !== '') {
      webhookData.append('genre', formData.bookGenre);
    }
    
    // Send to webhook server
    console.log('Sending book to webhook server...');
    const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
      method: 'POST',
      body: webhookData
      // Note: Don't set Content-Type header - browser will set it automatically with boundary
    });
    
    // Parse response
    const result = await response.json();
    
    // Check if request was successful
    if (!response.ok || !result.success) {
      throw new Error(result.error || result.message || `Server error: ${response.status}`);
    }
    
    // Success! Log the result for debugging
    console.log('Webhook processing successful:', result);
    console.log('Project ID:', result.projectId);
    console.log('Analysis:', result.analysis);
    
    // Redirect to the results page on the webhook server
    // This page shows the complete book analysis and download links
    window.location.href = `https://audiobooksmith.app${result.folderUrl}`;
    
    // Alternative: If you want to display results in your own component,
    // uncomment the following and create a results display component:
    /*
    setIsSubmitted(true);
    setAnalysisResults(result);
    // Then show your custom results component instead of redirecting
    */
    
  } catch (error) {
    console.error('Error submitting form to webhook:', error);
    
    // Handle specific error types with user-friendly messages
    let errorMessage = 'An error occurred while processing your book. Please try again.';
    
    if (error.message.includes('Failed to fetch') || error.message.includes('Network')) {
      errorMessage = 'Network error. Please check your internet connection and try again.';
    } else if (error.message.includes('Invalid file type')) {
      errorMessage = 'Please upload a valid book file (PDF, EPUB, DOCX, or TXT).';
    } else if (error.message.includes('File too large') || error.message.includes('size')) {
      errorMessage = 'File size must be less than 100MB. Please upload a smaller file.';
    } else if (error.message.includes('No file uploaded')) {
      errorMessage = 'Please select a book file to upload.';
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    setFormSubmitError(errorMessage);
    setErrors({ form: errorMessage });
    
  } finally {
    setLoading(false);
  }
};

// ============================================================================
// OPTIONAL: Add this state if you want to display results in your own component
// ============================================================================
// Add this to your useState declarations at the top of the component:
/*
const [analysisResults, setAnalysisResults] = useState(null);
*/

// ============================================================================
// OPTIONAL: Custom Results Display Component
// ============================================================================
// If you want to display results within audiobooksmith.com instead of redirecting,
// create this component and show it when isSubmitted is true:
/*
const AnalysisResultsDisplay = ({ results }) => {
  if (!results || !results.analysis) return null;
  
  const { analysis, projectId, files } = results;
  
  return (
    <div className="analysis-results">
      <h1>📚 Book Analysis Complete!</h1>
      
      <div className="success-message">
        ✅ Your book has been processed successfully!
      </div>
      
      <div className="book-info-section">
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
          <div className="stat">
            <label>Language</label>
            <value>{analysis.bookInfo.language}</value>
          </div>
        </div>
      </div>
      
      <div className="structure-section">
        <h2>📑 Structure Analysis</h2>
        <p><strong>Total Chapters:</strong> {analysis.structure.totalChapters}</p>
        <p><strong>Sections Detected:</strong> {analysis.structure.sectionsDetected.length}</p>
        
        {analysis.structure.chaptersDetected && analysis.structure.chaptersDetected.length > 0 && (
          <div className="chapters-list">
            <h3>Chapters Found:</h3>
            <ul>
              {analysis.structure.chaptersDetected.map((chapter, index) => (
                <li key={index}>{chapter}</li>
              ))}
            </ul>
          </div>
        )}
        
        {analysis.structure.sectionsDetected && analysis.structure.sectionsDetected.length > 0 && (
          <div className="sections-list">
            <h3>Sections Found:</h3>
            <ul>
              {analysis.structure.sectionsDetected.map((section, index) => (
                <li key={index}>{section}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      <div className="production-section">
        <h2>🎙️ Production Recommendations</h2>
        <div className="recommendations">
          <p><strong>Voice Type:</strong> {analysis.production.voiceType}</p>
          <p><strong>Tone:</strong> {analysis.production.tone}</p>
          <p><strong>Accent:</strong> {analysis.production.accent}</p>
          <div className="special-notes">
            <strong>📝 Notes:</strong>
            <p>{analysis.production.specialNotes}</p>
          </div>
        </div>
      </div>
      
      <div className="files-section">
        <h2>📁 Your Files</h2>
        <p>View all your processed files and download them:</p>
        <a 
          href={`https://audiobooksmith.app/files/view/${projectId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="view-files-button"
        >
          View All Files & Downloads
        </a>
      </div>
    </div>
  );
};
*/

// ============================================================================
// USAGE INSTRUCTIONS
// ============================================================================
/*
1. Open src/components/OnboardingPage.jsx

2. Find the existing validateForm function (around line 150)
   Replace it with the new validateForm function above

3. Find the existing handleSubmit function (around line 173)
   Replace the ENTIRE function with the new handleSubmit function above

4. Save the file

5. Test with a book file:
   - Fill in name, email, book title
   - Upload a PDF, EPUB, DOCX, or TXT file (< 100MB)
   - Click submit
   - You should be redirected to the analysis results page

6. If you want to display results in your own component:
   - Uncomment the analysisResults state
   - Uncomment the AnalysisResultsDisplay component
   - Modify handleSubmit to set results instead of redirecting
   - Show AnalysisResultsDisplay when isSubmitted is true

TESTING CHECKLIST:
□ Form validates required fields
□ Form validates file type (PDF, EPUB, DOCX, TXT, etc.)
□ Form validates file size (< 100MB)
□ Form shows loading state during upload
□ Form redirects to results page on success
□ Results page shows book analysis
□ Download links work
□ Error messages display correctly
□ Works with different file types
*/

// ============================================================================
// TROUBLESHOOTING
// ============================================================================
/*
If you get errors:

1. "Network error" or "Failed to fetch"
   - Check that webhook server is running
   - Test: curl https://audiobooksmith.app/webhook/health
   - Should return: {"status":"healthy",...}

2. "Invalid file type"
   - Make sure file has correct extension
   - Allowed: .pdf, .epub, .mobi, .txt, .docx, .doc, .rtf, .odt

3. "File too large"
   - File must be < 100MB
   - Compress or split the file

4. "CORS error"
   - Webhook server should allow cross-origin requests
   - This should already be configured

5. Results page doesn't load
   - Check browser console for errors
   - Verify the folderUrl in the response
   - Try accessing the URL directly

For more help, check:
- GRETA_FINAL_INSTRUCTIONS.md
- WEBHOOK_API_REFERENCE.md
- test_form.html (working example)
*/
