#!/usr/bin/env python3.11
"""
Standalone Flask webhook server for AudiobookSmith cross-server integration
This server receives file uploads from audiobooksmith.com and processes them
"""

from flask import Flask, request, jsonify
import os
import subprocess
import json
from datetime import datetime
import traceback

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "/home/ubuntu/audiobook_uploads"
PROCESSOR_SCRIPT = "/home/ubuntu/audiobook_processor.py"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/webhook/audiobook-process', methods=['POST'])
def process_audiobook():
    """
    Webhook endpoint that receives audiobook files and processes them
    
    Expected form data:
    - email: user's email address
    - bookTitle: title of the book
    - plan: subscription plan (free/premium)
    - bookFile: uploaded PDF/TXT file
    """
    try:
        # Log the request
        print(f"\n{'='*60}")
        print(f"📥 Received webhook request at {datetime.now().isoformat()}")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Form fields: {list(request.form.keys())}")
        print(f"   Files: {list(request.files.keys())}")
        
        # Extract form data
        email = request.form.get('email', 'unknown@example.com')
        book_title = request.form.get('bookTitle', 'Untitled')
        plan = request.form.get('plan', 'free')
        
        print(f"\n📋 Form Data:")
        print(f"   Email: {email}")
        print(f"   Book Title: {book_title}")
        print(f"   Plan: {plan}")
        
        # Get uploaded file
        if 'bookFile' not in request.files:
            print("❌ No file uploaded")
            return jsonify({
                "success": False,
                "error": "No file uploaded",
                "message": "Please upload a book file (PDF or TXT)"
            }), 400
        
        file = request.files['bookFile']
        
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({
                "success": False,
                "error": "Empty filename",
                "message": "The uploaded file has no name"
            }), 400
        
        # Save the uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_email = email.replace('@', '_at_').replace('.', '_')
        filename = f"{safe_email}_{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        print(f"\n💾 File saved:")
        print(f"   Filename: {filename}")
        print(f"   Path: {filepath}")
        print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            os.remove(filepath)
            print(f"❌ File too large: {file_size / 1024 / 1024:.2f} MB")
            return jsonify({
                "success": False,
                "error": "File too large",
                "message": f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size (100 MB)"
            }), 400
        
        # Process the audiobook using the Python script
        print(f"\n🔄 Processing audiobook...")
        print(f"   Script: {PROCESSOR_SCRIPT}")
        print(f"   Command: python3.11 {PROCESSOR_SCRIPT} {email} '{book_title}' {plan} {filepath}")
        
        try:
            result = subprocess.run(
                ['python3.11', PROCESSOR_SCRIPT, email, book_title, plan, filepath],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            print(f"\n📤 Script output:")
            print(f"   Return code: {result.returncode}")
            if result.stdout:
                print(f"   STDOUT:\n{result.stdout}")
            if result.stderr:
                print(f"   STDERR:\n{result.stderr}")
            
            if result.returncode == 0:
                # Parse the JSON output from the script
                try:
                    output_data = json.loads(result.stdout)
                    print(f"\n✅ Processing successful!")
                    print(f"   Output: {json.dumps(output_data, indent=2)}")
                    
                    return jsonify({
                        "success": True,
                        "message": "Audiobook processed successfully",
                        "data": output_data
                    }), 200
                except json.JSONDecodeError:
                    # If output is not JSON, return it as plain text
                    print(f"\n✅ Processing successful (non-JSON output)")
                    return jsonify({
                        "success": True,
                        "message": "Audiobook processed successfully",
                        "output": result.stdout
                    }), 200
            else:
                print(f"\n❌ Processing failed with return code {result.returncode}")
                return jsonify({
                    "success": False,
                    "error": "Processing failed",
                    "message": result.stderr or "Unknown error occurred",
                    "return_code": result.returncode
                }), 500
                
        except subprocess.TimeoutExpired:
            print(f"\n❌ Processing timed out after 5 minutes")
            return jsonify({
                "success": False,
                "error": "Processing timeout",
                "message": "The audiobook processing took too long (>5 minutes)"
            }), 500
        
    except Exception as e:
        print(f"\n❌ Unexpected error:")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AudiobookSmith Webhook Server",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return jsonify({
        "service": "AudiobookSmith Webhook Server",
        "version": "1.0.0",
        "endpoints": {
            "/webhook/audiobook-process": "POST - Process audiobook files",
            "/health": "GET - Health check",
            "/": "GET - API information"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AudiobookSmith Webhook Server")
    print("="*60)
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"🐍 Processor script: {PROCESSOR_SCRIPT}")
    print(f"📊 Max file size: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB")
    print(f"\n🌐 Starting server on http://0.0.0.0:5001")
    print(f"📡 Webhook endpoint: http://0.0.0.0:5001/webhook/audiobook-process")
    print("="*60 + "\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)
