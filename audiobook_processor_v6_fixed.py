"""
AudiobookSmith Book Processor v6 - Fixed Validation + Proper Folder Structure
- Stricter content validation to reject templates, proposals, guides
- Proper session-based folder structure with versioning
- Numbered folders for processing pipeline
"""

import os
import re
import json
import PyPDF2
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
    def __init__(self, pdf_path, project_id, user_email="unknown@example.com", working_dir="/root/audiobook_working"):
        self.pdf_path = pdf_path
        self.project_id = project_id
        self.user_email = user_email
        self.working_dir = working_dir
        
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
        
        # Create all directories
        self._create_folder_structure()
        
        # Validation thresholds
        self.MIN_WORD_COUNT = 1000
        self.MIN_PAGES = 3
        self.MAX_PAGES = 1000
    
    def sanitize_folder_name(self, name):
        """Sanitize folder name to be filesystem-safe"""
        # Replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        # Limit length
        if len(name) > 200:
            name = name[:200]
        return name or "unnamed"
    
    def _create_folder_structure(self):
        """Create complete folder structure"""
        # Create main directories
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.comparison_reports_dir, exist_ok=True)
        os.makedirs(self.quality_metrics_dir, exist_ok=True)
        
        # Create all processing folders
        for folder_path in self.folders.values():
            os.makedirs(folder_path, exist_ok=True)
        
        # Create ElevenLabs subfolders
        elevenlabs_subfolders = ['input_ssml', 'generated_audio', 'processing_logs', 'voice_settings']
        for subfolder in elevenlabs_subfolders:
            os.makedirs(os.path.join(self.folders["09_elevenlabs_integration"], subfolder), exist_ok=True)
        
        # Create Amazon delivery subfolders
        amazon_subfolders = ['audio_files', 'metadata', 'cover_art', 'submission_package']
        for subfolder in amazon_subfolders:
            os.makedirs(os.path.join(self.folders["10_final_delivery"], subfolder), exist_ok=True)
        
        print(f"✅ Created folder structure for session: {self.session_id}")
    
    def get_folder_structure(self):
        """Capture the complete folder structure"""
        structure = {
            "session_id": self.session_id,
            "user_folder": self.user_folder,
            "book_folder": self.book_folder,
            "session_path": self.session_dir,
            "folders": [],
            "files": [],
            "total_size": 0
        }
        
        try:
            # Walk through session directory
            for root, dirs, files in os.walk(self.session_dir):
                rel_path = os.path.relpath(root, self.session_dir)
                if rel_path == ".":
                    rel_path = ""
                
                # Add folders
                for dir_name in dirs:
                    folder_path = os.path.join(rel_path, dir_name) if rel_path else dir_name
                    structure["folders"].append({
                        "name": dir_name,
                        "path": folder_path,
                        "level": folder_path.count(os.sep)
                    })
                
                # Add files
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    rel_file_path = os.path.join(rel_path, file_name) if rel_path else file_name
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        structure["total_size"] += file_size
                        
                        ext = os.path.splitext(file_name)[1].lower()
                        file_type = {
                            ".txt": "Text",
                            ".json": "JSON",
                            ".pdf": "PDF",
                            ".mp3": "Audio",
                            ".wav": "Audio",
                            ".ssml": "SSML",
                            ".xml": "XML",
                            ".log": "Log"
                        }.get(ext, "Other")
                        
                        structure["files"].append({
                            "name": file_name,
                            "path": rel_file_path,
                            "size": file_size,
                            "size_formatted": self._format_file_size(file_size),
                            "type": file_type,
                            "extension": ext,
                            "level": rel_file_path.count(os.sep)
                        })
                    except Exception as e:
                        print(f"Warning: Could not get info for {file_name}: {e}")
            
            structure["total_size_formatted"] = self._format_file_size(structure["total_size"])
            structure["file_count"] = len(structure["files"])
            structure["folder_count"] = len(structure["folders"])
            
        except Exception as e:
            print(f"Warning: Could not capture folder structure: {e}")
        
        return structure
    
    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def extract_text_from_pdf(self):
        """Extract text from PDF file"""
        print(f"[1/6] Extracting text from PDF: {self.pdf_path}")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Validate page count
                if num_pages < self.MIN_PAGES:
                    raise ContentValidationError(
                        f"Document too short: {num_pages} pages",
                        f"This document is too short ({num_pages} pages). We accept books, short stories, and sample chapters with at least {self.MIN_PAGES} pages.",
                        ["Upload a book, short story, or sample chapter", "Minimum: 3 pages and 1,000 words"]
                    )
                
                if num_pages > self.MAX_PAGES:
                    raise ContentValidationError(
                        f"Document too long: {num_pages} pages",
                        f"This document is very long ({num_pages} pages). Please contact support for processing books over {self.MAX_PAGES} pages.",
                        ["Split your book into volumes", "Contact support for large book processing"]
                    )
                
                full_text = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n\n"
                
                # Validate text extraction
                if len(full_text.strip()) < 100:
                    raise ContentValidationError(
                        "PDF text extraction failed",
                        "Unable to extract text from this PDF. It may be scanned images or protected.",
                        ["Convert scanned PDFs to text using OCR", "Remove PDF password protection", "Export as a new PDF from your word processor"]
                    )
                
                # Save extracted text to 01_raw_files
                text_file = os.path.join(self.folders["01_raw_files"], "extracted_text.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                
                print(f"✅ Extracted {len(full_text)} characters from {num_pages} pages")
                return full_text, num_pages
                
        except ContentValidationError:
            raise
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            raise ContentValidationError(
                f"PDF processing error: {e}",
                "Unable to process this PDF file. It may be corrupted or in an unsupported format.",
                ["Try re-saving the PDF", "Export from your word processor as a new PDF", "Check that the file is not corrupted"]
            )
    
    def ai_validate_content(self, text):
        """Use AI to validate if this is suitable audiobook content - STRICT VERSION"""
        print("[2/6] Validating content suitability for audiobook production...")
        
        # Take sample from beginning, middle, and end
        sample_text = (
            text[:2000] + 
            "\n\n[... middle section ...]\n\n" + 
            text[len(text)//2:len(text)//2+1500] +
            "\n\n[... end section ...]\n\n" +
            text[-1000:]
        )
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a STRICT content validator for an audiobook production service. 
Your job is to REJECT any document that is not a narrative book, short story, or sample chapter meant for audiobook narration.

BE VERY STRICT. When in doubt, REJECT."""
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this document and determine if it's suitable for audiobook production.

**ACCEPT ONLY:**
- Fiction books (novels, short stories, novellas)
- Non-fiction narrative books (memoirs, biographies, autobiographies)
- Self-help books with continuous narrative
- Educational books with narrative structure
- Sample chapters from the above

**REJECT IMMEDIATELY:**
- Business proposals or proposal templates (even if they mention "services")
- Deployment guides, setup instructions, user manuals
- Technical documentation, API documentation
- How-to guides, tutorials, step-by-step instructions
- Requirements documents, specifications (SRS, PRD, etc.)
- Templates of any kind (proposal templates, form templates, etc.)
- Academic papers, research papers, theses
- Reports (business reports, technical reports, analysis reports)
- Presentations, slide decks
- Reference materials, dictionaries, glossaries
- Spreadsheets, data tables
- Forms, applications, questionnaires
- Marketing materials, brochures
- Legal documents, contracts
- Configuration files, code documentation
- Workflow documentation, process guides

**KEY INDICATORS TO REJECT:**
- Contains sections like "Overview", "Proposal", "Services", "Pricing", "Deliverables"
- Has placeholder text like "Replace with your own", "Sample content", "Use this template"
- Contains instructions for filling out the document
- Has form-like structure with fields to fill in
- Contains technical specifications or requirements
- Has step-by-step instructions or procedures
- Contains tables with pricing, services, or specifications

Document sample:
{sample_text}

Return a JSON object with this EXACT structure:
{{
  "is_suitable": true/false,
  "document_type": "Novel/Memoir/Proposal Template/Deployment Guide/etc",
  "confidence": 0.0-1.0,
  "reason": "Brief specific explanation why accepted or rejected",
  "is_book": true/false,
  "has_narrative": true/false,
  "is_template": true/false,
  "is_technical_doc": true/false,
  "estimated_genre": "Genre if it's a book, or 'N/A'"
}}

Return ONLY the JSON object, no other text."""
                    }
                ],
                temperature=0.1,  # Lower temperature for more consistent strict validation
                max_tokens=400
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = re.sub(r'^```json\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)
            
            validation = json.loads(result_text)
            
            # STRICT CHECKS
            
            # Check if it's a template
            if validation.get('is_template', False):
                raise ContentValidationError(
                    "Template document detected",
                    f"This appears to be a template document, not a book. Our service is for audiobook production, not template processing.",
                    [
                        "Upload an actual book, short story, or sample chapter",
                        "Not suitable: templates, forms, proposals, guides",
                        "Suitable: novels, memoirs, biographies, self-help books"
                    ]
                )
            
            # Check if it's technical documentation
            if validation.get('is_technical_doc', False):
                raise ContentValidationError(
                    "Technical documentation detected",
                    f"This appears to be technical documentation ({validation.get('document_type', 'document')}), not suitable for audiobook narration.",
                    [
                        "Upload a narrative book or story",
                        "Not suitable: guides, manuals, documentation, specifications",
                        "Suitable: fiction, memoirs, biographies, narrative non-fiction"
                    ]
                )
            
            # Check if suitable
            if not validation.get('is_suitable', False):
                document_type = validation.get('document_type', 'document')
                reason = validation.get('reason', 'Not suitable for audiobook production')
                
                raise ContentValidationError(
                    f"Content not suitable: {document_type}",
                    f"This appears to be a {document_type}, which is not suitable for audiobook production.\n\n{reason}",
                    [
                        "Upload a book, short story, or sample chapter (fiction or non-fiction)",
                        "Suitable: novels, short stories, memoirs, biographies, self-help books",
                        "Not suitable: proposals, guides, manuals, templates, reports, documentation"
                    ]
                )
            
            # Check if it's actually a book with narrative
            if not validation.get('is_book', True) or not validation.get('has_narrative', True):
                raise ContentValidationError(
                    "Not a narrative book",
                    f"This document ({validation.get('document_type', 'document')}) does not have the narrative structure needed for audiobook narration.",
                    [
                        "Upload a book with continuous narrative",
                        "Suitable: novels, memoirs, biographies, narrative non-fiction",
                        "Not suitable: reference materials, guides, reports, proposals"
                    ]
                )
            
            print(f"✅ Content validated: {validation.get('document_type')} - {validation.get('estimated_genre')}")
            return validation
            
        except ContentValidationError:
            raise
        except json.JSONDecodeError as e:
            print(f"⚠️ AI validation response parsing error: {e}")
            print(f"Response was: {result_text}")
            # If we can't parse the response, be conservative and reject
            raise ContentValidationError(
                "Validation error",
                "Unable to validate this document. It may not be suitable for audiobook production.",
                ["Try uploading a different document", "Ensure the PDF contains readable text", "Upload a narrative book or story"]
            )
        except Exception as e:
            print(f"⚠️ AI validation error: {e}")
            # On error, allow through but log warning
            print("Warning: Validation check failed, proceeding with caution")
            return {
                "is_suitable": True,
                "document_type": "Unknown",
                "confidence": 0.5,
                "reason": "Validation check failed",
                "is_book": True,
                "has_narrative": True
            }
    
    # [Rest of the methods remain the same as v5...]
    # ai_detect_chapters, ai_classify_book, calculate_metrics, process
    
    def process(self):
        """Main processing method"""
        try:
            print(f"\n{'='*70}")
            print(f"🚀 AUDIOBOOK PROCESSING STARTED")
            print(f"{'='*70}")
            print(f"Session ID: {self.session_id}")
            print(f"User: {self.user_email}")
            print(f"Project ID: {self.project_id}")
            print(f"Session Path: {self.session_dir}")
            print(f"{'='*70}\n")
            
            # Step 1: Extract text
            text, page_count = self.extract_text_from_pdf()
            
            # Step 2: STRICT AI validation
            validation = self.ai_validate_content(text)
            
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
            
            # For now, return basic analysis
            # Full chapter detection and classification will be added later
            
            analysis = {
                "projectId": self.project_id,
                "sessionId": self.session_id,
                "userEmail": self.user_email,
                "timestamp": datetime.now().isoformat(),
                "validation": validation,
                "bookInfo": {
                    "title": f"Book_{self.project_id}",
                    "author": "Unknown",
                    "genre": validation.get('estimated_genre', 'Unknown'),
                    "type": validation.get('document_type', 'Book'),
                    "language": "English"
                },
                "metrics": {
                    "word_count": word_count,
                    "page_count": page_count,
                    "reading_time": f"{int(word_count / 200)}m",
                    "audio_length": f"{int(word_count / 150)}m"
                },
                "structure": {
                    "total_chapters": 0,
                    "chapters": [],
                    "parts": [],
                    "sections": []
                },
                "recommendations": {
                    "voice_type": "Neutral, Professional",
                    "tone": "Neutral",
                    "accent": "American, Neutral",
                    "target_audience": "General",
                    "special_notes": "Ready for processing"
                },
                "folderStructure": self.get_folder_structure()
            }
            
            # Save analysis to 02_structure_analysis
            analysis_file = os.path.join(self.folders["02_structure_analysis"], "analysis.json")
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            # Also save to session root for compatibility
            root_analysis_file = os.path.join(self.session_dir, "analysis.json")
            with open(root_analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            print(f"\n✅ Analysis complete! Saved to: {analysis_file}")
            print(f"{'='*70}\n")
            
            return analysis
            
        except ContentValidationError as e:
            print(f"\n❌ Content Validation Failed: {e.message}")
            print(f"   User Message: {e.user_message}")
            if e.suggestions:
                print(f"   Suggestions:")
                for suggestion in e.suggestions:
                    print(f"     - {suggestion}")
            raise
        except Exception as e:
            print(f"\n❌ Processing Error: {e}")
            import traceback
            traceback.print_exc()
            raise
