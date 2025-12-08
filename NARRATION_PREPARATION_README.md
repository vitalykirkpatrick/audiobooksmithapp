# Narration Preparation Phase - Implementation Guide

**Version**: 1.0.0  
**Date**: December 2025  
**Status**: ✅ Tested and Production-Ready

---

## Overview

The Narration Preparation Phase is a critical bridge between chapter splitting (Phase 1) and SSML generation (Phase 3+). It transforms raw chapter files into culturally-authentic, narration-ready scripts with:

- **Cyrillic name conversion** (e.g., "Vitaly" → "Віталій")
- **SSML formatting** (timing breaks, pauses)
- **Chapter announcements** (intro/outro)
- **Hybrid location formatting** (e.g., "Фастівська street")

---

## Files Included

| File | Description |
|------|-------------|
| `narration_preparation_processor.py` | Core processor for transforming chapters |
| `audiobooksmith_integration.py` | Integration with existing AudiobookSmith pipeline |
| `test_narration_preparation.py` | Comprehensive test suite |
| `NARRATION_PREPARATION_README.md` | This file |

---

## Installation

### 1. Server Deployment

```bash
# Upload files to server
scp narration_preparation_processor.py root@audiobooksmith.app:/root/
scp audiobooksmith_integration.py root@audiobooksmith.app:/root/

# SSH into server
ssh root@audiobooksmith.app

# Install dependencies (if not already installed)
pip3 install openai
```

### 2. Environment Variables

Ensure `OPENAI_API_KEY` is set in the server environment:

```bash
# Add to .env file
echo "OPENAI_API_KEY=your_key_here" >> /root/.env

# Or export directly
export OPENAI_API_KEY="your_key_here"
```

---

## Usage

### Standalone Usage

Process all chapters in a directory:

```bash
python3 narration_preparation_processor.py \
    --book-profile /path/to/bookProfile.json \
    --input-dir /path/to/05_chapter_splits/ \
    --output-dir /path/to/06_ssml_generation/
```

Process a single chapter:

```bash
python3 narration_preparation_processor.py \
    --book-profile /path/to/bookProfile.json \
    --input-dir /path/to/05_chapter_splits/ \
    --output-dir /path/to/06_ssml_generation/ \
    --chapter-number 1
```

### Integration with AIBookProcessor

Add to `audiobook_processor_v8_universal_formats.py`:

```python
from audiobooksmith_integration import integrate_with_existing_processor

class AIBookProcessor:
    def process(self, input_file):
        # ... existing code ...
        
        # After chapter splitting
        self.split_chapters_to_files()
        
        # NEW: Run narration preparation
        integrate_with_existing_processor(self, self.session_dir)
        
        # Continue with SSML generation...
```

---

## Testing

Run the comprehensive test suite:

```bash
python3 test_narration_preparation.py
```

**Expected Output:**
```
============================================================
TEST RESULTS SUMMARY
============================================================
Tests Run:    3
Tests Passed: 3
Tests Failed: 0
Success Rate: 100.0%
============================================================
```

---

## Output Format

### Input (Raw Chapter)
```
Chapter 1: Once Upon a Time

Vitaly went to Chernivtsi. The headmaster Vasyl Ivanovych took care of him.
```

### Output (Narration-Ready)
```
<break time="2s" />

Now, let's move on to Chapter One.

<break time="0.5s" />

Chapter 1: Once Upon a Time

<break time="0.5s" />

Віталій went to Чернівці. The headmaster Василь Іванович took care of him.

<break time="2s" />

We've now come to the end of Chapter One.

Next up is Chapter Two: My First Misadventure.

<break time="0.5s" />
```

---

## Quality Validation

The processor automatically validates:

- ✅ Cyrillic name conversion (counts Cyrillic characters)
- ✅ SSML break tags (minimum 3 per chapter)
- ✅ Chapter announcements (intro/outro)
- ✅ Content integrity (length ratio check)

Results are saved in `narration_prep_report.json`.

---

## Troubleshooting

### Issue: "Book profile not found"
**Solution**: Ensure Phase 2 (Profile Building) has been run first and `bookProfile.json` exists in `02_structure_analysis/`.

### Issue: "No Cyrillic characters found"
**Solution**: Check that the `pronunciationGlossary` in `bookProfile.json` contains the correct name mappings.

### Issue: "OpenAI API error"
**Solution**: Verify `OPENAI_API_KEY` is set and has sufficient credits.

---

## Folder Structure

```
/audiobook_working/
└── {session_id}/
    ├── 02_structure_analysis/
    │   └── bookProfile.json          ← Input (Phase 2)
    ├── 05_chapter_splits/
    │   ├── chapter_01.txt             ← Input (Phase 1)
    │   ├── chapter_02.txt
    │   └── ...
    ├── 06_ssml_generation/
    │   ├── chapter_01_narration_ready.txt  ← Output
    │   ├── chapter_02_narration_ready.txt
    │   ├── narration_prep_report.json      ← Validation report
    │   └── narration_prep_metadata.json    ← Processing metadata
    └── ...
```

---

## API Reference

### NarrationPreparationProcessor

```python
processor = NarrationPreparationProcessor(book_profile_path)

# Process single chapter
result = processor.process_chapter(
    raw_chapter_path="/path/to/chapter_01.txt",
    chapter_number=1,
    output_path="/path/to/output.txt"
)

# Process all chapters
results = processor.process_all_chapters(
    input_dir="/path/to/chapters/",
    output_dir="/path/to/output/"
)
```

### AudiobookSmithPipeline

```python
pipeline = AudiobookSmithPipeline(
    working_dir="/audiobook_working/",
    session_id="2025-12-08T12-00-00"
)

# Run narration preparation
results = pipeline.run_narration_preparation()

# Get pipeline status
status = pipeline.get_pipeline_status()
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 2025 | Initial release with full testing |

---

## Support

For issues or questions, contact the AudiobookSmith development team or refer to the main documentation.
