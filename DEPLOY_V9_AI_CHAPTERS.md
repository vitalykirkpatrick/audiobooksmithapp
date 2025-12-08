# AudiobookSmith v9 Deployment - AI Chapter Detection

## What's New in v9

### ✨ Key Features
1. **AI Chapter Detection** - Eliminates false positives (page numbers, headers, footers)
2. **Simplified Processing** - Advanced features can be toggled on/off for debugging
3. **Universal Format Support** - PDF, EPUB, DOCX, TXT, RTF, MOBI, AZW, AZW3, ODT
4. **Smart Chapter Numbering** - Prologue=00, Chapters=01-99, Epilogue=900
5. **Better Error Handling** - Proper validation messages and suggestions
6. **10-Folder Pipeline** - Clean production folder structure

### 🔧 Technical Improvements
- AI-based chapter detection using GPT-4.1-mini
- Fallback regex detection if AI fails
- Proper content validation with user-friendly error messages
- Modular architecture (processor, extractor, detector separate)
- Better logging and debugging output

## Files Updated

### Core Processing
- `audiobook_processor_v9_ai_chapters.py` - Main processor with AI chapter detection
- `audiobook_webhook_server_v8_ai_chapters.py` - Webhook server with better error handling
- `universal_text_extractor.py` - Multi-format text extraction
- `language_detector.py` - Language detection for 74 supported languages
- `requirements.txt` - All Python dependencies

## Deployment Steps

### 1. Install Dependencies on Server

```bash
ssh root@audiobooksmith.app
cd /root
pip3 install -r requirements.txt
```

### 2. Stop Current Server

```bash
# Find and kill existing webhook server
ps aux | grep webhook
kill <PID>
```

### 3. Deploy New Files

```bash
# Copy new files to server
scp audiobook_processor_v9_ai_chapters.py root@audiobooksmith.app:/root/
scp audiobook_webhook_server_v8_ai_chapters.py root@audiobooksmith.app:/root/
scp universal_text_extractor.py root@audiobooksmith.app:/root/
scp language_detector.py root@audiobooksmith.app:/root/
scp requirements.txt root@audiobooksmith.app:/root/
```

### 4. Start New Server

```bash
ssh root@audiobooksmith.app
cd /root
nohup python3 audiobook_webhook_server_v8_ai_chapters.py > webhook.log 2>&1 &
```

### 5. Verify Server is Running

```bash
curl http://audiobooksmith.app:5001/webhook/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "AudiobookSmith Webhook Server v8",
  "timestamp": "2025-12-08T...",
  "upload_folder": "/root/audiobook_uploads",
  "working_dir": "/root/audiobook_working"
}
```

### 6. Test with Book Upload

Upload a test book through https://audiobooksmith.com and verify:
- ✅ No timeout errors
- ✅ Chapters detected correctly (no page numbers)
- ✅ Proper chapter numbering (00, 01, 02, etc.)
- ✅ All 10 folders created
- ✅ Chapter files in 05_chapter_splits/

## Folder Structure

Each processing session creates:

```
/root/audiobook_working/
└── {user_email}/
    └── book_projects/
        └── {book_name}/
            └── processing_sessions/
                └── {session_id}/
                    ├── 01_raw_text/
                    ├── 02_metadata/
                    ├── 03_chapter_analysis/
                    ├── 04_cleaned_text/
                    ├── 05_chapter_splits/
                    ├── 06_narration_prep/
                    ├── 07_voice_samples/
                    ├── 08_audio_ready/
                    ├── 09_quality_reports/
                    └── 10_delivery_package/
```

## Troubleshooting

### Server Not Responding
```bash
# Check if server is running
ps aux | grep webhook

# Check logs
tail -f /root/webhook.log

# Restart server
kill <PID>
nohup python3 audiobook_webhook_server_v8_ai_chapters.py > webhook.log 2>&1 &
```

### Chapter Detection Issues
- Check `03_chapter_analysis/detected_chapters.json` for AI-detected chapters
- Verify no page numbers or headers are being detected
- If AI detection fails, fallback regex should activate

### Processing Timeouts
- Advanced features (narration prep, voice recommendations) are disabled by default
- Can be enabled by setting flags in processor initialization
- Check `webhook.log` for detailed error messages

## Advanced Features (Currently Disabled)

To enable advanced features, modify `audiobook_webhook_server_v8_ai_chapters.py`:

```python
processor = AIBookProcessor(
    book_path=file_path,
    project_id=safe_filename,
    user_email=email,
    working_dir=WORKING_DIR,
    enable_narration_prep=True,  # Enable narration preparation
    enable_voice_recommendations=True  # Enable voice recommendations
)
```

## Environment Variables Required

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"  # Optional, for voice recommendations
```

## Testing Checklist

- [ ] Health check endpoint responds
- [ ] PDF upload works
- [ ] EPUB upload works
- [ ] DOCX upload works
- [ ] Chapters detected correctly (no false positives)
- [ ] Chapter numbering correct (00, 01, 02, ...)
- [ ] All 10 folders created
- [ ] Chapter files saved in 05_chapter_splits/
- [ ] Metadata extracted correctly
- [ ] Processing completes without timeout
- [ ] Analysis page displays results

## Rollback Plan

If v9 has issues, rollback to previous version:

```bash
ssh root@audiobooksmith.app
kill <webhook_pid>
nohup python3 audiobook_webhook_server_v7_universal.py > webhook.log 2>&1 &
```

## Support

For issues or questions:
- Check `/root/webhook.log` for detailed error messages
- Verify all dependencies installed: `pip3 list`
- Test chapter detection manually: `python3 audiobook_processor_v9_ai_chapters.py test_book.pdf`
