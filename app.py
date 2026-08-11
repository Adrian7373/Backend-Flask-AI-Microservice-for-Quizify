from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
import os
from models import MultipleChoiceQuiz, TrueFalseQuiz, IdentificationQuiz, GradingResult, EssayQuiz
import logging
import tempfile

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quizify-flask")

app = Flask(__name__)

CORS(app)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SCHEMA_MAP = {
    "MULTIPLE_CHOICE": MultipleChoiceQuiz,
    "TRUE_FALSE": TrueFalseQuiz,
    "IDETIFICATION": IdentificationQuiz,
    "ESSAY": EssayQuiz,
}

MODEL_NAME = "gemini-3.1-flash-lite"


def process_file_upload(file_obj) -> tuple[str, str]:
    """Saves Flask's FileStorage to a temporary local file and uploads it to Gemini API."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_obj.filename}") as temp_file:
        file_obj.save(temp_file.name)
        temp_path = temp_file.name

    logger.info(f"Uploading file '{file_obj.filename}' to Gemini Files API...")
    gemini_file = client.files.upload(file=temp_path)
    return temp_path, gemini_file


@app.route('/api/generate', methods=['POST'])
def generate_quiz():
    temp_path = None
    gemini_file = None

    try:
        # 1. Parse incoming request parameters
        input_type = request.form.get('inputType', 'Text')
        quiz_type = request.form.get('quizType', 'MULTIPLE_CHOICE')
        question_count = request.form.get('questionCount', '5')
        difficulty = request.form.get("difficulty", "normal")
        language = request.form.get("language", "English")

        # 2. Validate Quiz Type & Select Schema
        target_schema = SCHEMA_MAP.get(quiz_type)
        if not target_schema:
            return jsonify({"error": f"Invalid quizType: '{quiz_type}'"}), 400

        # 3. Build System Instructions & Generation Config
        system_instruction = (
            f"You are an assessment engine. Generate a {question_count}-question {quiz_type} quiz "
            f"at a '{difficulty}' difficulty level based strictly on the provided study material. "
            f"""CRITICAL DIFFICULTY RULES for '{difficulty}' mode:
        - 'easy': Target 5th-grade reading level. Use simple vocabulary. Prompts should be very direct.
        - 'normal': Target 9th-grade high school level. Standard vocabulary.
        - 'hard': Target college level. Require deep critical thinking."""
            f"CRITICAL LANGUAGE RULE: You MUST generate the entire quiz (questions, options, correct answers, and explanations) in {language}. If the source material is in a different language, translate the concepts accurately into {language}. "
            f"Ensure all items are factually accurate. "
            f"If 'easy', use basic recall. If 'normal', test comprehension. If 'hard', require deep analysis and critical thinking."
        )

        config = genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=target_schema,
            system_instruction=system_instruction,
            temperature=0.2,  # Low temperature for high factual precision
        )

        # 4. Prepare Contents Payload based on Input Type
        contents = []

        if input_type == 'Text':
            source_text = request.form.get('text', '').strip()
            if not source_text:
                return jsonify({"error": "No text content provided."}), 400
            contents.append(source_text)

        elif input_type in ['File', 'Image']:
            file_key = 'file' if input_type == 'File' else 'image'
            uploaded_file = request.files.get(file_key)

            if not uploaded_file or uploaded_file.filename == '':
                return jsonify({"error": f"No {file_key} uploaded."}), 400

            # Handle file staging and upload
            temp_path, gemini_file = process_file_upload(uploaded_file)
            contents.extend(
                [gemini_file, "Generate a quiz based on this uploaded material."])

        else:
            return jsonify({"error": f"Invalid inputType: '{input_type}'"}), 400

        # 5. Call Gemini AI
        logger.info(
            f"Generating {question_count} '{quiz_type}' questions via {MODEL_NAME}...")
        ai_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )

        # 6. Return Structured JSON directly to Next.js
        return ai_response.text, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred during quiz generation."}), 500

    finally:
        # Cleanup: Delete remote file from Gemini API & delete local temp file
        if gemini_file:
            try:
                client.files.delete(name=gemini_file.name)
                logger.info(f"Deleted remote Gemini file: {gemini_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete remote Gemini file: {e}")

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"Cleaned up local temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file: {e}")


@app.route('/api/insights', methods=['POST'])
def generate_insights():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        quiz_title = data.get('quizTitle', 'Unknown Quiz')
        questions = data.get('struggleQuestions', [])

        if not questions:
            return jsonify({"error": "No struggle questions provided"}), 400

        # Format the raw JSON array into a readable string for the prompt
        formatted_questions = ""
        for i, q in enumerate(questions, 1):
            formatted_questions += (
                f"\nQuestion {i}: {q.get('questionText')}\n"
                f"Correct Answer: {q.get('correctAnswer')}\n"
                f"Class Accuracy: {q.get('accuracy')}%\n"
            )

        prompt = f"""
        You are an expert teacher's assistant. Analyze the following class performance data for a quiz titled "{quiz_title}". 
        The students struggled most with these specific concepts:
        
        {formatted_questions}
        
        Write a brief, 3 sentences summary directly to the teacher. Do not use greetings like "Dear Teacher".
        
        Identify the likely root cause of the misconception based on the questions they missed. Look for the common thread.
        
        Keep the tone encouraging, professional, and directly actionable.
        """

        logger.info(f"Generating class insights for quiz: '{quiz_title}'...")

        # Use your existing Gemini client and model constant
        ai_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        return jsonify({
            "success": True,
            "insight": ai_response.text.strip()
        }), 200

    except Exception as e:
        logger.error(f"Error generating insight: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An internal error occurred while generating insights."
        }), 500


@app.route('/api/grade-answer', methods=['POST'])
def grade_answer():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload provided"}), 400

        question_text = data.get('questionText')
        rubric = data.get('rubric')  # The teacher's correct answer/concept
        student_answer = data.get('studentAnswer')
        # Support the language selector!
        language = data.get('language', 'English')

        if not all([question_text, rubric, student_answer]):
            return jsonify({"error": "Missing required fields."}), 400

        prompt = f"""
    You are an encouraging, compassionate teacher evaluating a student's essay response.
    
    Question: {question_text}
    Teacher's Rubric: {rubric}
    Student's Answer: {student_answer}
    
    GRADING INSTRUCTIONS:
    1. Be highly considerate. Do not demand exact vocabulary or perfect grammar. If the student demonstrates a clear conceptual understanding of the rubric's core ideas, consider it correct.
    2. Award partial credit generously. Look for what the student got right, rather than punishing them for what they missed.
    3. Determine if the answer passes the threshold for 'is_correct' (a score of 6 or higher means True).
    4. Score out of 10:
       - 9 to 10: Grasps the core concept perfectly, even if using their own words.
       - 6 to 8: Understands part of the concept, but missing a key detail.
       - 1 to 5: Tried, but fundamentally misunderstood the topic.
       - 0: Completely blank or entirely off-topic.
    5. Provide warm, constructive feedback in {language}. Always validate their effort first before gently correcting misconceptions.
    """

        logger.info(
            f"Grading short answer for question: '{question_text[:30]}...'")

        # Force Gemini to output the exact Pydantic schema
        config = genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GradingResult,
            temperature=0.2,
        )

        ai_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config
        )

        # Return the structured JSON directly to Next.js
        return ai_response.text, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        logger.error(f"Error grading answer: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An internal error occurred during AI grading."
        }), 500


# This stays at the very bottom of the file
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
