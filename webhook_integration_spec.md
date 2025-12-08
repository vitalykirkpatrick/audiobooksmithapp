# "Start Your Audiobook Journey" Form - Webhook Integration Specification

## Overview

The "Start Your Audiobook Journey" form on audiobooksmith.com will integrate with the webhook server on audiobooksmith.app to process full audiobook uploads (PDFs, ePubs, etc.) similar to how the Free Sample form currently works.

## Form Type Comparison

### Existing: Free Sample Form
- **Purpose**: Try service without commitment (text-to-speech sample)
- **Input**: Text snippet (100-500 characters)
- **Processing**: ElevenLabs API for audio generation
- **Output**: Short audio sample (3-8 seconds)
- **Account**: Auto-created if needed

### New: Start Your Audiobook Journey Form
- **Purpose**: Full audiobook creation from uploaded book file
- **Input**: Book file (PDF, ePub, MOBI, etc.) up to 100MB
- **Processing**: Book text extraction → Chapter detection → Audio generation
- **Output**: Complete audiobook with chapters
- **Account**: Required (triggers signup if not authenticated)

## Form Data Flow

### Step 1: Frontend Form Submission (audiobooksmith.com)

**Form Fields:**
```typescript
{
  email: string,              // User's email (required, validated)
  bookTitle: string,          // Book title (optional, extracted from file if empty)
  plan: string,               // Selected pricing tier: 'free' | 'starter' | 'professional' | 'business' | 'enterprise'
  bookFile: File              // Uploaded book file (PDF, ePub, MOBI, TXT)
}
```

**Frontend Validation:**
- Email format validation
- File size limit: 100MB
- File type validation: .pdf, .epub, .mobi, .txt
- Required fields check

**Submission Method:**
- HTTP POST with `multipart/form-data`
- Target: `https://audiobooksmith.app/webhook/audiobook-process`

### Step 2: Webhook Server Processing (audiobooksmith.app)

**Endpoint:** `POST /webhook/audiobook-process`

**Request Processing:**
1. Receive multipart form data
2. Validate all fields
3. Save uploaded file to disk
4. Extract book metadata (title, author, etc.)
5. Call audiobook processor script
6. Return response to frontend

**Response Format:**
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

### Step 3: Backend Processing (audiobooksmith.com)

After receiving webhook response, the frontend should:

1. **If user not authenticated:**
   - Auto-create account with provided email
   - Generate temporary password
   - Send welcome email with login link

2. **Create project record:**
   ```typescript
   const project = await db.insert(projects).values({
     userId: user.id,
     title: response.metadata.bookTitle,
     description: `Full audiobook from uploaded file`,
     status: 'processing',
     tier: formData.plan,
     audiobookId: response.audiobookId,
     metadata: response.metadata,
     createdAt: new Date()
   });
   ```

3. **Create credit record:**
   ```typescript
   await db.insert(projectCredits).values({
     userId: user.id,
     projectId: project.id,
     tier: formData.plan,
     creditsTotal: getCreditsByTier(formData.plan),
     creditsUsed: 1,
     creditsRemaining: getCreditsByTier(formData.plan) - 1
   });
   ```

4. **Create processing log:**
   ```typescript
   await db.insert(processingLogs).values({
     projectId: project.id,
     status: 'queued',
     message: 'Audiobook queued for processing',
     createdAt: new Date()
   });
   ```

5. **Send confirmation email:**
   - Subject: "Your Audiobook is Being Created"
   - Template: Include project details, estimated time, login link
   - Timing: Immediate

6. **Queue status polling:**
   - Poll webhook server every 30 seconds for status updates
   - Update project status in database
   - Send completion email when done

### Step 4: Status Updates

The frontend should poll for status updates:

**Polling Endpoint:** `GET /webhook/audiobook-status/{audiobookId}`

**Response:**
```json
{
  "audiobookId": "audio_xyz789",
  "status": "processing" | "completed" | "failed",
  "progress": 45,  // percentage
  "currentStep": "Generating chapter 3 of 9",
  "audioUrl": "https://s3.amazonaws.com/...",  // only when completed
  "error": null  // error message if failed
}
```

## Integration with Existing System

### 1. Account Creation (Similar to Free Sample)

