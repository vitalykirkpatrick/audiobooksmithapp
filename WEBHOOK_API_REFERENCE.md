# AudiobookSmith Webhook API Reference

## Base URL

```
https://audiobooksmith.app/webhook
```

## Endpoints

### 1. Health Check

**GET** `/webhook/health`

Check if the webhook server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "AudiobookSmith Webhook Server v3",
  "timestamp": "2025-12-08T07:48:44.313225",
  "version": "3.0.0"
}
```

---

### 2. Process Audiobook

**POST** `/webhook/audiobook-process`

Upload and process a book file for audiobook conversion.

**Request:**

Content-Type: `multipart/form-data`

**Required Fields:**
- `email` (string) - User's email address
- `name` (string) - User's full name
- `bookTitle` (string) - Title of the book
- `bookFile` (file) - The book file to process

**Optional Fields:**
- `genre` (string) - Book genre (Fiction, Non-Fiction, etc.)

**File Requirements:**
- **Allowed formats**: PDF, EPUB, MOBI, TXT, DOCX, DOC, RTF, ODT
- **Maximum size**: 100 MB
- **Encoding**: UTF-8 (for text files)

**Example Request (JavaScript):**
```javascript
const formData = new FormData();
formData.append('email', 'user@example.com');
formData.append('name', 'John Doe');
formData.append('bookTitle', 'My Amazing Book');
formData.append('bookFile', fileInput.files[0]);
formData.append('genre', 'Fiction');

const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

**Example Request (cURL):**
```bash
curl -X POST https://audiobooksmith.app/webhook/audiobook-process \
  -F "email=user@example.com" \
  -F "name=John Doe" \
  -F "bookTitle=My Amazing Book" \
  -F "genre=Fiction" \
  -F "bookFile=@/path/to/book.pdf"
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "projectId": "30561c306a88",
  "folderUrl": "/files/view/30561c306a88",
  "downloadUrl": "/files/download/30561c306a88/all",
  "analysis": {
    "bookInfo": {
      "title": "My Amazing Book",
      "author": "Unknown",
      "genre": "Fiction",
      "language": "English",
      "pages": 26,
      "wordCount": 6662,
      "characterCount": 36894,
      "estimatedReadingTime": "0h 33m",
      "estimatedAudioLength": "0h 44m"
    },
    "structure": {
      "totalChapters": 12,
      "chaptersDetected": [
        "Chapter 1: Introduction",
        "Chapter 2: The Journey Begins"
      ],
      "sectionsDetected": [
        "Prologue",
        "Epilogue",
        "About The Author"
      ],
      "hasTableOfContents": true
    },
    "content": {
      "averageWordLength": 4.79,
      "averageSentenceLength": 18.4,
      "paragraphs": 45
    },
    "production": {
      "voiceType": "Neutral, Professional",
      "tone": "Neutral, Balanced",
      "accent": "American, Neutral",
      "specialNotes": "Book contains 12 chapters. Recommended for neutral, balanced narration style."
    },
    "processing": {
      "status": "completed",
      "extractionMethod": "pdf",
      "extractionQuality": "good",
      "needsOCR": false,
      "processingTime": "0.07s"
    }
  },
  "files": {
    "manifest": "/files/download/30561c306a88/manifest.json",
    "analysis": "/files/download/30561c306a88/analysis.json",
    "extractedText": "/files/download/30561c306a88/text/extracted_text.txt",
    "originalFile": "/files/download/30561c306a88/My_Amazing_Book.pdf"
  },
  "message": "Book processed successfully!"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "No file uploaded",
  "message": "Failed to process audiobook"
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Failed to extract text from file",
  "message": "Failed to process audiobook"
}
```

---

### 3. View Project Files

**GET** `/files/view/<project_id>`

View the analysis results and download files for a processed book.

**Parameters:**
- `project_id` (string) - The unique project identifier returned from the process endpoint

**Example:**
```
https://audiobooksmith.app/files/view/30561c306a88
```

**Response:**

Returns an HTML page displaying:
- Book information (title, word count, pages, etc.)
- Structure analysis (chapters, sections)
- Production recommendations (voice type, tone, accent)
- Downloadable files with links

---

### 4. Download File

**GET** `/files/download/<project_id>/<filename>`

Download a specific file from a processed project.

**Parameters:**
- `project_id` (string) - The unique project identifier
- `filename` (string) - The file path relative to the project directory

**Examples:**
```
https://audiobooksmith.app/files/download/30561c306a88/manifest.json
https://audiobooksmith.app/files/download/30561c306a88/analysis.json
https://audiobooksmith.app/files/download/30561c306a88/text/extracted_text.txt
https://audiobooksmith.app/files/download/30561c306a88/My_Book.pdf
```

**Response:**

Returns the file as a download attachment.

---

## Data Types

### BookInfo
```typescript
interface BookInfo {
  title: string;              // Book title
  author: string;             // Author name (or "Unknown")
  genre: string;              // Book genre
  language: string;           // Detected language
  pages: number;              // Estimated page count
  wordCount: number;          // Total word count
  characterCount: number;     // Total character count
  estimatedReadingTime: string;  // e.g., "2h 15m"
  estimatedAudioLength: string;  // e.g., "3h 0m"
}
```

### Structure
```typescript
interface Structure {
  totalChapters: number;          // Number of chapters detected
  chaptersDetected: string[];     // List of chapter titles
  sectionsDetected: string[];     // List of special sections
  hasTableOfContents: boolean;    // Whether TOC was found
}
```

### Content
```typescript
interface Content {
  averageWordLength: number;      // Average characters per word
  averageSentenceLength: number;  // Average words per sentence
  paragraphs: number;             // Total paragraph count
}
```

