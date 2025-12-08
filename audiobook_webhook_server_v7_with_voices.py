"""
AudiobookSmith Webhook Server v7 - With Voice Selection
- All v6 features (validation + folder structure)
- Voice recommendation integration
- Voice sample serving
- Voice selection endpoint
"""

from flask import Flask, request, jsonify, send_file, render_template_string
import os
import json
import requests
from datetime import datetime
from audiobook_processor_v7_with_voices import AIBookProcessor, ContentValidationError

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/root/audiobook_uploads'
WORKING_DIR = '/root/audiobook_working'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WORKING_DIR, exist_ok=True)


def send_slack_notification(message, details=None):
    """Send notification to Slack"""
    if not SLACK_WEBHOOK_URL:
        return
    
    payload = {
        "text": message,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            }
        ]
    }
    
    if details:
        payload["blocks"].append({
            "type": "section",
            "fields": [{"type": "mrkdwn", "text": f"*{k}:*\n{v}"} for k, v in details.items()]
        })
    
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except:
        pass


@app.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "7.0.0",
        "features": ["validation", "folder_structure", "voice_recommendations"],
        "timestamp": datetime.now().isoformat()
    })


@app.route('/webhook/upload', methods=['POST'])
def upload_book():
    """Handle book upload and processing"""
    try:
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        book_file = request.files.get('bookFile')
        
        if not all([name, email, book_file]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = book_file.filename.replace(' ', '').replace('/', '_')
        file_path = os.path.join(UPLOAD_FOLDER, f"{email.replace('@', '_')}_{timestamp}_{safe_filename}")
        book_file.save(file_path)
        
        # Send Slack notification - Upload started
        send_slack_notification(
            f"📤 *New book upload started*",
            {
                "User": name,
                "Email": email,
                "File": book_file.filename,
                "Status": "Processing..."
            }
        )
        
        # Process book
        project_id = f"{email.split('@')[0]}_{timestamp}"
        
        try:
            processor = AIBookProcessor(
                pdf_path=file_path,
                project_id=project_id,
                user_email=email,
                working_dir=WORKING_DIR,
                elevenlabs_api_key=ELEVENLABS_API_KEY
            )
            
            result = processor.process()
            
            # Send Slack notification - Success
            send_slack_notification(
                f"✅ *Book processed successfully!*",
                {
                    "User": name,
                    "Email": email,
                    "Book Title": result['bookInfo']['title'],
                    "Genre": result['bookInfo']['genre'],
                    "Word Count": f"{result['metrics']['word_count']:,}",
                    "Pages": str(result['metrics']['page_count']),
                    "Voices Recommended": str(len(result.get('voiceRecommendations', {}).get('recommended_voices', []))),
                    "View Results": f"https://audiobooksmith.app/files/view/{result['sessionId']}"
                }
            )
            
            return jsonify({
                "success": True,
                "message": "Book processed successfully",
                "projectId": project_id,
                "sessionId": result['sessionId'],
                "folderUrl": f"https://audiobooksmith.app/files/view/{result['sessionId']}",
                "analysis": result
            })
            
        except ContentValidationError as e:
            # Send Slack notification - Validation failed
            send_slack_notification(
                f"⚠️ *Content validation failed*",
                {
                    "User": name,
                    "Email": email,
                    "File": book_file.filename,
                    "Reason": e.message
                }
            )
            
            return jsonify({
                "success": False,
                "error": "validation_failed",
                "message": e.user_message,
                "suggestions": e.suggestions
            }), 400
        
    except Exception as e:
        # Send Slack notification - Error
        send_slack_notification(
            f"❌ *Processing error*",
            {
                "User": name if 'name' in locals() else "Unknown",
                "Email": email if 'email' in locals() else "Unknown",
                "Error": str(e)
            }
        )
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/files/view/<session_id>', methods=['GET'])
def view_analysis(session_id):
    """Display analysis page with voice recommendations"""
    try:
        # Find analysis file
        # Search in all user folders
        for user_folder in os.listdir(WORKING_DIR):
            user_path = os.path.join(WORKING_DIR, user_folder)
            if not os.path.isdir(user_path):
                continue
            
            book_projects_path = os.path.join(user_path, 'book_projects')
            if not os.path.exists(book_projects_path):
                continue
            
            for book_folder in os.listdir(book_projects_path):
                sessions_path = os.path.join(book_projects_path, book_folder, 'processing_sessions', session_id)
                analysis_file = os.path.join(sessions_path, 'analysis.json')
                
                if os.path.exists(analysis_file):
                    with open(analysis_file, 'r') as f:
                        analysis = json.load(f)
                    
                    # Load HTML template
                    template_path = '/root/analysis_page_template_v3_with_voices.html'
                    with open(template_path, 'r') as f:
                        template = f.read()
                    
                    # Render template with Jinja2
                    from jinja2 import Template
                    rendered = Template(template).render(analysis=analysis)
                    
                    return rendered
        
        return jsonify({"error": "Analysis not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/files/voice-sample/<session_id>/<voice_id>.mp3', methods=['GET'])
def serve_voice_sample(session_id, voice_id):
    """Serve voice sample audio file"""
    try:
        # Find voice sample file
        for user_folder in os.listdir(WORKING_DIR):
            user_path = os.path.join(WORKING_DIR, user_folder)
            if not os.path.isdir(user_path):
                continue
            
            book_projects_path = os.path.join(user_path, 'book_projects')
            if not os.path.exists(book_projects_path):
                continue
            
            for book_folder in os.listdir(book_projects_path):
                sessions_path = os.path.join(book_projects_path, book_folder, 'processing_sessions', session_id)
                voice_sample_path = os.path.join(sessions_path, '09_elevenlabs_integration', 'voice_samples', f'{voice_id}.mp3')
                
                if os.path.exists(voice_sample_path):
                    return send_file(voice_sample_path, mimetype='audio/mpeg')
        
        return jsonify({"error": "Voice sample not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/webhook/select-voice', methods=['POST'])
def select_voice():
    """Save user's voice selection"""
    try:
        data = request.json
        session_id = data.get('sessionId')
        project_id = data.get('projectId')
        voice_id = data.get('voiceId')
        voice_name = data.get('voiceName')
        
        if not all([session_id, voice_id]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        # Find session directory
        for user_folder in os.listdir(WORKING_DIR):
            user_path = os.path.join(WORKING_DIR, user_folder)
            if not os.path.isdir(user_path):
                continue
            
            book_projects_path = os.path.join(user_path, 'book_projects')
            if not os.path.exists(book_projects_path):
                continue
            
            for book_folder in os.listdir(book_projects_path):
                sessions_path = os.path.join(book_projects_path, book_folder, 'processing_sessions', session_id)
                
                if os.path.exists(sessions_path):
                    # Save voice selection
                    voice_settings_dir = os.path.join(sessions_path, '09_elevenlabs_integration', 'voice_settings')
                    os.makedirs(voice_settings_dir, exist_ok=True)
                    
                    selection_file = os.path.join(voice_settings_dir, 'selected_voice.json')
                    selection_data = {
                        "voice_id": voice_id,
                        "voice_name": voice_name,
                        "selected_at": datetime.now().isoformat(),
                        "session_id": session_id,
                        "project_id": project_id
                    }
                    
                    with open(selection_file, 'w') as f:
                        json.dump(selection_data, f, indent=2)
                    
                    # Send Slack notification
                    send_slack_notification(
                        f"🎙️ *Voice selected*",
                        {
                            "Session": session_id,
                            "Voice": voice_name,
                            "Voice ID": voice_id
                        }
                    )
                    
                    return jsonify({
                        "success": True,
                        "message": "Voice selection saved",
                        "voice_id": voice_id,
                        "voice_name": voice_name
                    })
        
        return jsonify({"success": False, "error": "Session not found"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    print("="*70)
    print("AudiobookSmith Webhook Server v7 - With Voice Recommendations")
    print("="*70)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Working directory: {WORKING_DIR}")
    print(f"Slack notifications: {'Enabled' if SLACK_WEBHOOK_URL else 'Disabled'}")
    print(f"ElevenLabs: {'Enabled' if ELEVENLABS_API_KEY else 'Disabled'}")
    print("="*70)
    
    # Send startup notification
    send_slack_notification(
        "🚀 *AudiobookSmith Server Started*",
        {
            "Version": "7.0.0",
            "Features": "Validation, Folder Structure, Voice Recommendations",
            "Status": "Ready to accept uploads"
        }
    )
    
    app.run(host='0.0.0.0', port=5001, debug=False)
