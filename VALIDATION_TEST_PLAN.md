# Test Plan: validateForm Function - AudiobookSmith

## Overview
This test plan verifies the file validation and error handling logic in the new `validateForm` function for OnboardingPage.jsx.

---

## Test Environment Setup

**Prerequisites:**
- OnboardingPage.jsx updated with new validateForm function
- Development server running (npm run dev)
- Access to test files of various types and sizes

**Test Data Required:**
- Valid PDF file (< 100MB)
- Valid EPUB file (< 100MB)
- Valid DOCX file (< 100MB)
- Valid TXT file (< 100MB)
- Invalid file type (e.g., .exe, .zip, .mp3)
- Large file (> 100MB)
- Small file (< 1MB) for quick testing

---

## Test Cases

### Category 1: Required Field Validation

#### TC-001: Empty Name Field
**Objective:** Verify name field is required  
**Steps:**
1. Navigate to the onboarding form
2. Leave "Name" field empty
3. Fill in email, book title, and upload file
4. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message displayed: "Name is required"
- Name field is highlighted/focused
- Other fields remain valid

**Status:** [ ] Pass [ ] Fail

---

#### TC-002: Whitespace-Only Name
**Objective:** Verify name field rejects whitespace-only input  
**Steps:**
1. Enter only spaces in "Name" field (e.g., "   ")
2. Fill in other required fields
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Name is required"
- Name field is highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-003: Empty Email Field
**Objective:** Verify email field is required  
**Steps:**
1. Fill in name and book title
2. Leave "Email" field empty
3. Upload file
4. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Valid email is required"
- Email field is highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-004: Invalid Email Format
**Objective:** Verify email format validation  
**Test Data:**
- "notanemail" (no @ symbol)
- "user@" (no domain)
- "@domain.com" (no username)
- "user @domain.com" (space in email)
- "user@domain" (no TLD)

**Steps:**
1. Enter invalid email format
2. Fill in other required fields
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Valid email is required"
- Email field is highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-005: Valid Email Format
**Objective:** Verify valid email passes validation  
**Test Data:**
- "user@example.com"
- "test.user@domain.co.uk"
- "user+tag@example.com"

**Steps:**
1. Enter valid email
2. Fill in other required fields
3. Click submit

**Expected Result:**
- ✅ Email validation passes
- No error for email field

**Status:** [ ] Pass [ ] Fail

---

#### TC-006: Empty Book Title
**Objective:** Verify book title is required  
**Steps:**
1. Fill in name and email
2. Leave "Book Title" empty
3. Upload file
4. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Book title is required"
- Book title field is highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-007: Whitespace-Only Book Title
**Objective:** Verify book title rejects whitespace  
**Steps:**
1. Enter only spaces in "Book Title" (e.g., "   ")
2. Fill in other required fields
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Book title is required"

**Status:** [ ] Pass [ ] Fail

---

#### TC-008: No File Selected
**Objective:** Verify file upload is required  
**Steps:**
1. Fill in name, email, and book title
2. Do NOT upload any file
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Book file is required"
- File upload field is highlighted

**Status:** [ ] Pass [ ] Fail

---

### Category 2: File Type Validation

#### TC-009: Valid PDF File
**Objective:** Verify PDF files are accepted  
**Test File:** sample.pdf (any size < 100MB)  
**Steps:**
1. Fill in all required text fields
2. Upload PDF file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type
- Form proceeds to webhook submission

**Status:** [ ] Pass [ ] Fail

---

