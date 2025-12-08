# 🎨 Frontend Integration Guide - V7 Enhanced

**For:** Greta (Frontend Developer)  
**Date:** December 8, 2025  
**Priority:** HIGH

---

## 🎯 QUICK START

The backend now returns **MUCH MORE DATA** than before. Here's what changed:

### What You Need to Update

1. **Parse the new data fields** (title, author, themes, chapters)
2. **Display voice recommendations** with criteria and reasoning
3. **Show chapter list** with detected chapters
4. **Add theme tags** and narrative analysis
5. **Fix word count display** (currently shows "N/A")

---

## 📊 NEW DATA STRUCTURE

### Before (Old Response)
```javascript
{
  success: true,
  payload: {
    projectId: "abc123",
    metrics: {
      word_count: 107414  // ← This exists but frontend shows "N/A"
    }
  }
}
```

### After (New Response)
```javascript
{
  success: true,
  payload: {
    projectId: "abc123",
    bookInfo: {
      title: "Vitaly: From Orphan to Entrepreneur",  // ← NEW!
      author: "Vitaly Kirkpatrick",  // ← NEW!
      genre: "Memoir",  // ← Enhanced
      themes: ["Resilience", "Immigration", "Entrepreneurship"],  // ← NEW!
      narrative_tone: "Personal, reflective, inspirational",  // ← NEW!
      target_audience: "Adults interested in memoirs",  // ← NEW!
      content_warnings: ["Childhood trauma"],  // ← NEW!
      age_rating: "Adult"  // ← NEW!
    },
    metrics: {
      word_count: 107414,
      page_count: 289,
      reading_time: "537m",
      audio_length: "716m"
    },
    structure: {
      total_chapters: 46,  // ← NEW! (was 0 before)
      chapters: [  // ← NEW! (was empty before)
        {
          number: 1,
          title: "Chapter 1: The Beginning",
          start_text: "I was born in..."
        }
        // ... more chapters
      ],
      has_prologue: true,  // ← NEW!
      has_epilogue: true,  // ← NEW!
      structure_type: "chapters"  // ← NEW!
    },
    voiceRecommendations: {
      voice_criteria: {  // ← NEW!
        gender: "male",
        age_range: "young adult",
        accent: "American with subtle Eastern European inflection",
        tone: "warm, empathetic",
        voice_quality: "clear, smooth",
        pacing: "moderate",
        emotional_range: "expressive",
        reasoning: "As a memoir recounting the life of a Ukrainian orphan..."
      },
      recommended_voices: [  // ← Enhanced with more details
        {
          voice_id: "CwhRBWXzGAHq8TQ4Fs17",
          name: "Roger",
          description: "Easy going and perfect for casual conversations.",
          labels: {
            accent: "american",
            age: "middle_aged",
            gender: "male",
            use_case: "conversational"
          },
          preview_url: "https://...",
          match_score: 90,  // ← NEW!
          match_reason: "Male, American accent, clear voice..."  // ← NEW!
        }
        // ... 4 more voices
      ]
    }
  }
}
```

---

## 🛠️ CODE UPDATES NEEDED

### 1. Fix Word Count Display

**Current Issue:** Shows "N/A" even though backend returns the number

**Location:** Find where you display word count

**BEFORE (Wrong):**
```javascript
const wordCount = response.wordCount || 'N/A';
// or
const wordCount = response.metrics?.word_count || 'N/A';
```

**AFTER (Correct):**
```javascript
const payload = response.payload || response;
const wordCount = payload.metrics?.word_count || 0;

// Display with formatting
document.getElementById('wordCount').textContent = wordCount.toLocaleString();
// Shows: "107,414" instead of "N/A"
```

### 2. Display Book Title and Author

**Add this after successful upload:**

```javascript
const payload = response.payload;

// Extract book info
const title = payload.bookInfo?.title || 'Unknown';
const author = payload.bookInfo?.author || 'Unknown';
const genre = payload.bookInfo?.genre || 'Unknown';

// Update UI
document.getElementById('bookTitle').textContent = title;
document.getElementById('bookAuthor').textContent = `by ${author}`;
document.getElementById('bookGenre').textContent = genre;

// Example output:
// Title: "Vitaly: From Orphan to Entrepreneur"
// Author: "by Vitaly Kirkpatrick"
// Genre: "Memoir"
```

### 3. Display Themes

**Add a themes section:**

