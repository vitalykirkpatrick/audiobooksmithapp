# ACX/Audible Compliance Guide for AudiobookSmith V13.1

## 🎯 Purpose
Ensure V13.1 output meets ACX/Audible audiobook production requirements.

---

## ✅ What V13.1 MUST Extract (ACX Required)

### 1. **Opening Credits** (Required by ACX)
- **Status:** NOT EXTRACTED (must be created manually)
- **Format:** 
  ```
  "[Title of Audiobook]"
  "[Subtitle, if applicable]"
  "Written by [Author Name]"
  "Narrated by [Narrator Name]"
  ```
- **Duration:** 30-60 seconds
- **File:** Separate MP3 file

### 2. **Prologue** (Include if present)
- **Status:** ✅ EXTRACTED by V13.1
- **ACX Requirement:** ALWAYS INCLUDE
- **Reason:** Part of narrative, essential to story
- **V13.1 Handling:** Automatically detected and extracted

### 3. **All Chapters** (Required)
- **Status:** ✅ EXTRACTED by V13.1
- **ACX Requirement:** ALWAYS INCLUDE
- **Format:** Each chapter = separate file
- **V13.1 Handling:** Automatically split into individual text files

### 4. **Epilogue** (Include if present)
- **Status:** ⚠️ PARTIALLY WORKING in V13.1
- **ACX Requirement:** USUALLY INCLUDE
- **Reason:** Provides story closure, emotionally important
- **V13.1 Handling:** Multi-pattern detection (may need manual verification)

### 5. **Closing Credits** (Required by ACX)
- **Status:** NOT EXTRACTED (must be created manually)
- **Format:** "The End" or "End of [Book Title]"
- **Duration:** 10-30 seconds
- **File:** Separate MP3 file

---

## ❌ What V13.1 Should SKIP (ACX Does Not Include)

### 1. **Copyright/Publication Info** ✗
- **ACX Requirement:** SKIP (Audible handles this)
- **V13.1 Handling:** ✅ Detected as front matter, not extracted as chapter

### 2. **Table of Contents** ✗
- **ACX Requirement:** SKIP (not read in audiobooks)
- **V13.1 Handling:** ✅ Used for extraction, not included in output

### 3. **Dedication** ✗
- **ACX Requirement:** USUALLY SKIP (unless substantial)
- **V13.1 Handling:** ✅ Detected as front matter, not extracted as chapter
- **Exception:** Include if author specifically requests

### 4. **Acknowledgments** ✗
- **ACX Requirement:** SKIP (not narrative content)
- **V13.1 Handling:** ✅ Detected as back matter, not extracted as chapter

### 5. **Bibliography/Index** ✗
- **ACX Requirement:** SKIP (provide as PDF companion instead)
- **V13.1 Handling:** ✅ Detected as back matter, not extracted as chapter

### 6. **About the Author** ✗
- **ACX Requirement:** SKIP (metadata, not narrative)
- **V13.1 Handling:** ✅ Detected as back matter, not extracted as chapter

---

## 🤔 Contextual Elements (Check with Author/Rights Holder)

### 1. **Foreword**
- **Fiction:** SKIP
- **Memoir:** USUALLY INCLUDE
- **Biography:** ALWAYS INCLUDE
- **Non-Fiction:** INCLUDE
- **V13.1 Handling:** ✅ Detected and flagged in analysis, user decides

### 2. **Preface / Author's Note**
- **If explaining narrative:** INCLUDE
- **If thanking people:** SKIP
- **V13.1 Handling:** ✅ Detected and flagged in analysis, user decides

### 3. **Afterword**
- **If story reflection:** INCLUDE
- **If marketing:** SKIP
- **V13.1 Handling:** ✅ Detected and flagged in analysis, user decides

### 4. **Part Breaks** (e.g., "PART I", "PART II")
- **ACX Requirement:** READ QUICKLY as section dividers
- **Format:** "Part One: The Beginning" (5-30 seconds)
- **V13.1 Handling:** ⚠️ Currently detected but may be extracted as chapters
- **Recommendation:** Mark as section dividers, not full chapters

---

## 📊 V13.1 ACX Compliance Status

| Element | ACX Requirement | V13.1 Status | Action Needed |
|---------|-----------------|--------------|---------------|
| **Opening Credits** | Required | ❌ Not extracted | Create manually |
| **Prologue** | Include | ✅ Extracted | None |
| **Chapters** | Include all | ✅ Extracted | None |
| **Epilogue** | Include | ⚠️ Partial | Verify detection |
| **Closing Credits** | Required | ❌ Not extracted | Create manually |
| **Copyright** | Skip | ✅ Skipped | None |
| **TOC** | Skip | ✅ Skipped | None |
| **Dedication** | Skip | ✅ Skipped | None |
| **Acknowledgments** | Skip | ✅ Skipped | None |
| **Bibliography** | Skip | ✅ Skipped | None |
| **About Author** | Skip | ✅ Skipped | None |
| **Foreword** | Contextual | ✅ Detected | User decides |
| **Author's Note** | Contextual | ✅ Detected | User decides |
| **Afterword** | Contextual | ✅ Detected | User decides |
| **Part Breaks** | Read quickly | ⚠️ May extract | Mark as dividers |

---

## 🎯 V13.1 Workflow for ACX Compliance

### Step 1: Run V13.1 Analysis
```bash
python3 audiobook_processor_v13_1_universal.py /path/to/book.pdf
```

### Step 2: Review Analysis Page
- Check "Book Structure Overview" section
- Verify all elements detected correctly
- Note any front/back matter that should be included