#### TC-010: Valid EPUB File
**Objective:** Verify EPUB files are accepted  
**Test File:** sample.epub  
**Steps:**
1. Fill in all required fields
2. Upload EPUB file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-011: Valid DOCX File
**Objective:** Verify DOCX files are accepted  
**Test File:** sample.docx  
**Steps:**
1. Fill in all required fields
2. Upload DOCX file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-012: Valid TXT File
**Objective:** Verify TXT files are accepted  
**Test File:** sample.txt  
**Steps:**
1. Fill in all required fields
2. Upload TXT file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-013: Valid MOBI File
**Objective:** Verify MOBI files are accepted  
**Test File:** sample.mobi  
**Steps:**
1. Fill in all required fields
2. Upload MOBI file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-014: Valid RTF File
**Objective:** Verify RTF files are accepted  
**Test File:** sample.rtf  
**Steps:**
1. Fill in all required fields
2. Upload RTF file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-015: Valid ODT File
**Objective:** Verify ODT files are accepted  
**Test File:** sample.odt  
**Steps:**
1. Fill in all required fields
2. Upload ODT file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-016: Valid DOC File (Legacy Word)
**Objective:** Verify DOC files are accepted  
**Test File:** sample.doc  
**Steps:**
1. Fill in all required fields
2. Upload DOC file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No error for file type

**Status:** [ ] Pass [ ] Fail

---

#### TC-017: Invalid File Type - Executable
**Objective:** Verify executable files are rejected  
**Test File:** file.exe  
**Steps:**
1. Fill in all required fields
2. Upload .exe file
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Invalid file type. Allowed: PDF, EPUB, DOCX, TXT, MOBI, RTF, ODT"
- File upload field is highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-018: Invalid File Type - Archive
**Objective:** Verify archive files are rejected  
**Test Files:** file.zip, file.rar, file.7z  
**Steps:**
1. Fill in all required fields
2. Upload archive file
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Invalid file type. Allowed: PDF, EPUB, DOCX, TXT, MOBI, RTF, ODT"

**Status:** [ ] Pass [ ] Fail

---

#### TC-019: Invalid File Type - Media
**Objective:** Verify media files are rejected  
**Test Files:** file.mp3, file.mp4, file.jpg, file.png  
**Steps:**
1. Fill in all required fields
2. Upload media file
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "Invalid file type. Allowed: PDF, EPUB, DOCX, TXT, MOBI, RTF, ODT"

**Status:** [ ] Pass [ ] Fail

---

#### TC-020: Case Insensitive Extension
**Objective:** Verify file extensions are case-insensitive  
**Test Files:** 
- sample.PDF (uppercase)
- sample.Pdf (mixed case)
- sample.DOCX (uppercase)

**Steps:**
1. Fill in all required fields
2. Upload file with uppercase/mixed case extension
3. Click submit

**Expected Result:**
- ✅ File validation passes
- Extension check is case-insensitive

**Status:** [ ] Pass [ ] Fail

---

### Category 3: File Size Validation

#### TC-021: File Under Limit (Small)
**Objective:** Verify small files are accepted  
**Test File:** 1MB PDF file  
**Steps:**
1. Fill in all required fields
2. Upload 1MB file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No size error

**Status:** [ ] Pass [ ] Fail

---

#### TC-022: File Under Limit (Medium)
**Objective:** Verify medium files are accepted  
**Test File:** 50MB PDF file  
**Steps:**
1. Fill in all required fields
2. Upload 50MB file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No size error

**Status:** [ ] Pass [ ] Fail

---

#### TC-023: File At Limit (99.9MB)
**Objective:** Verify files just under limit are accepted  
**Test File:** 99.9MB file  
**Steps:**
1. Fill in all required fields
2. Upload 99.9MB file
3. Click submit

**Expected Result:**
- ✅ File validation passes
- No size error

**Status:** [ ] Pass [ ] Fail

---

#### TC-024: File Over Limit (101MB)
**Objective:** Verify files over 100MB are rejected  
**Test File:** 101MB file  
**Steps:**
1. Fill in all required fields
2. Upload 101MB file
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message: "File size must be less than 100MB (current: 101.0MB)"
- File upload field is highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-025: File Over Limit (200MB)
**Objective:** Verify very large files are rejected  
**Test File:** 200MB file  
**Steps:**
1. Fill in all required fields
2. Upload 200MB file
3. Click submit

**Expected Result:**
- ❌ Form does not submit
- Error message shows actual file size: "File size must be less than 100MB (current: 200.0MB)"

**Status:** [ ] Pass [ ] Fail

---

### Category 4: Multiple Field Validation

#### TC-026: All Fields Empty
**Objective:** Verify all validation errors show when all fields are empty  
**Steps:**
1. Leave all fields empty
2. Click submit

