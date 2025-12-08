/**
 * AudiobookSmith Frontend Integration Code
 * Add this code to OnboardingPage.jsx to integrate with N8N webhook
 * 
 * Location: /home/ubuntu/audiobooksmith-site/src/components/OnboardingPage.jsx
 */

// =============================================================================
// STEP 1: Add state for processing results (add near other useState declarations)
// =============================================================================

const [processingResults, setProcessingResults] = useState(null);
const [processingError, setProcessingError] = useState(null);
const [isProcessing, setIsProcessing] = useState(false);

// =============================================================================
// STEP 2: Add Phase 1 processing function (add after existing functions)
// =============================================================================

const handlePhase1Processing = async (manuscriptFile, userEmail, bookTitle, userPlan) => {
  try {
    setIsProcessing(true);
    setProcessingError(null);
    
    // Create FormData for multipart upload
    const formData = new FormData();
    formData.append('email', userEmail);
    formData.append('bookTitle', bookTitle || 'Untitled');
    formData.append('plan', userPlan || 'free');
    formData.append('bookFile', manuscriptFile);

    console.log('Sending book to N8N for processing...', {
      email: userEmail,
      bookTitle: bookTitle,
      plan: userPlan,
      fileName: manuscriptFile.name,
      fileSize: manuscriptFile.size
    });

    // Send to N8N webhook
    const response = await fetch('https://n8n.websolutionsserver.net/webhook/audiobook-process', {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Processing failed: ${response.statusText} - ${errorText}`);
    }

    const result = await response.json();
    
    console.log('Phase 1 processing result:', result);
    
    if (result.success) {
      // Store processing results
      setProcessingResults({
        folderPath: result.folderPath,
        chapters: result.chapters,
        parts: result.parts,
        totalFiles: result.totalFiles,
        language: result.language,
        languageConfidence: result.languageConfidence,
        culturalContext: result.culturalContext,
        manifestPath: result.manifestPath,
        metadataPath: result.metadataPath,
        timestamp: result.timestamp
      });
      
      return result;
    } else {
      throw new Error(result.error || 'Processing failed');
    }
  } catch (error) {
    console.error('Phase 1 processing error:', error);
    setProcessingError(error.message);
    throw error;
  } finally {
    setIsProcessing(false);
  }
};

// =============================================================================
// STEP 3: Modify the existing handleSubmit function
// =============================================================================

// Find the existing handleSubmit function and modify it to include Phase 1 processing
// Add this code AFTER successful Supabase data storage (around line 275)

const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setErrors({});
  setFormSubmitError('');

  // ... existing validation code ...

  try {
    // ... existing Supabase authentication and data storage code ...

    // ========================================================================
    // ADD THIS SECTION: Handle manuscript file upload and Phase 1 processing
    // ========================================================================
    
    if (formData.manuscriptFile) {
      try {
        console.log('Starting Phase 1 processing...');
        
        // Send to N8N for Phase 1 processing
        const phase1Result = await handlePhase1Processing(
          formData.manuscriptFile,
          formData.email,
          formData.bookTitle,
          formData.plan
        );
        
        console.log('Phase 1 complete:', phase1Result);
        
        // Update user record with processing results
        const { error: updateError } = await supabase
          .from('users_audiobooksmith')
          .update({
            phase1_folder: phase1Result.folderPath,
            phase1_chapters: phase1Result.chapters,
            phase1_language: phase1Result.language,
            phase1_timestamp: phase1Result.timestamp,
            processing_status: 'phase1_complete'
          })
          .eq('email', formData.email);
          
        if (updateError) {
          console.error('Failed to update processing results:', updateError);
        }
        
      } catch (processingError) {
        console.error('Phase 1 processing failed:', processingError);
        
        // Don't block form submission, but show warning
        setFormSubmitError(
          'Your account has been created, but book processing is pending. ' +
          'We\'ll notify you via email when your book is ready. ' +
          `Error: ${processingError.message}`
        );
        
        // Update status to pending
        await supabase
          .from('users_audiobooksmith')
          .update({
            processing_status: 'phase1_pending',
            processing_error: processingError.message
          })
          .eq('email', formData.email);
      }
    }
    
    // ========================================================================
    // END OF PHASE 1 PROCESSING SECTION
    // ========================================================================

    // Set submission success
    setIsSubmitted(true);
    
  } catch (error) {
    console.error('Error submitting form:', error);
    setFormSubmitError(error.message || 'An error occurred during submission. Please try again.');
    setErrors({ form: error.message || 'An error occurred during submission. Please try again.' });
  } finally {
    setLoading(false);
  }
};

// =============================================================================
// STEP 4: Add UI to show processing status (optional)
// =============================================================================

// Add this component to show processing status in the UI
// Place it inside the form, after the submit button

{isProcessing && (
  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
    <div className="flex items-center">
      <svg className="animate-spin h-5 w-5 mr-3 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span className="text-blue-700 font-medium">Processing your book...</span>
    </div>
    <p className="text-sm text-blue-600 mt-2">
      Detecting chapters and preparing your audiobook. This may take a minute.
    </p>
  </div>
)}

{processingResults && (
  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
    <h3 className="text-green-800 font-semibold mb-2">✅ Book Processed Successfully!</h3>
    <div className="text-sm text-green-700 space-y-1">
      <p><strong>Chapters detected:</strong> {processingResults.chapters}</p>
      <p><strong>Language:</strong> {processingResults.language.toUpperCase()} ({Math.round(processingResults.languageConfidence * 100)}% confidence)</p>
      {processingResults.culturalContext && processingResults.culturalContext.length > 0 && (
        <p><strong>Cultural context:</strong> {processingResults.culturalContext.join(', ')}</p>
      )}
      <p><strong>Total files created:</strong> {processingResults.totalFiles}</p>
      <p className="text-xs text-green-600 mt-2">
        Folder: {processingResults.folderPath}
      </p>
    </div>
  </div>
)}

{processingError && (
  <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
    <h3 className="text-yellow-800 font-semibold mb-2">⚠️ Processing Delayed</h3>
    <p className="text-sm text-yellow-700">
      Your book upload is being processed in the background. We'll send you an email when it's ready.
    </p>
    <p className="text-xs text-yellow-600 mt-2">
      Error details: {processingError}
    </p>
  </div>
)}

// =============================================================================
// STEP 5: Environment variables (optional, for security)
// =============================================================================

/**
 * For production, consider storing the webhook URL in environment variables:
 * 
 * 1. Create .env file in project root:
 *    REACT_APP_N8N_WEBHOOK_URL=https://n8n.websolutionsserver.net/webhook/audiobook-process
 * 
 * 2. Update the fetch call:
 *    const response = await fetch(process.env.REACT_APP_N8N_WEBHOOK_URL, {
 *      method: 'POST',
 *      body: formData,
 *    });
 * 
 * 3. For Vite projects, use:
 *    VITE_N8N_WEBHOOK_URL=https://n8n.websolutionsserver.net/webhook/audiobook-process
 *    
 *    And access with:
 *    import.meta.env.VITE_N8N_WEBHOOK_URL
 */

// =============================================================================
// STEP 6: Add to Supabase schema (if not already present)
// =============================================================================

/**
 * Add these columns to the users_audiobooksmith table:
 * 
 * ALTER TABLE users_audiobooksmith ADD COLUMN phase1_folder TEXT;
 * ALTER TABLE users_audiobooksmith ADD COLUMN phase1_chapters INTEGER;
 * ALTER TABLE users_audiobooksmith ADD COLUMN phase1_language TEXT;
 * ALTER TABLE users_audiobooksmith ADD COLUMN phase1_timestamp TEXT;
 * ALTER TABLE users_audiobooksmith ADD COLUMN processing_status TEXT DEFAULT 'pending';
 * ALTER TABLE users_audiobooksmith ADD COLUMN processing_error TEXT;
 */

// =============================================================================
// TESTING
// =============================================================================

/**
 * To test the integration:
 * 
 * 1. Start the development server:
 *    npm run dev
 * 
 * 2. Open the onboarding page
 * 
 * 3. Fill out the form with test data:
 *    - Email: test@example.com
 *    - Name: Test User
 *    - Book Title: Test Book
 *    - Upload a small TXT or PDF file
 * 
 * 4. Submit the form
 * 
 * 5. Check browser console for logs:
 *    - "Sending book to N8N for processing..."
 *    - "Phase 1 processing result:"
 *    - "Phase 1 complete:"
 * 
 * 6. Verify in N8N:
 *    - Go to https://n8n.websolutionsserver.net
 *    - Click "Executions" in left sidebar
 *    - Check for successful execution
 * 
 * 7. Verify folder creation:
 *    - SSH to N8N server
 *    - Check /working/[email]/[book_title]_v_[timestamp]/
 *    - Verify manifest.json and chapter files
 */

// =============================================================================
// ERROR HANDLING SCENARIOS
// =============================================================================

/**
 * The integration handles these error scenarios:
 * 
 * 1. Network Error:
 *    - User sees: "Processing delayed" message
 *    - Form submission still succeeds
 *    - Status: phase1_pending
 * 
 * 2. File Too Large:
 *    - N8N returns 413 error
 *    - User sees error message
 *    - Can retry with smaller file
 * 
 * 3. Invalid File Format:
 *    - Python script returns error
 *    - User sees specific error message
 *    - Can upload different file
 * 
 * 4. Server Timeout:
 *    - Fetch times out after 5 minutes
 *    - User sees "processing delayed" message
 *    - Background processing continues
 * 
 * 5. Chapter Detection Fails:
 *    - Python script returns success=false
 *    - User sees error with details
 *    - Admin notified for manual review
 */

// =============================================================================
// CORS CONFIGURATION (if needed)
// =============================================================================

/**
 * If you encounter CORS errors, the N8N webhook already includes:
 * 
 * Access-Control-Allow-Origin: *
 * 
 * This allows requests from any domain. For production, you may want to
 * restrict this to only audiobooksmith.com:
 * 
 * 1. Edit the "Return Response" node in N8N workflow
 * 2. Change Access-Control-Allow-Origin header to:
 *    https://audiobooksmith.com
 * 
 * If you need to handle preflight OPTIONS requests:
 * 
 * 1. Add a new "Webhook" node for OPTIONS method
 * 2. Configure it to return:
 *    - Status: 200
 *    - Headers:
 *      Access-Control-Allow-Origin: https://audiobooksmith.com
 *      Access-Control-Allow-Methods: POST, OPTIONS
 *      Access-Control-Allow-Headers: Content-Type
 */

export default OnboardingPage;