```typescript
// Check if user exists
let user = await db.query.users.findFirst({
  where: eq(users.email, formData.email)
});

if (!user) {
  // Create new user
  const temporaryPassword = generateSecurePassword();
  const [newUser] = await db.insert(users).values({
    email: formData.email,
    name: extractNameFromEmail(formData.email),
    password: await hashPassword(temporaryPassword),
    role: 'customer',
    tier: formData.plan,
    status: 'active',
    emailVerified: false,
    createdAt: new Date()
  }).returning();
  
  user = newUser;
  
  // Send welcome email
  await sendEmail({
    to: user.email,
    subject: 'Welcome to AudiobookSmith - Your Audiobook is Being Created',
    template: 'audiobook-welcome',
    data: {
      name: user.name,
      loginUrl: `${process.env.APP_URL}/login`,
      resetPasswordUrl: `${process.env.APP_URL}/reset-password?email=${encodeURIComponent(user.email)}`,
      estimatedTime: '15-30 minutes'
    }
  });
}
```

### 2. Email Notifications

**Email 1: Immediate Confirmation**
- **Trigger:** Form submission successful
- **Subject:** "Your Audiobook is Being Created"
- **Content:**
  - Welcome message
  - Project details (book title, plan, estimated time)
  - Login link
  - Password reset link (if new user)
  - Status tracking link

**Email 2: Processing Updates** (Optional)
- **Trigger:** Every 25% progress
- **Subject:** "Your Audiobook is 25% Complete"
- **Content:**
  - Progress update
  - Current step
  - Estimated time remaining

**Email 3: Completion**
- **Trigger:** Processing complete
- **Subject:** "Your Audiobook is Ready!"
- **Content:**
  - Download link
  - Dashboard link
  - Project details
  - Next steps

### 3. Credit Management

```typescript
function getCreditsByTier(tier: string): number {
  const credits = {
    'free': 1,
    'starter': 10,
    'professional': 50,
    'business': 200,
    'enterprise': 1000
  };
  return credits[tier] || 1;
}
```

## Frontend Implementation Example

```typescript
// client/src/components/AudiobookJourneyForm.tsx

import { useState } from 'react';

interface FormData {
  email: string;
  bookTitle: string;
  plan: string;
  bookFile: File | null;
}

export const AudiobookJourneyForm = () => {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    bookTitle: '',
    plan: 'starter',
    bookFile: null
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Frontend validation
    if (!formData.email || !formData.bookFile) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    if (formData.bookFile.size > 100 * 1024 * 1024) {
      toast.error('File size must be less than 100MB');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Create FormData for multipart upload
      const uploadData = new FormData();
      uploadData.append('email', formData.email);
      uploadData.append('bookTitle', formData.bookTitle);
      uploadData.append('plan', formData.plan);
      uploadData.append('bookFile', formData.bookFile);
      
      // Send to webhook server
      const response = await fetch('https://audiobooksmith.app/webhook/audiobook-process', {
        method: 'POST',
        body: uploadData,
        // Track upload progress
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Process successful response
        await processWebhookResponse(result);
        
        toast.success(result.message);
        
        // Reset form
        setFormData({
          email: '',
          bookTitle: '',
          plan: 'starter',
          bookFile: null
        });
      } else {
        toast.error(result.message || 'An error occurred');
      }
    } catch (error) {
      console.error('Submission error:', error);
      toast.error('Failed to submit form. Please try again.');
    } finally {
      setIsSubmitting(false);
      setProgress(0);
    }
  };
  
  const processWebhookResponse = async (webhookData: any) => {
    // Call backend to create project and user account
    const result = await trpc.projects.createFromWebhook.mutate({
      email: formData.email,
      plan: formData.plan,
      webhookResponse: webhookData
    });
    
    return result;
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
};
```

## Backend tRPC Procedure

