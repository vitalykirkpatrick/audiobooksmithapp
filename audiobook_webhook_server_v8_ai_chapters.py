"""
AudiobookSmith Webhook Server v8 - AI Chapter Detection
- Handles book uploads and processing
- AI-based chapter detection
- Better error handling and timeouts
- Supports all ebook formats
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import shutil
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = "/root/audiobook_uploads"
WORKING_DIR = "/root/audiobook_working"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORKING_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf', 'epub', 'docx', 'doc', 'txt', 'rtf', 
    'mobi', 'azw', 'azw3', 'odt', 'pages'
}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AudiobookSmith Webhook Server v8",
        "timestamp": datetime.now().isoformat(),
        "upload_folder": UPLOAD_FOLDER,
        "working_dir": WORKING_DIR
    })


@app.route('/webhook/upload', methods=['POST'])
def upload_book():
    """Handle book upload and processing"""
    print("\n" + "="*70)
    print("📥 NEW UPLOAD REQUEST")
    print("="*70)
    
    try:
        # Get form data
        name = request.form.get('name', 'Unknown')
        email = request.form.get('email', 'unknown@example.com')
        
        print(f"👤 User: {name} ({email})")
        
        # Check if file is present
        if 'bookFile' not in request.files:
            print("❌ No file in request")
            return jsonify({
                "success": False,
                "message": "No file uploaded. Please select a book file."
            }), 400
        
        file = request.files['bookFile']
        
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({
                "success": False,
                "message": "No file selected. Please choose a book file."
            }), 400
        
        if not allowed_file(file.filename):
            print(f"❌ Invalid file type: {file.filename}")
            return jsonify({
                "success": False,
                "message": f"File type not supported. Please upload: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            }), 400
        
        print(f"📚 File: {file.filename}")
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        file.save(file_path)
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"💾 Saved: {safe_filename} ({file_size_mb:.2f} MB)")
        
        # Process the book
        print("🔄 Starting processing...")
        
        from audiobook_processor_v9_ai_chapters import AIBookProcessor
        
        processor = AIBookProcessor(
            book_path=file_path,
            project_id=safe_filename,
            user_email=email,
            working_dir=WORKING_DIR,
            enable_narration_prep=True,  # Enabled
            enable_voice_recommendations=True  # Enabled
        )
        
        result = processor.process_book()
        
        if not result.get("success"):
            print(f"❌ Processing failed: {result.get('error')}")
            return jsonify({
                "success": False,
                "message": result.get("error", "Processing failed"),
                "suggestions": result.get("suggestions", [])
            }), 400
        
        # Build response
        session_id = result["session_id"]
        metadata = result["metadata"]
        chapters = result["chapters"]
        validation = result["validation"]
        
        print(f"✅ Processing complete: {len(chapters)} chapters")
        
        response_data = {
            "success": True,
            "message": "Book processed successfully!",
            "payload": {
                "analysis": {
                    "sessionId": session_id,
                    "bookMetadata": {
                        "title": metadata.get("title", "Unknown Title"),
                        "author": metadata.get("author", "Unknown Author"),
                        "genre": metadata.get("genre", "Unknown"),
                        "wordCount": validation.get("word_count", 0),
                        "estimatedPages": validation.get("estimated_pages", 0)
                    },
                    "chapterStructure": {
                        "totalChapters": len(chapters),
                        "chapters": [
                            {
                                "number": ch["number"],
                                "title": ch["title"],
                                "wordCount": ch["word_count"]
                            }
                            for ch in chapters
                        ]
                    },
                    "folderStructure": {
                        "sessionDirectory": result["session_dir"],
                        "folders": list(result["folder_structure"].keys())
                    }
                }
            }
        }
        
        print("="*70 + "\n")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        print(f"\n❌ ERROR: {error_msg}")
        print(f"📋 Traceback:\n{error_trace}")
        print("="*70 + "\n")
        
        return jsonify({
            "success": False,
            "message": f"Server error: {error_msg}",
            "error": error_msg
        }), 500


@app.route('/files/view/<session_id>', methods=['GET'])
def view_session(session_id):
    """View processing session results"""
    try:
        # Find session directory
        for root, dirs, files in os.walk(WORKING_DIR):
            # Check if this root path ends with the session_id and contains processing_sessions
            if root.endswith(session_id) and "processing_sessions" in root:
                # root already points to the session directory
                report_path = os.path.join(root, "10_delivery_package", "processing_report.json")
                if os.path.exists(report_path):
                    import json
                    from datetime import datetime
                    
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                    
                    # Load HTML template (v2 with advanced features)
                    template_path = os.path.join(os.path.dirname(__file__), "analysis_results_template_v2.html")
                    with open(template_path, 'r') as f:
                        html_template = f.read()
                    
                    # Extract data from report
                    metadata = report.get('metadata', {})
                    validation = report.get('validation', {})
                    chapters = report.get('chapters', [])
                    narration_chapters = report.get('narration_chapters', [])
                    voice_recommendations = report.get('voice_recommendations', {})
                    estimated_duration = report.get('estimated_duration', 'N/A')
                    folder_structure = report.get('folder_structure', {})
                    
                    # Format chapters HTML (with duration if available)
                    chapters_html = ""
                    for i, chapter in enumerate(chapters):
                        chapter_num = chapter.get('number', '00')
                        is_epilogue = chapter_num == '900'
                        badge_class = 'epilogue' if is_epilogue else ''
                        
                        # Get duration from narration chapters if available
                        duration_html = ""
                        if narration_chapters and i < len(narration_chapters):
                            duration_min = narration_chapters[i].get('estimated_duration_minutes', 0)
                            duration_html = f'<span class="chapter-duration">~{int(duration_min)} min</span>'
                        
                        chapters_html += f'''
                        <div class="chapter-item">
                            <span class="chapter-number {badge_class}">{chapter_num}</span>
                            <span class="chapter-title">{chapter.get('title', 'Untitled')}</span>
                            <span class="chapter-words">{chapter.get('word_count', 0):,} words{duration_html}</span>
                        </div>
                        '''
                    
                    # Format voice recommendations HTML
                    voice_section_html = ""
                    if voice_recommendations and 'error' not in voice_recommendations:
                        language = voice_recommendations.get('detected_language', 'English')
                        primary = voice_recommendations.get('primary_voice', {})
                        alternatives = voice_recommendations.get('alternative_voices', [])
                        narration_style = voice_recommendations.get('narration_style', 'conversational')
                        
                        voice_section_html = f'''
                        <div class="card">
                            <h2><span class="icon">🎤</span> Voice Recommendations</h2>
                            <p style="color: #666; margin-bottom: 20px;">AI-recommended narrator voices for your {language} audiobook</p>
                            
                            <h3>Primary Recommendation</h3>
                            <div class="voice-card">
                                <h4>🎯 Best Match</h4>
                                <div class="voice-details">
                                    <div class="voice-detail"><strong>Type:</strong> {primary.get('type', 'N/A').title()}</div>
                                    <div class="voice-detail"><strong>Age:</strong> {primary.get('age_range', 'N/A').title()}</div>
                                    <div class="voice-detail"><strong>Tone:</strong> {primary.get('tone', 'N/A').title()}</div>
                                    <div class="voice-detail"><strong>Accent:</strong> {primary.get('accent', 'N/A')}</div>
                                </div>
                                <div class="voice-reasoning">
                                    💡 {primary.get('reasoning', 'No reasoning provided')}
                                </div>
                            </div>
                            
                            <h3>Alternative Options</h3>
                        '''
                        
                        for i, alt in enumerate(alternatives[:2], 1):
                            voice_section_html += f'''
                            <div class="voice-card">
                                <h4>Option {i}</h4>
                                <div class="voice-details">
                                    <div class="voice-detail"><strong>Type:</strong> {alt.get('type', 'N/A').title()}</div>
                                    <div class="voice-detail"><strong>Age:</strong> {alt.get('age_range', 'N/A').title()}</div>
                                    <div class="voice-detail"><strong>Tone:</strong> {alt.get('tone', 'N/A').title()}</div>
                                    <div class="voice-detail"><strong>Accent:</strong> {alt.get('accent', 'N/A')}</div>
                                </div>
                                <div class="voice-reasoning">
                                    💡 {alt.get('reasoning', 'No reasoning provided')}
                                </div>
                            </div>
                            '''
                        
                        voice_section_html += f'''
                            <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin-top: 15px;">
                                <strong>📖 Recommended Narration Style:</strong> {narration_style.title()}
                            </div>
                        </div>
                        '''
                    
                    # Format folders HTML
                    folders_html = ""
                    folder_names = [
                        "01_raw_text",
                        "02_metadata",
                        "03_chapter_analysis",
                        "04_cleaned_text",
                        "05_chapter_splits",
                        "06_narration_prep",
                        "07_voice_samples",
                        "08_audio_ready",
                        "09_quality_reports",
                        "10_delivery_package"
                    ]
                    for folder in folder_names:
                        folders_html += f'<div class="folder-item">{folder}</div>\n'
                    
                    # Format processing date
                    try:
                        date_obj = datetime.strptime(session_id, "%Y-%m-%dT%H-%M-%S")
                        processing_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
                    except:
                        processing_date = session_id
                    
                    # Replace template variables
                    html = html_template.replace('{{session_id}}', session_id)
                    html = html.replace('{{processing_date}}', processing_date)
                    html = html.replace('{{language}}', voice_recommendations.get('detected_language', 'English'))
                    html = html.replace('{{title}}', metadata.get('title', 'Unknown Title'))
                    html = html.replace('{{author}}', metadata.get('author', 'Unknown Author'))
                    html = html.replace('{{genre}}', metadata.get('genre', 'Unknown'))
                    html = html.replace('{{chapter_count}}', str(len(chapters)))
                    html = html.replace('{{word_count}}', f"{validation.get('word_count', 0):,}")
                    html = html.replace('{{page_count}}', str(validation.get('estimated_pages', 0)))
                    html = html.replace('{{character_count}}', f"{validation.get('character_count', 0):,}")
                    html = html.replace('{{estimated_duration}}', estimated_duration)
                    html = html.replace('{{chapters}}', chapters_html)
                    html = html.replace('{{voice_recommendations_section}}', voice_section_html)
                    html = html.replace('{{folders}}', folders_html)
                    
                    return html
        
        return jsonify({
            "success": False,
            "message": "Session not found"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/files/download/<session_id>/<folder>/<filename>', methods=['GET'])
def download_file(session_id, folder, filename):
    """Download a file from a processing session"""
    try:
        # Find session directory
        for root, dirs, files in os.walk(WORKING_DIR):
            if session_id in root and folder in root:
                folder_path = os.path.join(root, folder)
                if os.path.exists(os.path.join(folder_path, filename)):
                    return send_from_directory(folder_path, filename, as_attachment=True)
        
        return jsonify({
            "success": False,
            "message": "File not found"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("AudiobookSmith Webhook Server v8 - AI Chapter Detection")
    print("="*70)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Working directory: {WORKING_DIR}")
    print(f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
