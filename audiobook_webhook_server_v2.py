#!/usr/bin/env python3
"""
AudiobookSmith Webhook Server v2 - Simplified Testing Version
Handles book uploads and provides file browser for testing
"""

import os
import sys
import json
import uuid
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, send_from_directory, abort

# Configuration
UPLOAD_DIR = Path("/root/audiobook_webhook/uploads")
PROCESSED_DIR = Path("/root/audiobook_webhook/processed")
LOG_FILE = Path("/root/audiobook_webhook/logs/webhook_server.log")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.pdf', '.epub', '.mobi', '.txt', '.docx', '.doc'}

# Create directories
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# File browser HTML template
FILE_BROWSER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AudiobookSmith - File Browser</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .metadata {
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 1px solid #e9ecef;
        }
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .metadata-item {
            display: flex;
            flex-direction: column;
        }
        .metadata-label {
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .metadata-value {
            font-size: 14px;
            color: #212529;
            font-weight: 500;
        }
        .content {
            padding: 30px;
        }
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 20px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            font-size: 14px;
        }
        .breadcrumb a {
            color: #667eea;
            text-decoration: none;
        }
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        .breadcrumb-separator {
            color: #6c757d;
        }
        .file-list {
            list-style: none;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            transition: background 0.2s;
        }
        .file-item:hover {
            background: #f8f9fa;
        }
        .file-item:last-child {
            border-bottom: none;
        }
        .file-icon {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #667eea;
            color: white;
            border-radius: 8px;
            margin-right: 15px;
            font-size: 18px;
        }
        .file-icon.folder {
            background: #ffc107;
        }
        .file-info {
            flex: 1;
        }
        .file-name {
            font-size: 15px;
            color: #212529;
            margin-bottom: 4px;
        }
        .file-name a {
            color: #212529;
            text-decoration: none;
        }
        .file-name a:hover {
            color: #667eea;
        }
        .file-meta {
            font-size: 13px;
            color: #6c757d;
        }
        .file-actions {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            border: none;
            cursor: pointer;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }
        .empty-state svg {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        .footer {
            background: #f8f9fa;
            padding: 20px 30px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            font-size: 13px;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 AudiobookSmith File Browser</h1>
            <p>Project ID: {{ project_id }}</p>
        </div>
        
        {% if metadata %}
        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Email</div>
                    <div class="metadata-value">{{ metadata.email }}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Name</div>
                    <div class="metadata-value">{{ metadata.name }}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Uploaded File</div>
                    <div class="metadata-value">{{ metadata.uploadedFile }}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Processed At</div>
                    <div class="metadata-value">{{ metadata.processedAt }}</div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <div class="content">
            <div class="breadcrumb">
                <a href="/files/view/{{ project_id }}">🏠 Home</a>
                {% if path %}
                <span class="breadcrumb-separator">›</span>
                {% for part in path.split('/') %}
                    {% if part %}
                    <a href="/files/view/{{ project_id }}/{{ path.split('/')[:loop.index]|join('/') }}">{{ part }}</a>
                    {% if not loop.last %}<span class="breadcrumb-separator">›</span>{% endif %}
                    {% endif %}
                {% endfor %}
                {% endif %}
            </div>
            
            {% if files %}
            <ul class="file-list">
                {% for file in files %}
                <li class="file-item">
                    <div class="file-icon {% if file.is_dir %}folder{% endif %}">
                        {% if file.is_dir %}📁{% else %}📄{% endif %}
                    </div>
                    <div class="file-info">
                        <div class="file-name">
                            {% if file.is_dir %}
                            <a href="/files/view/{{ project_id }}/{{ file.path }}">{{ file.name }}</a>
                            {% else %}
                            {{ file.name }}
                            {% endif %}
                        </div>
                        <div class="file-meta">
                            {{ file.size }} • Modified {{ file.modified }}
                        </div>
                    </div>
                    <div class="file-actions">
                        {% if not file.is_dir %}
                        <a href="/files/download/{{ project_id }}/{{ file.path }}" class="btn btn-primary" download>
                            ⬇️ Download
                        </a>
                        {% endif %}
                    </div>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                </svg>
                <p>No files found in this directory</p>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            AudiobookSmith © 2025 • Testing Environment
        </div>
    </div>
</body>
</html>
'''

def format_size(size):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_file_info(path):
    """Get file information"""
    stat = path.stat()
    return {
        'name': path.name,
        'path': str(path.relative_to(PROCESSED_DIR)).replace('\\', '/'),
        'is_dir': path.is_dir(),
        'size': format_size(stat.st_size) if not path.is_dir() else '-',
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AudiobookSmith Webhook Server v2',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/webhook/audiobook-process', methods=['POST'])
def process_audiobook():
    """Process audiobook upload"""
    try:
        # Validate request
        if 'bookFile' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded',
                'message': 'Please upload a book file'
            }), 400
        
        # Get form data
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        book_file = request.files['bookFile']
        
        # Validate required fields
        if not email or not name:
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Please provide email and name'
            }), 400
        
        # Validate file
        if book_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        file_ext = Path(book_file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return jsonify({
                'success': False,
                'error': 'Invalid file format',
                'message': f'Please upload a valid book file ({", ".join(ALLOWED_EXTENSIONS)})'
            }), 400
        
        # Generate project ID
        project_id = str(uuid.uuid4())[:8]
        
        # Create project directories
        project_dir = PROCESSED_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        upload_path = project_dir / f"original{file_ext}"
        book_file.save(str(upload_path))
        
        logger.info(f"File uploaded: {upload_path} ({format_size(upload_path.stat().st_size)})")
        
        # Save metadata
        metadata = {
            'email': email,
            'name': name,
            'uploadedFile': book_file.filename,
            'originalExtension': file_ext,
            'processedAt': datetime.utcnow().isoformat(),
            'projectId': project_id
        }
        
        metadata_path = project_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Call processor script (if exists)
        processor_script = Path("/root/audiobook_webhook/audiobook_processor.py")
        if processor_script.exists():
            try:
                result = subprocess.run(
                    ['python3', str(processor_script), str(upload_path), str(project_dir)],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                logger.info(f"Processor output: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Processor errors: {result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning("Processor script timed out")
            except Exception as e:
                logger.error(f"Processor error: {e}")
        
        # Generate folder URL
        folder_url = f"https://audiobooksmith.app/files/view/{project_id}"
        
        # Return success response
        response = {
            'success': True,
            'message': 'Book processed successfully!',
            'projectId': project_id,
            'folderUrl': folder_url,
            'metadata': metadata
        }
        
        logger.info(f"Processing complete: {project_id}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'message': str(e)
        }), 500

@app.route('/files/view/<project_id>', methods=['GET'])
@app.route('/files/view/<project_id>/<path:subpath>', methods=['GET'])
def view_files(project_id, subpath=''):
    """View project files"""
    try:
        # Get project directory
        project_dir = PROCESSED_DIR / project_id
        
        if not project_dir.exists():
            abort(404, description="Project not found")
        
        # Get target directory
        if subpath:
            target_dir = project_dir / subpath
        else:
            target_dir = project_dir
        
        if not target_dir.exists() or not target_dir.is_dir():
            abort(404, description="Directory not found")
        
        # Load metadata
        metadata_path = project_dir / 'metadata.json'
        metadata = None
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # List files
        files = []
        for item in sorted(target_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            if item.name.startswith('.'):
                continue
            files.append(get_file_info(item))
        
        # Render template
        return render_template_string(
            FILE_BROWSER_TEMPLATE,
            project_id=project_id,
            path=subpath,
            files=files,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"View error: {e}", exc_info=True)
        abort(500, description=str(e))

@app.route('/files/download/<project_id>/<path:filepath>', methods=['GET'])
def download_file(project_id, filepath):
    """Download a file"""
    try:
        project_dir = PROCESSED_DIR / project_id
        file_path = project_dir / filepath
        
        if not file_path.exists() or not file_path.is_file():
            abort(404, description="File not found")
        
        # Security check: ensure file is within project directory
        if not str(file_path.resolve()).startswith(str(project_dir.resolve())):
            abort(403, description="Access denied")
        
        return send_from_directory(
            file_path.parent,
            file_path.name,
            as_attachment=True
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        abort(500, description=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting AudiobookSmith Webhook Server v2 on port {port}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"Processed directory: {PROCESSED_DIR}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
