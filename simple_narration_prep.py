"""
Simplified Narration Preparation (No Book Profile Required)
Prepares chapter files for Audible/ACX narration with:
- Cyrillic name conversion
- SSML breaks
- Chapter transitions
- Part announcements
"""

import os
import re
import json
from openai import OpenAI
from multilingual_narration_prep import detect_book_language, SUPPORTED_LANGUAGES


def prepare_chapter_for_narration(
    chapter_text: str,
    chapter_number: int,
    chapter_title: str,
    book_info: dict,
    is_prologue: bool = False,
    is_epilogue: bool = False,
    part_info: dict = None,
    next_chapter_title: str = None
) -> str:
    """
    Transform a raw chapter into an Audible-ready narration script.
    
    Args:
        chapter_text: Raw chapter content
        chapter_number: Chapter number (1, 2, 3...)
        chapter_title: Chapter title
        book_info: Dict with title, author, genre
        is_prologue: True if this is the prologue
        is_epilogue: True if this is the epilogue
        part_info: Dict with part_number and part_title if this starts a new part
        next_chapter_title: Title of the next chapter (for outro)
    
    Returns:
        Narration-ready text with SSML and native name spellings
    """
    
    client = OpenAI()
    
    # Detect language if not already provided
    if 'language_info' not in book_info:
        language_info = detect_book_language(book_info, chapter_text[:1000])
    else:
        language_info = book_info['language_info']
    
    lang_name = language_info.get('language_name', 'English')
    lang_code = language_info.get('primary_language', 'eng')
    script = language_info.get('script', 'Latin')
    
    # Build the transformation prompt
    prompt = f"""You are preparing a chapter for professional audiobook narration (Audible/ACX standards).

**Book Information:**
- Title: {book_info.get('title', 'Unknown')}
- Author: {book_info.get('author', 'Unknown')}
- Genre: {book_info.get('genre', 'Fiction')}
- Primary Language: {lang_name} ({lang_code})
- Script System: {script}

**Chapter Information:**
- Chapter: {"Prologue" if is_prologue else "Epilogue" if is_epilogue else f"Chapter {chapter_number}: {chapter_title}"}
- Part: {part_info.get('part_title') if part_info else 'N/A'}

**Your Task:**
Transform the raw chapter text below into a narration-ready script following these EXACT requirements:

1. **Opening Transition:**
   - Start with `<break time="2s" />`
   - If this is the start of a new Part, announce it: "Now, we begin Part [Number]: [Part Title]."
   - Add `<break time="0.5s" />`
   - Announce the chapter: "Chapter [Number]: [Title]" or "Prologue" or "Epilogue"
   - Add `<break time="0.5s" />`

2. **Name Conversion (CRITICAL for {lang_name}):**
   - Identify ALL proper nouns (people, places)
   - Convert transliterated names to their NATIVE {script} spelling
   - Examples for {lang_name}:
     * If Ukrainian: "Vitaly" → "Віталій", "Chernivtsi" → "Чернівці"
     * If Russian: "Dmitry" → "Дмитрий", "Moscow" → "Москва"
     * If Arabic: "Ahmed" → "أحمد", "Cairo" → "القاهرة"
     * If Japanese: "Tanaka" → "田中", "Tokyo" → "東京"
     * If Chinese: "Li Wei" → "李伟", "Beijing" → "北京"
     * If Greek: "Dimitrios" → "Δημήτριος", "Athens" → "Αθήνα"
     * If Hebrew: "David" → "דוד", "Jerusalem" → "ירושלים"
     * If Hindi: "Raj" → "राज", "Delhi" → "दिल्ली"
     * If Korean: "Kim" → "김", "Seoul" → "서울"
     * If German: "München" (not "Munich"), "Müller" (not "Muller")
     * If French: "François" (not "Francois"), "Côte d'Azur" (not "Cote d'Azur")
     * If Spanish: "José" (not "Jose"), "Málaga" (not "Malaga")
   - This ensures AI narrator uses correct native pronunciation

3. **Unit Conversions (for US audiences):**
   - Convert metric units to US equivalents in parentheses:
     * "5 kilometers" → "5 kilometers (about 3 miles)"
     * "100 kilograms" → "100 kilograms (about 220 pounds)"
     * "30 degrees Celsius" → "30 degrees Celsius (86 degrees Fahrenheit)"
     * "2 meters" → "2 meters (about 6.5 feet)"
   - Add context for foreign currency:
     * "100 rubles" → "100 rubles (approximately X dollars at the time)"
     * "50 pounds sterling" → "50 pounds sterling (about X dollars)"
   - Only add conversions when the measurement is significant to the story

4. **Abbreviation Expansion:**
   - Expand ALL abbreviations for clarity:
     * "Dr." → "Doctor"
     * "Mr." → "Mister"
     * "Mrs." → "Missus"
     * "Ms." → "Miss" or "Miz"
     * "etc." → "et cetera"
     * "e.g." → "for example"
     * "i.e." → "that is"
     * "vs." → "versus"
     * "St." → "Street" or "Saint" (context-dependent)
   - Spell out acronyms on first use:
     * "USSR" → "U.S.S.R." or "the Soviet Union"
     * "USA" → "U.S.A." or "the United States"
     * "UK" → "U.K." or "the United Kingdom"
   - Expand time abbreviations:
     * "a.m." → "A.M."
     * "p.m." → "P.M."

5. **Content:**
   - Include the COMPLETE chapter text with NO omissions or summaries
   - Preserve all paragraphs, dialogue, and narrative flow
   - Add `<break time="0.3s" />` between paragraphs
   - Remove page numbers, headers, footers, and any publishing artifacts

6. **Closing Transition:**
   - Add `<break time="2s" />`
   - State: "We've now come to the end of [Chapter Name]."
   - Add: "Let us continue this journey together."
   - If next chapter exists: "Next up is [Next Chapter Title]."
   - End with `<break time="0.5s" />`

5. **Quality Standards:**
   - Maintain the original author's voice and tone
   - Preserve all dialogue and formatting
   - Ensure smooth narrative flow for audio listening

**Raw Chapter Text:**
{chapter_text}

**Narration-Ready Output:**"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert audiobook script preparer specializing in {lang_name} content. You transform raw text into narration-ready scripts with proper SSML formatting and convert transliterated names to native {script} spelling for accurate AI pronunciation. You NEVER omit content or summarize - you include EVERYTHING from the original text."},
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=16000
        )
        
        narration_ready = response.choices[0].message.content.strip()
        
        return narration_ready
        
    except Exception as e:
        print(f"❌ Error preparing chapter: {e}")
        # Fallback: return original with basic formatting
        return f"""<break time="2s" />