```typescript
// server/routers/projects.ts

createFromWebhook: publicProcedure
  .input(z.object({
    email: z.string().email(),
    plan: z.enum(['free', 'starter', 'professional', 'business', 'enterprise']),
    webhookResponse: z.object({
      projectId: z.string(),
      audiobookId: z.string(),
      status: z.string(),
      metadata: z.object({
        bookTitle: z.string(),
        author: z.string().optional(),
        pages: z.number().optional(),
        wordCount: z.number().optional(),
        chapters: z.number().optional()
      })
    })
  }))
  .mutation(async ({ input, ctx }) => {
    // 1. Check/create user
    let user = await ctx.db.query.users.findFirst({
      where: eq(users.email, input.email)
    });
    
    if (!user) {
      // Create new user (similar to free sample flow)
      user = await createUserAccount(input.email, input.plan);
    }
    
    // 2. Create project
    const [project] = await ctx.db.insert(projects).values({
      userId: user.id,
      title: input.webhookResponse.metadata.bookTitle,
      description: 'Full audiobook from uploaded file',
      status: 'processing',
      tier: input.plan,
      audiobookId: input.webhookResponse.audiobookId,
      metadata: input.webhookResponse.metadata,
      createdAt: new Date()
    }).returning();
    
    // 3. Create credit record
    await ctx.db.insert(projectCredits).values({
      userId: user.id,
      projectId: project.id,
      tier: input.plan,
      creditsTotal: getCreditsByTier(input.plan),
      creditsUsed: 1,
      creditsRemaining: getCreditsByTier(input.plan) - 1,
      createdAt: new Date()
    });
    
    // 4. Create processing log
    await ctx.db.insert(processingLogs).values({
      projectId: project.id,
      status: 'queued',
      message: 'Audiobook queued for processing',
      createdAt: new Date()
    });
    
    // 5. Send confirmation email
    await sendEmail({
      to: user.email,
      subject: 'Your Audiobook is Being Created',
      template: 'audiobook-welcome',
      data: {
        name: user.name,
        bookTitle: input.webhookResponse.metadata.bookTitle,
        estimatedTime: '15-30 minutes',
        loginUrl: `${process.env.APP_URL}/login`,
        dashboardUrl: `${process.env.APP_URL}/dashboard`,
        projectUrl: `${process.env.APP_URL}/projects/${project.id}`
      }
    });
    
    // 6. Start status polling (background job)
    await queueStatusPolling(project.id, input.webhookResponse.audiobookId);
    
    return {
      projectId: project.id,
      status: 'success',
      message: 'Your audiobook is being created! Check your email for updates.'
    };
  })
```

## Error Handling

### Webhook Server Errors

```typescript
// Common error codes from webhook server
const ERROR_CODES = {
  INVALID_FILE_FORMAT: 'Please upload a PDF, ePub, MOBI, or TXT file',
  FILE_TOO_LARGE: 'File size must be less than 100MB',
  PROCESSING_ERROR: 'An error occurred while processing your book',
  INVALID_EMAIL: 'Please provide a valid email address',
  MISSING_FIELDS: 'Please fill in all required fields'
};
```

### Frontend Error Handling

```typescript
try {
  const response = await fetch(webhookUrl, { method: 'POST', body: formData });
  const result = await response.json();
  
  if (!result.success) {
    // Show user-friendly error message
    toast.error(ERROR_CODES[result.code] || result.message);
    return;
  }
  
  // Process success
} catch (error) {
  // Network or server error
  toast.error('Unable to connect to server. Please try again later.');
  console.error('Webhook error:', error);
}
```

## Status Polling Implementation

```typescript
// Background job to poll webhook server for status updates
export const pollAudiobookStatus = async (projectId: string, audiobookId: string) => {
  const maxAttempts = 120; // 1 hour with 30-second intervals
  let attempts = 0;
  
  const poll = async () => {
    try {
      const response = await fetch(
        `https://audiobooksmith.app/webhook/audiobook-status/${audiobookId}`
      );
      const status = await response.json();
      
      // Update project status
      await db.update(projects)
        .set({
          status: status.status,
          progress: status.progress,
          updatedAt: new Date()
        })
        .where(eq(projects.id, projectId));
      
      // Log progress
      await db.insert(processingLogs).values({
        projectId,
        status: status.status,
        message: status.currentStep,
        createdAt: new Date()
      });
      
      if (status.status === 'completed') {
        // Send completion email
        await sendCompletionEmail(projectId, status.audioUrl);
        return; // Stop polling
      }
      
      if (status.status === 'failed') {
        // Send error email
        await sendErrorEmail(projectId, status.error);
        return; // Stop polling
      }
      
      // Continue polling if still processing
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(poll, 30000); // Poll every 30 seconds
      }
    } catch (error) {
      console.error('Status polling error:', error);
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(poll, 30000);
      }
    }
  };
  
  // Start polling
  poll();
};
```