**Expected Result:**
- ❌ Form does not submit
- Multiple error messages displayed:
  - "Name is required"
  - "Valid email is required"
  - "Book title is required"
  - "Book file is required"
- First error field is focused

**Status:** [ ] Pass [ ] Fail

---

#### TC-027: Multiple Invalid Fields
**Objective:** Verify multiple validation errors  
**Steps:**
1. Enter invalid email (no @)
2. Leave book title empty
3. Upload invalid file type (.zip)
4. Click submit

**Expected Result:**
- ❌ Form does not submit
- Multiple error messages:
  - "Valid email is required"
  - "Book title is required"
  - "Invalid file type..."
- First error field is focused

**Status:** [ ] Pass [ ] Fail

---

#### TC-028: All Fields Valid
**Objective:** Verify form submits when all validations pass  
**Steps:**
1. Enter valid name: "John Doe"
2. Enter valid email: "john@example.com"
3. Enter valid book title: "My Test Book"
4. Upload valid PDF file (< 100MB)
5. Click submit

**Expected Result:**
- ✅ All validations pass
- No error messages
- Form submits to webhook
- Loading state is shown
- Redirects to results page

**Status:** [ ] Pass [ ] Fail

---

### Category 5: Error Clearing Behavior

#### TC-029: Error Clears on Field Edit
**Objective:** Verify error message clears when user corrects the field  
**Steps:**
1. Submit form with empty name
2. Observe error: "Name is required"
3. Type in name field
4. Observe error message

**Expected Result:**
- ✅ Error message disappears when user starts typing
- Field is no longer highlighted

**Status:** [ ] Pass [ ] Fail

---

#### TC-030: File Error Clears on New Upload
**Objective:** Verify file error clears when user uploads new file  
**Steps:**
1. Upload invalid file type (.zip)
2. Submit form
3. Observe error message
4. Upload valid file (.pdf)
5. Observe error message

**Expected Result:**
- ✅ Error message clears when valid file is selected
- File field is no longer highlighted

**Status:** [ ] Pass [ ] Fail

---

### Category 6: Edge Cases

#### TC-031: File Name with Multiple Extensions
**Objective:** Verify validation uses last extension  
**Test File:** "my.book.pdf.txt"  
**Steps:**
1. Upload file with multiple extensions
2. Submit form

**Expected Result:**
- ✅ Validation checks last extension (.txt)
- File is accepted

**Status:** [ ] Pass [ ] Fail

---

#### TC-032: File Name Without Extension
**Objective:** Verify files without extensions are rejected  
**Test File:** "mybook" (no extension)  
**Steps:**
1. Upload file without extension
2. Submit form

**Expected Result:**
- ❌ Form does not submit
- Error: "Invalid file type..."

**Status:** [ ] Pass [ ] Fail

---

#### TC-033: Very Long File Name
**Objective:** Verify long file names are handled  
**Test File:** "a_very_long_file_name_that_goes_on_and_on_and_on_for_a_very_long_time.pdf"  
**Steps:**
1. Upload file with very long name
2. Submit form

**Expected Result:**
- ✅ File is accepted
- Validation works correctly

**Status:** [ ] Pass [ ] Fail

---

#### TC-034: Special Characters in File Name
**Objective:** Verify special characters in file names  
**Test Files:**
- "my book (draft).pdf"
- "book-final_v2.pdf"
- "book's_title.pdf"

**Steps:**
1. Upload file with special characters
2. Submit form

**Expected Result:**
- ✅ File is accepted
- Validation works correctly

**Status:** [ ] Pass [ ] Fail

---

#### TC-035: Unicode Characters in File Name
**Objective:** Verify unicode/international characters  
**Test Files:**
- "книга.pdf" (Cyrillic)
- "本.pdf" (Chinese)
- "café.pdf" (accented)

**Steps:**
1. Upload file with unicode characters
2. Submit form

**Expected Result:**
- ✅ File is accepted
- Validation works correctly

**Status:** [ ] Pass [ ] Fail

---

## Test Execution Summary

**Total Test Cases:** 35

