// Custom Database Client - Updated for AudiobookSmith Webhook Integration
class DatabaseClient {
  constructor() {
    // Use environment variable or default to empty (no backend needed for book upload)
    this.baseURL = process.env.REACT_APP_API_URL || '';
    this.webhookURL = process.env.REACT_APP_WEBHOOK_URL || 'https://audiobooksmith.app';
    this.authToken = localStorage.getItem('auth_token');
  }

  async makeRequest(endpoint, options = {}) {
    // If no baseURL is set, return mock data or skip the request
    if (!this.baseURL) {
      console.warn(`API call to ${endpoint} skipped - no backend configured`);
      return { error: 'Backend not configured' };
    }

    const url = `${this.baseURL}/api${endpoint}`;
    const headers = { ...options.headers };
    
    // Only add content-type if not FormData (browser sets it automatically for FormData)
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const config = { ...options, headers };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'API request failed');
      return data;
    } catch (error) {
      console.error('API Error:', error);
      return { error: error.message };
    }
  }

  // Auth Methods (currently not implemented - return mock data)
  async signUp(userData) {
    console.warn('SignUp not implemented - using mock mode');
    return { success: false, error: 'Authentication not configured' };
  }

  async signIn(credentials) {
    console.warn('SignIn not implemented - using mock mode');
    return { success: false, error: 'Authentication not configured' };
  }

  // --- Public Demo Methods ---
  
  async getDemoSample(voiceId, textHash) {
    // Return empty/mock data for demos since backend isn't available
    console.warn('Demo samples not available - no backend configured');
    return { error: 'Demo backend not configured' };
  }

  async uploadDemo(file, voiceId, textHash) {
    console.warn('Demo upload not available - no backend configured');
    return { error: 'Demo backend not configured' };
  }

  // --- File Upload Method - UPDATED TO USE WEBHOOK ---
  
  async uploadFile(file, email, name, bookTitle, genre) {
    try {
      console.log('Uploading file to webhook server...');
      
      const formData = new FormData();
      formData.append('email', email);
      formData.append('name', name);
      formData.append('bookTitle', bookTitle);
      formData.append('bookFile', file);
      if (genre) formData.append('genre', genre);
      
      // Send to webhook server
      const response = await fetch(`${this.webhookURL}/webhook/audiobook-process`, {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (!response.ok || !result.success) {
        throw new Error(result.error || result.message || 'Upload failed');
      }
      
      console.log('Upload successful:', result);
      return result;
      
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  }
  
  async upsert(table, data, conflictColumn) {
    console.warn('Database upsert not available - no backend configured');
    return { error: 'Database backend not configured' };
  }
}

const database = new DatabaseClient();
export default database;
