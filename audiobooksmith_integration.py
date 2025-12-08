"""
AudiobookSmith Pipeline Integration
Integrates the Narration Preparation Processor into the existing AudiobookSmith workflow

This module provides integration points between:
- Phase 1: Chapter Splitting (audiobook_processor_v8_universal_formats.py)
- Phase 1.5: Narration Preparation (narration_preparation_processor.py) [NEW]
- Phase 2: Profile Building (already exists)
- Phase 3+: SSML Generation and beyond

Author: Manus AI
Version: 1.0.0
Date: December 2025
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional
from narration_preparation_processor import NarrationPreparationProcessor

logger = logging.getLogger(__name__)


class AudiobookSmithPipeline:
    """
    Orchestrates the complete AudiobookSmith processing pipeline with
    the new Narration Preparation phase.
    """
    
    def __init__(self, working_dir: str, session_id: str):
        """
        Initialize the pipeline for a specific processing session.
        
        Args:
            working_dir: Base working directory (e.g., /audiobook_working/)
            session_id: Unique session identifier
        """
        self.working_dir = Path(working_dir)
        self.session_id = session_id
        self.session_dir = self.working_dir / session_id
        
        # Define folder structure
        self.folders = {
            'raw_files': self.session_dir / '01_raw_files',
            'structure_analysis': self.session_dir / '02_structure_analysis',
            'processed_text': self.session_dir / '03_processed_text',
            'language_processing': self.session_dir / '04_language_processing',
            'chapter_splits': self.session_dir / '05_chapter_splits',
            'ssml_generation': self.session_dir / '06_ssml_generation',
            'audio_ready': self.session_dir / '07_audio_ready',
            'quality_control': self.session_dir / '08_quality_control',
            'elevenlabs_integration': self.session_dir / '09_elevenlabs_integration',
            'final_delivery': self.session_dir / '10_final_delivery',
            'rollback_data': self.session_dir / '99_rollback_data'
        }
        
        # Create all folders
        for folder in self.folders.values():
            folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized pipeline for session {session_id}")
    
    def run_narration_preparation(self) -> Dict:
        """
        Run the Narration Preparation phase.
        
        This phase transforms raw chapter files from 05_chapter_splits/
        into narration-ready files in 06_ssml_generation/
        
        Returns:
            Dict with processing results
        """
        logger.info("Starting Narration Preparation phase")
        
        # Locate book profile from Phase 2
        book_profile_path = self.folders['structure_analysis'] / 'bookProfile.json'
        
        if not book_profile_path.exists():
            raise FileNotFoundError(
                f"Book profile not found at {book_profile_path}. "
                "Please run Phase 2 (Profile Building) first."
            )
        
        # Initialize processor
        processor = NarrationPreparationProcessor(str(book_profile_path))
        
        # Process all chapters
        results = processor.process_all_chapters(
            input_dir=str(self.folders['chapter_splits']),
            output_dir=str(self.folders['ssml_generation'])
        )
        
        # Save processing metadata
        metadata = {
            'session_id': self.session_id,
            'phase': 'narration_preparation',
            'input_dir': str(self.folders['chapter_splits']),
            'output_dir': str(self.folders['ssml_generation']),
            'results': results
        }
        
        metadata_path = self.folders['ssml_generation'] / 'narration_prep_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Narration Preparation complete: {results['successful']}/{results['total_chapters']} chapters")
        
        return results
    
    def get_pipeline_status(self) -> Dict:
        """Get the current status of all pipeline phases."""
        status = {
            'session_id': self.session_id,
            'phases': {}
        }
        
        # Check each phase
        phase_checks = {
            'phase_1_chapter_splits': (self.folders['chapter_splits'], '*.txt'),
            'phase_2_profile_building': (self.folders['structure_analysis'], 'bookProfile.json'),
            'phase_1.5_narration_prep': (self.folders['ssml_generation'], '*_narration_ready.txt'),
            'phase_3_ssml_generation': (self.folders['ssml_generation'], '*_ssml.txt'),
            'phase_4_audio_ready': (self.folders['audio_ready'], '*.mp3'),
        }
        
        for phase_name, (folder, pattern) in phase_checks.items():
            if pattern.startswith('*'):
                files = list(folder.glob(pattern))
                status['phases'][phase_name] = {
                    'completed': len(files) > 0,
                    'file_count': len(files)
                }
            else:
                file_path = folder / pattern
                status['phases'][phase_name] = {
                    'completed': file_path.exists(),
                    'file_path': str(file_path) if file_path.exists() else None
                }
        
        return status


def integrate_with_existing_processor(processor_instance, session_dir: str):
    """
    Integration helper to add narration preparation to existing
    AIBookProcessor workflow.
    
    This function should be called after chapter splitting is complete.
    
    Args:
        processor_instance: Instance of AIBookProcessor
        session_dir: Session directory path
    
    Example:
        # In audiobook_processor_v8_universal_formats.py, after split_chapters_to_files():
        from audiobooksmith_integration import integrate_with_existing_processor
        integrate_with_existing_processor(self, self.session_dir)
    """
    logger.info("Running integrated narration preparation")
    
    try:
        # Create pipeline instance
        pipeline = AudiobookSmithPipeline(
            working_dir=str(Path(session_dir).parent.parent.parent.parent),
            session_id=Path(session_dir).name
        )
        
        # Run narration preparation
        results = pipeline.run_narration_preparation()
        
        # Update processor instance with results
        if hasattr(processor_instance, 'narration_prep_results'):
            processor_instance.narration_prep_results = results
        
        logger.info("Integrated narration preparation completed successfully")
        return results
    
    except Exception as e:
        logger.error(f"Integrated narration preparation failed: {e}")
        raise


def create_sample_book_profile(output_path: str):
    """
    Create a sample book profile for testing purposes.
    Based on the VITALY book example.
    """
    sample_profile = {
        "bibliographicMetadata": {
            "title": "VITALY: The MisAdventures of a Ukrainian Orphan",
            "author": "Vitaly Magidov",
            "originalScript": "English with Ukrainian/Russian cultural elements",
            "languageOfOriginalText": "English",
            "originalNationalityNote": "Ukrainian memoir written in English"
        },
        "structuralOutline": {
            "frontMatter": ["Cover", "Copyright", "Dedication", "Prologue"],
            "parts": [
                {
                    "label": "Part I: Orphanage",
                    "chapters": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
                },
                {
                    "label": "Part II: Foster Care",
                    "chapters": [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
                },
                {
                    "label": "Part III: Into Adulthood",
                    "chapters": [29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46]
                }
            ],
            "backMatter": ["Epilogue", "About the Author"],
            "chapterCount": 46,
            "chapterTitles": [
                "Once Upon a Time",
                "My First Misadventure",
                "Lullabies in the Rain",
                # ... (add all 46 chapter titles)
            ]
        },
        "linguisticCulturalProfile": {
            "primaryLanguage": "English",
            "nationalityContext": "Ukrainian",
            "regionalisms": ["kopeks", "Detski Dom", "Subbotnik"],
            "culturalReferences": ["Kolyada", "Svyatyy Mykolay", "Ravlik-Pavlik"],
            "localizationAdvice": "Use Cyrillic for all Ukrainian/Russian names and cultural terms"
        },
        "namedEntitiesAndTerminology": {
            "characters": [
                {"name": "Vitaly", "transliteration": "Віталій", "role": "Main character", "isForeignName": True},
                {"name": "Mamochka", "transliteration": "Мамочка", "role": "Mother figure", "isForeignName": True},
                {"name": "Tyotya Valya", "transliteration": "Тьотя Валя", "role": "Guardian", "isForeignName": True},
                {"name": "Vasyl Ivanovych", "transliteration": "Василь Іванович", "role": "Headmaster", "isForeignName": True},
                {"name": "Evheniya Mikitivna", "transliteration": "Євгенія Микитівна", "role": "Mother", "isForeignName": True},
                {"name": "Tamara Petrivna", "transliteration": "Тамара Петрівна", "role": "Teacher", "isForeignName": True}
            ],
            "places": [
                {"name": "Chernivtsi", "transliteration": "Чернівці", "isForeignName": True},
                {"name": "Kyiv", "transliteration": "Київ", "isForeignName": True},
                {"name": "Fastivska Street", "transliteration": "Фастівська street", "isForeignName": True},
                {"name": "Prut River", "transliteration": "Прут river", "isForeignName": True}
            ],
            "pronunciationGlossary": {
                "Vitaly": "Віталій",
                "Mamochka": "Мамочка",
                "Tyotya Valya": "Тьотя Валя",
                "Vasyl Ivanovych": "Василь Іванович",
                "Evheniya Mikitivna": "Євгенія Микитівна",
                "Tamara Petrivna": "Тамара Петрівна",
                "Chernivtsi": "Чернівці",
                "Kyiv": "Київ",
                "Fastivska": "Фастівська",
                "Prut": "Прут"
            }
        },
        "narrativeStyleAndTone": {
            "pointOfView": "First person",
            "narrativePace": "Reflective",
            "toneDescriptors": ["nostalgic", "emotional", "resilient"],
            "recommendedSSMLBreakRules": {
                "chapterStart": "2s",
                "chapterEnd": "2s",
                "sceneTransition": "0.5s",
                "dialogueChange": "0.3s",
                "afterQuote": "0.8s"
            }
        },
        "technicalAndAudioSettings": {
            "elevenLabsNote": "Use native non-Latin pronunciation; speak Cyrillic names directly",
            "voiceProfiles": ["1v4nQmtM66ypA1nvXQj5"],
            "audioFormat": "mp3_44100_128"
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_profile, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created sample book profile at {output_path}")


def main():
    """Example usage and testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AudiobookSmith Pipeline Integration')
    parser.add_argument('--working-dir', required=True, help='Working directory')
    parser.add_argument('--session-id', required=True, help='Session ID')
    parser.add_argument('--action', choices=['prepare', 'status', 'create-sample'], 
                       default='prepare', help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'create-sample':
        output_path = Path(args.working_dir) / args.session_id / '02_structure_analysis' / 'bookProfile.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        create_sample_book_profile(str(output_path))
        print(f"Sample book profile created at {output_path}")
    
    elif args.action == 'status':
        pipeline = AudiobookSmithPipeline(args.working_dir, args.session_id)
        status = pipeline.get_pipeline_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'prepare':
        pipeline = AudiobookSmithPipeline(args.working_dir, args.session_id)
        results = pipeline.run_narration_preparation()
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
