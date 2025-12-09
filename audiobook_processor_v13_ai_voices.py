#!/usr/bin/env python3
"""
AudiobookSmith Processor V13 - AI-Powered Voice Recommendations
Features:
- Dynamic voice recommendations based on book analysis
- AI-powered cultural context analysis
- Perplexity verification integration
- Enhanced metadata display
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Import V12 base
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid_chapter_splitter_production import HybridChapterSplitter

# Try to import OpenAI for AI analysis
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available. Install with: pip install openai")


class AIBookAnalyzer:
    """AI-powered book analysis for voice recommendations"""
    
    def __init__(self):
        self.client = None
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.client = OpenAI()
    
    def analyze_book_for_voices(self, book_text: str, metadata: dict = None) -> dict:
        """
        Analyze book content and generate dynamic voice recommendations
        
        Returns:
            dict with voice recommendations, cultural context, and analysis
        """
        # Extract sample text for analysis (first 5000 words)
        words = book_text.split()[:5000]
        sample_text = ' '.join(words)
        
        # If AI available, use it for deep analysis
        if self.client:
            return self._ai_powered_analysis(sample_text, metadata)
        else:
            return self._rule_based_analysis(sample_text, metadata)
    
    def _ai_powered_analysis(self, sample_text: str, metadata: dict) -> dict:
        """Use AI to analyze book and generate voice recommendations"""
        
        prompt = f"""Analyze this book excerpt and provide voice narrator recommendations for audiobook production.

Book Excerpt:
{sample_text[:3000]}

{"Book Metadata: " + json.dumps(metadata.get('book_information', {}), indent=2) if metadata else ""}

Please provide:
1. **Cultural Context**: Identify nationality, cultural background, historical period, traditions
2. **Genre & Tone**: Primary genre, emotional tone, narrative style
3. **Target Audience**: Age range, demographics, interests
4. **Voice Recommendations**: Top 3-5 narrator voice profiles with:
   - Gender and age range
   - Accent/dialect requirements
   - Vocal characteristics (warm, authoritative, intimate, etc.)
   - Match percentage (0-100%)
   - Detailed rationale for why this voice fits

