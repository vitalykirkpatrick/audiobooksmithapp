# AudiobookSmith V6 - Complete Fix Deployment Guide

## 🎯 What's Fixed in V6

### 1. **STRICT Content Validation** ✅
- **Problem**: Technical documents, proposals, and guides were being accepted
- **Solution**: Enhanced AI validation with strict rejection rules
- **Result**: Now properly rejects templates, proposals, guides, manuals, documentation

### 2. **Proper Folder Structure** ✅
- **Problem**: Simple flat structure (text/, audio/, analysis.json)
- **Solution**: Session-based versioning with numbered processing pipeline
- **Result**: Matches your n8n automation system with 19 folders per session

---

## 📦 Files to Deploy

1. **audiobook_processor_v6_fixed.py** - Enhanced processor with validation + folder structure
2. **audiobook_webhook_server_v6.py** - Updated webhook server (to be created)
3. **analysis_page_template_v2.html** - New HTML template with folder structure display

---

## 🧪 Test Results

### Test 1: SRS Requirements Document
```
Status: ✅ REJECTED
Reason: "Template document detected"
Message: "This appears to be a template document, not a book"
```

### Test 2: Vitaly Memoir Book
```
Status: ✅ ACCEPTED
Type: Memoir
Word Count: 107,414
Pages: 386
Folders Created: 19
```

---

## 📁 New Folder Structure

### Complete Structure
```
/root/audiobook_working/
└── vitmag_at_gmail_com/                    # User folder
    └── book_projects/                      # All books container
        └── book_vitaly_test/               # Book folder
            ├── processing_sessions/        # Version control
            │   ├── 2025-12-08T06-28-18/   # Session 1 (timestamp)
            │   │   ├── 01_raw_files/
            │   │   │   └── extracted_text.txt
            │   │   ├── 02_structure_analysis/
            │   │   │   └── analysis.json
            │   │   ├── 03_processed_text/
            │   │   ├── 04_language_processing/
            │   │   ├── 05_chapter_splits/
            │   │   ├── 06_ssml_generation/
            │   │   ├── 07_audio_ready/
            │   │   ├── 08_quality_control/
            │   │   ├── 09_elevenlabs_integration/
            │   │   │   ├── input_ssml/
            │   │   │   ├── generated_audio/
            │   │   │   ├── processing_logs/
            │   │   │   └── voice_settings/
            │   │   ├── 10_final_delivery/
            │   │   │   ├── audio_files/
            │   │   │   ├── metadata/
            │   │   │   ├── cover_art/
            │   │   │   └── submission_package/
            │   │   ├── 99_rollback_data/
            │   │   └── analysis.json (root copy)
            │   ├── 2025-12-08T10-15-30/   # Session 2 (reprocessing)
            │   └── 2025-12-09T14-22-45/   # Session 3 (final)
            ├── comparison_reports/         # Compare sessions
            └── quality_metrics/            # Analytics
```

### Folder Counts
- **Main pipeline folders**: 11 (01-10, 99)
- **ElevenLabs subfolders**: 4
- **Amazon delivery subfolders**: 4
- **Total per session**: 19 folders

---

## 🚀 Deployment Steps

### Step 1: SSH to Server
```bash
ssh root@172.245.67.47
# Password: Chernivtsi_23
```

### Step 2: Backup Current Files
```bash
cd /root
mkdir -p backups/v5_backup_$(date +%Y%m%d_%H%M%S)
cp audiobook_processor_v5_validated.py backups/v5_backup_$(date +%Y%m%d_%H%M%S)/
cp audiobook_webhook_server_v5_validated.py backups/v5_backup_$(date +%Y%m%d_%H%M%S)/
```

### Step 3: Upload New Files

**Option A: Using scp from your local machine**
```bash
scp audiobook_processor_v6_fixed.py root@172.245.67.47:/root/
scp audiobook_webhook_server_v6.py root@172.245.67.47:/root/
scp analysis_page_template_v2.html root@172.245.67.47:/root/
```

**Option B: Using nano/vim on server**
```bash
# Copy content from local files and paste into server
nano /root/audiobook_processor_v6_fixed.py
nano /root/audiobook_webhook_server_v6.py
nano /root/analysis_page_template_v2.html
```

### Step 4: Update Webhook Server Service

The webhook server needs to import the new processor:

```bash
nano /root/audiobook_webhook_server.py
```

Update the import line:
```python
from audiobook_processor_v6_fixed import AIBookProcessor, ContentValidationError
```