```javascript
const themes = payload.bookInfo?.themes || [];

if (themes.length > 0) {
  const themesContainer = document.getElementById('themesContainer');
  themesContainer.innerHTML = '<h4>Main Themes:</h4>';
  
  themes.forEach(theme => {
    const tag = document.createElement('span');
    tag.className = 'theme-tag';
    tag.textContent = theme;
    themesContainer.appendChild(tag);
  });
}

// CSS for theme tags:
// .theme-tag {
//   display: inline-block;
//   background: #e0e7ff;
//   color: #4338ca;
//   padding: 4px 12px;
//   border-radius: 16px;
//   margin: 4px;
//   font-size: 14px;
// }
```

### 4. Display Narrative Analysis

**Add narrative information:**

```javascript
const narrativeTone = payload.bookInfo?.narrative_tone || '';
const targetAudience = payload.bookInfo?.target_audience || '';
const ageRating = payload.bookInfo?.age_rating || '';
const contentWarnings = payload.bookInfo?.content_warnings || [];

// Display narrative tone
if (narrativeTone) {
  document.getElementById('narrativeTone').textContent = narrativeTone;
}

// Display target audience
if (targetAudience) {
  document.getElementById('targetAudience').textContent = targetAudience;
}

// Display age rating
if (ageRating) {
  document.getElementById('ageRating').textContent = ageRating;
}

// Display content warnings
if (contentWarnings.length > 0) {
  const warningsDiv = document.getElementById('contentWarnings');
  warningsDiv.innerHTML = '<strong>Content Warnings:</strong> ' + contentWarnings.join(', ');
}
```

### 5. Display Chapter Information

**Show detected chapters:**

```javascript
const totalChapters = payload.structure?.total_chapters || 0;
const chapters = payload.structure?.chapters || [];
const hasPrologue = payload.structure?.has_prologue || false;
const hasEpilogue = payload.structure?.has_epilogue || false;

// Update chapter count
document.getElementById('chapterCount').textContent = totalChapters;

// Display chapter list
if (chapters.length > 0) {
  const chapterList = document.getElementById('chapterList');
  chapterList.innerHTML = '<h4>Chapters:</h4>';
  
  if (hasPrologue) {
    chapterList.innerHTML += '<div class="chapter-item">Prologue</div>';
  }
  
  chapters.forEach(chapter => {
    const chapterDiv = document.createElement('div');
    chapterDiv.className = 'chapter-item';
    chapterDiv.innerHTML = `
      <strong>${chapter.title}</strong>
      <p class="chapter-preview">${chapter.start_text}</p>
    `;
    chapterList.appendChild(chapterDiv);
  });
  
  if (hasEpilogue) {
    chapterList.innerHTML += '<div class="chapter-item">Epilogue</div>';
  }
}
```

### 6. Display Voice Recommendations with Criteria

**Show AI reasoning for voice selection:**

```javascript
const voiceRecs = payload.voiceRecommendations;

if (voiceRecs) {
  // Display voice criteria (the "why")
  const criteria = voiceRecs.voice_criteria;
  
  if (criteria) {
    document.getElementById('voiceCriteriaSection').innerHTML = `
      <h4>🎙️ Ideal Voice Profile</h4>
      <div class="voice-criteria">
        <p><strong>Gender:</strong> ${criteria.gender}</p>
        <p><strong>Age Range:</strong> ${criteria.age_range}</p>
        <p><strong>Accent:</strong> ${criteria.accent}</p>
        <p><strong>Tone:</strong> ${criteria.tone}</p>
        <p><strong>Voice Quality:</strong> ${criteria.voice_quality}</p>
        <p><strong>Pacing:</strong> ${criteria.pacing}</p>
        <p><strong>Emotional Range:</strong> ${criteria.emotional_range}</p>
      </div>
      <div class="voice-reasoning">
        <h5>Why these characteristics?</h5>
        <p>${criteria.reasoning}</p>
      </div>
    `;
  }
  
  // Display recommended voices
  const voices = voiceRecs.recommended_voices || [];
  const voicesContainer = document.getElementById('voicesContainer');
  voicesContainer.innerHTML = '<h4>Top Voice Matches:</h4>';
  
  voices.forEach((voice, index) => {
    const voiceCard = document.createElement('div');
    voiceCard.className = 'voice-card';
    voiceCard.innerHTML = `
      <div class="voice-header">
        <h5>${index + 1}. ${voice.name}</h5>
        <span class="match-score">${voice.match_score}% Match</span>
      </div>
      <p class="voice-description">${voice.description}</p>
      <div class="voice-labels">
        ${voice.labels?.accent ? `<span class="label">📍 ${voice.labels.accent}</span>` : ''}
        ${voice.labels?.age ? `<span class="label">👤 ${voice.labels.age}</span>` : ''}
        ${voice.labels?.gender ? `<span class="label">⚧ ${voice.labels.gender}</span>` : ''}
      </div>
      <p class="match-reason"><strong>Why this voice:</strong> ${voice.match_reason}</p>
      <div class="voice-actions">
        <audio controls src="${voice.preview_url}"></audio>
        <button class="select-voice-btn" data-voice-id="${voice.voice_id}">
          Select This Voice
        </button>
      </div>
    `;
    voicesContainer.appendChild(voiceCard);
  });
}
```

