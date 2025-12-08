"""
Narration Preparation Processor
AudiobookSmith - Phase 1.5 (Bridge between Chapter Splitting and SSML Generation)

This module transforms raw chapter files into narration-ready scripts with:
- Cultural authenticity (Cyrillic name conversion)
- SSML formatting (breaks, timing)
- Chapter announcements (intro/outro)
- Part introductions
- Quality validation

Author: Manus AI
Version: 1.0.0
Date: December 2025
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('narration_prep.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NarrationPreparationProcessor:
    """
    Processes raw chapter files into narration-ready scripts using AI-powered
    cultural authentication and SSML formatting.
    """
    
    def __init__(self, book_profile_path: str, openai_api_key: Optional[str] = None):
        """
        Initialize the processor with a book profile.
        
        Args:
            book_profile_path: Path to the bookProfile.json from Phase 2
            openai_api_key: OpenAI API key (defaults to environment variable)
        """
        self.book_profile = self._load_book_profile(book_profile_path)
        self.client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
        self.pronunciation_glossary = self._extract_pronunciation_glossary()
        self.ssml_break_rules = self._extract_ssml_break_rules()
        self.structural_outline = self.book_profile.get('structuralOutline', {})
        
        logger.info(f"Initialized NarrationPreparationProcessor with {len(self.pronunciation_glossary)} name mappings")
    
    def _load_book_profile(self, path: str) -> Dict:
        """Load and validate the book profile JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            logger.info(f"Loaded book profile from {path}")
            return profile
        except Exception as e:
            logger.error(f"Failed to load book profile: {e}")
            raise
    
    def _extract_pronunciation_glossary(self) -> Dict[str, str]:
        """Extract pronunciation glossary from book profile."""
        glossary = {}
        
        # From namedEntitiesAndTerminology
        entities = self.book_profile.get('namedEntitiesAndTerminology', {})
        
        # Characters
        for char in entities.get('characters', []):
            if char.get('isForeignName') and char.get('transliteration'):
                glossary[char['name']] = char['transliteration']
        
        # Places
        for place in entities.get('places', []):
            if place.get('isForeignName') and place.get('transliteration'):
                glossary[place['name']] = place['transliteration']
        
        # Direct pronunciation glossary
        if 'pronunciationGlossary' in entities:
            glossary.update(entities['pronunciationGlossary'])
        
        return glossary
    
    def _extract_ssml_break_rules(self) -> Dict[str, str]:
        """Extract SSML break rules from book profile."""
        narrative_style = self.book_profile.get('narrativeStyleAndTone', {})
        return narrative_style.get('recommendedSSMLBreakRules', {
            'chapterStart': '2s',
            'chapterEnd': '2s',
            'sceneTransition': '0.5s',
            'dialogueChange': '0.3s',
            'afterQuote': '0.8s'
        })
    
    def _get_chapter_metadata(self, chapter_number: int) -> Dict:
        """Get metadata for a specific chapter from structural outline."""
        chapters = self.structural_outline.get('chapterTitles', [])
        parts = self.structural_outline.get('parts', [])
        
        metadata = {
            'title': chapters[chapter_number - 1] if chapter_number <= len(chapters) else f"Chapter {chapter_number}",
            'is_part_start': False,
            'part_title': None,
            'next_chapter_title': chapters[chapter_number] if chapter_number < len(chapters) else None
        }
        
        # Check if this chapter starts a new part
        for part in parts:
            if chapter_number in part.get('chapters', []) and chapter_number == part['chapters'][0]:
                metadata['is_part_start'] = True
                metadata['part_title'] = part.get('label', '')
        
        return metadata
    
    def _build_narration_prompt(self, raw_text: str, chapter_number: int) -> str:
        """Build the AI prompt for narration preparation."""
        chapter_meta = self._get_chapter_metadata(chapter_number)
        
        prompt = f"""**You are an expert AI Narration Engineer.**

Your task is to transform a raw book chapter into a high-fidelity, narration-ready script. You must follow all rules and formatting requirements precisely, using the provided `bookProfile` to ensure cultural and contextual accuracy.

---

### **INPUT DATA**

**1. Book Profile**
```json
{json.dumps(self.book_profile, indent=2, ensure_ascii=False)}
```

**2. Chapter Metadata**
- Chapter Number: {chapter_number}
- Chapter Title: {chapter_meta['title']}
- Is Part Start: {chapter_meta['is_part_start']}
- Part Title: {chapter_meta.get('part_title', 'N/A')}
- Next Chapter Title: {chapter_meta.get('next_chapter_title', 'N/A')}

**3. Raw Chapter Text**
```text
{raw_text}
```

---

### **PROCESSING RULES & REQUIREMENTS**

**1. Cultural Authenticity & Name Conversion**
   - **Primary Rule**: You MUST replace all English-spelled proper nouns (characters, places) with their Cyrillic `transliteration` from the pronunciation glossary.
   - **Pronunciation Glossary**: {json.dumps(self.pronunciation_glossary, ensure_ascii=False)}
   - **Example**: If the text says "Vitaly went to Chernivtsi", and the glossary is {{"Vitaly": "Віталій", "Chernivtsi": "Чернівці"}}, the output MUST be "Віталій went to Чернівці".
   - **Hybrid Formatting**: For locations followed by an English noun (e.g., "street", "river"), maintain the hybrid structure. Example: "Fastivska street" becomes "Фастівська street".
   - **Cultural Terms**: Do NOT translate or alter cultural terms.
   - **Native Pronunciation**: The AI narrator will speak the Cyrillic script directly. Your output must contain the Cyrillic characters.

**2. SSML Formatting & Structure**
   - **SSML Break Rules**: {json.dumps(self.ssml_break_rules, ensure_ascii=False)}
   - **Chapter Start**: Insert `<break time="{self.ssml_break_rules.get('chapterStart', '2s')}" />` at the very beginning.
   - **Chapter End**: Insert `<break time="{self.ssml_break_rules.get('chapterEnd', '2s')}" />` at the very end.
   - **Scene Transitions**: Insert `<break time="{self.ssml_break_rules.get('sceneTransition', '0.5s')}" />` between paragraphs that indicate a scene change.
   - **After Quotes**: Insert `<break time="{self.ssml_break_rules.get('afterQuote', '0.8s')}" />` after block quotes or poems.
   
   - **Chapter Announcements**:
     - **Intro**: Add "Now, let's move on to Chapter {chapter_number}." before the chapter title.
     - **Outro**: Add "We've now come to the end of Chapter {chapter_number}." after the content.
     - **Next Chapter**: Add "Next up is Chapter {chapter_number + 1}: {chapter_meta.get('next_chapter_title', 'To be continued')}." if there is a next chapter.
   
   - **Part Introductions**: {"Add a part introduction: 'Now, we begin " + chapter_meta.get('part_title', '') + ".' before the chapter announcement." if chapter_meta['is_part_start'] else "No part introduction needed."}

**3. Content Filtering & Cleaning**
   - **Remove**: Page numbers, headers, footers, and any other non-narrative elements.
   - **Preserve**: The complete narrative text, paragraph breaks, and dialogue formatting.
   - **No Summarization**: Do NOT summarize, paraphrase, or alter the original narrative content in any way.

---

### **QUALITY CONTROL CHECKLIST**

Before finalizing your output, verify:
- [ ] All names and places from the pronunciation glossary are converted to Cyrillic
- [ ] Hybrid locations are correctly formatted (e.g., "Фастівська street")
- [ ] All `<break>` tags are inserted according to the rules
- [ ] Chapter announcements (intro and outro) are present
- [ ] No narrative text has been omitted, summarized, or invented
- [ ] The output is clean, readable, and follows all structural guidelines

---

**Now, process the provided data and generate the final, narration-ready script. Output ONLY the narration-ready text with SSML tags. Do not include any explanations or metadata.**
"""
        return prompt
    
    def process_chapter(self, raw_chapter_path: str, chapter_number: int, output_path: str) -> Dict:
        """
        Process a single raw chapter file into a narration-ready script.
        
        Args:
            raw_chapter_path: Path to the raw chapter text file
            chapter_number: Chapter number (1-indexed)
            output_path: Path to save the narration-ready output
        
        Returns:
            Dict with processing results and validation status
        """
        logger.info(f"Processing chapter {chapter_number}: {raw_chapter_path}")
        
        try:
            # Read raw chapter text
            with open(raw_chapter_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            # Build prompt
            prompt = self._build_narration_prompt(raw_text, chapter_number)
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API for chapter {chapter_number}")
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",  # Using the model specified in the environment
                messages=[
                    {"role": "system", "content": "You are an expert AI Narration Engineer specializing in culturally-authentic audiobook script preparation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistency
                max_tokens=16000  # Sufficient for long chapters
            )
            
            narration_ready_text = response.choices[0].message.content
            
            # Validate output
            validation_results = self._validate_output(narration_ready_text, raw_text, chapter_number)
            
            # Save output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(narration_ready_text)
            
            logger.info(f"Successfully processed chapter {chapter_number} -> {output_path}")
            
            return {
                'chapter_number': chapter_number,
                'input_path': raw_chapter_path,
                'output_path': output_path,
                'validation': validation_results,
                'status': 'success'
            }
        
        except Exception as e:
            logger.error(f"Failed to process chapter {chapter_number}: {e}")
            return {
                'chapter_number': chapter_number,
                'input_path': raw_chapter_path,
                'output_path': output_path,
                'error': str(e),
                'status': 'failed'
            }
    
    def _validate_output(self, narration_text: str, raw_text: str, chapter_number: int) -> Dict:
        """Validate the narration-ready output against quality checklist."""
        validation = {
            'cyrillic_names_found': 0,
            'ssml_breaks_found': 0,
            'chapter_announcement_present': False,
            'content_length_ratio': 0.0,
            'warnings': []
        }
        
        # Check for Cyrillic characters (indicates name conversion)
        cyrillic_pattern = re.compile(r'[\u0400-\u04FF]+')
        validation['cyrillic_names_found'] = len(cyrillic_pattern.findall(narration_text))
        
        # Check for SSML breaks
        break_pattern = re.compile(r'<break time="[^"]+"\s*/>')
        validation['ssml_breaks_found'] = len(break_pattern.findall(narration_text))
        
        # Check for chapter announcements
        if f"Chapter {chapter_number}" in narration_text:
            validation['chapter_announcement_present'] = True
        
        # Check content length ratio (should be close to 1.0, allowing for SSML additions)
        raw_length = len(raw_text.strip())
        narration_length = len(re.sub(r'<break[^>]*>', '', narration_text).strip())
        validation['content_length_ratio'] = narration_length / raw_length if raw_length > 0 else 0.0
        
        # Generate warnings
        if validation['cyrillic_names_found'] == 0:
            validation['warnings'].append("No Cyrillic characters found - name conversion may not have occurred")
        
        if validation['ssml_breaks_found'] < 3:
            validation['warnings'].append("Fewer than 3 SSML breaks found - formatting may be incomplete")
        
        if not validation['chapter_announcement_present']:
            validation['warnings'].append("Chapter announcement not found")
        
        if validation['content_length_ratio'] < 0.8 or validation['content_length_ratio'] > 1.2:
            validation['warnings'].append(f"Content length ratio {validation['content_length_ratio']:.2f} is outside expected range")
        
        return validation
    
    def process_all_chapters(self, input_dir: str, output_dir: str) -> Dict:
        """
        Process all chapter files in a directory.
        
        Args:
            input_dir: Directory containing raw chapter files
            output_dir: Directory to save narration-ready files
        
        Returns:
            Summary of processing results
        """
        input_path = Path(input_dir)
        chapter_files = sorted(input_path.glob('*.txt'))
        
        results = {
            'total_chapters': len(chapter_files),
            'successful': 0,
            'failed': 0,
            'chapter_results': []
        }
        
        for idx, chapter_file in enumerate(chapter_files, start=1):
            output_file = Path(output_dir) / f"{chapter_file.stem}_narration_ready.txt"
            result = self.process_chapter(str(chapter_file), idx, str(output_file))
            results['chapter_results'].append(result)
            
            if result['status'] == 'success':
                results['successful'] += 1
            else:
                results['failed'] += 1
        
        # Save summary report
        report_path = Path(output_dir) / 'narration_prep_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processing complete: {results['successful']}/{results['total_chapters']} chapters successful")
        
        return results


def main():
    """Example usage of the NarrationPreparationProcessor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare chapters for narration')
    parser.add_argument('--book-profile', required=True, help='Path to bookProfile.json')
    parser.add_argument('--input-dir', required=True, help='Directory with raw chapter files')
    parser.add_argument('--output-dir', required=True, help='Directory for narration-ready files')
    parser.add_argument('--chapter-number', type=int, help='Process single chapter (optional)')
    
    args = parser.parse_args()
    
    processor = NarrationPreparationProcessor(args.book_profile)
    
    if args.chapter_number:
        # Process single chapter
        chapter_file = Path(args.input_dir) / f"chapter_{args.chapter_number:02d}.txt"
        output_file = Path(args.output_dir) / f"chapter_{args.chapter_number:02d}_narration_ready.txt"
        result = processor.process_chapter(str(chapter_file), args.chapter_number, str(output_file))
        print(json.dumps(result, indent=2))
    else:
        # Process all chapters
        results = processor.process_all_chapters(args.input_dir, args.output_dir)
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
