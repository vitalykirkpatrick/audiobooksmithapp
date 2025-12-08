"""
ElevenLabs Voice Recommendation System
Analyzes books and recommends the top 10 most suitable narration voices
"""

import os
import json
import requests
from typing import List, Dict, Optional
from openai import OpenAI

class ElevenLabsVoiceRecommender:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io"
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        self.openai_client = OpenAI()  # For AI recommendations
        
    def get_available_voices(self, category: Optional[str] = None) -> List[Dict]:
        """
        Fetch all available voices from ElevenLabs
        
        Args:
            category: Filter by category (professional, premade, etc.)
        
        Returns:
            List of voice dictionaries
        """
        url = f"{self.base_url}/v2/voices"
        params = {}
        
        if category:
            params['category'] = category
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('voices', [])
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []
    
    def analyze_book_for_voice(self, book_info: Dict, book_excerpt: str) -> Dict:
        """
        Use AI to analyze book and determine ideal voice characteristics
        
        Args:
            book_info: Dictionary with title, genre, author, etc.
            book_excerpt: First few paragraphs of the book
        
        Returns:
            Dictionary with recommended voice characteristics
        """
        prompt = f"""Analyze this book and recommend the ideal audiobook narrator voice characteristics.

Book Information:
- Title: {book_info.get('title', 'Unknown')}
- Genre: {book_info.get('genre', 'Unknown')}
- Type: {book_info.get('document_type', 'Unknown')}
- Author: {book_info.get('author', 'Unknown')}

Book Excerpt (first paragraphs):
{book_excerpt[:1000]}

Based on this information, recommend the ideal voice characteristics for the audiobook narrator:

1. Gender (male/female/neutral)
2. Age range (young adult, middle-aged, mature, elderly)
3. Accent (American, British, Australian, Irish, etc.)
4. Tone (warm, professional, energetic, calm, authoritative, empathetic)
5. Voice quality (deep, high, raspy, smooth, clear)
6. Pacing (slow, moderate, fast)
7. Emotional range (dramatic, subtle, expressive, neutral)

Return ONLY a JSON object with these exact keys:
{{
    "gender": "male/female/neutral",
    "age_range": "young adult/middle-aged/mature/elderly",
    "accent": "American/British/etc",
    "tone": "warm, empathetic",
    "voice_quality": "deep, smooth",
    "pacing": "moderate",
    "emotional_range": "expressive",
    "reasoning": "Brief explanation of why these characteristics fit this book"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert audiobook producer who recommends ideal narrator voices for books."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error analyzing book for voice: {e}")
            return {
                "gender": "neutral",
                "age_range": "middle-aged",
                "accent": "American",
                "tone": "professional",
                "voice_quality": "clear",
                "pacing": "moderate",
                "emotional_range": "balanced",
                "reasoning": "Default recommendation due to analysis error"
            }
    
    def match_voices_to_criteria(self, voices: List[Dict], criteria: Dict, top_n: int = 5) -> List[Dict]:
        """
        Use AI to match available voices to the recommended criteria
        
        Args:
            voices: List of available voices from ElevenLabs
            criteria: Recommended voice characteristics from analyze_book_for_voice
            top_n: Number of top matches to return
        
        Returns:
            List of top N matching voices with match scores
        """
        # Create a simplified voice list for AI analysis
        voice_summaries = []
        for voice in voices[:100]:  # Limit to first 100 to avoid token limits
            voice_summaries.append({
                "voice_id": voice.get('voice_id'),
                "name": voice.get('name'),
                "description": voice.get('description', ''),
                "labels": voice.get('labels', {}),
                "category": voice.get('category', ''),
                "preview_url": voice.get('preview_url', '')
            })
        
        prompt = f"""You are matching audiobook narrator voices to a book's requirements.

Required Voice Characteristics:
{json.dumps(criteria, indent=2)}

Available Voices:
{json.dumps(voice_summaries, indent=2)}

Analyze each voice and select the TOP {top_n} voices that best match the required characteristics.
Consider: gender, accent, age, tone, and description.