**Breakdown by Category:**
- Required Field Validation: 8 tests
- File Type Validation: 12 tests
- File Size Validation: 5 tests
- Multiple Field Validation: 3 tests
- Error Clearing Behavior: 2 tests
- Edge Cases: 5 tests

**Priority Levels:**
- **Critical (Must Pass):** TC-001 to TC-028
- **Important:** TC-029 to TC-030
- **Nice to Have:** TC-031 to TC-035

---

## Testing Checklist

### Pre-Testing
- [ ] Development environment is running
- [ ] OnboardingPage.jsx updated with new validateForm
- [ ] Test files prepared (various types and sizes)
- [ ] Browser console open for debugging

### During Testing
- [ ] Record pass/fail for each test case
- [ ] Screenshot any unexpected behavior
- [ ] Note browser console errors
- [ ] Test in multiple browsers (Chrome, Firefox, Safari)
- [ ] Test on mobile devices (responsive)

### Post-Testing
- [ ] All critical tests passed
- [ ] Document any failures
- [ ] Create bug reports for failures
- [ ] Retest after fixes
- [ ] Sign off on validation logic

---

## Bug Report Template

If a test fails, use this template:

```
Bug ID: VAL-XXX
Test Case: TC-XXX
Severity: Critical / High / Medium / Low

Description:
[What went wrong]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Result:
[What should happen]

Actual Result:
[What actually happened]

Browser: [Chrome 120 / Firefox 121 / etc.]
Screenshot: [Attach if applicable]
Console Errors: [Copy any errors]
```

---

## Success Criteria

The validation function is considered **ready for production** when:

✅ All 28 critical test cases pass (TC-001 to TC-028)  
✅ Error messages are clear and user-friendly  
✅ Form prevents invalid submissions  
✅ Valid submissions proceed to webhook  
✅ No console errors during validation  
✅ Works in Chrome, Firefox, and Safari  
✅ Works on mobile devices  

---

## Quick Test Script

For rapid testing, use this sequence:

```
1. Empty form → Submit (should show 4 errors)
2. Fill name → Error clears
3. Fill email → Error clears
4. Fill book title → Error clears
5. Upload .zip file → Submit (should show file type error)
6. Upload 150MB file → Submit (should show size error)
7. Upload valid PDF → Submit (should succeed)
```

**Expected time:** 5 minutes  
**Result:** All validations working correctly

---

## Automated Testing (Optional)

For automated testing, consider:

```javascript
describe('validateForm', () => {
  it('should reject empty name', () => {
    const formData = { name: '', email: 'test@test.com', bookTitle: 'Test', manuscriptFile: mockFile };
    const errors = validateForm(formData);
    expect(errors.name).toBe('Name is required');
  });
  
  it('should reject invalid email', () => {
    const formData = { name: 'Test', email: 'invalid', bookTitle: 'Test', manuscriptFile: mockFile };
    const errors = validateForm(formData);
    expect(errors.email).toBe('Valid email is required');
  });
  
  it('should reject invalid file type', () => {
    const mockFile = new File([''], 'test.zip', { type: 'application/zip' });
    const formData = { name: 'Test', email: 'test@test.com', bookTitle: 'Test', manuscriptFile: mockFile };
    const errors = validateForm(formData);
    expect(errors.manuscriptFile).toContain('Invalid file type');
  });
  
  it('should reject file over 100MB', () => {
    const largeFile = new File(['x'.repeat(101 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' });
    const formData = { name: 'Test', email: 'test@test.com', bookTitle: 'Test', manuscriptFile: largeFile };
    const errors = validateForm(formData);
    expect(errors.manuscriptFile).toContain('100MB');
  });
  
  it('should accept valid form', () => {
    const validFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const formData = { name: 'Test', email: 'test@test.com', bookTitle: 'Test', manuscriptFile: validFile };
    const errors = validateForm(formData);
    expect(Object.keys(errors).length).toBe(0);
  });
});
```

---

**Test Plan Version:** 1.0  
**Created:** December 8, 2025  
**Last Updated:** December 8, 2025  
**Owner:** AudiobookSmith QA Team