### 7. Complete Form Submission Example

**Full working example:**

```javascript
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const submitButton = document.getElementById('submitButton');
  const formData = new FormData(e.target);
  
  try {
    submitButton.disabled = true;
    submitButton.textContent = 'Processing...';
    
    // Submit to backend
    const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Upload failed');
    }
    
    // Extract payload
    const payload = result.payload;
    
    // 1. Display book info
    document.getElementById('bookTitle').textContent = payload.bookInfo?.title || 'Unknown';
    document.getElementById('bookAuthor').textContent = payload.bookInfo?.author || 'Unknown';
    document.getElementById('bookGenre').textContent = payload.bookInfo?.genre || 'Unknown';
    
    // 2. Display metrics
    const wordCount = payload.metrics?.word_count || 0;
    const pageCount = payload.metrics?.page_count || 0;
    const chapterCount = payload.structure?.total_chapters || 0;
    
    document.getElementById('wordCount').textContent = wordCount.toLocaleString();
    document.getElementById('pageCount').textContent = pageCount;
    document.getElementById('chapterCount').textContent = chapterCount;
    
    // 3. Display themes
    const themes = payload.bookInfo?.themes || [];
    const themesContainer = document.getElementById('themes');
    themesContainer.innerHTML = themes.map(theme => 
      `<span class="theme-tag">${theme}</span>`
    ).join('');
    
    // 4. Display narrative info
    document.getElementById('narrativeTone').textContent = 
      payload.bookInfo?.narrative_tone || 'N/A';
    document.getElementById('targetAudience').textContent = 
      payload.bookInfo?.target_audience || 'N/A';
    
    // 5. Display chapters
    const chapters = payload.structure?.chapters || [];
    const chapterList = document.getElementById('chapterList');
    chapterList.innerHTML = chapters.map(ch => 
      `<div class="chapter-item">
        <strong>${ch.title}</strong>
        <p>${ch.start_text}</p>
      </div>`
    ).join('');
    
    // 6. Display voice recommendations
    const voiceRecs = payload.voiceRecommendations;
    if (voiceRecs) {
      // Voice criteria
      const criteria = voiceRecs.voice_criteria;
      document.getElementById('voiceReasoning').textContent = criteria?.reasoning || '';
      
      // Recommended voices
      const voices = voiceRecs.recommended_voices || [];
      const voicesContainer = document.getElementById('voices');
      voicesContainer.innerHTML = voices.map((voice, i) => 
        `<div class="voice-card">
          <h5>${i + 1}. ${voice.name} (${voice.match_score}% match)</h5>
          <p>${voice.description}</p>
          <p><em>${voice.match_reason}</em></p>
          <audio controls src="${voice.preview_url}"></audio>
        </div>`
      ).join('');
    }
    
    // Show success
    alert('Analysis complete!');
    
  } catch (error) {
    console.error('Error:', error);
    alert('Error: ' + error.message);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = 'Submit';
  }
});
```

---

## 🎨 SUGGESTED UI LAYOUT

### Book Overview Section
```html
<div class="book-overview">
  <h2 id="bookTitle">Loading...</h2>
  <p id="bookAuthor">by Unknown</p>
  <span id="bookGenre" class="genre-badge">Genre</span>
  <span id="ageRating" class="age-badge">Age Rating</span>
  
  <div class="metrics">
    <div class="metric">
      <span class="metric-value" id="wordCount">N/A</span>
      <span class="metric-label">Words</span>
    </div>
    <div class="metric">
      <span class="metric-value" id="pageCount">N/A</span>
      <span class="metric-label">Pages</span>
    </div>
    <div class="metric">
      <span class="metric-value" id="chapterCount">N/A</span>
      <span class="metric-label">Chapters</span>
    </div>
  </div>
</div>
```

