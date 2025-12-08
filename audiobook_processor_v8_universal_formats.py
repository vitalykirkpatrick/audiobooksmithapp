"""
AudiobookSmith Book Processor v8 - Universal Format Support
- All v7 features (validation, folder structure, voice recommendations)
- Support for PDF, EPUB, DOCX, TXT, RTF, MOBI, AZW formats
- Universal text extraction with format detection
- Automatic voice sample generation using book excerpt
"""

from progress_tracker import ProgressTracker
from universal_text_extractor import UniversalTextExtractor
import os
import re
import json
from datetime import datetime
from openai import OpenAI

# Import voice recommender
import sys
sys.path.insert(0, os.path.dirname(__file__))
from elevenlabs_voice_recommender import ElevenLabsVoiceRecommender
from prepare_voice_sample_text import prepare_voice_sample_text
from simple_narration_prep import prepare_chapter_for_narration


class ContentValidationError(Exception):
    """Custom exception for content validation failures"""
    def __init__(self, message, user_message, suggestions=None):
        self.message = message
        self.user_message = user_message
        self.suggestions = suggestions or []
        super().__init__(self.message)


class AIBookProcessor:
    def __init__(self, pdf_path, project_id, user_email="unknown@example.com", 
                 working_dir="/root/audiobook_working", elevenlabs_api_key=None):
        self.pdf_path = pdf_path
        self.project_id = project_id
        self.user_email = user_email
        self.working_dir = working_dir
        
        # ElevenLabs API key
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        
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
            "01_raw_files": os.path.join(self.session_dir, "01_raw_files"),
            "02_structure_analysis": os.path.join(self.session_dir, "02_structure_analysis"),
            "03_processed_text": os.path.join(self.session_dir, "03_processed_text"),
            "04_language_processing": os.path.join(self.session_dir, "04_language_processing"),
            "05_chapter_splits": os.path.join(self.session_dir, "05_chapter_splits"),
            "06_ssml_generation": os.path.join(self.session_dir, "06_ssml_generation"),
            "07_audio_ready": os.path.join(self.session_dir, "07_audio_ready"),
            "08_quality_control": os.path.join(self.session_dir, "08_quality_control"),
            "09_elevenlabs_integration": os.path.join(self.session_dir, "09_elevenlabs_integration"),
            "10_final_delivery": os.path.join(self.session_dir, "10_final_delivery"),
            "99_rollback_data": os.path.join(self.session_dir, "99_rollback_data")
        }
        
        # Additional folders
        self.comparison_reports_dir = os.path.join(self.book_dir, "comparison_reports")
        self.quality_metrics_dir = os.path.join(self.book_dir, "quality_metrics")
        
        # Initialize OpenAI client
        self.client = OpenAI()
        
        # Initialize voice recommender if API key available
        self.voice_recommender = None
        if self.elevenlabs_api_key:
            try:
                self.voice_recommender = ElevenLabsVoiceRecommender(self.elevenlabs_api_key)
            except Exception as e:
                print(f"⚠️ Could not initialize voice recommender: {e}")
        
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
        """Create complete folder structure"""
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.comparison_reports_dir, exist_ok=True)
        os.makedirs(self.quality_metrics_dir, exist_ok=True)
        
        for folder_path in self.folders.values():
            os.makedirs(folder_path, exist_ok=True)
        
        # Create ElevenLabs subfolders
        elevenlabs_subfolders = ['input_ssml', 'generated_audio', 'processing_logs', 'voice_settings', 'voice_samples']
        for subfolder in elevenlabs_subfolders:
            os.makedirs(os.path.join(self.folders["09_elevenlabs_integration"], subfolder), exist_ok=True)
        
        # Create Amazon delivery subfolders
        amazon_subfolders = ['audio_files', 'metadata', 'cover_art', 'submission_package']
        for subfolder in amazon_subfolders:
            os.makedirs(os.path.join(self.folders["10_final_delivery"], subfolder), exist_ok=True)
        
        print(f"✅ Created folder structure for session: {self.session_id}")
    
    def extract_text_from_pdf(self):
        """Extract text from any supported ebook format (renamed for compatibility)"""
        print(f"[1/7] Extracting text from: {self.pdf_path}")
        
        # Update progress (if tracker is available)
        if hasattr(self, 'progress_tracker') and self.progress_tracker:
            self.progress_tracker.update(15, "Extracting Text", f"Reading {UniversalTextExtractor.get_format_name(self.pdf_path)}...")
        
        try:
            # Check if format is supported
            if not UniversalTextExtractor.is_supported(self.pdf_path):
                file_ext = os.path.splitext(self.pdf_path)[1]
                raise ContentValidationError(
                    f"Unsupported file format: {file_ext}",
                    f"This file format ({file_ext}) is not supported. Please upload a PDF, EPUB, DOCX, or TXT file.",
                    ["Convert your file to PDF", "Export as EPUB", "Save as DOCX or TXT"]
                )
            
            # Extract text using universal extractor
            extractor = UniversalTextExtractor(self.pdf_path)
            text, page_count = extractor.extract()
            
            # Save extracted text
            text_file = os.path.join(self.folders["01_raw_files"], "extracted_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"✅ Extracted {len(text)} characters from {page_count} pages")
            return text, page_count
            
        except ContentValidationError:
            raise
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            raise ContentValidationError(
                f"Text extraction error: {e}",
                "Unable to process this file. It may be corrupted or in an unsupported format.",
                ["Try re-saving the file", "Convert to PDF format", "Check that the file is not corrupted"]
            )
    
    def ai_validate_content(self, text):
        """STRICT AI validation to reject non-book documents"""
        print(f"[2/7] Validating content suitability for audiobook production...")
        
        sample = text[:3000]
        
        prompt = f"""You are a strict content validator for an audiobook production service.

Analyze this document and determine if it is suitable for audiobook production.

Document sample:
{sample}

STRICT RULES:
✅ ACCEPT ONLY:
- Fiction books (novels, short stories, novellas)
- Non-fiction narrative books (memoirs, biographies, autobiographies)
- Self-help books with narrative structure
- Educational books with narrative flow
- Sample chapters from books

❌ REJECT ALL:
- Business proposals or templates
- Deployment guides, setup instructions, how-to guides
- Technical documentation, API documentation
- Requirements documents (SRS, PRD, specifications)
- Templates of any kind (forms, applications, etc.)
- Academic papers, research papers
- Reports (business, technical, analysis)
- Presentations, slide decks
- Reference materials, glossaries
- Marketing materials, brochures
- Legal documents, contracts
- Configuration files, code documentation
- Workflow documentation
- Instruction manuals, user guides

Return ONLY a JSON object:
{{
    "is_suitable": true/false,
    "document_type": "Novel/Memoir/Template/Guide/Report/etc",
    "estimated_genre": "Fiction/Non-fiction/Memoir/etc",
    "confidence": 0.0-1.0,
    "reason": "Brief explanation",
    "rejection_category": "template/guide/report/manual/academic/etc" (if rejected)
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a strict content validator. Reject anything that is not a narrative book or story."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if not result.get('is_suitable', False):
                rejection_category = result.get('rejection_category', 'unsuitable content')
                
                user_messages = {
                    "template": "This appears to be a template document, not a book. Our service is for audiobook production, not template processing.",
                    "guide": "This appears to be a guide or instruction manual, not a book suitable for audiobook narration.",
                    "report": "This appears to be a report or analysis document, not a narrative book.",
                    "manual": "This appears to be a technical or user manual, not a book for audiobook production.",
                    "academic": "This appears to be an academic paper or research document, not a narrative book."
                }
                
                user_message = user_messages.get(rejection_category, 
                    "This document is not suitable for audiobook production. We accept narrative books and stories only.")
                
                print(f"❌ Content Validation Failed: {result.get('reason')}")
                print(f"   User Message: {user_message}")
                
                raise ContentValidationError(
                    result.get('reason', 'Content not suitable'),
                    user_message,
                    ["Upload an actual book, short story, or sample chapter",
                     "Not suitable: templates, forms, proposals, guides",
                     "Suitable: novels, memoirs, biographies, self-help books"]
                )
            
            print(f"✅ Content validated: {result.get('document_type')} - {result.get('estimated_genre')}")
            return result
            
        except ContentValidationError:
            raise
        except Exception as e:
            print(f"⚠️ AI validation error: {e}")
            return {
                "is_suitable": True,
                "document_type": "Unknown",
                "confidence": 0.5,
                "reason": "Validation check failed",
                "estimated_genre": "Unknown"
            }
    
    def ai_extract_metadata(self, text):
        """Extract title, author, and detailed metadata using AI"""
        print(f"[3/7] Extracting book metadata (title, author, themes)...")
        
        # Use first 5000 characters for metadata extraction
        sample = text[:5000]
        
        prompt = """Analyze this book excerpt and extract key metadata.
    
    Book excerpt:
    """ + sample + """
    
    Extract and return ONLY a JSON object with:
    {
        "title": "The actual book title (if found in text)",
        "author": "The author's name (if found in text)",
        "genre": "Specific genre (e.g., Memoir, Thriller, Romance, Self-Help)",
        "themes": ["theme1", "theme2", "theme3"],
        "narrative_tone": "Description of narrative voice and tone",
        "target_audience": "Who this book is for",
        "content_warnings": ["any sensitive content"],
        "estimated_age_rating": "General/Teen/Adult"
    }
    
    If title or author not found in text, use "Unknown"."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a literary analyst. Extract metadata from book text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            import json
            metadata = json.loads(response.choices[0].message.content)
            print(f"✅ Metadata extracted: {metadata.get('title')} by {metadata.get('author')}")
            return metadata
            
        except Exception as e:
            print(f"⚠️ Metadata extraction error: {e}")
            return {
                "title": "Unknown",
                "author": "Unknown",
                "genre": "Unknown",
                "themes": [],
                "narrative_tone": "Unknown",
                "target_audience": "General",
                "content_warnings": [],
                "estimated_age_rating": "General"
            }
    
    
    def ai_detect_chapters(self, text):
        """Detect chapters using AI analysis"""
        print(f"[4/7] Detecting chapters and structure...")
        
        # Use more text for chapter detection (first 100000 chars to cover more chapters)
        sample = text[:100000]
        
        prompt = """Analyze this book text and detect all chapters.
    
    Book text:
    """ + sample + """
    
    Detect chapter markers like:
    - "Chapter 1", "Chapter One", "CHAPTER 1"
    - "Part I", "Part One" (only if they mark major sections)
    - "Prologue", "Epilogue"
    - "Section 1", numbered sections
    - Any other chapter/section markers
    
    IMPORTANT:
    - For "start_text", provide the first 10-20 words of the ACTUAL CHAPTER CONTENT (not just the title)
    - Skip Part/Section markers that are just headers - focus on actual chapters with content
    - If a Part marker is followed immediately by a Chapter, only include the Chapter
    
    Return ONLY a JSON object:
    {
        "total_chapters": number,
        "chapters": [
            {
                "number": 1,
                "title": "Chapter title or 'Chapter 1'",
                "start_text": "First 10-20 words of actual chapter content (not the title)"
            }
        ],
        "has_prologue": true/false,
        "has_epilogue": true/false,
        "structure_type": "chapters/parts/sections/mixed"
    }
    
    Example:
    If the text shows:
    'Chapter 1: The Beginning\nIt was a dark and stormy night when...'
    Then start_text should be: "It was a dark and stormy night when"
    
    If no clear chapters found, return total_chapters: 0 and empty chapters array."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a book structure analyzer. Detect chapters and sections."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            structure = json.loads(response.choices[0].message.content)
            total = structure.get('total_chapters', 0)
            print(f"✅ Detected {total} chapters")
            return structure
            
        except Exception as e:
            print(f"⚠️ Chapter detection error: {e}")
            return {
                "total_chapters": 0,
                "chapters": [],
                "has_prologue": False,
                "has_epilogue": False,
                "structure_type": "unknown"
            }
    
    def split_chapters_to_files(self, text, chapter_structure):
        """Split text into individual chapter files using regex - ACX COMPLIANT"""
        import re
        print(f"[5/7] Splitting text into chapter files (regex-based)...")
        
        # Define chapter marker patterns (more selective to avoid page numbers)
        chapter_patterns = [
            # Pattern 1: "Chapter X" or "CHAPTER X"
            r'(?:^|\n)\s*(?:CHAPTER|Chapter)\s+(\d+|[IVXLCDM]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)(?:\s*[:\-\.]?\s*([^\n]*))?(?:\n|$)',
            
            # Pattern 2: Single digit (1-50) followed by newline AND a title line (to avoid page numbers)
            r'(?:^|\n)\s*([1-9]|[1-4][0-9]|50)\s*\n\s*([A-Z][^\n]{3,50})\s*\n',
            
            # Pattern 3: Prologue, Epilogue, etc
            r'(?:^|\n)\s*(Prologue|Epilogue|Preface|Introduction|Conclusion)(?:\s*[:\-]?\s*([^\n]*))?(?:\n|$)',
            
            # Pattern 4: Part markers
            r'(?:^|\n)\s*(?:PART|Part)\s+([IVXLCDM]+|One|Two|Three|Four|Five)(?:\s*[:\-\.]?\s*([^\n]*))?(?:\n|$)',
        ]
        
        # Find all chapter markers
        chapter_markers = []
        for pattern in chapter_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                pos = match.start()
                groups = match.groups()
                chapter_num = groups[0] if groups else ""
                chapter_title = groups[1] if len(groups) > 1 and groups[1] else ""
                full_title = f"{chapter_num} {chapter_title}".strip() if chapter_title else chapter_num.strip()
                
                chapter_markers.append({
                    'position': pos,
                    'number': chapter_num,
                    'title': full_title
                })
        
        # Remove duplicates at same position
        unique_markers = []
        seen_positions = set()
        for marker in sorted(chapter_markers, key=lambda x: x['position']):
            is_duplicate = any(abs(marker['position'] - pos) < 50 for pos in seen_positions)
            if not is_duplicate:
                unique_markers.append(marker)
                seen_positions.add(marker['position'])
        
        chapter_markers = sorted(unique_markers, key=lambda x: x['position'])
        
        print(f"  Found {len(chapter_markers)} chapter markers")
        
        if not chapter_markers:
            print("⚠️ No chapters detected, saving full text")
            full_text_file = os.path.join(self.folders["05_chapter_splits"], "full_text.txt")
            with open(full_text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            return {"chapter_files": [{"file": "full_text.txt", "title": "Full Text", "word_count": len(text.split())}]}
        
        # Extract chapters
        chapter_files = []
        for i, marker in enumerate(chapter_markers):
            start_pos = marker['position']
            end_pos = chapter_markers[i + 1]['position'] if i < len(chapter_markers) - 1 else len(text)
            
            chapter_text = text[start_pos:end_pos].strip()
            safe_title = self.sanitize_folder_name(marker['title']) or f"Chapter_{i+1}"
            filename = f"{i+1:02d}_{safe_title}.txt"
            filepath = os.path.join(self.folders["05_chapter_splits"], filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chapter_text)
            
            word_count = len(chapter_text.split())
            chapter_files.append({
                "number": i + 1,
                "title": marker['title'],
                "file": filename,
                "word_count": word_count,
                "path": filepath,
                "start_pos": start_pos,
                "end_pos": end_pos
            })
            
            print(f"  ✓ {filename} ({word_count:,} words)")
        
        self._create_credits_files(chapter_files)
        print(f"✅ Split into {len(chapter_files)} chapter files + credits")
        return {"chapter_files": chapter_files}
    

    def prepare_chapters_for_narration(self, chapter_split_result, book_info):
        """
        Prepare all chapter files for narration with Cyrillic names and SSML formatting.
        This creates Audible-ready narration scripts in the 06_narration_prep folder.
        """
        print(f"\n[4/7] Preparing chapters for narration...")
        
        chapter_files = chapter_split_result.get('chapter_files', [])
        if not chapter_files:
            print("⚠️ No chapter files to prepare")
            return None
        
        # Create narration prep output directory
        narration_output_dir = os.path.join(self.session_dir, "06_narration_prep")
        os.makedirs(narration_output_dir, exist_ok=True)
        
        results = {
            "total_chapters": len(chapter_files),
            "successful": 0,
            "failed": 0,
            "chapter_results": []
        }
        
        for i, chapter_file_info in enumerate(chapter_files):
            chapter_path = chapter_file_info['path']
            chapter_title = chapter_file_info['title']
            
            print(f"   [{i+1}/{len(chapter_files)}] Preparing: {chapter_title}")
            
            try:
                # Read raw chapter
                with open(chapter_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                
                # Determine chapter info
                is_prologue = 'prologue' in chapter_title.lower()
                is_epilogue = 'epilogue' in chapter_title.lower()
                chapter_number = i + 1 if not (is_prologue or is_epilogue) else None
                
                # Get next chapter title
                next_title = chapter_files[i+1]['title'] if i+1 < len(chapter_files) else None
                
                # Prepare for narration
                narration_ready = prepare_chapter_for_narration(
                    chapter_text=raw_text,
                    chapter_number=chapter_number or i+1,
                    chapter_title=chapter_title,
                    book_info=book_info,
                    is_prologue=is_prologue,
                    is_epilogue=is_epilogue,
                    part_info=None,  # TODO: Detect parts from chapter structure
                    next_chapter_title=next_title
                )
                
                # Save narration-ready file
                output_filename = f"{str(i+1).zfill(2)}_{chapter_title.replace(' ', '_').replace(':', '')}_narration_ready.txt"
                output_path = os.path.join(narration_output_dir, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(narration_ready)
                
                results["successful"] += 1
                results["chapter_results"].append({
                    "chapter_number": i+1,
                    "chapter_title": chapter_title,
                    "status": "success",
                    "output_file": output_path,
                    "validation": {
                        "cyrillic_names_found": narration_ready.count('і') + narration_ready.count('І'),  # Simple check
                        "ssml_breaks_found": narration_ready.count('<break')
                    }
                })
                
            except Exception as e:
                print(f"      ❌ Error: {e}")
                results["failed"] += 1
                results["chapter_results"].append({
                    "chapter_number": i+1,
                    "chapter_title": chapter_title,
                    "status": "failed",
                    "error": str(e)
                })
        
        print(f"✅ Narration preparation complete!")
        print(f"   Successful: {results['successful']}/{results['total_chapters']}")
        print(f"   Output: {narration_output_dir}")
        
        return results

    def _create_credits_files(self, chapter_files):
        """Create opening and closing credits files per ACX requirements"""
        # Opening credits
        opening_credits = f"""Opening Credits

Title: {self.project_id}
Narrated by: [Narrator Name]

"""
        opening_file = os.path.join(self.folders["05_chapter_splits"], "00_opening_credits.txt")
        with open(opening_file, 'w', encoding='utf-8') as f:
            f.write(opening_credits)
        
        # Closing credits
        closing_credits = f"""Closing Credits

You have been listening to {self.project_id}
Narrated by: [Narrator Name]

The End.
"""
        max_num = max([cf.get('number', 0) for cf in chapter_files], default=0)
        closing_file = os.path.join(self.folders["05_chapter_splits"], f"{len(chapter_files)+2:02d}_closing_credits.txt")
        with open(closing_file, 'w', encoding='utf-8') as f:
            f.write(closing_credits)
        
        print(f"  ✓ 00_opening_credits.txt (credits)")
        print(f"  ✓ {len(chapter_files)+2:02d}_closing_credits.txt (credits)")
    
    def number_to_word(self, num):
        """Convert number to word (1 -> one, 2 -> two, etc.)"""
        words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty']
        if num < len(words):
            return words[num]
        return str(num)
    
    def recommend_voices(self, text, book_info):
        """Recommend and generate voice samples"""
        if not self.voice_recommender:
            print("⚠️ Voice recommender not available (missing API key)")
            return None
        
        print(f"[3/7] Generating voice recommendations...")
        
        # Extract first 1000 characters for sample
        raw_excerpt = text[:1000].strip()
        
        # Prepare narration-ready excerpt with native name spellings
        print(f"   Preparing excerpt with native name pronunciation...")
        book_excerpt = prepare_voice_sample_text(raw_excerpt, book_info, max_length=1000)
        print(f"   ✅ Names converted to native spelling for accurate pronunciation")
        
        # Get voice recommendations
        voice_output_dir = self.folders["09_elevenlabs_integration"]
        
        try:
            voice_results = self.voice_recommender.recommend_voices_for_book(
                book_info=book_info,
                book_excerpt=book_excerpt,
                output_dir=voice_output_dir,
                top_n=5  # Generate 5 voice recommendations
            )
            
            print(f"✅ Voice recommendations generated!")
            return voice_results
        except Exception as e:
            print(f"⚠️ Voice recommendation error: {e}")
            return None
    
    def get_folder_structure(self):
        """Get complete folder structure information"""
        structure = {
            "session_id": self.session_id,
            "session_path": self.session_dir,
            "folders": [],
            "files": [],
            "folder_count": 0,
            "file_count": 0,
            "total_size": 0,
            "total_size_formatted": "0 B"
        }
        
        # Walk through session directory
        for root, dirs, files in os.walk(self.session_dir):
            rel_root = os.path.relpath(root, self.session_dir)
            level = 0 if rel_root == '.' else rel_root.count(os.sep) + 1
            
            for dir_name in dirs:
                dir_path = os.path.join(rel_root, dir_name) if rel_root != '.' else dir_name
                structure["folders"].append({
                    "name": dir_name,
                    "path": dir_path,
                    "level": level
                })
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.join(rel_root, file_name) if rel_root != '.' else file_name
                
                try:
                    file_size = os.path.getsize(file_path)
                    structure["total_size"] += file_size
                    
                    # Determine file type
                    ext = os.path.splitext(file_name)[1].lower()
                    file_type_map = {
                        '.txt': 'Text',
                        '.json': 'JSON',
                        '.pdf': 'PDF',
                        '.mp3': 'Audio',
                        '.wav': 'Audio',
                        '.xml': 'XML'
                    }
                    file_type = file_type_map.get(ext, 'File')
                    
                    structure["files"].append({
                        "name": file_name,
                        "path": rel_path,
                        "size": file_size,
                        "size_formatted": self._format_file_size(file_size),
                        "type": file_type,
                        "level": level
                    })
                except:
                    pass
        
        structure["folder_count"] = len(structure["folders"])
        structure["file_count"] = len(structure["files"])
        structure["total_size_formatted"] = self._format_file_size(structure["total_size"])
        
        # Generate visual tree representation
        structure["tree"] = self._generate_folder_tree()
        
        return structure
    
    def _generate_folder_tree(self):
        """Generate a visual tree representation of the folder structure"""
        tree_lines = []
        tree_lines.append(f"📁 {os.path.basename(self.session_dir)}/")
        
        # Get all folders and files
        items = []
        for root, dirs, files in os.walk(self.session_dir):
            rel_root = os.path.relpath(root, self.session_dir)
            level = 0 if rel_root == '.' else rel_root.count(os.sep) + 1
            
            # Add directories
            for dir_name in sorted(dirs):
                items.append({
                    'type': 'dir',
                    'name': dir_name,
                    'level': level,
                    'parent': rel_root
                })
            
            # Add files
            for file_name in sorted(files):
                items.append({
                    'type': 'file',
                    'name': file_name,
                    'level': level,
                    'parent': rel_root,
                    'size': os.path.getsize(os.path.join(root, file_name))
                })
        
        # Build tree structure
        current_path = []
        for item in sorted(items, key=lambda x: (x['parent'], x['type'] == 'file', x['name'])):
            level = item['level']
            indent = "  " * level
            
            if item['type'] == 'dir':
                tree_lines.append(f"{indent}├── 📁 {item['name']}/")
            else:
                # Determine icon based on file type
                ext = os.path.splitext(item['name'])[1].lower()
                icon_map = {
                    '.txt': '📄',
                    '.json': '📋',
                    '.pdf': '📕',
                    '.mp3': '🎵',
                    '.wav': '🎵',
                    '.xml': '📰'
                }
                icon = icon_map.get(ext, '📄')
                size_str = self._format_file_size(item['size'])
                tree_lines.append(f"{indent}├── {icon} {item['name']} ({size_str})")
        
        return "\n".join(tree_lines)
    
    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def process(self):
        """Main processing method"""
        # Initialize progress tracker
        tracker = ProgressTracker(self.session_id)
        
        try:
            print(f"\n{'='*70}")
            print(f"🚀 AUDIOBOOK PROCESSING STARTED")
            print(f"{'='*70}")
            print(f"Session ID: {self.session_id}")
            print(f"User: {self.user_email}")
            print(f"Project ID: {self.project_id}")
            print(f"Session Path: {self.session_dir}")
            print(f"{'='*70}\n")
            
            # Step 1: Extract text (0-20%)
            tracker.update(5, "Extracting Text", "Reading PDF and extracting content...", eta_seconds=15)
            text, page_count = self.extract_text_from_pdf()
            tracker.update(20, "Text Extracted", f"Extracted {len(text.split())} words from {page_count} pages", eta_seconds=40)
            
            # Step 2: STRICT AI validation (20-40%)
            tracker.update(25, "Validating Content", "AI analyzing document type and quality...", eta_seconds=35)
            validation = self.ai_validate_content(text)
            tracker.update(40, "Content Validated", f"Verified as {validation.get('document_type', 'Book')}", eta_seconds=30)
            
            # Step 3: Word count validation
            words = text.split()
            word_count = len(words)
            
            if word_count < self.MIN_WORD_COUNT:
                raise ContentValidationError(
                    f"Document too short: {word_count} words",
                    f"This document is too short ({word_count:,} words). We accept books and short stories with at least {self.MIN_WORD_COUNT:,} words.",
                    ["Upload a book or short story", f"Minimum: {self.MIN_WORD_COUNT:,} words and {self.MIN_PAGES} pages"]
                )
            
            print(f"✅ Content validation passed!")
            print(f"   Document type: {validation.get('document_type')}")
            print(f"   Genre: {validation.get('estimated_genre')}")
            print(f"   Word count: {word_count:,}")
            print(f"   Pages: {page_count}")
            
            # Step 4: Extract metadata (40-50%)
            tracker.update(42, "Extracting Metadata", "AI analyzing title, author, and themes...", eta_seconds=30)
            metadata = self.ai_extract_metadata(text)
            
            # Step 5: Detect chapters (50-60%)
            tracker.update(50, "Detecting Chapters", "AI analyzing book structure...", eta_seconds=25)
            chapter_structure = self.ai_detect_chapters(text)
            
            # Step 5.5: Split chapters into files (60-65%)
            tracker.update(60, "Splitting Chapters", "Creating individual chapter files...", eta_seconds=20)
            chapter_split_result = self.split_chapters_to_files(text, chapter_structure)
            tracker.update(65, "Chapters Split", f"Created {len(chapter_split_result.get('chapter_files', []))} chapter files", eta_seconds=15)
            
            # Merge metadata with validation (needed for narration prep)
            book_info = {
                "title": metadata.get('title', 'Unknown'),
                "author": metadata.get('author', 'Unknown'),
                "genre": metadata.get('genre', validation.get('estimated_genre', 'Unknown')),
                "document_type": validation.get('document_type', 'Book'),
                "themes": metadata.get('themes', []),
                "narrative_tone": metadata.get('narrative_tone', 'Unknown'),
                "target_audience": metadata.get('target_audience', 'General'),
                "content_warnings": metadata.get('content_warnings', []),
                "age_rating": metadata.get('estimated_age_rating', 'General')
            }
            
            # Step 5.6: Prepare chapters for narration (65-70%)
            tracker.update(66, "Preparing Narration", "Converting names to Cyrillic and adding SSML...", eta_seconds=30)
            narration_prep_result = self.prepare_chapters_for_narration(chapter_split_result, book_info)
            if narration_prep_result:
                tracker.update(70, "Narration Ready", f"Prepared {narration_prep_result['successful']} chapters with native pronunciation", eta_seconds=12)
            
            # Merge metadata with validation
            book_info = {
                "title": metadata.get('title', 'Unknown'),
                "author": metadata.get('author', 'Unknown'),
                "genre": metadata.get('genre', validation.get('estimated_genre', 'Unknown')),
                "document_type": validation.get('document_type', 'Book'),
                "themes": metadata.get('themes', []),
                "narrative_tone": metadata.get('narrative_tone', 'Unknown'),
                "target_audience": metadata.get('target_audience', 'General'),
                "content_warnings": metadata.get('content_warnings', []),
                "age_rating": metadata.get('estimated_age_rating', 'General')
            }
            
            # Step 6: Generate voice recommendations (60-85%)
            tracker.update(60, "Generating Voices", "Creating AI voice recommendations...", eta_seconds=15)
            voice_recommendations = self.recommend_voices(text, book_info)
            if voice_recommendations:
                tracker.update(85, "Voices Generated", f"Created {len(voice_recommendations.get('recommended_voices', []))} voice samples", eta_seconds=5)
            else:
                tracker.update(85, "Voices Generated", "Voice recommendations ready", eta_seconds=5)
            
            # Build analysis
            analysis = {
                "projectId": self.project_id,
                "sessionId": self.session_id,
                "userEmail": self.user_email,
                "timestamp": datetime.now().isoformat(),
                "validation": validation,
                "bookInfo": {
                    "title": book_info.get('title', 'Unknown'),
                    "author": book_info.get('author', 'Unknown'),
                    "genre": book_info.get('genre', 'Unknown'),
                    "type": book_info.get('document_type', 'Book'),
                    "language": "English",
                    "themes": book_info.get('themes', []),
                    "narrative_tone": book_info.get('narrative_tone', 'Unknown'),
                    "target_audience": book_info.get('target_audience', 'General'),
                    "content_warnings": book_info.get('content_warnings', []),
                    "age_rating": book_info.get('age_rating', 'General')
                },
                "metrics": {
                    "word_count": word_count,
                    "page_count": page_count,
                    "reading_time": f"{int(word_count / 200)}m",
                    "audio_length": f"{int(word_count / 150)}m"
                },
                "structure": {
                    "total_chapters": chapter_structure.get('total_chapters', 0),
                    "chapters": chapter_structure.get('chapters', []),
                    "chapter_files": chapter_split_result.get('chapter_files', []),
                    "has_prologue": chapter_structure.get('has_prologue', False),
                    "has_epilogue": chapter_structure.get('has_epilogue', False),
                    "structure_type": chapter_structure.get('structure_type', 'unknown')
                },
                "recommendations": {
                    "voice_type": "Neutral, Professional",
                    "tone": "Neutral",
                    "accent": "American, Neutral",
                    "target_audience": "General",
                    "special_notes": "Ready for processing"
                },
                "voiceRecommendations": voice_recommendations,
                "folderStructure": self.get_folder_structure()
            }
            
            # Save analysis (90-100%)
            tracker.update(90, "Finalizing", "Saving analysis results...", eta_seconds=3)
            
            analysis_file = os.path.join(self.folders["02_structure_analysis"], "analysis.json")
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            root_analysis_file = os.path.join(self.session_dir, "analysis.json")
            with open(root_analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            tracker.complete("Analysis complete! Your audiobook is ready.")
            
            print(f"✅ Analysis complete! Saved to: {analysis_file}")
            print(f"{'='*70}\n")
            
            return analysis
            
        except ContentValidationError as e:
            tracker.error(str(e.user_message))
            raise
        except Exception as e:
            tracker.error(f"Processing failed: {str(e)}")
            print(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            raise
