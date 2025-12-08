#!/usr/bin/env python3
"""
AudiobookSmith Webhook Server v4 - AI-Powered with Slack Notifications
Simplified form (name, email, file, comments) with AI-powered book analysis and Slack alerts
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import sys
import json
import uuid
import shutil
import requests
from datetime import datetime
import traceback

# Add the processor to path
sys.path.insert(0, '/root/audiobook_webhook')

# Import the AI processor
from audiobook_processor_v4_ai import AIBookProcessor

app = Flask(__name__)
CORS(app, resources={
    r"/webhook/*": {
        "origins": ["https://audiobooksmith.com", "http://localhost:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuration
WORKING_DIR = "/root/audiobook_working"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Slack Configuration
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')  # Set via environment variable
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', 'general')  # Default to 'general' if not set

# Ensure working directory exists
os.makedirs(WORKING_DIR, exist_ok=True)


def send_slack_notification(message, color="good", fields=None):
    """Send notification to Slack channel"""
    try:
        payload = {
            "channel": f"#{SLACK_CHANNEL}",
            "username": "AudiobookSmith Bot",
            "icon_emoji": ":books:",
            "attachments": [{
                "color": color,
                "text": message,
                "fields": fields or [],
                "footer": "AudiobookSmith",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Slack notification sent: {message[:50]}...")
        else:
            print(f"⚠️ Slack notification failed: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Slack notification error: {e}")


@app.route('/webhook/audiobook-process', methods=['POST', 'OPTIONS'])
def process_audiobook():
    """
    Simplified webhook endpoint - only requires: name, email, file, comments (optional)
    AI automatically detects: title, author, genre, chapters, etc.
    """
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        print(f"\n{'='*70}")
        print(f"📥 NEW REQUEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        # Extract simplified form data
        name = request.form.get('name', 'Anonymous')
        email = request.form.get('email', 'unknown@example.com')
        comments = request.form.get('comments', '')
        
        print(f"\n👤 User Information:")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        if comments:
            print(f"   Comments: {comments}")
        
        # Send Slack notification - Upload started
        send_slack_notification(
            f"📤 New book upload started",
            color="warning",
            fields=[
                {"title": "User", "value": name, "short": True},
                {"title": "Email", "value": email, "short": True},
                {"title": "Status", "value": "Processing...", "short": False}
            ]
        )
        
        # Get uploaded file
        if 'bookFile' not in request.files:
            print("❌ No file uploaded")
            send_slack_notification(
                f"❌ Upload failed - No file provided by {name}",
                color="danger"
            )
            return jsonify({
                "success": False,
                "error": "No file uploaded",
                "message": "Please upload a book file (PDF)"
            }), 400
        
        file = request.files['bookFile']
        
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({
                "success": False,
                "error": "Empty filename"
            }), 400
        
        # Generate unique project ID
        project_id = str(uuid.uuid4()).replace('-', '')[:16]
        project_dir = os.path.join(WORKING_DIR, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        print(f"\n📁 Project Setup:")
        print(f"   Project ID: {project_id}")
        print(f"   Directory: {project_dir}")
        
        # Save uploaded file
        original_filename = file.filename
        pdf_path = os.path.join(project_dir, original_filename)
        file.save(pdf_path)
        
        file_size = os.path.getsize(pdf_path)
        print(f"\n💾 File Saved:")
        print(f"   Filename: {original_filename}")
        print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            shutil.rmtree(project_dir)
            print(f"❌ File too large")
            send_slack_notification(
                f"❌ Upload failed - File too large ({file_size / 1024 / 1024:.1f} MB) from {name}",
                color="danger"
            )
            return jsonify({
                "success": False,
                "error": "File too large",
                "message": f"Maximum file size is 100 MB"
            }), 400
        
        # Process with AI
        print(f"\n🤖 Starting AI Processing...")
        print(f"{'='*70}")
        
        try:
            processor = AIBookProcessor(pdf_path, project_id, WORKING_DIR)
            analysis = processor.generate_analysis()
            
            if not analysis:
                raise Exception("Processing failed - no analysis generated")
            
            # Save user metadata
            metadata = {
                "user": {
                    "name": name,
                    "email": email,
                    "comments": comments
                },
                "upload": {
                    "filename": original_filename,
                    "size": file_size,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            metadata_file = os.path.join(project_dir, "user_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create manifest
            manifest = {
                "projectId": project_id,
                "created": datetime.now().isoformat(),
                "user": name,
                "email": email,
                "files": {
                    "original": original_filename,
                    "analysis": "analysis.json",
                    "extracted_text": "text/extracted_text.txt",
                    "user_metadata": "user_metadata.json"
                }
            }
            
            manifest_file = os.path.join(project_dir, "manifest.json")
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"\n{'='*70}")
            print(f"✅ PROCESSING COMPLETE")
            print(f"{'='*70}")
            
            # Send Slack notification - Success
            folder_url = f"https://audiobooksmith.app/files/view/{project_id}"
            
            send_slack_notification(
                f"✅ Book processed successfully!",
                color="good",
                fields=[
                    {"title": "User", "value": name, "short": True},
                    {"title": "Email", "value": email, "short": True},
                    {"title": "Book Title", "value": analysis['bookInfo']['title'], "short": True},
                    {"title": "Author", "value": analysis['bookInfo']['author'], "short": True},
                    {"title": "Genre", "value": f"{analysis['bookInfo']['genre']} ({analysis['bookInfo']['type']})", "short": True},
                    {"title": "Chapters", "value": str(analysis['structure']['total_chapters']), "short": True},
                    {"title": "Word Count", "value": f"{analysis['metrics']['word_count']:,}", "short": True},
                    {"title": "Pages", "value": str(analysis['metrics']['page_count']), "short": True},
                    {"title": "View Results", "value": f"<{folder_url}|Click here>", "short": False}
                ]
            )
            
            # Return success with folder URL
            return jsonify({
                "success": True,
                "projectId": project_id,
                "folderUrl": folder_url,
                "message": "Book processed successfully",
                "analysis": {
                    "title": analysis['bookInfo']['title'],
                    "author": analysis['bookInfo']['author'],
                    "genre": analysis['bookInfo']['genre'],
                    "type": analysis['bookInfo']['type'],
                    "chapters": analysis['structure']['total_chapters'],
                    "wordCount": analysis['metrics']['word_count'],
                    "pages": analysis['metrics']['page_count']
                }
            }), 200
            
        except Exception as e:
            print(f"\n❌ Processing Error:")
            print(traceback.format_exc())
            
            # Send Slack notification - Error
            send_slack_notification(
                f"❌ Processing failed for {name}",
                color="danger",
                fields=[
                    {"title": "Error", "value": str(e), "short": False},
                    {"title": "File", "value": original_filename, "short": True}
                ]
            )
            
            # Clean up failed project
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            
            return jsonify({
                "success": False,
                "error": "Processing failed",
                "message": str(e)
            }), 500
        
    except Exception as e:
        print(f"\n❌ Server Error:")
        print(traceback.format_exc())
        
        send_slack_notification(
            f"❌ Server error occurred",
            color="danger",
            fields=[
                {"title": "Error", "value": str(e), "short": False}
            ]
        )
        
        return jsonify({
            "success": False,
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/files/view/<project_id>', methods=['GET'])
def view_analysis(project_id):
    """Serve the analysis results page with enhanced chapter display"""
    
    try:
        project_dir = os.path.join(WORKING_DIR, project_id)
        analysis_file = os.path.join(project_dir, "analysis.json")
        
        if not os.path.exists(analysis_file):
            return f"<h1>Project not found</h1><p>Project ID: {project_id}</p>", 404
        
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
        
        # Get all files in project
        files = []
        for filename in os.listdir(project_dir):
            filepath = os.path.join(project_dir, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                files.append({
                    "name": filename,
                    "path": filename,
                    "size": size,
                    "size_display": format_file_size(size)
                })
        
        # Check for text files
        text_dir = os.path.join(project_dir, "text")
        if os.path.exists(text_dir):
            for filename in os.listdir(text_dir):
                filepath = os.path.join(text_dir, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    files.append({
                        "name": filename,
                        "path": f"text/{filename}",
                        "size": size,
                        "size_display": format_file_size(size)
                    })
        
        # Render enhanced HTML template
        return render_analysis_page(analysis, files, project_id)
        
    except Exception as e:
        print(f"Error viewing analysis: {e}")
        traceback.print_exc()
        return f"<h1>Error loading analysis</h1><p>{str(e)}</p>", 500


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1024 / 1024:.1f} MB"


def render_analysis_page(analysis, files, project_id):
    """Render the enhanced analysis page with all chapters"""
    
    book_info = analysis.get('bookInfo', {})
    metrics = analysis.get('metrics', {})
    structure = analysis.get('structure', {})
    recommendations = analysis.get('recommendations', {})
    
    # Build chapters HTML
    chapters_html = ""
    chapters = structure.get('chapters', [])
    parts = structure.get('parts', [])
    
    if parts:
        # Organized by parts
        for part in parts:
            chapters_html += f'<div class="part-section">'
            chapters_html += f'<h3>Part {part["number"]}: {part["title"]}</h3>'
            chapters_html += f'<div class="chapters-in-part">'
            
            for chapter in chapters:
                if chapter['number'] in part.get('chapters', []):
                    chapters_html += f'<div class="chapter-item">'
                    chapters_html += f'<span class="chapter-number">Chapter {chapter["number"]}</span>'
                    chapters_html += f'<span class="chapter-title">{chapter["title"]}</span>'
                    chapters_html += f'</div>'
            
            chapters_html += f'</div></div>'
    elif chapters:
        # Just chapters, no parts
        for chapter in chapters:
            chapters_html += f'<div class="chapter-item">'
            chapters_html += f'<span class="chapter-number">Chapter {chapter["number"]}</span>'
            chapters_html += f'<span class="chapter-title">{chapter["title"]}</span>'
            chapters_html += f'</div>'
    else:
        chapters_html = '<p style="color: #666;">No chapters detected</p>'
    
    # Build files HTML
    files_html = ""
    for file in files:
        files_html += f'''
        <div class="file-item">
            <div>
                <strong>{file["name"]}</strong><br>
                <span style="color: #666; font-size: 0.9em;">{file["path"]} • {file["size_display"]}</span>
            </div>
            <a href="#" class="download-btn" onclick="alert('Download functionality coming soon'); return false;">Download</a>
        </div>
        '''
    
    # Build themes HTML
    themes_html = ""
    for theme in book_info.get('themes', []):
        themes_html += f'<span class="theme-badge">{theme}</span>'
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>AudiobookSmith - {book_info.get('title', 'Book Analysis')}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            padding: 20px; 
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ 
            background: white; 
            border-radius: 15px; 
            padding: 30px; 
            margin-bottom: 20px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
        }}
        .header h1 {{ color: #667eea; font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ color: #666; font-size: 1.1em; }}
        .card {{ 
            background: white; 
            border-radius: 15px; 
            padding: 25px; 
            margin-bottom: 20px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
        }}
        .card h2 {{ 
            color: #333; 
            margin-bottom: 15px; 
            font-size: 1.8em; 
            border-bottom: 3px solid #667eea; 
            padding-bottom: 10px; 
        }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-top: 20px; 
        }}
        .stat-item {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 10px; 
            border-left: 4px solid #667eea; 
        }}
        .stat-label {{ color: #666; font-size: 0.9em; margin-bottom: 5px; }}
        .stat-value {{ color: #333; font-size: 1.5em; font-weight: bold; word-wrap: break-word; }}
        .success-badge {{ 
            background: #10b981; 
            color: white; 
            padding: 5px 15px; 
            border-radius: 20px; 
            font-size: 0.9em; 
            display: inline-block; 
            margin-bottom: 15px; 
        }}
        .chapter-list {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin-top: 15px; 
            max-height: 500px;
            overflow-y: auto;
        }}
        .chapter-item {{ 
            padding: 12px; 
            margin: 8px 0;
            background: white;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        .chapter-number {{
            font-weight: bold;
            color: #667eea;
            min-width: 100px;
        }}
        .chapter-title {{
            color: #333;
            flex: 1;
        }}
        .part-section {{
            margin: 20px 0;
            padding: 15px;
            background: #e9ecef;
            border-radius: 8px;
        }}
        .part-section h3 {{
            color: #764ba2;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .chapters-in-part {{
            margin-left: 15px;
        }}
        .file-item {{ 
            background: #f8f9fa; 
            padding: 12px 15px; 
            margin: 8px 0; 
            border-radius: 8px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }}
        .file-item:hover {{ background: #e9ecef; }}
        .download-btn {{ 
            background: #667eea; 
            color: white; 
            padding: 8px 20px; 
            border-radius: 6px; 
            text-decoration: none; 
            font-size: 0.9em; 
        }}
        .download-btn:hover {{ background: #5568d3; }}
        .theme-badge {{
            display: inline-block;
            background: #e9ecef;
            padding: 5px 12px;
            border-radius: 15px;
            margin: 5px;
            font-size: 0.9em;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Book Analysis Complete!</h1>
            <p>Your audiobook has been processed and analyzed using AI. Here are the results:</p>
            <div class="success-badge">✓ AI Processing Successful</div>
        </div>
        
        <div class="card">
            <h2>📖 Book Information</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Title</div>
                    <div class="stat-value">{book_info.get('title', 'Unknown')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Author</div>
                    <div class="stat-value">{book_info.get('author', 'Unknown')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Genre</div>
                    <div class="stat-value">{book_info.get('genre', 'Unknown')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Type</div>
                    <div class="stat-value">{book_info.get('type', 'Unknown')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Word Count</div>
                    <div class="stat-value">{metrics.get('word_count', 0):,}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Pages</div>
                    <div class="stat-value">{metrics.get('page_count', 0)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Reading Time</div>
                    <div class="stat-value">{metrics.get('reading_time', 'N/A')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Audio Length</div>
                    <div class="stat-value">{metrics.get('audio_length', 'N/A')}</div>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <div class="stat-label">Themes</div>
                <div>
                    {themes_html if themes_html else '<span style="color: #666;">No themes detected</span>'}
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📑 Structure Analysis</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Total Chapters</div>
                    <div class="stat-value">{structure.get('total_chapters', 0)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Parts/Sections</div>
                    <div class="stat-value">{len(structure.get('parts', []))}</div>
                </div>
            </div>
            
            <div class="chapter-list">
                <h3 style="margin-bottom: 15px; color: #333;">Chapters:</h3>
                {chapters_html}
            </div>
        </div>
        
        <div class="card">
            <h2>🎙️ Production Recommendations</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Voice Type</div>
                    <div class="stat-value" style="font-size: 1.2em;">{recommendations.get('voice_type', 'Neutral')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Tone</div>
                    <div class="stat-value" style="font-size: 1.2em;">{recommendations.get('tone', 'Neutral')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Accent</div>
                    <div class="stat-value" style="font-size: 1.2em;">{recommendations.get('accent', 'Neutral')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Target Audience</div>
                    <div class="stat-value" style="font-size: 1.2em;">{recommendations.get('target_audience', 'General')}</div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                <strong>📝 Special Notes:</strong><br>
                {recommendations.get('special_notes', 'No special notes')}
            </div>
        </div>
        
        <div class="card">
            <h2>📁 Project Files</h2>
            <p style="color: #666; margin-bottom: 15px;">Download your processed files below:</p>
            {files_html}
        </div>
    </div>
</body>
</html>
    '''
    
    return html


@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "service": "AudiobookSmith Webhook Server v4 (AI-Powered + Slack)",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "4.0.0",
        "features": ["AI Chapter Detection", "Auto Genre Classification", "Simplified Form", "Slack Notifications"]
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return "AudiobookSmith Server - Use /webhook endpoints", 200


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 AudiobookSmith Webhook Server v4 (AI-Powered + Slack)")
    print("="*70)
    print(f"📁 Working directory: {WORKING_DIR}")
    print(f"📊 Max file size: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB")
    print(f"🤖 AI Features: Chapter Detection, Genre Classification")
    print(f"📢 Slack Notifications: Enabled")
    print(f"\n🌐 Starting server on http://0.0.0.0:5001")
    print(f"📡 Webhook endpoint: http://0.0.0.0:5001/webhook/audiobook-process")
    print(f"📊 Analysis viewer: http://0.0.0.0:5001/files/view/{{project_id}}")
    print("="*70 + "\n")
    
    # Send startup notification
    send_slack_notification(
        "🚀 AudiobookSmith Webhook Server v4 started successfully",
        color="good",
        fields=[
            {"title": "Version", "value": "4.0.0", "short": True},
            {"title": "Features", "value": "AI + Slack", "short": True}
        ]
    )
    
    app.run(host='0.0.0.0', port=5001, debug=False)
