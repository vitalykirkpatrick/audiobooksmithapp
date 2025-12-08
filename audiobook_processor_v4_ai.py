#!/usr/bin/env python3
"""
AudiobookSmith Book Processor v4 - AI-Powered Edition
Enhanced with OpenAI for intelligent chapter detection and genre classification
"""

import os
import re
import json
import PyPDF2
from datetime import datetime
from openai import OpenAI

class AIBookProcessor:
    def __init__(self, pdf_path, project_id, working_dir="/root/audiobook_working"):
        self.pdf_path = pdf_path
        self.project_id = project_id
        self.working_dir = working_dir
        self.project_dir = os.path.join(working_dir, project_id)
        self.text_dir = os.path.join(self.project_dir, "text")
        self.audio_dir = os.path.join(self.project_dir, "audio")
        
        # Initialize OpenAI client (API key from environment)
        self.client = OpenAI()
        
        # Create directories
        os.makedirs(self.text_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
    def extract_text_from_pdf(self):
        """Extract text from PDF file"""
        print(f"[1/5] Extracting text from PDF: {self.pdf_path}")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                full_text = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n\n"
                
                # Save extracted text
                text_file = os.path.join(self.text_dir, "extracted_text.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                
                print(f"✅ Extracted {len(full_text)} characters from {num_pages} pages")
                return full_text, num_pages
                
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return "", 0
    
    def ai_detect_chapters(self, text):
        """Use AI to intelligently detect chapters and their titles"""
        print("[2/5] Using AI to detect chapters and structure...")
        
        # Take first 15000 characters for table of contents analysis
        sample_text = text[:15000]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a book structure analyzer. Extract chapter information from the table of contents or chapter headings. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this book text and extract ALL chapters with their titles.

Book text:
{sample_text}

Return a JSON object with this EXACT structure:
{{
  "chapters": [
    {{"number": 1, "title": "Chapter Title"}},
    {{"number": 2, "title": "Another Chapter"}}
  ],
  "parts": [
    {{"number": 1, "title": "Part Name", "chapters": [1, 2, 3]}}
  ],
  "total_chapters": 0
}}

If you see a table of contents, extract ALL chapters from it. Include chapter numbers and full titles.
Return ONLY the JSON object, no other text."""
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = re.sub(r'^```json\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)
            
            chapter_data = json.loads(result_text)
            
            print(f"✅ AI detected {chapter_data.get('total_chapters', 0)} chapters")
            return chapter_data
            
        except Exception as e:
            print(f"⚠️ AI chapter detection failed: {e}")
            # Fallback to basic detection
            return self.basic_chapter_detection(text)
    
    def basic_chapter_detection(self, text):
        """Fallback: Basic chapter detection using patterns"""
        print("Using fallback chapter detection...")
        
        chapters = []
        chapter_pattern = r'(?:Chapter|CHAPTER)\s+(\d+)[:\s]*([^\n]+)'
        matches = re.findall(chapter_pattern, text[:10000])
        
        for num, title in matches:
            chapters.append({
                "number": int(num),
                "title": title.strip()
            })
        
        return {
            "chapters": chapters,
            "parts": [],
            "total_chapters": len(chapters)
        }
    
    def ai_classify_book(self, text):
        """Use AI to automatically classify the book genre and type"""
        print("[3/5] Using AI to classify book genre and type...")
        
        # Take a sample from beginning for classification
        sample_text = text[:5000]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a book classification expert. Analyze the text and determine the genre, type, and key characteristics. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this book excerpt and classify it.

Book excerpt:
{sample_text}

Return a JSON object with this EXACT structure:
{{
  "title": "Book Title",
  "author": "Author Name (if mentioned)",
  "genre": "Primary Genre",
  "subgenre": "Subgenre if applicable",
  "type": "Fiction/Non-Fiction/Memoir/Biography/etc",
  "themes": ["theme1", "theme2", "theme3"],
  "tone": "Overall tone (e.g., Inspirational, Dark, Humorous)",
  "target_audience": "Who this book is for",
  "voice_recommendation": "Recommended narrator voice type",
  "accent_recommendation": "Recommended accent"
}}

Return ONLY the JSON object, no other text."""
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = re.sub(r'^```json\s*', '', result_text)
                result_text = re.sub(r'\s*```$', '', result_text)
            
            classification = json.loads(result_text)
            
            print(f"✅ Book classified as: {classification.get('genre', 'Unknown')} - {classification.get('type', 'Unknown')}")
            return classification
            
        except Exception as e:
            print(f"⚠️ AI classification failed: {e}")
            return {
                "title": "Unknown",
                "author": "Unknown",
                "genre": "Unknown",
                "subgenre": "",
                "type": "Unknown",
                "themes": [],
                "tone": "Neutral",
                "target_audience": "General",
                "voice_recommendation": "Neutral, Professional",
                "accent_recommendation": "Neutral"
            }
    
    def calculate_metrics(self, text, num_pages):
        """Calculate word count, reading time, and audio length"""
        print("[4/5] Calculating metrics...")
        
        words = text.split()
        word_count = len(words)
        
        # Reading time (average 200 words per minute)
        reading_minutes = word_count / 200
        reading_hours = int(reading_minutes // 60)
        reading_mins = int(reading_minutes % 60)
        
        # Audio length (average 150 words per minute for narration)
        audio_minutes = word_count / 150
        audio_hours = int(audio_minutes // 60)
        audio_mins = int(audio_minutes % 60)
        
        metrics = {
            "word_count": word_count,
            "page_count": num_pages,
            "reading_time": f"{reading_hours}h {reading_mins}m",
            "audio_length": f"{audio_hours}h {audio_mins}m"
        }
        
        print(f"✅ Metrics calculated: {word_count} words, {num_pages} pages")
        return metrics
    
    def generate_analysis(self):
        """Main processing function"""
        print(f"\n{'='*60}")
        print(f"AudiobookSmith AI Book Processor v4")
        print(f"Project ID: {self.project_id}")
        print(f"{'='*60}\n")
        
        # Step 1: Extract text
        text, num_pages = self.extract_text_from_pdf()
        if not text:
            return None
        
        # Step 2: AI chapter detection
        chapter_data = self.ai_detect_chapters(text)
        
        # Step 3: AI book classification
        classification = self.ai_classify_book(text)
        
        # Step 4: Calculate metrics
        metrics = self.calculate_metrics(text, num_pages)
        
        # Step 5: Combine all data
        print("[5/5] Generating final analysis...")
        
        analysis = {
            "projectId": self.project_id,
            "timestamp": datetime.now().isoformat(),
            "bookInfo": {
                "title": classification.get("title", "Unknown"),
                "author": classification.get("author", "Unknown"),
                "genre": classification.get("genre", "Unknown"),
                "subgenre": classification.get("subgenre", ""),
                "type": classification.get("type", "Unknown"),
                "themes": classification.get("themes", []),
                "language": "English"
            },
            "metrics": metrics,
            "structure": {
                "total_chapters": chapter_data.get("total_chapters", 0),
                "chapters": chapter_data.get("chapters", []),
                "parts": chapter_data.get("parts", []),
                "sections": []
            },
            "recommendations": {
                "voice_type": classification.get("voice_recommendation", "Neutral, Professional"),
                "tone": classification.get("tone", "Neutral"),
                "accent": classification.get("accent_recommendation", "Neutral"),
                "target_audience": classification.get("target_audience", "General"),
                "special_notes": f"Book contains {chapter_data.get('total_chapters', 0)} chapters. {classification.get('tone', 'Neutral')} narration style recommended."
            }
        }
        
        # Save analysis
        analysis_file = os.path.join(self.project_dir, "analysis.json")
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Analysis complete! Saved to: {analysis_file}")
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Title: {analysis['bookInfo']['title']}")
        print(f"  Author: {analysis['bookInfo']['author']}")
        print(f"  Genre: {analysis['bookInfo']['genre']} ({analysis['bookInfo']['type']})")
        print(f"  Chapters: {analysis['structure']['total_chapters']}")
        print(f"  Word Count: {metrics['word_count']:,}")
        print(f"  Pages: {metrics['page_count']}")
        print(f"{'='*60}\n")
        
        return analysis


def main():
    """Command line interface"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 audiobook_processor_v4_ai.py <pdf_path> <project_id>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    project_id = sys.argv[2]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    processor = AIBookProcessor(pdf_path, project_id)
    analysis = processor.generate_analysis()
    
    if analysis:
        print("✅ Processing complete!")
    else:
        print("❌ Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