### Step 5: Restart Service
```bash
systemctl restart audiobook-webhook
systemctl status audiobook-webhook
```

### Step 6: Check Logs
```bash
journalctl -u audiobook-webhook -f
```

### Step 7: Test

**Test 1: Upload a technical document (should be rejected)**
```bash
curl -X POST https://audiobooksmith.app/webhook/upload \
  -F "name=Test User" \
  -F "email=test@example.com" \
  -F "bookFile=@deployment_guide.pdf"
```

Expected: Error message about template/guide not suitable

**Test 2: Upload a real book (should be accepted)**
```bash
curl -X POST https://audiobooksmith.app/webhook/upload \
  -F "name=Test User" \
  -F "email=test@example.com" \
  -F "bookFile=@vitaly_book.pdf"
```

Expected: Success with folder structure displayed

---

## 🔍 Validation Rules

### ✅ ACCEPTS
- Fiction books (novels, short stories, novellas)
- Non-fiction narrative books (memoirs, biographies)
- Self-help books with narrative
- Educational books with narrative structure
- Sample chapters (1,000+ words, 3+ pages)

### ❌ REJECTS
- Business proposals or templates
- Deployment guides, setup instructions
- Technical documentation, API docs
- How-to guides, tutorials
- Requirements documents (SRS, PRD)
- Templates of any kind
- Academic papers, research papers
- Reports (business, technical, analysis)
- Presentations, slide decks
- Reference materials
- Forms, applications
- Marketing materials
- Legal documents
- Configuration files
- Workflow documentation

---

## 📊 What Users See

### Rejected Document
```
⚠️ Content Validation Failed

This appears to be a template document, not a book. 
Our service is for audiobook production, not template processing.

Suggestions:
• Upload an actual book, short story, or sample chapter
• Not suitable: templates, forms, proposals, guides
• Suitable: novels, memoirs, biographies, self-help books
```

### Accepted Book
```
✅ Book Analysis Complete!

Session ID: 2025-12-08T06-28-18
Document Type: Memoir
Genre: Memoir
Word Count: 107,414
Pages: 386

📁 Folder Structure Created:
19 folders in processing pipeline
Files: extracted_text.txt, analysis.json
```

---

## 🔧 Troubleshooting

### Issue: Validation too strict
**Solution**: Adjust temperature in `ai_validate_content()` method (currently 0.1)

### Issue: Folder structure not showing
**Solution**: Check that `get_folder_structure()` is called in `process()` method

### Issue: Service won't start
**Solution**: Check logs with `journalctl -u audiobook-webhook -n 50`

### Issue: Import errors
**Solution**: Ensure PyPDF2 and openai are installed:
```bash
pip3 install PyPDF2 openai
```

---

## 📈 Benefits

### For Users
1. **Clear feedback** on what content is accepted
2. **Helpful suggestions** when content is rejected
3. **Transparency** - see exactly what folders/files were created
4. **Professional** quality control

### For You
1. **No wasted processing** on invalid content
2. **Proper versioning** - never lose work
3. **Easy comparison** between processing sessions
4. **Scalable** - unlimited books per user
5. **Real-time alerts** via Slack

### For System
1. **Organized** - clean folder structure
2. **Traceable** - session-based processing
3. **Recoverable** - rollback capability
4. **Amazon-ready** - proper Audible structure
5. **ElevenLabs-ready** - TTS integration folders

---

## ✅ Deployment Checklist

- [ ] Backup current files
- [ ] Upload v6 processor
- [ ] Upload v6 webhook server
- [ ] Upload v2 HTML template
- [ ] Update service configuration
- [ ] Restart service
- [ ] Check logs for errors
- [ ] Test with invalid document (should reject)
- [ ] Test with valid book (should accept)
- [ ] Verify folder structure is created
- [ ] Check Slack notifications
- [ ] Test analysis page display

---

## 🎯 Success Criteria

1. ✅ Technical documents are rejected with clear messages
2. ✅ Valid books are accepted and processed
3. ✅ 19 folders created per session
4. ✅ Analysis page shows folder structure
5. ✅ Slack notifications working
6. ✅ No errors in logs

---

## 📞 Support

If you encounter issues:
1. Check logs: `journalctl -u audiobook-webhook -n 100`
2. Verify files uploaded correctly
3. Test with simple curl commands
4. Rollback to v5 if needed

---

**Estimated Deployment Time**: 20-30 minutes

**Risk Level**: Low (easy rollback to v5)

**Testing Required**: Yes (both valid and invalid documents)