Return ONLY a JSON array of the top {top_n} voice IDs in order of best match:
{{
    "recommendations": [
        {{
            "voice_id": "voice_id_here",
            "match_score": 95,
            "match_reason": "Perfect match because..."
        }}
    ]
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at matching narrator voices to books based on voice characteristics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            recommendations = result.get('recommendations', [])
            
            # Enrich recommendations with full voice data
            voice_map = {v['voice_id']: v for v in voices}
            enriched_recommendations = []
            
            for rec in recommendations[:top_n]:
                voice_id = rec['voice_id']
                if voice_id in voice_map:
                    voice_data = voice_map[voice_id].copy()
                    voice_data['match_score'] = rec.get('match_score', 0)
                    voice_data['match_reason'] = rec.get('match_reason', '')
                    enriched_recommendations.append(voice_data)
            
            return enriched_recommendations
            
        except Exception as e:
            print(f"Error matching voices: {e}")
            # Fallback: return first N voices
            return voices[:top_n]
    
    def generate_voice_sample(self, voice_id: str, text: str, output_path: str) -> bool:
        """
        Generate a voice sample using ElevenLabs TTS
        
        Args:
            voice_id: ElevenLabs voice ID
            text: Text to convert to speech
            output_path: Where to save the MP3 file
        
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}"
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Save audio file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Error generating voice sample for {voice_id}: {e}")
            return False
    
    def recommend_voices_for_book(self, book_info: Dict, book_excerpt: str, 
                                   output_dir: str, top_n: int = 5) -> Dict:
        """
        Complete workflow: analyze book, recommend voices, generate samples
        
        Args:
            book_info: Book metadata (title, genre, etc.)
            book_excerpt: First few paragraphs for sample generation
            output_dir: Directory to save voice samples
            top_n: Number of voices to recommend
        
        Returns:
            Dictionary with recommendations and sample paths
        """
        print(f"\n{'='*70}")
        print("🎙️ VOICE RECOMMENDATION SYSTEM")
        print(f"{'='*70}")
        
        # Step 1: Analyze book for ideal voice characteristics
        print("\n[1/4] Analyzing book for ideal voice characteristics...")
        voice_criteria = self.analyze_book_for_voice(book_info, book_excerpt)
        print(f"✅ Recommended characteristics:")
        print(f"   Gender: {voice_criteria.get('gender')}")
        print(f"   Age: {voice_criteria.get('age_range')}")
        print(f"   Accent: {voice_criteria.get('accent')}")
        print(f"   Tone: {voice_criteria.get('tone')}")
        
        # Step 2: Get available voices
        print("\n[2/4] Fetching available voices from ElevenLabs...")
        all_voices = self.get_available_voices()
        print(f"✅ Found {len(all_voices)} available voices")
        
        # Step 3: Match voices to criteria
        print(f"\n[3/4] Matching voices to book characteristics...")
        recommended_voices = self.match_voices_to_criteria(all_voices, voice_criteria, top_n)
        print(f"✅ Selected top {len(recommended_voices)} matching voices")
        
        # Step 4: Generate voice samples
        print(f"\n[4/4] Generating voice samples...")
        sample_text = book_excerpt[:500]  # First 500 characters for sample
        
        voice_samples_dir = os.path.join(output_dir, "voice_samples")
        os.makedirs(voice_samples_dir, exist_ok=True)
        
        results = []
        for i, voice in enumerate(recommended_voices, 1):
            voice_id = voice['voice_id']
            voice_name = voice['name']
            sample_path = os.path.join(voice_samples_dir, f"{voice_id}.mp3")
            
            print(f"   [{i}/{len(recommended_voices)}] Generating sample for {voice_name}...")
            
            success = self.generate_voice_sample(voice_id, sample_text, sample_path)
            
            results.append({
                "voice_id": voice_id,
                "name": voice_name,
                "description": voice.get('description', ''),
                "labels": voice.get('labels', {}),
                "preview_url": voice.get('preview_url', ''),
                "match_score": voice.get('match_score', 0),
                "match_reason": voice.get('match_reason', ''),
                "sample_path": sample_path if success else None,
                "sample_generated": success
            })
        
        print(f"\n✅ Voice recommendation complete!")
        print(f"   Recommended voices: {len(results)}")
        print(f"   Samples generated: {sum(1 for r in results if r['sample_generated'])}")
        
        return {
            "voice_criteria": voice_criteria,
            "recommended_voices": results,
            "sample_text": sample_text
        }


# Standalone test function
if __name__ == "__main__":
    # Test with sample book info
    api_key = os.getenv("ELEVENLABS_API_KEY", "sk_b006ebce7fa44b04bdc0037b5858fbdaa62e85688177a5b4")
    
    recommender = ElevenLabsVoiceRecommender(api_key)
    
    book_info = {
        "title": "VITALY The MisAdventures of a Ukrainian Orphan",
        "genre": "Memoir",
        "document_type": "Memoir",
        "author": "Vitaly Magidov"
    }
    
    book_excerpt = """
    I was born in the Soviet Union in 1982, in a small town called Chernivtsi, 
    located in the southwestern part of Ukraine. My early years were marked by 
    uncertainty and hardship, as I found myself in the foster care system at a 
    young age. This is my story of survival, resilience, and the search for 
    belonging in a world that often felt cold and unwelcoming.
    """
    
    results = recommender.recommend_voices_for_book(
        book_info=book_info,
        book_excerpt=book_excerpt,
        output_dir="/tmp/test_voices",
        top_n=5
    )
    
    print("\n" + "="*70)
    print("RESULTS:")
    print(json.dumps(results, indent=2, default=str))