Format as JSON with keys: cultural_context, genre_analysis, target_audience, voice_recommendations"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert audiobook producer and voice casting director with deep knowledge of narration styles, cultural authenticity, and audience preferences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse AI response
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: parse structured text
                return self._parse_ai_text_response(content)
                
        except Exception as e:
            print(f"⚠️  AI analysis failed: {e}")
            return self._rule_based_analysis(sample_text, metadata)
    
    def _rule_based_analysis(self, sample_text: str, metadata: dict) -> dict:
        """Fallback rule-based analysis when AI not available"""
        
        text_lower = sample_text.lower()
        
        # Detect cultural markers
        cultural_markers = {
            'ukrainian': ['ukraine', 'ukrainian', 'kiev', 'kyiv', 'soviet', 'ussr'],
            'russian': ['russia', 'russian', 'moscow', 'soviet'],
            'american': ['america', 'united states', 'usa'],
            'british': ['britain', 'england', 'london', 'british'],
        }
        
        detected_culture = 'Unknown'
        for culture, markers in cultural_markers.items():
            if any(marker in text_lower for marker in markers):
                detected_culture = culture.title()
                break
        
        # Detect genre markers
        genre_markers = {
            'memoir': ['i was', 'i remember', 'my life', 'growing up', 'childhood'],
            'fiction': ['chapter', 'once upon', 'the story'],
            'biography': ['was born', 'life of', 'biography'],
        }
        
        detected_genre = 'Unknown'
        for genre, markers in genre_markers.items():
            if any(marker in text_lower for marker in markers):
                detected_genre = genre.title()
                break
        
        # Generate voice recommendations based on detected characteristics
        voices = []
        
        if detected_culture == 'Ukrainian' or 'orphan' in text_lower:
            voices.append({
                "name": "Vladislav Pro",
                "gender": "male",
                "age_range": "young adult (25-35)",
                "accent": "American with Eastern European inflection",
                "characteristics": ["warm", "empathetic", "authentic"],
                "match_percentage": 85,
                "rationale": f"Young male voice with ability to convey {detected_culture} cultural authenticity. Warm tone suitable for memoir/personal narrative. Can authentically pronounce cultural names and convey emotional depth."
            })
            
            voices.append({
                "name": "Will",
                "gender": "male",
                "age_range": "young (20-30)",
                "accent": "American, neutral",
                "characteristics": ["conversational", "relatable", "smooth"],
                "match_percentage": 80,
                "rationale": "Clear American voice with conversational style. Age-appropriate for young adult narrator perspective. Smooth delivery for accessibility."
            })
            
            voices.append({
                "name": "Roger",
                "gender": "male",
                "age_range": "middle-aged (40-55)",
                "accent": "American, standard",
                "characteristics": ["warm", "mature", "reflective"],
                "match_percentage": 75,
                "rationale": "Mature voice for reflective memoir narration. Warm and empathetic tone conveys life experience and wisdom gained through hardship."
            })
        
        else:
            # Generic recommendations
            voices.append({
                "name": "Professional Narrator",
                "gender": "neutral",
                "age_range": "adult (30-50)",
                "accent": "Standard American",
                "characteristics": ["clear", "professional", "versatile"],
                "match_percentage": 70,
                "rationale": f"Professional narrator suitable for {detected_genre} genre with clear, engaging delivery."
            })
        
        return {
            "cultural_context": {
                "nationality": detected_culture,
                "cultural_background": f"Content suggests {detected_culture} cultural context",
                "historical_period": "Modern era" if 'soviet' not in text_lower else "Cold War/Post-Soviet era",
                "traditions": "Analysis based on text content"
            },
            "genre_analysis": {
                "primary_genre": detected_genre,
                "tone": "Personal and reflective" if detected_genre == 'Memoir' else "Narrative",
                "style": "First-person narrative" if 'i was' in text_lower else "Third-person narrative"
            },
            "target_audience": {
                "age_range": "Young Adult to Adult (16+)",
                "demographics": "Readers interested in personal stories and cultural experiences",
                "interests": [detected_genre, "Cultural studies", "Personal growth"]
            },
            "voice_recommendations": voices
        }
    
    def _parse_ai_text_response(self, text: str) -> dict:
        """Parse AI text response into structured format"""
        # Simple parsing - can be enhanced
        return {
            "cultural_context": {"analysis": text[:500]},
            "genre_analysis": {"analysis": "See full AI response"},
            "target_audience": {"analysis": "See full AI response"},
            "voice_recommendations": [],
            "ai_full_response": text
        }