### Production
```typescript
interface Production {
  voiceType: string;      // Recommended voice type
  tone: string;           // Recommended tone
  accent: string;         // Recommended accent
  specialNotes: string;   // Additional recommendations
}
```

### Processing
```typescript
interface Processing {
  status: string;             // "completed", "failed", etc.
  extractionMethod: string;   // "pdf", "txt", "docx", etc.
  extractionQuality: string;  // "good", "poor"
  needsOCR: boolean;          // Whether OCR is needed
  processingTime: string;     // e.g., "0.07s"
}
```

---

## Error Codes

| Status Code | Error | Description |
|------------|-------|-------------|
| 400 | No file uploaded | The `bookFile` field is missing |
| 400 | Empty filename | The uploaded file has no name |
| 400 | Invalid file type | File type is not supported |
| 404 | Project not found | The specified project ID doesn't exist |
| 404 | File not found | The specified file doesn't exist in the project |
| 500 | Processing error | An error occurred during book processing |

---

## Rate Limits

Currently, there are no rate limits enforced. However, please be considerate:
- Maximum file size: 100 MB
- Recommended: No more than 10 requests per minute per user

---

## File Processing Times

Typical processing times by file size:

| File Size | Processing Time |
|-----------|----------------|
| < 1 MB | < 1 second |
| 1-10 MB | 1-2 seconds |
| 10-50 MB | 2-5 seconds |
| 50-100 MB | 5-10 seconds |

*Note: Times may vary based on file format and server load.*

---

## Supported File Formats

### PDF (.pdf)
- ✅ Text-based PDFs (preferred)
- ⚠️ Scanned PDFs (may require OCR, not currently supported)
- Best for: Published books, manuscripts

### EPUB (.epub)
- ✅ Standard EPUB format
- ✅ EPUB3 format
- Best for: E-books, digital publications

### Word Documents (.docx, .doc)
- ✅ Microsoft Word 2007+ (.docx)
- ✅ Microsoft Word 97-2003 (.doc)
- Best for: Manuscripts, drafts

### Plain Text (.txt)
- ✅ UTF-8 encoding (preferred)
- ✅ ASCII encoding
- Best for: Simple manuscripts, drafts

### Other Formats
- ✅ MOBI (.mobi) - Kindle format
- ✅ Rich Text Format (.rtf)
- ✅ OpenDocument Text (.odt)

---

## Best Practices

### 1. File Preparation
- Use text-based PDFs (not scanned images)
- Ensure proper encoding (UTF-8 for text files)
- Include chapter markers in your document
- Use standard formatting (headings, paragraphs)

### 2. Error Handling
```javascript
try {
  const response = await fetch(url, { method: 'POST', body: formData });
  const result = await response.json();
  
  if (!response.ok || !result.success) {
    throw new Error(result.error || 'Processing failed');
  }
  
  // Handle success
  handleSuccess(result);
  
} catch (error) {
  // Handle error
  if (error.message.includes('Network')) {
    showError('Connection failed. Please check your internet.');
  } else {
    showError(error.message);
  }
}
```

### 3. User Feedback
- Show upload progress
- Display processing status
- Provide clear error messages
- Allow users to download results

---

## Examples

### React Component Example
```jsx
import { useState } from 'react';

function BookUploadForm() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('email', e.target.email.value);
    formData.append('name', e.target.name.value);
    formData.append('bookTitle', e.target.bookTitle.value);
    formData.append('bookFile', file);
    
    try {
      const response = await fetch(
        'https://audiobooksmith.app/webhook/audiobook-process',
        { method: 'POST', body: formData }
      );
      
      const data = await response.json();
      
      if (data.success) {
        setResult(data);
        // Redirect to results
        window.location.href = `https://audiobooksmith.app${data.folderUrl}`;
      } else {
        throw new Error(data.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input name="email" type="email" required />
      <input name="name" type="text" required />
      <input name="bookTitle" type="text" required />
      <input 
        type="file" 
        onChange={(e) => setFile(e.target.files[0])}
        accept=".pdf,.epub,.docx,.txt"
        required 
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Upload Book'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}
```

### Python Example
```python
import requests

def process_book(email, name, book_title, file_path):
    url = 'https://audiobooksmith.app/webhook/audiobook-process'
    
    with open(file_path, 'rb') as f:
        files = {'bookFile': f}
        data = {
            'email': email,
            'name': name,
            'bookTitle': book_title
        }
        
        response = requests.post(url, files=files, data=data)
        result = response.json()
        
        if result['success']:
            print(f"Success! Project ID: {result['projectId']}")
            print(f"View results: https://audiobooksmith.app{result['folderUrl']}")
            return result
        else:
            print(f"Error: {result['error']}")
            return None

# Usage
result = process_book(
    email='user@example.com',
    name='John Doe',
    book_title='My Book',
    file_path='/path/to/book.pdf'
)
```

---

## Changelog

### Version 3.0.0 (Current)
- ✅ Comprehensive book analysis
- ✅ Chapter and section detection
- ✅ Production recommendations
- ✅ Beautiful results display page
- ✅ Multiple file format support
- ✅ Improved error handling

### Version 2.0.0
- Basic file processing
- Simple analysis
- JSON response

### Version 1.0.0
- Initial release
- File upload only

---

## Support

For issues or questions:
- Check server health: `https://audiobooksmith.app/webhook/health`
- Review error messages in the response
- Verify file format and size requirements
- Test with a small text file first

---

**Last Updated**: December 8, 2025  
**API Version**: 3.0.0  
**Server**: https://audiobooksmith.app
