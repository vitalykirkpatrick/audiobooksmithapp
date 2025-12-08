"""
AudiobookSmith Book Processor v9 - AI Chapter Detection
- Universal format support (PDF, EPUB, DOCX, TXT, RTF, MOBI, AZW, AZW3)
- AI-based chapter detection (eliminates false positives)
- Simplified processing with toggleable advanced features
- Smart chapter numbering (Prologue=00, Chapters=01-99, Epilogue=900)
- 10-folder production pipeline
"""

import os
import re
import json
from datetime import datetime
from openai import OpenAI


class ContentValidationError(Exception):
    """Custom exception for content validation failures"""
    def __init__(self, message, user_message, suggestions=None):
        self.message = message
        self.user_message = user_message
        self.suggestions = suggestions or []
        super().__init__(self.message)


class AIBookProcessor:
    def __init__(self, book_path, project_id, user_email="unknown@example.com", 
                 working_dir="/root/audiobook_working", 
                 enable_narration_prep=False,
                 enable_voice_recommendations=False,
                 openai_api_key=None,
                 openai_org_id=None):
        self.book_path = book_path
        self.project_id = project_id
        self.user_email = user_email
        self.working_dir = working_dir
        self.enable_narration_prep = enable_narration_prep
        self.enable_voice_recommendations = enable_voice_recommendations
        
        # Set OpenAI credentials if provided
        if openai_api_key:
            os.environ['OPENAI_API_KEY'] = openai_api_key
        if openai_org_id:
            os.environ['OPENAI_ORG_ID'] = openai_org_id
        
        # Create session-based folder structure
        self.session_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        # Main structure: working_dir/user_folder/book_projects/book_name/processing_sessions/session_id/
        self.user_folder = self.sanitize_folder_name(user_email.replace('@', '_at_').replace('.', '_'))
        self.book_folder = self.sanitize_folder_name(f"book_{project_id}")
        
        self.user_dir = os.path.join(working_dir, self.user_folder)
        self.book_projects_dir = os.path.join(self.user_dir, "book_projects")
        self.book_dir = os.path.join(self.book_projects_dir, self.book_folder)
        self.processing_sessions_dir = os.path.join(self.book_dir, "processing_sessions")
        self.session_dir = os.path.join(self.processing_sessions_dir, self.session_id)
        
        # Processing pipeline folders (numbered for order)
        self.folders = {
            "01_raw_text": os.path.join(self.session_dir, "01_raw_text"),
            "02_metadata": os.path.join(self.session_dir, "02_metadata"),
            "03_chapter_analysis": os.path.join(self.session_dir, "03_chapter_analysis"),
            "04_cleaned_text": os.path.join(self.session_dir, "04_cleaned_text"),
            "05_chapter_splits": os.path.join(self.session_dir, "05_chapter_splits"),
            "06_narration_prep": os.path.join(self.session_dir, "06_narration_prep"),
            "07_voice_samples": os.path.join(self.session_dir, "07_voice_samples"),
            "08_audio_ready": os.path.join(self.session_dir, "08_audio_ready"),
            "09_quality_reports": os.path.join(self.session_dir, "09_quality_reports"),
            "10_delivery_package": os.path.join(self.session_dir, "10_delivery_package")
        }
        
        # Initialize OpenAI client
        self.client = OpenAI()
        
        # Create all directories
        self._create_folder_structure()
        
        # Validation thresholds
        self.MIN_WORD_COUNT = 1000
        self.MIN_PAGES = 3
        self.MAX_PAGES = 1000
    
    def sanitize_folder_name(self, name):
        """Sanitize folder name to be filesystem-safe"""
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.strip('. ')
        if len(name) > 200:
            name = name[:200]
        return name or "unnamed"
    
    def _create_folder_structure(self):
        """Create all necessary folders"""
        os.makedirs(self.session_dir, exist_ok=True)
        for folder_name, folder_path in self.folders.items():
            os.makedirs(folder_path, exist_ok=True)
    
    def extract_text_from_book(self):
        """Extract text from book file using UniversalTextExtractor"""
        print(f"📖 Extracting text from {os.path.basename(self.book_path)}...")
        
        try:
            from universal_text_extractor import UniversalTextExtractor
            extractor = UniversalTextExtractor()
            text = extractor.extract_text(self.book_path)
            
            if not text or len(text.strip()) < 100:
                raise ContentValidationError(
                    "Text extraction failed or resulted in insufficient content",
                    "Unable to extract readable text from the uploaded file. Please ensure the file is not corrupted or password-protected.",
                    ["Try uploading a different format (PDF, EPUB, DOCX, TXT)", 
                     "Ensure the file is not password-protected",
                     "Check if the file contains actual text (not just scanned images)"]
                )
            
            # Save raw text
            raw_text_path = os.path.join(self.folders["01_raw_text"], "full_book_text.txt")
            with open(raw_text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"✅ Extracted {len(text)} characters")
            return text
            
        except ImportError:
            # Fallback to simple PDF extraction if UniversalTextExtractor not available
            print("⚠️ UniversalTextExtractor not found, using fallback PDF extraction")
            return self._fallback_pdf_extraction()
    
    def _fallback_pdf_extraction(self):
        """Fallback PDF extraction using PyPDF2"""
        try:
            import PyPDF2
            text = ""
            with open(self.book_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            if not text or len(text.strip()) < 100:
                raise ContentValidationError(
                    "PDF text extraction failed",
                    "Unable to extract text from PDF. The file may be scanned images or corrupted.",
                    ["Try uploading an EPUB or DOCX version", 
                     "Ensure the PDF contains selectable text"]
                )
            
            return text
        except Exception as e:
            raise ContentValidationError(
                f"Text extraction error: {str(e)}",
                "Failed to read the book file. Please try a different format.",
                ["Upload as EPUB, DOCX, or TXT format"]
            )
    
    def validate_content(self, text):
        """Validate extracted content meets minimum requirements"""
        print("🔍 Validating content...")
        
        # Count words
        words = text.split()
        word_count = len(words)
        
        # Estimate pages (250 words per page)
        estimated_pages = word_count / 250
        
        print(f"📊 Word count: {word_count:,}")
        print(f"📄 Estimated pages: {estimated_pages:.0f}")
        
        # Check minimum word count
        if word_count < self.MIN_WORD_COUNT:
            raise ContentValidationError(
                f"Content too short: {word_count} words (minimum: {self.MIN_WORD_COUNT})",
                f"The uploaded book is too short ({word_count:,} words). AudiobookSmith requires at least {self.MIN_WORD_COUNT:,} words.",
                ["Upload a longer book or manuscript",
                 "Combine multiple chapters into one file"]
            )
        
        # Check maximum pages
        if estimated_pages > self.MAX_PAGES:
            raise ContentValidationError(
                f"Content too long: {estimated_pages:.0f} pages (maximum: {self.MAX_PAGES})",
                f"The uploaded book is too long ({estimated_pages:.0f} pages). Please contact support for processing books over {self.MAX_PAGES} pages.",
                ["Split the book into volumes",
                 "Contact support for enterprise processing"]
            )
        
        print("✅ Content validation passed")
        return {
            "word_count": word_count,
            "estimated_pages": int(estimated_pages),
            "character_count": len(text)
        }
    
    def extract_metadata_with_ai(self, text):
        """Extract book metadata using AI"""
        print("🤖 Extracting metadata with AI...")
        
        # Use first 5000 characters for metadata extraction
        sample_text = text[:5000]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a book metadata extraction expert. Extract title, author, and genre from the provided text. Return ONLY valid JSON."},
                    {"role": "user", "content": f"Extract the book title, author name, and genre from this text:\n\n{sample_text}\n\nReturn JSON format: {{\"title\": \"...\", \"author\": \"...\", \"genre\": \"...\"}}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            metadata_json = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            metadata_json = re.sub(r'^```json\s*|\s*```$', '', metadata_json, flags=re.MULTILINE)
            metadata = json.loads(metadata_json)
            
            # Save metadata
            metadata_path = os.path.join(self.folders["02_metadata"], "book_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Metadata extracted: {metadata.get('title', 'Unknown')} by {metadata.get('author', 'Unknown')}")
            return metadata
            
        except Exception as e:
            print(f"⚠️ AI metadata extraction failed: {e}")
            return {
                "title": "Unknown Title",
                "author": "Unknown Author",
                "genre": "Unknown"
            }
    
    def detect_chapters_with_ai(self, text):
        """Detect chapters using AI to eliminate false positives"""
        print("🤖 Detecting chapters with AI...")
        
        # Skip table of contents by finding where actual content starts
        # Look for "Prologue" followed by actual paragraph text (not just page numbers)
        prologue_pattern = r'Prologue\s+[A-Z][a-z]'
        prologue_match = re.search(prologue_pattern, text)
        
        if prologue_match:
            # Start analysis from the prologue onwards (skip TOC)
            text_to_analyze = text[prologue_match.start():]
            print(f"  ✅ Skipped {prologue_match.start()} characters (TOC section)")
        else:
            # If no prologue found, skip first 10,000 chars as fallback
            text_to_analyze = text[10000:] if len(text) > 10000 else text
            print(f"  ⚠️  No prologue found, skipped first 10,000 chars")
        
        # Split text into chunks for analysis
        max_chunk_size = 50000  # Characters per chunk
        chunks = []
        for i in range(0, len(text_to_analyze), max_chunk_size):
            chunks.append(text_to_analyze[i:i + max_chunk_size])
        
        all_chapters = []
        
        for chunk_idx, chunk in enumerate(chunks):
            print(f"  Analyzing chunk {chunk_idx + 1}/{len(chunks)}...")
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "You are a chapter detection expert. Identify ONLY actual chapter headings from the BODY TEXT, NOT from table of contents, page numbers, headers, or footers. Skip any section that looks like a contents/index page. Return JSON array of chapter titles."},
                        {"role": "user", "content": f"Find all chapter headings in this text. IMPORTANT: Skip the table of contents section entirely - only detect chapters that appear in the actual body text with surrounding paragraphs. Ignore page numbers, running headers, footers, and TOC entries. Look for chapter markers followed by actual story content. Return ONLY chapter titles as JSON array:\n\n{chunk[:10000]}"}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                result = response.choices[0].message.content.strip()
                result = re.sub(r'^```json\s*|\s*```$', '', result, flags=re.MULTILINE)
                chapters = json.loads(result)
                
                if isinstance(chapters, list):
                    all_chapters.extend(chapters)
                    
            except Exception as e:
                print(f"⚠️ AI chapter detection failed for chunk {chunk_idx + 1}: {e}")
        
        # If AI detection fails or finds nothing, use fallback regex
        if not all_chapters:
            print("⚠️ AI detection found no chapters, using fallback regex...")
            all_chapters = self._fallback_chapter_detection(text)
        
        # Find positions of chapters in the body text (text_to_analyze, not full text)
        chapter_data = []
        for chapter_title in all_chapters:
            # Try multiple matching strategies
            match = None
            
            # Strategy 1: Exact match in body text
            pattern = re.escape(chapter_title)
            match = re.search(pattern, text_to_analyze, re.IGNORECASE)
            
            # Strategy 2: If no match, try matching just the core title without numbers/prefixes
            if not match:
                # Remove common prefixes like "Chapter 1:", "1.", etc.
                core_title = re.sub(r'^(Chapter\s+\d+[:\s]+|\d+[.\s]+)', '', chapter_title, flags=re.IGNORECASE).strip()
                if core_title:
                    pattern = re.escape(core_title)
                    match = re.search(pattern, text_to_analyze, re.IGNORECASE)
            
            # Strategy 3: Look for chapter number patterns followed by title
            if not match and 'chapter' in chapter_title.lower():
                # Extract chapter number
                num_match = re.search(r'\d+', chapter_title)
                if num_match:
                    chapter_num = num_match.group()
                    # Look for patterns like "Chapter 1", "CHAPTER 1", "1.", etc.
                    patterns = [
                        rf'Chapter\s+{chapter_num}[:\s]',
                        rf'CHAPTER\s+{chapter_num}[:\s]',
                        rf'^{chapter_num}[.\s]+',
                    ]
                    for p in patterns:
                        match = re.search(p, text_to_analyze, re.MULTILINE)
                        if match:
                            break
            
            if match:
                # Calculate actual position in original text
                # Need to account for the offset if we skipped TOC
                offset = len(text) - len(text_to_analyze)
                chapter_data.append({
                    "title": chapter_title,
                    "position": match.start() + offset
                })
        
        # Sort by position
        chapter_data.sort(key=lambda x: x["position"])
        
        # Assign smart chapter numbers
        numbered_chapters = []
        regular_chapter_num = 1
        
        for chapter in chapter_data:
            title = chapter["title"]
            title_lower = title.lower()
            
            if "prologue" in title_lower:
                chapter_num = "00"
            elif "epilogue" in title_lower:
                chapter_num = "900"
            else:
                chapter_num = f"{regular_chapter_num:02d}"
                regular_chapter_num += 1
            
            numbered_chapters.append({
                "number": chapter_num,
                "title": title,
                "position": chapter["position"]
            })
        
        # Save chapter analysis
        chapter_analysis_path = os.path.join(self.folders["03_chapter_analysis"], "detected_chapters.json")
        with open(chapter_analysis_path, 'w', encoding='utf-8') as f:
            json.dump(numbered_chapters, f, indent=2)
        
        print(f"✅ Detected {len(numbered_chapters)} chapters")
        return numbered_chapters
    
    def _fallback_chapter_detection(self, text):
        """Fallback regex-based chapter detection"""
        patterns = [
            r'^Chapter\s+\d+',
            r'^CHAPTER\s+\d+',
            r'^\d+\.\s+[A-Z]',
            r'^Part\s+\d+',
            r'^Prologue',
            r'^Epilogue'
        ]
        
        chapters = []
        for line in text.split('\n'):
            line = line.strip()
            for pattern in patterns:
                if re.match(pattern, line):
                    chapters.append(line)
                    break
        
        return chapters[:50]  # Limit to 50 chapters max
    
    def split_into_chapters(self, text, chapter_data):
        """Split text into individual chapter files"""
        print("✂️ Splitting text into chapters...")
        
        if not chapter_data:
            print("⚠️ No chapters detected, saving as single file")
            chapter_path = os.path.join(self.folders["05_chapter_splits"], "00_full_book.txt")
            with open(chapter_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return [{
                "number": "00",
                "title": "Full Book",
                "file": "00_full_book.txt",
                "word_count": len(text.split())
            }]
        
        split_chapters = []
        
        for i, chapter in enumerate(chapter_data):
            # Get chapter text
            start_pos = chapter["position"]
            end_pos = chapter_data[i + 1]["position"] if i + 1 < len(chapter_data) else len(text)
            chapter_text = text[start_pos:end_pos].strip()
            
            # Calculate word count
            word_count = len(chapter_text.split())
            
            # Validate chapter has reasonable content
            if word_count < 100 and i < len(chapter_data) - 1:
                print(f"  ⚠️  Chapter '{chapter['title']}' has only {word_count} words - might be misdetected")
            
            # Save chapter file
            chapter_num = chapter["number"]
            safe_title = self.sanitize_folder_name(chapter["title"])
            filename = f"{chapter_num}_{safe_title}.txt"
            chapter_path = os.path.join(self.folders["05_chapter_splits"], filename)
            
            with open(chapter_path, 'w', encoding='utf-8') as f:
                f.write(chapter_text)
            
            split_chapters.append({
                "number": chapter_num,
                "title": chapter["title"],
                "file": filename,
                "word_count": word_count
            })
            
            print(f"  ✅ Chapter {chapter_num}: {chapter['title'][:50]}... ({word_count} words)")
        
        print(f"✅ Split into {len(split_chapters)} chapter files")
        return split_chapters
    
    def prepare_narration_text(self, split_chapters):
        """Prepare narration-ready text for each chapter"""
        if not self.enable_narration_prep:
            print("⏭️  Narration prep disabled")
            return []
        
        print("\n📝 Preparing narration-ready text...")
        narration_chapters = []
        
        for chapter in split_chapters:
            # Read chapter file
            chapter_path = os.path.join(self.folders["05_chapter_splits"], chapter["file"])
            with open(chapter_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Clean text for narration
            narration_text = self.clean_for_narration(text, chapter["title"])
            
            # Save narration-ready file
            narration_filename = f"narration_{chapter['file']}"
            narration_path = os.path.join(self.folders["06_narration_prep"], narration_filename)
            with open(narration_path, 'w', encoding='utf-8') as f:
                f.write(narration_text)
            
            narration_chapters.append({
                "number": chapter["number"],
                "title": chapter["title"],
                "file": narration_filename,
                "word_count": len(narration_text.split()),
                "estimated_duration_minutes": len(narration_text.split()) / 150  # ~150 words per minute
            })
        
        print(f"✅ Prepared {len(narration_chapters)} narration files")
        return narration_chapters
    
    def clean_for_narration(self, text, chapter_title):
        """Clean text for natural narration"""
        # Add chapter announcement at the beginning
        narration_text = f"{chapter_title}\n\n{text}"
        
        # Remove excessive whitespace
        narration_text = re.sub(r'\n{3,}', '\n\n', narration_text)
        narration_text = re.sub(r' {2,}', ' ', narration_text)
        
        # Expand common abbreviations for better narration
        abbreviations = {
            r'\bMr\.': 'Mister',
            r'\bMrs\.': 'Missus',
            r'\bDr\.': 'Doctor',
            r'\bProf\.': 'Professor',
            r'\bSt\.': 'Saint',
            r'\betc\.': 'etcetera',
        }
        
        for abbr, expansion in abbreviations.items():
            narration_text = re.sub(abbr, expansion, narration_text)
        
        return narration_text.strip()
    
    def recommend_voices(self, metadata, split_chapters):
        """Recommend ElevenLabs voices based on book metadata"""
        if not self.enable_voice_recommendations:
            print("⏭️  Voice recommendations disabled")
            return {}
        
        print("\n🎤 Generating voice recommendations...")
        
        # Detect language
        try:
            from language_detector import LanguageDetector
            detector = LanguageDetector()
            
            # Get sample text from first chapter
            first_chapter_path = os.path.join(self.folders["05_chapter_splits"], split_chapters[0]["file"])
            with open(first_chapter_path, 'r', encoding='utf-8') as f:
                sample_text = f.read()[:1000]  # First 1000 chars
            
            language_info = detector.detect_language(sample_text)
            language = language_info.get('language', 'English')
            language_code = language_info.get('code', 'en')
        except Exception as e:
            print(f"⚠️  Language detection failed: {e}")
            language = "English"
            language_code = "en"
        
        # Use AI to recommend voices
        try:
            client = OpenAI()
            
            prompt = f"""Based on this book information, recommend 3 suitable narrator voice types:

Title: {metadata.get('title', 'Unknown')}
Author: {metadata.get('author', 'Unknown')}
Genre: {metadata.get('genre', 'Unknown')}
Language: {language}
Chapters: {len(split_chapters)}

Provide recommendations in this JSON format:
{{
  "primary_voice": {{
    "type": "male/female/neutral",
    "age_range": "young/middle-aged/mature",
    "tone": "warm/authoritative/energetic/calm",
    "accent": "American/British/Neutral",
    "reasoning": "why this voice fits"
  }},
  "alternative_voices": [
    {{
      "type": "...",
      "age_range": "...",
      "tone": "...",
      "accent": "...",
      "reasoning": "..."
    }}
  ],
  "narration_style": "dramatic/conversational/documentary/storytelling"
}}"""
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            voice_recommendations = json.loads(response.choices[0].message.content)
            voice_recommendations["detected_language"] = language
            voice_recommendations["language_code"] = language_code
            
            # Save recommendations
            recommendations_path = os.path.join(self.folders["07_voice_samples"], "voice_recommendations.json")
            with open(recommendations_path, 'w', encoding='utf-8') as f:
                json.dump(voice_recommendations, f, indent=2)
            
            print(f"✅ Voice recommendations generated ({language})")
            return voice_recommendations
            
        except Exception as e:
            print(f"⚠️  Voice recommendation failed: {e}")
            return {
                "detected_language": language,
                "language_code": language_code,
                "error": str(e)
            }
    
    def process_book(self):
        """Main processing pipeline"""
        print("\n" + "="*70)
        print("AudiobookSmith Book Processor v9 - AI Chapter Detection")
        print("="*70 + "\n")
        
        try:
            # Step 1: Extract text
            text = self.extract_text_from_book()
            
            # Step 2: Validate content
            validation_results = self.validate_content(text)
            
            # Step 3: Extract metadata
            metadata = self.extract_metadata_with_ai(text)
            
            # Step 4: Detect chapters with AI
            chapter_data = self.detect_chapters_with_ai(text)
            
            # Step 5: Split into chapters
            split_chapters = self.split_into_chapters(text, chapter_data)
            
            # Step 6: Prepare narration text (if enabled)
            narration_chapters = self.prepare_narration_text(split_chapters)
            
            # Step 7: Recommend voices (if enabled)
            voice_recommendations = self.recommend_voices(metadata, split_chapters)
            
            # Calculate total estimated audiobook duration
            if narration_chapters:
                total_duration = sum(ch.get('estimated_duration_minutes', 0) for ch in narration_chapters)
                hours = int(total_duration // 60)
                minutes = int(total_duration % 60)
                estimated_duration = f"{hours}h {minutes}m"
            else:
                total_words = validation_results['word_count']
                total_minutes = total_words / 150
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                estimated_duration = f"{hours}h {minutes}m"
            
            # Build final result
            result = {
                "success": True,
                "session_id": self.session_id,
                "session_dir": self.session_dir,
                "metadata": metadata,
                "validation": validation_results,
                "chapters": split_chapters,
                "narration_chapters": narration_chapters,
                "voice_recommendations": voice_recommendations,
                "estimated_duration": estimated_duration,
                "folder_structure": self.folders
            }
            
            # Save final report
            report_path = os.path.join(self.folders["10_delivery_package"], "processing_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            print("\n" + "="*70)
            print("✅ PROCESSING COMPLETE")
            print("="*70)
            print(f"📊 Session ID: {self.session_id}")
            print(f"📚 Book: {metadata.get('title', 'Unknown')}")
            print(f"✍️ Author: {metadata.get('author', 'Unknown')}")
            print(f"📖 Chapters: {len(split_chapters)}")
            print(f"📝 Words: {validation_results['word_count']:,}")
            print("="*70 + "\n")
            
            return result
            
        except ContentValidationError as e:
            print(f"\n❌ Validation Error: {e.user_message}")
            return {
                "success": False,
                "error": e.user_message,
                "suggestions": e.suggestions
            }
        except Exception as e:
            print(f"\n❌ Processing Error: {str(e)}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}"
            }


if __name__ == "__main__":
    # Test with a sample book
    import sys
    if len(sys.argv) > 1:
        book_path = sys.argv[1]
        processor = AIBookProcessor(
            book_path=book_path,
            project_id="test_book",
            user_email="test@audiobooksmith.com"
        )
        result = processor.process_book()
        print(json.dumps(result, indent=2))