{"Prologue" if is_prologue else "Epilogue" if is_epilogue else f"Chapter {chapter_number}: {chapter_title}"}

<break time="0.5s" />

{chapter_text}

<break time="2s" />

We've now come to the end of {"the Prologue" if is_prologue else "the Epilogue" if is_epilogue else f"Chapter {chapter_number}"}.

<break time="0.5s" />"""


def process_all_chapters(
    chapter_files_dir: str,
    output_dir: str,
    book_info: dict,
    chapter_structure: list
) -> dict:
    """
    Process all chapter files in a directory.
    
    Args:
        chapter_files_dir: Path to folder with raw chapter .txt files
        output_dir: Path to save narration-ready files
        book_info: Book metadata
        chapter_structure: List of dicts with chapter info
    
    Returns:
        Processing results summary
    """
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        "total_chapters": len(chapter_structure),
        "successful": 0,
        "failed": 0,
        "chapter_results": []
    }
    
    for i, chapter in enumerate(chapter_structure):
        chapter_file = os.path.join(chapter_files_dir, chapter['filename'])
        
        if not os.path.exists(chapter_file):
            print(f"⚠️ Chapter file not found: {chapter_file}")
            results["failed"] += 1
            continue
        
        print(f"\n[{i+1}/{len(chapter_structure)}] Processing: {chapter['title']}")
        
        # Read raw chapter
        with open(chapter_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        # Determine next chapter
        next_title = chapter_structure[i+1]['title'] if i+1 < len(chapter_structure) else None
        
        # Prepare for narration
        narration_ready = prepare_chapter_for_narration(
            chapter_text=raw_text,
            chapter_number=chapter.get('number', i+1),
            chapter_title=chapter['title'],
            book_info=book_info,
            is_prologue=chapter.get('is_prologue', False),
            is_epilogue=chapter.get('is_epilogue', False),
            part_info=chapter.get('part_info'),
            next_chapter_title=next_title
        )
        
        # Save narration-ready file
        output_filename = f"{str(i+1).zfill(2)}_{chapter['title'].replace(' ', '_').replace(':', '')}_narration_ready.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(narration_ready)
        
        print(f"✅ Saved: {output_filename}")
        
        results["successful"] += 1
        results["chapter_results"].append({
            "chapter": chapter['title'],
            "status": "success",
            "output_file": output_path
        })
    
    return results


# Test function
if __name__ == "__main__":
    test_text = """The beginning of November 1979 reflected the air of Communist Russia. It was almost always raining, and the weather influenced my little town of Chernivtsi, located in western Ukraine near the Romanian border.

Not far from the center of the town lay a petite woman of thirty-eight. She had blond hair, dark brown eyes, and tiny wrinkles that unfairly aged her face. The doctors and nurses rushed around her as she gave birth to her fourth child.

"What will you call him?" the nurse asked the exhausted mother.

After a moment of deafening silence, she accepted the child, answering, "Vitaly."

I was four kilograms when I was born, and as my name suggests, I was full of life. But my mother, Evheniya Mikitivna, could not keep me. The headmaster Vasyl Ivanovych took care of me at the orphanage on Fastivska Street."""

    result = prepare_chapter_for_narration(
        chapter_text=test_text,
        chapter_number=1,
        chapter_title="Once Upon a Time",
        book_info={
            "title": "VITALY: The MisAdventures of a Ukrainian Orphan",
            "author": "Vitaly Magidov",
            "genre": "Memoir"
        },
        next_chapter_title="My First Misadventure"
    )
    
    print("=" * 70)
    print("NARRATION-READY OUTPUT:")
    print("=" * 70)
    print(result)