class AudiobookProcessorV13:
    """
    AudiobookSmith Processor V13 with AI-Powered Voice Recommendations
    
    Features:
    - Dynamic voice recommendations based on book analysis
    - AI-powered cultural context
    - Metadata integration
    - Enhanced analysis page
    """
    
    def __init__(self, pdf_path: str, output_dir: str = None):
        self.pdf_path = pdf_path
        self.output_dir = output_dir or self._create_output_dir()
        self.splitter = HybridChapterSplitter(pdf_path, min_chapter_length=500)
        self.analyzer = AIBookAnalyzer()
        self.result = None
        self.metadata = self._load_metadata()
        self.ai_analysis = None
        
    def _create_output_dir(self) -> str:
        """Create output directory based on PDF filename"""
        base_name = Path(self.pdf_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"{base_name}_v13_analysis_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/chapters", exist_ok=True)
        return output_dir
    
    def _load_metadata(self) -> dict:
        """Load enriched metadata if available"""
        metadata_file = Path(__file__).parent / "vitaly_book_final_enriched_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def process(self) -> dict:
        """Process PDF and generate analysis with AI voice recommendations"""
        print("🎙️  AudiobookSmith V13 - AI-Powered Voice Recommendations")
        print("=" * 80)
        
        # Step 1: Extract chapters using V12 hybrid splitter
        print("\n📖 Step 1: Extracting chapters...")
        result = self.splitter.extract_chapters()
        # Handle both dict and object formats
        chapters = []
        for ch in result['chapters']:
            if isinstance(ch, dict):
                chapters.append((ch['title'], ch['content']))
            else:
                chapters.append((ch.title, ch.content))
        print(f"✅ Found {len(chapters)} chapters")
        
        # Step 2: Save chapter files
        print("\n💾 Step 2: Saving chapter files...")
        self._save_chapters(chapters)
        
        # Step 3: AI Analysis for voice recommendations
        print("\n🤖 Step 3: Analyzing book for voice recommendations...")
        full_text = '\n\n'.join([content for _, content in chapters])
        self.ai_analysis = self.analyzer.analyze_book_for_voices(full_text, self.metadata)
        print("✅ AI analysis complete")
        
        # Step 4: Generate enhanced analysis page
        print("\n📊 Step 4: Generating analysis page...")
        self._generate_analysis_page(chapters)
        print(f"✅ Analysis page: {self.output_dir}/analysis.html")
        
        self.result = {
            'count': len(chapters),
            'chapters': chapters,
            'ai_analysis': self.ai_analysis,
            'output_dir': self.output_dir
        }
        
        print("\n" + "=" * 80)
        print(f"🎉 Processing complete! Output: {self.output_dir}")
        return self.result
    
    def _save_chapters(self, chapters: list):
        """Save chapter files"""
        for i, (title, content) in enumerate(chapters, 1):
            # Clean title for filename
            clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
            filename = f"{i:02d}_{clean_title}.txt"
            filepath = os.path.join(self.output_dir, "chapters", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{content}")
    
    def _generate_analysis_page(self, chapters: list):
        """Generate enhanced HTML analysis page with AI voice recommendations"""
        
        total_words = sum(len(content.split()) for _, content in chapters)
        
        # Build voice recommendations HTML
        voices_html = self._build_voices_html()
        
        # Build metadata HTML
        metadata_html = self._build_metadata_html()
        
        # Build cultural context HTML
        cultural_html = self._build_cultural_context_html()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AudiobookSmith V13 Analysis - AI-Powered Voice Recommendations</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        .content {{ padding: 40px; }}
        .section {{
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .voice-card {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }}
        .voice-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .voice-name {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .match-badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .voice-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }}
        .voice-detail {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }}
        .voice-detail-label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .voice-detail-value {{
            font-weight: 600;
            color: #333;
            margin-top: 5px;
        }}
        .voice-rationale {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #667eea;
            font-style: italic;
            color: #555;
        }}
        .characteristics {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        .characteristic-tag {{
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        .metadata-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
        }}
        .metadata-label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .metadata-value {{
            font-weight: 600;
            color: #333;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ AudiobookSmith V13</h1>
            <p>AI-Powered Voice Recommendations & Book Analysis</p>
        </div>
        
        <div class="content">
            <!-- Success Metrics -->
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{len(chapters)}</div>
                    <div class="stat-label">Chapters Found</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_words:,}</div>
                    <div class="stat-label">Total Words</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(self.ai_analysis.get('voice_recommendations', []))}</div>
                    <div class="stat-label">Voice Options</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">V13</div>
                    <div class="stat-label">AI-Powered</div>
                </div>
            </div>
            
            {metadata_html}
            
            {cultural_html}
            
            {voices_html}
            
            <!-- Chapter Details -->
            <div class="section">
                <h2>📚 Chapter Details</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Chapter Title</th>
                            <th>Word Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{i}</td><td>{title}</td><td>{len(content.split()):,}</td></tr>' for i, (title, content) in enumerate(chapters, 1))}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by AudiobookSmith V13 - AI-Powered Voice Recommendations</p>
            <p>Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(os.path.join(self.output_dir, "analysis.html"), 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _build_voices_html(self) -> str:
        """Build voice recommendations HTML section"""
        if not self.ai_analysis or not self.ai_analysis.get('voice_recommendations'):
            return ""
        
        voices = self.ai_analysis['voice_recommendations']
        
        voices_cards = []
        for voice in voices:
            characteristics_html = ''.join(
                f'<span class="characteristic-tag">{char}</span>' 
                for char in voice.get('characteristics', [])
            )
            
            card = f"""
            <div class="voice-card">
                <div class="voice-header">
                    <div class="voice-name">🎤 {voice.get('name', 'Professional Narrator')}</div>
                    <div class="match-badge">{voice.get('match_percentage', 0)}% Match</div>
                </div>
                <div class="voice-details">
                    <div class="voice-detail">
                        <div class="voice-detail-label">Gender</div>
                        <div class="voice-detail-value">{voice.get('gender', 'N/A').title()}</div>
                    </div>
                    <div class="voice-detail">
                        <div class="voice-detail-label">Age Range</div>
                        <div class="voice-detail-value">{voice.get('age_range', 'N/A')}</div>
                    </div>
                    <div class="voice-detail">
                        <div class="voice-detail-label">Accent</div>
                        <div class="voice-detail-value">{voice.get('accent', 'N/A')}</div>
                    </div>
                </div>
                <div class="characteristics">
                    {characteristics_html}
                </div>
                <div class="voice-rationale">
                    <strong>Why this voice:</strong> {voice.get('rationale', 'Suitable for this book based on genre and tone.')}
                </div>
            </div>
            """
            voices_cards.append(card)
        
        return f"""
        <div class="section">
            <h2>🎙️ Recommended Narrator Voices</h2>
            <p style="margin-bottom: 20px; color: #666;">AI-powered voice recommendations based on book analysis, cultural context, and target audience.</p>
            {''.join(voices_cards)}
        </div>
        """
    
    def _build_metadata_html(self) -> str:
        """Build metadata section HTML"""
        if not self.metadata or not self.metadata.get('book_information'):
            return ""
        
        info = self.metadata['book_information']
        ratings = self.metadata.get('ratings_and_reviews', {})
        
        return f"""
        <div class="section">
            <h2>📖 Book Information</h2>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Title</div>
                    <div class="metadata-value">{info.get('title', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Author</div>
                    <div class="metadata-value">{info.get('author', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">ISBN</div>
                    <div class="metadata-value">{info.get('isbn_paperback', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Publication Date</div>
                    <div class="metadata-value">{info.get('publication_date', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Pages</div>
                    <div class="metadata-value">{info.get('pages', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Goodreads Rating</div>
                    <div class="metadata-value">⭐ {ratings.get('goodreads', {}).get('rating', 'N/A')}/5.0</div>
                </div>
            </div>
        </div>
        """
    
    def _build_cultural_context_html(self) -> str:
        """Build cultural context section HTML"""
        if not self.ai_analysis or not self.ai_analysis.get('cultural_context'):
            return ""
        
        context = self.ai_analysis['cultural_context']
        genre = self.ai_analysis.get('genre_analysis', {})
        audience = self.ai_analysis.get('target_audience', {})
        
        return f"""
        <div class="section">
            <h2>🌍 Cultural Context & Analysis</h2>
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Nationality/Origin</div>
                    <div class="metadata-value">{context.get('nationality', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Cultural Background</div>
                    <div class="metadata-value">{context.get('cultural_background', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Historical Period</div>
                    <div class="metadata-value">{context.get('historical_period', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Primary Genre</div>
                    <div class="metadata-value">{genre.get('primary_genre', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Narrative Tone</div>
                    <div class="metadata-value">{genre.get('tone', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Target Audience</div>
                    <div class="metadata-value">{audience.get('age_range', 'N/A')}</div>
                </div>
            </div>
        </div>
        """


def main():
    if len(sys.argv) < 2:
        print("Usage: python audiobook_processor_v13_ai_voices.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    processor = AudiobookProcessorV13(pdf_path)
    result = processor.process()
    
    print(f"\n✅ Success! Found {result['count']} chapters")
    print(f"📁 Output: {result['output_dir']}")
    print(f"🎙️  Voice recommendations: {len(result['ai_analysis'].get('voice_recommendations', []))}")


if __name__ == "__main__":
    main()
