// ============================================================================
// HANDLESUBMIT FUNCTION WITH COMPREHENSIVE DEBUGGING
// Replace your existing handleSubmit with this version to diagnose the issue
// ============================================================================

const handleSubmit = async (e) => {
  e.preventDefault();
  setFormSubmitError(null);
  
  // DEBUG: Log that form submission started
  console.log('=== FORM SUBMISSION STARTED ===');
  console.log('Current formData:', {
    name: formData.name,
    email: formData.email,
    bookTitle: formData.bookTitle,
    manuscriptFile: formData.manuscriptFile ? {
      name: formData.manuscriptFile.name,
      size: formData.manuscriptFile.size,
      type: formData.manuscriptFile.type
    } : null
  });
  
  // Check if upgrade is needed (for free plan word count limits)
  if (requiresUpgrade) {
    console.log('DEBUG: Upgrade required, redirecting...');
    handleUpgrade();
    return;
  }
  
  // Validate form
  console.log('DEBUG: Validating form...');
  if (!validateForm()) {
    console.log('DEBUG: Validation failed');
    const firstErrorField = Object.keys(errors)[0];
    const errorElement = document.getElementById(firstErrorField);
    if (errorElement) {
      errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    return;
  }
  console.log('DEBUG: Validation passed');
  
  try {
    setLoading(true);
    console.log('DEBUG: Loading state set to true');
    
    // Create FormData for multipart/form-data upload
    const webhookData = new FormData();
    
    // Required fields
    webhookData.append('email', formData.email);
    webhookData.append('name', formData.name);
    webhookData.append('bookTitle', formData.bookTitle);
    webhookData.append('bookFile', formData.manuscriptFile);
    
    // Optional fields
    if (formData.bookGenre && formData.bookGenre.trim() !== '') {
      webhookData.append('genre', formData.bookGenre);
    }
    
    // DEBUG: Log FormData contents
    console.log('DEBUG: FormData created with fields:');
    for (let [key, value] of webhookData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes)`);
      } else {
        console.log(`  ${key}: ${value}`);
      }
    }
    
    // Define the webhook URL
    const webhookUrl = 'https://audiobooksmith.app/webhook/audiobook-process';
    console.log('DEBUG: Webhook URL:', webhookUrl);
    
    // Send to webhook server
    console.log('DEBUG: Sending POST request to webhook...');
    console.log('DEBUG: Request details:', {
      url: webhookUrl,
      method: 'POST',
      body: 'FormData with file'
    });
    
    let response;
    try {
      response = await fetch(webhookUrl, {
        method: 'POST',
        body: webhookData
        // Note: Don't set Content-Type header - browser will set it automatically with boundary
      });
      
      console.log('DEBUG: Response received');
      console.log('DEBUG: Response status:', response.status);
      console.log('DEBUG: Response statusText:', response.statusText);
      console.log('DEBUG: Response ok:', response.ok);
      console.log('DEBUG: Response headers:', {
        'content-type': response.headers.get('content-type'),
        'access-control-allow-origin': response.headers.get('access-control-allow-origin')
      });
      
    } catch (fetchError) {
      console.error('DEBUG: Fetch failed with error:', fetchError);
      console.error('DEBUG: Error name:', fetchError.name);
      console.error('DEBUG: Error message:', fetchError.message);
      console.error('DEBUG: Error stack:', fetchError.stack);
      throw fetchError;
    }
    
    // Parse response
    console.log('DEBUG: Parsing JSON response...');
    let result;
    try {
      const responseText = await response.text();
      console.log('DEBUG: Raw response text:', responseText.substring(0, 500)); // First 500 chars
      result = JSON.parse(responseText);
      console.log('DEBUG: Parsed JSON result:', result);
    } catch (parseError) {
      console.error('DEBUG: Failed to parse JSON:', parseError);
      throw new Error(`Invalid JSON response from server: ${parseError.message}`);
    }
    
    // Check if request was successful
    if (!response.ok || !result.success) {
      console.error('DEBUG: Request failed');
      console.error('DEBUG: Response not ok or result.success is false');
      console.error('DEBUG: result.error:', result.error);
      console.error('DEBUG: result.message:', result.message);
      throw new Error(result.error || result.message || `Server error: ${response.status}`);
    }
    
    // Success!
    console.log('=== WEBHOOK PROCESSING SUCCESSFUL ===');
    console.log('Project ID:', result.projectId);
    console.log('Folder URL:', result.folderUrl);
    console.log('Analysis:', result.analysis);
    
    // Construct redirect URL
    const redirectUrl = `https://audiobooksmith.app${result.folderUrl}`;
    console.log('DEBUG: Redirecting to:', redirectUrl);
    
    // Redirect to the results page
    window.location.href = redirectUrl;
    
  } catch (error) {
    console.error('=== ERROR OCCURRED ===');
    console.error('Error object:', error);
    console.error('Error name:', error.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    
    // Handle specific error types with user-friendly messages
    let errorMessage = 'An error occurred while processing your book. Please try again.';
    
    if (error.message.includes('Failed to fetch')) {
      errorMessage = 'Network error: Could not connect to the server. Please check your internet connection and try again.';
      console.error('DEBUG: This is a CORS or network connectivity issue');
      console.error('DEBUG: Possible causes:');
      console.error('  1. CORS not configured on server');
      console.error('  2. Server is down');
      console.error('  3. Network firewall blocking request');
      console.error('  4. Invalid SSL certificate');
    } else if (error.message.includes('NetworkError')) {
      errorMessage = 'Network error: Unable to reach the server. Please try again.';
    } else if (error.message.includes('Invalid file type')) {
      errorMessage = 'Please upload a valid book file (PDF, EPUB, DOCX, or TXT).';
    } else if (error.message.includes('File too large') || error.message.includes('size')) {
      errorMessage = 'File size must be less than 100MB. Please upload a smaller file.';
    } else if (error.message.includes('No file uploaded')) {
      errorMessage = 'Please select a book file to upload.';
    } else if (error.message.includes('Invalid JSON')) {
      errorMessage = 'Server returned invalid response. Please try again.';
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    console.error('DEBUG: Setting error message:', errorMessage);
    setFormSubmitError(errorMessage);
    setErrors({ form: errorMessage });
    
  } finally {
    console.log('DEBUG: Setting loading to false');
    setLoading(false);
    console.log('=== FORM SUBMISSION ENDED ===');
  }
};

// ============================================================================
// ADDITIONAL DEBUGGING: Test webhook connectivity on page load
// ============================================================================
// Add this useEffect to your component to test connectivity when page loads

/*
useEffect(() => {
  // Test webhook server connectivity on component mount
  const testWebhookConnectivity = async () => {
    console.log('=== TESTING WEBHOOK CONNECTIVITY ===');
    try {
      const response = await fetch('https://audiobooksmith.app/webhook/health');
      const data = await response.json();
      console.log('✅ Webhook server is reachable');
      console.log('Health check response:', data);
    } catch (error) {
      console.error('❌ Webhook server is NOT reachable');
      console.error('Error:', error.message);
    }
  };
  
  testWebhookConnectivity();
}, []);
*/

// ============================================================================
// HOW TO USE THIS DEBUG VERSION
// ============================================================================
/*
1. Replace your existing handleSubmit function with this one

2. Add the useEffect hook above to test connectivity on page load

3. Open browser DevTools (F12) and go to Console tab

4. Try submitting the form

5. Watch the console output - it will show:
   - When form submission starts
   - Form data being sent
   - Webhook URL being used
   - Request details
   - Response status and headers
   - Any errors with detailed information

6. Share the console output with me so I can diagnose the exact issue

EXPECTED CONSOLE OUTPUT (if working):
=== FORM SUBMISSION STARTED ===
Current formData: {...}
DEBUG: Validating form...
DEBUG: Validation passed
DEBUG: Loading state set to true
DEBUG: FormData created with fields: ...
DEBUG: Webhook URL: https://audiobooksmith.app/webhook/audiobook-process
DEBUG: Sending POST request to webhook...
DEBUG: Response received
DEBUG: Response status: 200
DEBUG: Response ok: true
DEBUG: Parsing JSON response...
DEBUG: Parsed JSON result: {...}
=== WEBHOOK PROCESSING SUCCESSFUL ===
DEBUG: Redirecting to: https://audiobooksmith.app/files/view/...

EXPECTED CONSOLE OUTPUT (if CORS issue):
=== FORM SUBMISSION STARTED ===
...
DEBUG: Sending POST request to webhook...
DEBUG: Fetch failed with error: TypeError: Failed to fetch
DEBUG: Error name: TypeError
DEBUG: Error message: Failed to fetch
=== ERROR OCCURRED ===
DEBUG: This is a CORS or network connectivity issue

EXPECTED CONSOLE OUTPUT (if server down):
=== FORM SUBMISSION STARTED ===
...
DEBUG: Sending POST request to webhook...
DEBUG: Fetch failed with error: TypeError: NetworkError when attempting to fetch resource
*/