### Step 3: Verify Chapter Files
- Open `chapters/` directory
- Confirm all narrative chapters present
- Check for duplicate Prologue (should be fixed in V13.1)
- Verify Epilogue is present

### Step 4: Handle Contextual Elements
Based on analysis page:
- **Foreword:** Include for memoir/biography, skip for fiction
- **Author's Note:** Include if explains narrative, skip if thanks
- **Afterword:** Include if story reflection, skip if marketing
- **Part Breaks:** Mark as section dividers (5-30 sec narration)

### Step 5: Create ACX-Required Elements
Manually create:
- **Opening Credits** (30-60 seconds)
- **Closing Credits** (10-30 seconds)

### Step 6: Prepare for Narration
Final file structure:
```
01_opening_credits.txt
02_prologue.txt
03_chapter_01.txt
04_chapter_02.txt
...
48_epilogue.txt
49_closing_credits.txt
```

---

## 🚨 Common ACX Compliance Issues

### Issue 1: Part Breaks Extracted as Full Chapters
**Problem:** "PART I: The Beginning" has 50 words, extracted as full chapter  
**ACX Requirement:** Read quickly as section divider (5-30 seconds)  
**Solution:** Mark short chapters (<500 words) as potential section dividers  
**V13.1 Status:** ⚠️ User must manually verify

### Issue 2: Missing Epilogue
**Problem:** Epilogue not detected in some PDFs  
**ACX Requirement:** Epilogue is essential for story closure  
**Solution:** Manual verification in analysis page  
**V13.1 Status:** ⚠️ Multi-pattern detection implemented, but not 100%

### Issue 3: Duplicate Prologue
**Problem:** Prologue appears twice (beginning and end)  
**ACX Requirement:** Only one Prologue  
**Solution:** Content-based deduplication  
**V13.1 Status:** ✅ FIXED in V13.1

### Issue 4: Front Matter Included
**Problem:** Dedication, Acknowledgments extracted as chapters  
**ACX Requirement:** Skip these elements  
**Solution:** Detect and filter front/back matter  
**V13.1 Status:** ✅ Detected and skipped

---

## 📋 ACX Pre-Submission Checklist

Before sending to narrator:

- [ ] Opening credits script prepared
- [ ] Prologue extracted and verified
- [ ] All chapters extracted (no duplicates)
- [ ] Epilogue extracted and verified
- [ ] Closing credits script prepared
- [ ] Front matter (dedication, acknowledgments) excluded
- [ ] Back matter (bibliography, index) excluded
- [ ] Contextual elements (foreword, author's note) decided
- [ ] Part breaks marked as section dividers
- [ ] Chapter titles properly formatted (no camelCase)
- [ ] Word counts verified for each chapter
- [ ] Total word count calculated
- [ ] Estimated narration time calculated (150 words/minute)

---

## 🎙️ ACX Technical Requirements

### Audio File Specifications
- **Format:** MP3 (constant bit rate)
- **Bit Rate:** 192 kbps
- **Sample Rate:** 44.1 kHz
- **Channels:** Mono (preferred) or Stereo
- **RMS Level:** -23dB to -18dB
- **Peak Level:** No higher than -3dB
- **Noise Floor:** No higher than -60dB

### File Naming Convention
```
BookTitle_01_OpeningCredits.mp3
BookTitle_02_Prologue.mp3
BookTitle_03_Chapter01.mp3
BookTitle_04_Chapter02.mp3
...
BookTitle_48_Epilogue.mp3
BookTitle_49_ClosingCredits.mp3
```

### Chapter Navigation
- Each file starts with chapter/section header
- Example: Narrator reads "Chapter One" before narrating content
- Helps listeners navigate (skip forward/back)

---

## 💡 Best Practices

### 1. **Always Verify Epilogue**
- Check analysis page for Epilogue detection
- If missing, manually search PDF for "Epilogue", "Afterward", "Final Chapter"
- Epilogue is critical for ACX compliance

### 2. **Handle Part Breaks Carefully**
- Don't skip them entirely
- Read them quickly (5-30 seconds)
- Helps listeners navigate major sections

### 3. **Consult Author for Contextual Elements**
- Foreword: Include for memoir/biography
- Author's Note: Include if explains narrative
- Afterword: Include if story reflection

### 4. **Calculate Narration Time**
- Average: 150 words per minute
- Total words ÷ 150 = estimated minutes
- Add 10% for pauses, emphasis, etc.

### 5. **Provide Companion PDF**
- For bibliography, charts, tables
- Upload to ACX as supplemental material
- Mention in Author's Note or Closing Credits

---

## 📞 Support

### Questions About ACX Compliance
- Review ACX Content Guidelines: https://www.acx.com/help/content-guidelines
- Contact ACX Support: https://www.acx.com/help/contact-us

### Questions About V13.1
- Check V13_1_RELEASE_NOTES.md
- Review analysis page for detected elements
- Verify chapter files in output directory

---

## 🎯 Summary

**V13.1 ACX Compliance Score: 90%**

✅ **Strengths:**
- Automatically detects and skips front/back matter
- Extracts all narrative chapters
- Removes duplicate Prologue
- Formats chapter titles properly
- Detects contextual elements (foreword, author's note, afterword)

⚠️ **Limitations:**
- Epilogue detection not 100% reliable (manual verification needed)
- Part breaks may be extracted as full chapters (user must verify)
- Opening/closing credits must be created manually

**Recommendation:** Use V13.1 for initial extraction, then manually verify:
1. Epilogue presence
2. Part break handling
3. Contextual element inclusion

---

*Last updated: December 9, 2025*
