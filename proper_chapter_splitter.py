"""
Proper Chapter Content Splitter
Combines v5's simple AI detection with actual content splitting
"""

import re
import os
from openai import OpenAI


class ProperChapterSplitter:
    def __init__(self, openai_api_key=None, openai_org_id=None):
        """Initialize with OpenAI credentials"""
        if openai_api_key:
            self.client = OpenAI(api_key=openai_api_key, organization=openai_org_id)
        else:
            self.client = OpenAI()  # Use environment variable
    
    def detect_chapters_from_toc(self, text):
        """
        Use AI to detect chapters from table of contents (first 15k chars)
        This is the v5 approach that works reliably
        """
        print("[Chapter Detection] Analyzing table of contents...")
        
        # Take first 15000 characters for TOC analysis (v5 approach)
        sample_text = text[:15000]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a book structure analyzer. Extract chapter information from the table of contents. Return ONLY valid JSON."
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
  "total_chapters": 0
}}

If you see a table of contents, extract ALL chapters from it. Include chapter numbers and full titles.
If you see "Prologue" or "Epilogue", include them as separate entries.
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
            
            import json
            chapter_data = json.loads(result_text)
            
            print(f"✅ AI detected {len(chapter_data.get('chapters', []))} chapters from TOC")
            return chapter_data.get('chapters', [])
            
        except Exception as e:
            print(f"⚠️ AI chapter detection failed: {e}")
            return self._fallback_chapter_detection(text)
    
    def _fallback_chapter_detection(self, text):
        """Fallback: Basic regex chapter detection"""
        print("Using fallback regex detection...")
        
        chapters = []
        
        # Pattern 1: "Chapter N: Title" or "Chapter N Title"
        pattern1 = r'(?:Chapter|CHAPTER)\s+(\d+)[:\s]*([^\n]{3,50})'
        matches1 = re.findall(pattern1, text[:10000])
        
        for num, title in matches1:
            chapters.append({
                "number": int(num),
                "title": f"Chapter {num}: {title.strip()}"
            })
        
        # Pattern 2: Standalone numbers followed by title (like "1 Once Upon a Time")
        pattern2 = r'^\s*(\d+)\s+([A-Z][a-z]{2,}[^\n]{5,50})$'
        matches2 = re.findall(pattern2, text[:10000], re.MULTILINE)
        
        for num, title in matches2:
            if int(num) not in [c['number'] for c in chapters]:
                chapters.append({
                    "number": int(num),
                    "title": f"{num} {title.strip()}"
                })
        
        # Sort by chapter number
        chapters.sort(key=lambda x: x['number'])
        
        print(f"✅ Regex detected {len(chapters)} chapters")
        return chapters
    
    def find_chapter_positions(self, text, chapters):
        """
        Find where each chapter actually starts in the full book text
        Returns list of (chapter_info, start_position) tuples
        """
        print("[Position Finding] Locating chapters in book text...")
        
        chapter_positions = []
        
        for chapter in chapters:
            title = chapter['title']
            number = chapter.get('number', 0)
            
            # Create multiple search patterns for this chapter
            patterns = []
            
            # Pattern 1: Exact title
            patterns.append(re.escape(title))
            
            # Pattern 2: Title without number prefix
            title_without_num = re.sub(r'^\d+\s+', '', title)
            if title_without_num != title:
                patterns.append(re.escape(title_without_num))
            
            # Pattern 3: Chapter number followed by title
            if number > 0:
                patterns.append(rf'{number}\s+{re.escape(title_without_num)}')
                patterns.append(rf'Chapter\s+{number}[:\s]+{re.escape(title_without_num)}')
            
            # Search for the chapter in the text (skip first 15k to avoid TOC)
            search_text = text[15000:]  # Skip TOC
            position = None
            
            for pattern in patterns:
                try:
                    match = re.search(pattern, search_text, re.IGNORECASE)
                    if match:
                        position = 15000 + match.start()  # Adjust for skipped TOC
                        break
                except:
                    continue
            
            if position:
                chapter_positions.append({
                    'number': number,
                    'title': title,
                    'position': position
                })
                print(f"  ✓ Found: {title} at position {position}")
            else:
                print(f"  ✗ Not found: {title}")
        
        # Sort by position
        chapter_positions.sort(key=lambda x: x['position'])
        
        print(f"✅ Located {len(chapter_positions)} chapters in text")
        return chapter_positions
    
    def split_chapters_to_files(self, text, chapter_positions, output_dir):
        """
        Split the book text into chapter files based on positions
        Returns list of created files with metadata
        """
        print(f"[Content Splitting] Creating chapter files in {output_dir}...")
        
        os.makedirs(output_dir, exist_ok=True)
        created_files = []
        
        for i, chapter in enumerate(chapter_positions):
            # Determine start and end positions
            start_pos = chapter['position']
            end_pos = chapter_positions[i + 1]['position'] if i < len(chapter_positions) - 1 else len(text)
            
            # Extract chapter content
            content = text[start_pos:end_pos].strip()
            word_count = len(content.split())
            
            # Create filename
            chapter_num = chapter['number']
            safe_title = re.sub(r'[^\w\s-]', '', chapter['title'])
            safe_title = re.sub(r'\s+', ' ', safe_title).strip()
            
            # Use smart numbering (Epilogue = 900, etc.)
            if 'epilogue' in safe_title.lower():
                filename = f"900_{safe_title}.txt"
            elif 'prologue' in safe_title.lower():
                filename = f"00_{safe_title}.txt"
            else:
                filename = f"{chapter_num:02d}_{safe_title}.txt"
            
            filepath = os.path.join(output_dir, filename)
            
            # Write content to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append({
                'number': chapter_num,
                'title': chapter['title'],
                'file': filename,
                'word_count': word_count,
                'size_bytes': len(content.encode('utf-8'))
            })
            
            print(f"  ✓ Created: {filename} ({word_count} words)")
        
        print(f"✅ Created {len(created_files)} chapter files")
        return created_files
    
    def process_book(self, text, output_dir):
        """
        Complete chapter processing pipeline:
        1. Detect chapters from TOC
        2. Find positions in full text
        3. Split and save to files
        """
        print("\n" + "="*60)
        print("PROPER CHAPTER SPLITTING SYSTEM")
        print("="*60 + "\n")
        
        # Step 1: Detect chapters from TOC
        chapters = self.detect_chapters_from_toc(text)
        
        if not chapters:
            print("⚠️ No chapters detected, creating single full book file")
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "00_full_book.txt"), 'w', encoding='utf-8') as f:
                f.write(text)
            return [{
                'number': 0,
                'title': 'Full Book',
                'file': '00_full_book.txt',
                'word_count': len(text.split()),
                'size_bytes': len(text.encode('utf-8'))
            }]
        
        # Step 2: Find chapter positions
        chapter_positions = self.find_chapter_positions(text, chapters)
        
        if not chapter_positions:
            print("⚠️ Could not locate chapters in text, creating single file")
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "00_full_book.txt"), 'w', encoding='utf-8') as f:
                f.write(text)
            return [{
                'number': 0,
                'title': 'Full Book',
                'file': '00_full_book.txt',
                'word_count': len(text.split()),
                'size_bytes': len(text.encode('utf-8'))
            }]
        
        # Step 3: Split and save
        created_files = self.split_chapters_to_files(text, chapter_positions, output_dir)
        
        print("\n" + "="*60)
        print(f"CHAPTER SPLITTING COMPLETE: {len(created_files)} files created")
        print("="*60 + "\n")
        
        return created_files
