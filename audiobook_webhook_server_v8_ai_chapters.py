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
            enable_narration_prep=False,  # Disabled for now
            enable_voice_recommendations=False  # Disabled for now
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
            if session_id in root and "processing_sessions" in root:
                session_dir = os.path.join(root, session_id)
                if os.path.exists(session_dir):
                    report_path = os.path.join(session_dir, "10_delivery_package", "processing_report.json")
                    if os.path.exists(report_path):
                        import json
                        with open(report_path, 'r') as f:
                            report = json.load(f)
                        return jsonify({
                            "success": True,
                            "session_id": session_id,
                            "report": report
                        })
        
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
