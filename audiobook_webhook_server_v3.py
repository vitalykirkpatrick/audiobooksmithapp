#!/usr/bin/env python3
"""
AudiobookSmith Webhook Server v3 - With Book Analysis
Receives book uploads, performs comprehensive analysis, and returns detailed results
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os
import json
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess
import re

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/root/audiobook_uploads'
WORKING_FOLDER = '/root/audiobook_working'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'pdf', 'epub', 'mobi', 'txt', 'docx', 'doc', 'rtf', 'odt'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORKING_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """Extract text from various file formats"""
    ext = file_path.rsplit('.', 1)[1].lower()
    
    try:
        if ext == 'pdf':
            # Use pdftotext
            result = subprocess.run(['pdftotext', file_path, '-'], 
                                  capture_output=True, text=True, timeout=60)
            return result.stdout if result.returncode == 0 else ""
        
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif ext in ['docx', 'doc']:
            # Use python-docx if available
            try:
                from docx import Document
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except:
                return ""
        
        elif ext == 'epub':
            # Use ebooklib if available
            try:
                import ebooklib
                from ebooklib import epub
                from bs4 import BeautifulSoup
                
                book = epub.read_epub(file_path)
                text = []
                for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text.append(soup.get_text())
                return '\n'.join(text)
            except:
                return ""
        
        else:
            return ""
    
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def analyze_book_content(text, file_info):
    """Perform comprehensive book analysis"""
    
    # Basic statistics
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    
    # Estimate pages (250 words per page average)
    estimated_pages = max(1, word_count // 250)
    
    # Estimate reading and audio time
    reading_time_minutes = max(1, word_count // 200)  # 200 words per minute
    audio_time_minutes = max(1, word_count // 150)  # 150 words per minute for narration
    
    # Detect chapters
    chapter_pattern = r'(?:Chapter|CHAPTER)\s+(\d+|[IVXLCDM]+)(?:\s*[:\-]\s*(.+))?'
    chapters = re.findall(chapter_pattern, text)
    
    # Detect sections
    sections = []
    section_keywords = ['prologue', 'epilogue', 'introduction', 'preface', 'foreword', 
                       'dedication', 'acknowledgments', 'about the author', 'copyright']
    
    text_lower = text.lower()
    for keyword in section_keywords:
        if keyword in text_lower:
            sections.append(keyword.title())
    
    # Extract potential title and author from first 1000 characters
    first_part = text[:1000]
    lines = [line.strip() for line in first_part.split('\n') if line.strip()]
    
    # Try to find title (usually in first few lines)
    potential_title = file_info.get('original_filename', 'Unknown').rsplit('.', 1)[0]
    if lines:
        # Check if first line looks like a title (short, capitalized)
        if len(lines[0]) < 100 and lines[0].isupper():
            potential_title = lines[0]
    
    # Detect language (simple heuristic)
    common_english_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'that', 'for']
    english_word_count = sum(1 for word in words[:1000] if word.lower() in common_english_words)
    language = "English" if english_word_count > 50 else "Unknown"
    
    # Production recommendations
    avg_word_length = sum(len(word) for word in words[:1000]) / min(len(words), 1000)
    if avg_word_length > 5.5:
        tone = "Formal, Academic"
    elif avg_word_length < 4.5:
        tone = "Conversational, Simple"
    else:
        tone = "Neutral, Balanced"
    
    analysis = {
        "bookInfo": {
            "title": potential_title,
            "author": "Unknown",  # Would need more sophisticated extraction
            "genre": "Unknown",  # Would need AI classification
            "language": language,
            "pages": estimated_pages,
            "wordCount": word_count,
            "characterCount": char_count,
            "estimatedReadingTime": f"{reading_time_minutes // 60}h {reading_time_minutes % 60}m",
            "estimatedAudioLength": f"{audio_time_minutes // 60}h {audio_time_minutes % 60}m"
        },
        "structure": {
            "totalChapters": len(chapters),
            "chaptersDetected": [f"Chapter {ch[0]}: {ch[1]}" if ch[1] else f"Chapter {ch[0]}" for ch in chapters[:10]],
            "sectionsDetected": sections,
            "hasTableOfContents": "contents" in text_lower or "table of contents" in text_lower
        },
        "content": {
            "averageWordLength": round(avg_word_length, 2),
            "averageSentenceLength": round(word_count / max(1, text.count('.')), 1),
            "paragraphs": text.count('\n\n') + 1
        },
        "production": {
            "voiceType": "Neutral, Professional",
            "tone": tone,
            "accent": "American, Neutral",
            "specialNotes": f"Book contains {len(chapters)} chapters. Recommended for {tone.lower()} narration style."
        },
        "processing": {
            "status": "completed",
            "extractionMethod": file_info.get('file_type', 'unknown'),
            "extractionQuality": "good" if word_count > 100 else "poor",
            "needsOCR": word_count < 100,
            "processingTime": file_info.get('processing_time', 'N/A')
        }
    }
    
    return analysis

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        "service": "AudiobookSmith Webhook Server v3",
        "status": "running",
        "version": "3.0.0",
        "endpoints": {
            "health": "/webhook/health",
            "process": "/webhook/audiobook-process",
            "view_files": "/files/view/<project_id>",
            "download": "/files/download/<project_id>/<filename>"
        }
    })

@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AudiobookSmith Webhook Server v3",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    })

@app.route('/webhook/audiobook-process', methods=['POST'])
def process_audiobook():
    """Process uploaded audiobook file"""
    start_time = datetime.now()
    
    try:
        # Validate request
        if 'bookFile' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        file = request.files['bookFile']
        if file.filename == '':
            return jsonify({"success": False, "error": "Empty filename"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400
        
        # Get form data
        email = request.form.get('email', 'unknown@example.com')
        name = request.form.get('name', 'Unknown User')
        book_title = request.form.get('bookTitle', 'Untitled Book')
        genre = request.form.get('genre', 'Unknown')
        
        # Generate project ID
        project_id = hashlib.md5(f"{email}{book_title}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Create project directory
        project_dir = os.path.join(WORKING_FOLDER, project_id)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'text'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'audio'), exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(project_dir, filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Extract text and analyze
        print(f"Extracting text from {filename}...")
        text_content = extract_text_from_file(file_path)
        
        file_info = {
            "original_filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "processing_time": f"{(datetime.now() - start_time).total_seconds():.2f}s"
        }
        
        print(f"Analyzing book content...")
        analysis = analyze_book_content(text_content, file_info)
        
        # Update analysis with user-provided data
        if book_title and book_title != 'Untitled Book':
            analysis['bookInfo']['title'] = book_title
        if genre and genre != 'Unknown':
            analysis['bookInfo']['genre'] = genre
        
        # Save analysis to file
        analysis_path = os.path.join(project_dir, 'analysis.json')
        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Save extracted text
        text_path = os.path.join(project_dir, 'text', 'extracted_text.txt')
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        # Create manifest
        manifest = {
            "projectId": project_id,
            "email": email,
            "name": name,
            "uploadDate": datetime.now().isoformat(),
            "originalFile": filename,
            "fileSize": file_size,
            "analysis": analysis
        }
        
        manifest_path = os.path.join(project_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Build response
        response = {
            "success": True,
            "projectId": project_id,
            "folderUrl": f"/files/view/{project_id}",
            "downloadUrl": f"/files/download/{project_id}/all",
            "analysis": analysis,
            "files": {
                "manifest": f"/files/download/{project_id}/manifest.json",
                "analysis": f"/files/download/{project_id}/analysis.json",
                "extractedText": f"/files/download/{project_id}/text/extracted_text.txt",
                "originalFile": f"/files/download/{project_id}/{filename}"
            },
            "message": "Book processed successfully!"
        }
        
        print(f"✅ Project {project_id} processed successfully")
        return jsonify(response), 200
    
    except Exception as e:
        print(f"❌ Error processing audiobook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to process audiobook"
        }), 500

@app.route('/files/view/<project_id>')
def view_files(project_id):
    """View project files in a web interface"""
    project_dir = os.path.join(WORKING_FOLDER, project_id)
    
    if not os.path.exists(project_dir):
        return "Project not found", 404
    
    # Load analysis
    analysis_path = os.path.join(project_dir, 'analysis.json')
    analysis = {}
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r') as f:
            analysis = json.load(f)
    
    # Get file list
    files = []
    for root, dirs, filenames in os.walk(project_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, project_dir)
            file_size = os.path.getsize(file_path)
            files.append({
                "name": filename,
                "path": rel_path,
                "size": f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB",
                "download_url": f"/files/download/{project_id}/{rel_path}"
            })
    
    # Render HTML page
    html = render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>AudiobookSmith - Book Analysis Results</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; border-radius: 15px; padding: 30px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .header h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #666; font-size: 1.1em; }
        .card { background: white; border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .card h2 { color: #333; margin-bottom: 15px; font-size: 1.8em; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-item { background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #667eea; }
        .stat-label { color: #666; font-size: 0.9em; margin-bottom: 5px; }
        .stat-value { color: #333; font-size: 1.5em; font-weight: bold; }
        .file-list { list-style: none; }
        .file-item { background: #f8f9fa; padding: 12px 15px; margin: 8px 0; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .file-item:hover { background: #e9ecef; }
        .download-btn { background: #667eea; color: white; padding: 8px 20px; border-radius: 6px; text-decoration: none; font-size: 0.9em; }
        .download-btn:hover { background: #5568d3; }
        .success-badge { background: #10b981; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; display: inline-block; margin-bottom: 15px; }
        .chapter-list { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px; }
        .chapter-item { padding: 8px 0; border-bottom: 1px solid #dee2e6; }
        .chapter-item:last-child { border-bottom: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Book Analysis Complete!</h1>
            <p>Your audiobook has been processed and analyzed. Here are the results:</p>
            <div class="success-badge">✓ Processing Successful</div>
        </div>
        
        <div class="card">
            <h2>📖 Book Information</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Title</div>
                    <div class="stat-value">{{ analysis.bookInfo.title }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Word Count</div>
                    <div class="stat-value">{{ "{:,}".format(analysis.bookInfo.wordCount) }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Pages</div>
                    <div class="stat-value">{{ analysis.bookInfo.pages }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Reading Time</div>
                    <div class="stat-value">{{ analysis.bookInfo.estimatedReadingTime }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Audio Length</div>
                    <div class="stat-value">{{ analysis.bookInfo.estimatedAudioLength }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Language</div>
                    <div class="stat-value">{{ analysis.bookInfo.language }}</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📑 Structure Analysis</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Total Chapters</div>
                    <div class="stat-value">{{ analysis.structure.totalChapters }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Sections Detected</div>
                    <div class="stat-value">{{ analysis.structure.sectionsDetected|length }}</div>
                </div>
            </div>
            {% if analysis.structure.chaptersDetected %}
            <div class="chapter-list">
                <strong>Chapters Found:</strong>
                {% for chapter in analysis.structure.chaptersDetected %}
                <div class="chapter-item">{{ chapter }}</div>
                {% endfor %}
            </div>
            {% endif %}
            {% if analysis.structure.sectionsDetected %}
            <div class="chapter-list" style="margin-top: 15px;">
                <strong>Sections Found:</strong>
                {% for section in analysis.structure.sectionsDetected %}
                <div class="chapter-item">{{ section }}</div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>🎙️ Production Recommendations</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Voice Type</div>
                    <div class="stat-value" style="font-size: 1.2em;">{{ analysis.production.voiceType }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Tone</div>
                    <div class="stat-value" style="font-size: 1.2em;">{{ analysis.production.tone }}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Accent</div>
                    <div class="stat-value" style="font-size: 1.2em;">{{ analysis.production.accent }}</div>
                </div>
            </div>
            <div style="margin-top: 15px; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <strong>📝 Special Notes:</strong><br>
                {{ analysis.production.specialNotes }}
            </div>
        </div>
        
        <div class="card">
            <h2>📁 Project Files</h2>
            <p style="color: #666; margin-bottom: 15px;">Download your processed files below:</p>
            <ul class="file-list">
                {% for file in files %}
                <li class="file-item">
                    <div>
                        <strong>{{ file.name }}</strong><br>
                        <small style="color: #666;">{{ file.path }} • {{ file.size }}</small>
                    </div>
                    <a href="{{ file.download_url }}" class="download-btn" download>Download</a>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
    """, analysis=analysis, files=files, project_id=project_id)
    
    return html

@app.route('/files/download/<project_id>/<path:filename>')
def download_file(project_id, filename):
    """Download a specific file from project"""
    project_dir = os.path.join(WORKING_FOLDER, project_id)
    
    if not os.path.exists(project_dir):
        return "Project not found", 404
    
    file_path = os.path.join(project_dir, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    
    directory = os.path.dirname(file_path)
    filename_only = os.path.basename(file_path)
    
    return send_from_directory(directory, filename_only, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"""
╔════════════════════════════════════════════════════════════╗
║  AudiobookSmith Webhook Server v3 Starting...             ║
╚════════════════════════════════════════════════════════════╝

📍 Server running on port {port}
📁 Upload folder: {UPLOAD_FOLDER}
📁 Working folder: {WORKING_FOLDER}
🔧 Max file size: {MAX_FILE_SIZE / (1024*1024):.0f}MB
✅ Ready to process audiobooks!

Endpoints:
  • Health: http://localhost:{port}/webhook/health
  • Process: http://localhost:{port}/webhook/audiobook-process
  • View: http://localhost:{port}/files/view/<project_id>
    """)
    
    app.run(host='0.0.0.0', port=port, debug=False)
