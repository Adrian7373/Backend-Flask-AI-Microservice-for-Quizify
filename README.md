# Backend Flask AI Microservice for Quizify

A Flask-based AI microservice used by a Next.js application to:

- Generate quizzes from text, files, or images
- Grade short-answer/essay responses
- Generate teacher insights from class quiz performance

This service uses **Google Gemini** (`gemini-3.1-flash-lite`) and returns structured JSON designed for easy consumption in a frontend app.

---

## Features

- **Quiz Generation** with support for:
  - Multiple Choice
  - True/False
  - Identification
  - Essay prompts
- **Flexible Input Sources**:
  - Raw text
  - Uploaded document file
  - Uploaded image
- **AI Essay/Short-Answer Grading** with score, pass/fail, and feedback
- **Class Performance Insights** for teachers
- **CORS enabled** for frontend integration

---

## Tech Stack

- Python 3
- Flask
- Flask-CORS
- Google GenAI SDK
- Pydantic (schema-based structured output)
- python-dotenv

---

## Project Structure

```txt
.
├── app.py           # Flask app + API routes
├── models.py        # Pydantic response schemas
├── requirements.txt # Python dependencies
└── .gitignore
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key
```

---

## Local Setup

### 1) Clone repository

```bash
git clone https://github.com/Adrian7373/Backend-Flask-AI-Microservice-for-Quizify.git
cd Backend-Flask-AI-Microservice-for-Quizify
```

### 2) Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows (PowerShell):

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the service

```bash
python app.py
```

By default, the service runs on:

```txt
http://localhost:5000
```

---

## API Endpoints

### `POST /api/generate`

Generates a quiz based on text/file/image input.

**Content-Type:** `multipart/form-data`

#### Form fields

- `inputType`: `Text` | `File` | `Image`
- `quizType`: `MULTIPLE_CHOICE` | `TRUE_FALSE` | `IDENTIFICATION` | `ESSAY`
- `questionCount`: number as string (example: `5`)
- `difficulty`: `easy` | `normal` | `hard`
- `language`: output language (example: `English`, `Filipino`)
- For `Text`: `text` field is required
- For `File`: `file` upload is required
- For `Image`: `image` upload is required

#### Example (Text input)

```bash
curl -X POST http://localhost:5000/api/generate \
  -F "inputType=Text" \
  -F "quizType=MULTIPLE_CHOICE" \
  -F "questionCount=5" \
  -F "difficulty=normal" \
  -F "language=English" \
  -F "text=Photosynthesis is the process by which green plants..."
```

---

### `POST /api/grade-answer`

Grades a short-answer/essay response using rubric-based AI scoring.

**Content-Type:** `application/json`

#### Request body

```json
{
  "questionText": "Explain why photosynthesis is important.",
  "rubric": "Mentions energy conversion, glucose production, and oxygen release.",
  "studentAnswer": "It turns sunlight into food and gives off oxygen.",
  "language": "English"
}
```

#### Response shape

```json
{
  "score": 8,
  "is_correct": true,
  "feedback": "Great effort! You identified the key purpose of photosynthesis..."
}
```

---

### `POST /api/insights`

Generates teacher-facing insight text from commonly missed questions.

**Content-Type:** `application/json`

#### Request body

```json
{
  "quizTitle": "Biology Quiz 1",
  "struggleQuestions": [
    {
      "questionText": "What is chlorophyll?",
      "correctAnswer": "A green pigment used in photosynthesis",
      "accuracy": 42
    }
  ]
}
```

#### Response shape

```json
{
  "success": true,
  "insight": "Students appear to confuse pigment function with plant structure..."
}
```

---

## Next.js Integration Notes

- Set your frontend API base URL to this Flask service (for example, `http://localhost:5000` in local development).
- Send:
  - `FormData` for `/api/generate`
  - JSON payloads for `/api/grade-answer` and `/api/insights`
- Since CORS is enabled in Flask, browser requests from your Next.js app are supported.

---

## Deployment

`gunicorn` is included in dependencies for production hosting.

Example:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

Use environment variables from your hosting provider for `GEMINI_API_KEY` and disable Flask debug mode in production.

---

## Error Handling

The API returns:

- `400` for missing/invalid inputs
- `500` for internal generation or grading failures

Check server logs for detailed error traces.

---

