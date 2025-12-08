# Correct Folder Structure for AudiobookSmith

Based on the n8n automation system documentation, here is the proper folder structure:

## Complete Folder Structure

```
01_USER_WORKSPACES/vitmag_gmail_com/
├── book_projects/                              # Container for all books
│   ├── VITALY_-_The_Misadventures_of_a_Ukrainian_Orphan/
│   │   ├── processing_sessions/                # Version control
│   │   │   ├── 2025-07-16T14-30-25/           # Session 1
│   │   │   │   ├── 01_raw_files/
│   │   │   │   ├── 02_raw_chapters/
│   │   │   │   ├── 03_processed_chapters/
│   │   │   │   └── 04_amazon_audible_ready/
│   │   │   ├── 2025-07-16T16-45-12/           # Session 2 (improved)
│   │   │   └── 2025-07-17T09-15-30/           # Session 3 (final)
│   │   ├── comparison_reports/                 # Quality comparisons
│   │   └── quality_metrics/                    # Analytics
│   ├── My_Second_Book/                         # Future book 2
│   │   ├── processing_sessions/
│   │   ├── comparison_reports/
│   │   └── quality_metrics/
│   └── My_Third_Book/                          # Future book 3
├── user_config/                                # User preferences
├── analytics/                                  # Cross-book analytics
└── language_assets/ukrainian/                  # Language resources
```

## Processing Session Folders (Within Each Session)

Based on the workflow JSON, each processing session should have these numbered folders:

```
2025-07-16T14-30-25/                           # Session folder (timestamp)
├── 01_raw_files/                              # Original uploaded files
├── 02_structure_analysis/                     # Structure analysis results
├── 03_processed_text/                         # Processed text content
├── 04_language_processing/                    # Ukrainian conversions
├── 05_chapter_splits/                         # Individual chapters
├── 06_ssml_generation/                        # SSML files for TTS
├── 07_audio_ready/                            # Amazon Audible structure
│   ├── Part_01/
│   │   ├── Chapter_01/
│   │   ├── Chapter_02/
│   │   └── ...
│   ├── Part_02/
│   └── Part_03/
├── 08_quality_control/                        # Quality checks
├── 09_elevenlabs_integration/                 # ElevenLabs processing
│   ├── input_ssml/
│   ├── generated_audio/
│   ├── processing_logs/
│   └── voice_settings/
├── 10_final_delivery/                         # Amazon delivery package
│   ├── audio_files/
│   ├── metadata/
│   ├── cover_art/
│   └── submission_package/
└── 99_rollback_data/                          # Backup for recovery
```

## Key Features

1. **Session-Based Versioning**: Each processing attempt gets timestamped folder
2. **Never Lose Work**: All versions preserved
3. **Easy Comparison**: Compare different processing sessions
4. **Multi-Book Support**: Unlimited books per user
5. **Amazon Audible Ready**: Proper folder structure for submission
6. **ElevenLabs Integration**: Dedicated folders for TTS processing
7. **Rollback Capability**: Can restore from any previous version

## Folder Numbering System

- `01-10`: Main processing pipeline folders (numbered for order)
- `99`: Special folders (rollback, backup)
- Folders are numbered to show processing order
- Each folder has a specific purpose in the pipeline

## Current Issue

The current webhook processor only creates:
```
project_id/
├── text/
│   └── extracted_text.txt
├── audio/
└── analysis.json
```

This needs to be updated to match the proper structure above.
