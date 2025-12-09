#!/usr/bin/env python3
"""
AudiobookSmith V13.2 - Quick Test Runner
Tests V13.2 modules with a PDF file
"""

import sys
from pathlib import Path
from v13_2_modules import (
    AdvancedEpilogueDetector,
    SmartTextSampler,
    AIAnalysisCache,
    CreditsGenerator,
    BookMetadata,
)

def test_v13_2(pdf_path: str):
    """Test all V13.2 features"""
    print("="*80)
    print("AudiobookSmith V13.2 - Module Test")
    print("="*80)
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    output_dir = Path.cwd() / f"{pdf_path.stem}_v13.2_test"
    output_dir.mkdir(exist_ok=True)
    
    # Test 1: Epilogue Detection
    print("\n1. Testing Advanced Epilogue Detection...")
    detector = AdvancedEpilogueDetector(str(pdf_path))
    epilogue = detector.detect()
    if epilogue:
        print(f"   ✅ Found on page {epilogue['page']}, {epilogue['word_count']:,} words")
    else:
        print(f"   ⚠️  Not found")
    detector.close()
    
    # Test 2: Smart Sampling
    print("\n2. Testing Smart Text Sampling...")
    sampler = SmartTextSampler(str(pdf_path))
    sample = sampler.extract_sample(1000)
    print(f"   ✅ Extracted {len(sample.split())} words from 5 locations")
    sampler.close()
    
    # Test 3: Credits Generation
    print("\n3. Testing Credits Generation...")
    metadata = BookMetadata(
        title="Test Book",
        author="Test Author",
        narrator="Test Narrator",
        use_ai_narration=True
    )
    credits = CreditsGenerator(metadata)
    credits_files = credits.save_credits(output_dir)
    print(f"   ✅ Opening: {Path(credits_files['opening']).name}")
    print(f"   ✅ Closing: {Path(credits_files['closing']).name}")
    
    # Test 4: AI Cache
    print("\n4. Testing AI Cache...")
    cache = AIAnalysisCache()
    cached = cache.get(str(pdf_path))
    if cached:
        print(f"   ✅ Cache hit")
    else:
        print(f"   ℹ️  Cache miss (first run)")
        cache.set(str(pdf_path), {'test': 'data'})
        print(f"   ✅ Cached for next time")
    
    print("\n" + "="*80)
    print(f"✅ All tests complete! Output: {output_dir}")
    print("="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_v13_2.py <pdf_file>")
        sys.exit(1)
    
    test_v13_2(sys.argv[1])