### Themes Section
```html
<div class="themes-section">
  <h3>Main Themes</h3>
  <div id="themes" class="theme-tags">
    <!-- Theme tags will be inserted here -->
  </div>
</div>
```

### Narrative Analysis Section
```html
<div class="narrative-section">
  <h3>Narrative Analysis</h3>
  <p><strong>Tone:</strong> <span id="narrativeTone">N/A</span></p>
  <p><strong>Target Audience:</strong> <span id="targetAudience">N/A</span></p>
  <div id="contentWarnings" class="warnings"></div>
</div>
```

### Chapters Section
```html
<div class="chapters-section">
  <h3>Chapter Structure</h3>
  <div id="chapterList" class="chapter-list">
    <!-- Chapters will be inserted here -->
  </div>
</div>
```

### Voice Recommendations Section
```html
<div class="voice-section">
  <h3>🎙️ AI-Recommended Narrator Voices</h3>
  
  <div id="voiceCriteriaSection" class="voice-criteria-section">
    <!-- Voice criteria will be inserted here -->
  </div>
  
  <div id="voicesContainer" class="voices-container">
    <!-- Voice cards will be inserted here -->
  </div>
</div>
```

---

## 🎨 SUGGESTED CSS

```css
/* Theme tags */
.theme-tag {
  display: inline-block;
  background: #e0e7ff;
  color: #4338ca;
  padding: 6px 14px;
  border-radius: 20px;
  margin: 4px;
  font-size: 14px;
  font-weight: 500;
}

/* Voice card */
.voice-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.voice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.match-score {
  background: #10b981;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.voice-labels {
  display: flex;
  gap: 8px;
  margin: 12px 0;
}

.voice-labels .label {
  background: #f3f4f6;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
}

.match-reason {
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
  padding: 12px;
  margin: 12px 0;
  font-size: 14px;
  font-style: italic;
}

.voice-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 16px;
}

.select-voice-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.select-voice-btn:hover {
  background: #4338ca;
}

/* Chapter items */
.chapter-item {
  background: #f9fafb;
  border-left: 3px solid #6366f1;
  padding: 12px;
  margin: 8px 0;
  border-radius: 4px;
}

.chapter-preview {
  color: #6b7280;
  font-size: 13px;
  margin-top: 4px;
}

/* Voice criteria */
.voice-criteria {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.voice-reasoning {
  background: #fef3c7;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.voice-reasoning h5 {
  margin-top: 0;
  color: #92400e;
}
```

---

## ✅ TESTING CHECKLIST

After implementing these changes:

- [ ] Word count shows actual number (e.g., "107,414")
- [ ] Book title shows AI-detected title (not "Book_projectId")
- [ ] Author name displays correctly
- [ ] Genre shows specific genre
- [ ] Themes display as styled tags
- [ ] Narrative tone shows
- [ ] Target audience displays
- [ ] Age rating shows
- [ ] Content warnings display (if any)
- [ ] Chapter count shows correct number
- [ ] Chapter list displays with titles and previews
- [ ] Voice criteria section shows
- [ ] Voice reasoning displays
- [ ] 5 recommended voices show
- [ ] Each voice shows match score
- [ ] Voice match reasons display
- [ ] Audio preview players work
- [ ] Voice labels show (accent, age, gender)

---

## 🆘 TROUBLESHOOTING

### Issue: Word count still shows "N/A"
**Solution:** Make sure you're accessing `response.payload.metrics.word_count`, not `response.metrics.word_count`

### Issue: Chapters show as 0
**Solution:** Backend now detects chapters. Access via `response.payload.structure.total_chapters`

### Issue: Voice recommendations don't show
**Solution:** Check `response.payload.voiceRecommendations.recommended_voices` array

### Issue: Title shows as "Book_projectId"
**Solution:** Use `response.payload.bookInfo.title` for AI-detected title

---

## 📞 NEED HELP?

If you encounter issues:
1. Check browser console for errors
2. Check Network tab to see actual API response
3. Verify you're accessing `response.payload.*` not `response.*`
4. Test with: `console.log(JSON.stringify(response, null, 2))`

The backend is returning all this data correctly - it's just a matter of parsing and displaying it! 🚀
