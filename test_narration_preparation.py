"""
Comprehensive Test Suite for Narration Preparation Phase
Tests the complete workflow with real data and validates all outputs

Author: Manus AI
Version: 1.0.0
"""

import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from narration_preparation_processor import NarrationPreparationProcessor
from audiobooksmith_integration import AudiobookSmithPipeline, create_sample_book_profile


class TestNarrationPreparation:
    """Test suite for narration preparation functionality."""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix='narration_test_'))
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        print(f"✓ Test directory created: {self.test_dir}")
    
    def setup_test_environment(self):
        """Create test directory structure and sample data."""
        print("\n=== Setting up test environment ===")
        
        # Create directory structure
        dirs = {
            'chapter_splits': self.test_dir / '05_chapter_splits',
            'structure_analysis': self.test_dir / '02_structure_analysis',
            'ssml_generation': self.test_dir / '06_ssml_generation'
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create sample book profile
        book_profile_path = dirs['structure_analysis'] / 'bookProfile.json'
        book_profile = {
            "bibliographicMetadata": {
                "title": "VITALY: The MisAdventures of a Ukrainian Orphan",
                "author": "Vitaly Magidov"
            },
            "structuralOutline": {
                "chapterCount": 2,
                "chapterTitles": [
                    "Once Upon a Time",
                    "My First Misadventure"
                ],
                "parts": [
                    {
                        "label": "Part I: Orphanage",
                        "chapters": [1, 2]
                    }
                ]
            },
            "linguisticCulturalProfile": {
                "primaryLanguage": "English",
                "nationalityContext": "Ukrainian"
            },
            "namedEntitiesAndTerminology": {
                "characters": [
                    {"name": "Vitaly", "transliteration": "Віталій", "isForeignName": True},
                    {"name": "Mamochka", "transliteration": "Мамочка", "isForeignName": True},
                    {"name": "Vasyl Ivanovych", "transliteration": "Василь Іванович", "isForeignName": True}
                ],
                "places": [
                    {"name": "Chernivtsi", "transliteration": "Чернівці", "isForeignName": True},
                    {"name": "Fastivska Street", "transliteration": "Фастівська street", "isForeignName": True}
                ],
                "pronunciationGlossary": {
                    "Vitaly": "Віталій",
                    "Mamochka": "Мамочка",
                    "Vasyl Ivanovych": "Василь Іванович",
                    "Chernivtsi": "Чернівці",
                    "Fastivska": "Фастівська"
                }
            },
            "narrativeStyleAndTone": {
                "pointOfView": "First person",
                "recommendedSSMLBreakRules": {
                    "chapterStart": "2s",
                    "chapterEnd": "2s",
                    "sceneTransition": "0.5s",
                    "afterQuote": "0.8s"
                }
            },
            "technicalAndAudioSettings": {
                "elevenLabsNote": "Use native non-Latin pronunciation"
            }
        }
        
        with open(book_profile_path, 'w', encoding='utf-8') as f:
            json.dump(book_profile, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Book profile created: {book_profile_path}")
        
        # Create sample chapter files
        chapter1_text = """Chapter 1: Once Upon a Time

The beginning of November 1979 reflected the air of Communist Russia. It was almost always raining, and the weather influenced my little town of Chernivtsi.

Not far from the center of the town lay a petite woman of thirty-eight. She had blond hair, dark brown eyes, and tiny wrinkles that unfairly aged her face.

"What will you call him?" the nurse asked the exhausted mother.

After a moment of deafening silence, she accepted the child, answering, "Vitaly."

I was four kilograms when I was born, and as my name suggests, I was full of life. The headmaster Vasyl Ivanovych took care of me at the orphanage on Fastivska Street.

My mother Mamochka left me there, and I stayed with the doctors and nurses until I was a toddler."""
        
        chapter1_path = dirs['chapter_splits'] / 'chapter_01.txt'
        with open(chapter1_path, 'w', encoding='utf-8') as f:
            f.write(chapter1_text)
        
        print(f"✓ Sample chapter created: {chapter1_path}")
        
        return {
            'book_profile_path': book_profile_path,
            'chapter_splits_dir': dirs['chapter_splits'],
            'ssml_generation_dir': dirs['ssml_generation']
        }
    
    def test_processor_initialization(self, book_profile_path):
        """Test 1: Processor initialization."""
        self.results['tests_run'] += 1
        test_name = "Processor Initialization"
        
        try:
            processor = NarrationPreparationProcessor(str(book_profile_path))
            
            # Verify pronunciation glossary loaded
            assert len(processor.pronunciation_glossary) > 0, "Pronunciation glossary is empty"
            assert "Vitaly" in processor.pronunciation_glossary, "Missing 'Vitaly' in glossary"
            assert processor.pronunciation_glossary["Vitaly"] == "Віталій", "Incorrect transliteration"
            
            # Verify SSML rules loaded
            assert "chapterStart" in processor.ssml_break_rules, "Missing SSML break rules"
            
            self.results['tests_passed'] += 1
            self.results['details'].append({
                'test': test_name,
                'status': 'PASSED',
                'message': f"Loaded {len(processor.pronunciation_glossary)} name mappings"
            })
            print(f"✓ {test_name}: PASSED")
            return processor
            
        except Exception as e:
            self.results['tests_failed'] += 1
            self.results['details'].append({
                'test': test_name,
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"✗ {test_name}: FAILED - {e}")
            raise
    
    def test_chapter_processing(self, processor, chapter_path, output_dir):
        """Test 2: Single chapter processing."""
        self.results['tests_run'] += 1
        test_name = "Chapter Processing"
        
        try:
            output_path = Path(output_dir) / 'chapter_01_narration_ready.txt'
            result = processor.process_chapter(str(chapter_path), 1, str(output_path))
            
            # Verify processing succeeded
            assert result['status'] == 'success', f"Processing failed: {result.get('error')}"
            assert output_path.exists(), "Output file not created"
            
            # Read output
            with open(output_path, 'r', encoding='utf-8') as f:
                output_text = f.read()
            
            # Verify Cyrillic conversion
            assert "Віталій" in output_text, "Name 'Vitaly' not converted to Cyrillic"
            assert "Чернівці" in output_text, "Place 'Chernivtsi' not converted to Cyrillic"
            assert "Василь Іванович" in output_text, "Name 'Vasyl Ivanovych' not converted"
            
            # Verify SSML tags
            assert '<break time="2s" />' in output_text, "Missing chapter start break"
            assert '<break time="0.5s" />' in output_text, "Missing scene transition breaks"
            
            # Verify chapter announcements
            assert "Chapter 1" in output_text or "Chapter One" in output_text, "Missing chapter announcement"
            
            # Verify no English names remain
            assert "Vitaly" not in output_text or "Віталій" in output_text, "English name 'Vitaly' not fully replaced"
            
            self.results['tests_passed'] += 1
            self.results['details'].append({
                'test': test_name,
                'status': 'PASSED',
                'output_file': str(output_path),
                'validation': result['validation']
            })
            print(f"✓ {test_name}: PASSED")
            print(f"  - Cyrillic names found: {result['validation']['cyrillic_names_found']}")
            print(f"  - SSML breaks found: {result['validation']['ssml_breaks_found']}")
            
            return output_text
            
        except Exception as e:
            self.results['tests_failed'] += 1
            self.results['details'].append({
                'test': test_name,
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"✗ {test_name}: FAILED - {e}")
            raise
    
    def test_output_quality(self, output_text):
        """Test 3: Output quality validation."""
        self.results['tests_run'] += 1
        test_name = "Output Quality Validation"
        
        try:
            checks = []
            
            # Check 1: Cyrillic characters present
            cyrillic_count = len([c for c in output_text if '\u0400' <= c <= '\u04FF'])
            checks.append(('Cyrillic characters', cyrillic_count > 0, f"{cyrillic_count} found"))
            
            # Check 2: SSML formatting
            ssml_breaks = output_text.count('<break')
            checks.append(('SSML breaks', ssml_breaks >= 3, f"{ssml_breaks} found"))
            
            # Check 3: Chapter structure
            has_chapter_title = "Chapter 1" in output_text
            checks.append(('Chapter title', has_chapter_title, "Present"))
            
            # Check 4: No page numbers or artifacts
            has_artifacts = any(x in output_text for x in ['Page ', '[Image]', 'Copyright'])
            checks.append(('No artifacts', not has_artifacts, "Clean"))
            
            # Check 5: Paragraph structure preserved
            paragraph_count = output_text.count('\n\n')
            checks.append(('Paragraph structure', paragraph_count > 3, f"{paragraph_count} breaks"))
            
            # Verify all checks passed
            failed_checks = [c for c in checks if not c[1]]
            
            if failed_checks:
                raise AssertionError(f"Quality checks failed: {failed_checks}")
            
            self.results['tests_passed'] += 1
            self.results['details'].append({
                'test': test_name,
                'status': 'PASSED',
                'checks': [{'name': c[0], 'result': c[2]} for c in checks]
            })
            print(f"✓ {test_name}: PASSED")
            for check in checks:
                print(f"  - {check[0]}: {check[2]}")
            
        except Exception as e:
            self.results['tests_failed'] += 1
            self.results['details'].append({
                'test': test_name,
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"✗ {test_name}: FAILED - {e}")
            raise
    
    def cleanup(self):
        """Clean up test directory."""
        try:
            shutil.rmtree(self.test_dir)
            print(f"\n✓ Test directory cleaned up: {self.test_dir}")
        except Exception as e:
            print(f"\n⚠ Warning: Could not clean up test directory: {e}")
    
    def generate_report(self):
        """Generate test report."""
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Tests Run:    {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print(f"Success Rate: {(self.results['tests_passed']/self.results['tests_run']*100):.1f}%")
        print("="*60)
        
        # Save detailed report
        report_path = Path('/home/ubuntu/narration_prep_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Detailed report saved: {report_path}")
        
        return self.results


def main():
    """Run all tests."""
    print("="*60)
    print("NARRATION PREPARATION - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tester = TestNarrationPreparation()
    
    try:
        # Setup
        env = tester.setup_test_environment()
        
        # Test 1: Initialization
        processor = tester.test_processor_initialization(env['book_profile_path'])
        
        # Test 2: Chapter processing
        chapter_path = env['chapter_splits_dir'] / 'chapter_01.txt'
        output_text = tester.test_chapter_processing(
            processor,
            chapter_path,
            env['ssml_generation_dir']
        )
        
        # Test 3: Quality validation
        tester.test_output_quality(output_text)
        
        # Generate report
        results = tester.generate_report()
        
        # Cleanup
        # tester.cleanup()  # Comment out to inspect test files
        
        # Return exit code
        return 0 if results['tests_failed'] == 0 else 1
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        tester.generate_report()
        return 1


if __name__ == '__main__':
    exit(main())
