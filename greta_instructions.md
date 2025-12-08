# Instructions for Greta: Processing the "Start Your Audiobook Journey" Form

**Author:** Manus AI
**Date:** December 7, 2025
**Version:** 1.0

## 1.0 Introduction

This document provides comprehensive instructions for processing the "Start Your Audiobook Journey" form on audiobooksmith.com. The process involves integrating with a new webhook server at audiobooksmith.app to handle full audiobook creation from user-uploaded book files. This guide details the data flow, API interactions, and response handling required to implement this feature.

## 2.0 Form Processing Overview

The "Start Your Audiobook Journey" form enables users to upload a book file (e.g., PDF, ePub) and have it converted into a full audiobook. This process is asynchronous and leverages a webhook to manage the long-running task of book processing and audio generation.

### 2.1 Key Differences from Free Sample Form

| Feature | Free Sample Form | Start Your Audiobook Journey Form |
|---|---|---|
| **Purpose** | Try service with text snippet | Create full audiobook from file |
| **Input** | Text (100-500 characters) | Book file (PDF, ePub, MOBI, TXT) |
| **File Size** | N/A | Up to 100MB |
| **Processing** | ElevenLabs API (text-to-speech) | Book text extraction, chapter detection, audio generation |
| **Output** | Short audio sample (3-8 seconds) | Complete audiobook with chapters |
| **Account** | Auto-created if needed | Required (triggers signup if not authenticated) |

## 3.0 Data Flow and Webhook Integration

The process is divided into four main steps: frontend submission, webhook processing, backend processing, and status updates.

### 3.1 Step 1: Frontend Form Submission

The frontend form on audiobooksmith.com will collect the following data:

- **Email:** User's email address (required, validated)
- **Book Title:** Title of the book (optional)
- **Plan:** Selected pricing tier (e.g., 'free', 'starter')
- **Book File:** The uploaded book file

**Submission Details:**
- **Method:** HTTP POST with `multipart/form-data`
- **Endpoint:** `https://audiobooksmith.app/webhook/audiobook-process`

### 3.2 Step 2: Webhook Server Processing

The webhook server at audiobooksmith.app will receive the form data and perform the following actions:

1. Validate all incoming fields.
2. Save the uploaded book file to disk.
3. Extract metadata from the book (title, author, etc.).
4. Call the audiobook processor script to begin processing.
5. Return an immediate JSON response to the frontend.

**Success Response:**
```json
{
  "success": true,
  "projectId": "proj_abc123",
  "audiobookId": "audio_xyz789",
  "status": "processing",
  "message": "Your audiobook is being created! Check your email for updates.",
  "estimatedTime": "15-30 minutes",
  "metadata": {
    "bookTitle": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "pages": 180,
    "wordCount": 47094,
    "chapters": 9
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid file format",
  "message": "Please upload a PDF, ePub, MOBI, or TXT file",
  "code": "INVALID_FILE_FORMAT"
}
```

### 3.3 Step 3: Backend Processing

Upon receiving a successful response from the webhook, the backend on audiobooksmith.com will:

1. **Create User Account:** If the user is not authenticated, create a new account with the provided email and send a welcome email.
2. **Create Project Record:** Create a new project in the database with the details from the webhook response.
3. **Create Credit Record:** Deduct credits based on the user's plan.
4. **Create Processing Log:** Log the start of the audiobook processing.
5. **Send Confirmation Email:** Send an email to the user confirming that their audiobook is being created.
6. **Queue Status Polling:** Start a background job to poll the webhook server for status updates.

### 3.4 Step 4: Status Updates

The backend will poll the webhook server for status updates on the audiobook creation.

- **Polling Endpoint:** `GET /webhook/audiobook-status/{audiobookId}`
- **Polling Interval:** Every 30 seconds

**Status Response:**
```json
{
  "audiobookId": "audio_xyz789",
  "status": "processing" | "completed" | "failed",
  "progress": 45,
  "currentStep": "Generating chapter 3 of 9",
  "audioUrl": "https://s3.amazonaws.com/...",
  "error": null
}
```

## 4.0 Implementation Details

### 4.1 Account Creation

The account creation process should be similar to the existing Free Sample form. If the user's email does not exist in the database, a new user account should be created with a temporary password, and a welcome email should be sent.

### 4.2 Email Notifications

Three types of emails should be sent:

1. **Immediate Confirmation:** Sent upon successful form submission.
2. **Processing Updates (Optional):** Sent at key milestones (e.g., 25%, 50%, 75% complete).
3. **Completion:** Sent when the audiobook is ready, with a download link.

### 4.3 Error Handling

The frontend should handle errors from the webhook server gracefully, displaying user-friendly messages based on the error code received.

## 5.0 Frontend Example

```typescript
// client/src/components/AudiobookJourneyForm.tsx

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Frontend validation
  if (!formData.email || !formData.bookFile) {
    toast.error("Please fill in all required fields");
    return;
  }
  
  setIsSubmitting(true);
  
  try {
    const uploadData = new FormData();
    uploadData.append("email", formData.email);
    uploadData.append("bookTitle", formData.bookTitle);
    uploadData.append("plan", formData.plan);
    uploadData.append("bookFile", formData.bookFile);
    
    const response = await fetch("https://audiobooksmith.app/webhook/audiobook-process", {
      method: "POST",
      body: uploadData
    });
    
    const result = await response.json();
    
    if (result.success) {
      await processWebhookResponse(result);
      toast.success(result.message);
    } else {
      toast.error(result.message || "An error occurred");
    }
  } catch (error) {
    toast.error("Failed to submit form. Please try again.");
  } finally {
    setIsSubmitting(false);
  }
};
```

## 6.0 Backend tRPC Procedure

```typescript
// server/routers/projects.ts

createFromWebhook: publicProcedure
  .input(/* Zod schema for webhook response */)
  .mutation(async ({ input, ctx }) => {
    // 1. Check/create user
    // 2. Create project
    // 3. Create credit record
    // 4. Create processing log
    // 5. Send confirmation email
    // 6. Start status polling
  });
```

## 7.0 Conclusion

By following these instructions, Greta can successfully integrate the "Start Your Audiobook Journey" form with the new webhook server, providing a seamless experience for users to create full audiobooks from their book files. The asynchronous nature of the webhook ensures that the user interface remains responsive while the long-running task of audiobook creation is handled in the background.

---

**References:**

[1] AudiobookSmith-Complete-User-Journey-Map.md.pdf
