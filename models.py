from pydantic import BaseModel, Field

# ==========================================
# 1. MULTIPLE CHOICE MODELS
# ==========================================


class MultipleChoiceQuestion(BaseModel):
    # This matches `questionText` in Prisma
    questionText: str = Field(description="The multiple choice question text.")

    # This matches the `options` JSON array in Prisma
    options: list[str] = Field(
        description="Exactly 4 possible answers. Do not include letter prefixes like 'A)' or 'B)'."
    )

    # This matches `correctAnswer` in Prisma
    correctAnswer: str = Field(
        description="The exact text of the correct option.")

    # This matches `explanation` in Prisma
    explanation: str = Field(
        description="A brief explanation of why this answer is correct.")


class MultipleChoiceQuiz(BaseModel):
    title: str = Field(description="A catchy title for the generated quiz.")
    description: str = Field(
        description="A short description of the quiz content.")
    difficulty: str = Field(
        description="The difficulty level of the quiz: easy, normal, or hard")
    questions: list[MultipleChoiceQuestion]


# ==========================================
# 2. TRUE/FALSE MODELS
# ==========================================
class TrueFalseQuestion(BaseModel):
    questionText: str = Field(
        description="A definitive statement that is either true or false.")

    options: list[str] = Field(
        description="Always exactly two strings: ['True', 'False']."
    )

    correctAnswer: str = Field(
        description="Must be exactly the string 'True' or 'False'.")

    explanation: str = Field(
        description="Explanation of why the statement is true or false.")


class TrueFalseQuiz(BaseModel):
    title: str = Field(description="A catchy title for the generated quiz.")
    description: str = Field(
        description="A short description of the quiz content.")
    difficulty: str = Field(
        description="The difficulty level of the quiz: easy, normal, or hard")
    questions: list[TrueFalseQuestion]


# ==========================================
# 3. IDENTIFICATION MODELS
# ==========================================
class IdentificationQuestion(BaseModel):
    questionText: str = Field(
        description="A question requiring a specific term, name, or concept as the answer."
    )

    options: list[str] = Field(
        description="Always an empty array: []"
    )

    correctAnswer: str = Field(
        description="The precise term or concept being identified.")

    explanation: str = Field(
        description="Brief context or definition of the answer.")


class IdentificationQuiz(BaseModel):
    title: str = Field(description="A catchy title for the generated quiz.")
    description: str = Field(
        description="A short description of the quiz content.")
    difficulty: str = Field(
        description="The difficulty level of the quiz: easy, normal, or hard")
    questions: list[IdentificationQuestion]
