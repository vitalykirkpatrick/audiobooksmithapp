"""
Simple, reliable chapter detection using only regex
No AI, no chunking, no complex logic - just works
"""

import re

def detect_chapters_simple(text):
    """
    Detect chapters using simple regex patterns on the entire text.
    Returns list of (position, title) tuples sorted by position.
    """
    chapters = []
    
    # Pattern 1: Prologue
    for match in re.finditer(r'^(Prologue|PROLOGUE)\s*$', text, re.MULTILINE):
        chapters.append((match.start(), "Prologue"))
    
    # Pattern 2: Part markers (I The Beginning, II Foster Care, III Into Adulthood)
    for match in re.finditer(r'^([IVX]+)\s+([A-Z][^\n]{5,40})$', text, re.MULTILINE):
        roman = match.group(1)
        title = match.group(2).strip()
        chapters.append((match.start(), f"{roman} {title}"))
    
    # Pattern 3: Numbered chapters with titles (1 Once Upon a Time, 2 My First Misadventure)
    for match in re.finditer(r'^(\d+)\s*\n\s*([A-Z][^\n]{5,50})$', text, re.MULTILINE):
        num = match.group(1)
        title = match.group(2).strip()
        chapters.append((match.start(), f"{num} {title}"))
    
    # Pattern 4: Chapter N: Title format
    for match in re.finditer(r'^Chapter\s+(\d+)[:\s]+([^\n]{3,50})$', text, re.MULTILINE | re.IGNORECASE):
        num = match.group(1)
        title = match.group(2).strip()
        chapters.append((match.start(), f"Chapter {num}: {title}"))
    
    # Pattern 5: Just chapter numbers on their own line followed by content
    for match in re.finditer(r'^\s*(\d+)\s*$', text, re.MULTILINE):
        num = match.group(1)
        # Check if this is followed by substantial text (not just another number)
        pos = match.end()
        next_100 = text[pos:pos+100].strip()
        if next_100 and not next_100[0].isdigit():
            # Try to extract title from next line
            next_line_match = re.search(r'^([A-Z][^\n]{3,50})', next_100, re.MULTILINE)
            if next_line_match:
                title = next_line_match.group(1).strip()
                chapters.append((match.start(), f"{num} {title}"))
            else:
                chapters.append((match.start(), f"Chapter {num}"))
    
    # Pattern 6: Epilogue
    for match in re.finditer(r'^(Epilogue|EPILOGUE)\s*$', text, re.MULTILINE):
        chapters.append((match.start(), "Epilogue"))
    
    # Sort by position
    chapters.sort(key=lambda x: x[0])
    
    # Remove duplicates that are too close together (within 500 chars)
    filtered = []
    for i, (pos, title) in enumerate(chapters):
        # Check if this is too close to the previous chapter
        if i > 0:
            prev_pos = filtered[-1][0]
            if pos - prev_pos < 500:
                # Too close, skip this one
                print(f"  Skipping duplicate '{title}' at pos {pos} (too close to previous)")
                continue
        filtered.append((pos, title))
    
    print(f"✅ Detected {len(filtered)} chapters using simple regex")
    return filtered


def split_chapters_simple(text, chapters):
    """
    Split text into chapter files based on detected positions.
    Returns list of (number, title, content, word_count) tuples.
    """
    if not chapters:
        return [("00", "Full Book", text, len(text.split()))]
    
    split_chapters = []
    
    for i, (pos, title) in enumerate(chapters):
        # Get content from this chapter to the next (or end of book)
        start = pos
        end = chapters[i + 1][0] if i + 1 < len(chapters) else len(text)
        content = text[start:end].strip()
        word_count = len(content.split())
        
        # Assign chapter number
        if "prologue" in title.lower():
            num = "00"
        elif "epilogue" in title.lower():
            num = "900"
        else:
            # Extract number from title if present, otherwise sequential
            num_match = re.search(r'^\d+', title)
            if num_match:
                num = f"{int(num_match.group()):02d}"
            else:
                # Part markers or unnumbered chapters
                num = f"{i:02d}"
        
        split_chapters.append((num, title, content, word_count))
        print(f"  Chapter {num}: {title[:40]}... ({word_count} words)")
    
    return split_chapters
