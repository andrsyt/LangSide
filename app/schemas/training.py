from pydantic import BaseModel, Field, field_validator

SEMANTIC_ANCHOR_CUSTOM_MIN_LENGTH = 10
SEMANTIC_ANCHOR_CUSTOM_MAX_LENGTH = 500


class WordIntroInfo(BaseModel):
    """Data for the word-intro screen before mini-training."""

    translation: str
    examples: list[str]
    synonyms: list[str]
    explanation: str | None


class SynonymsRecallResult(BaseModel):
    correct: bool
    correct_synonyms: list[str]
    incorrect_synonyms: list[str]


class AssociationV2Input(BaseModel):
    image: str
    action: str
    emotion: str


class AssociationsSubmitRequest(BaseModel):
    """Legacy freeform associations and/or structured association 2.0."""

    associations: list[str] | None = None
    association_v2: AssociationV2Input | None = None


class SemanticAnchorExercise(BaseModel):
    exercise_id: int
    explanation: str
    example: str
    anchor_variants: list[str]
    anchor_prompts_personalized: bool = False
    context_variants: list[str]


class SemanticAnchorSubmitRequest(BaseModel):
    exercise_id: int
    chosen_anchor_id: int = Field(
        ...,
        ge=0,
        le=2,
        description="Anchor template: 0 situation, 1 emotion, 2 image",
    )
    custom_anchor_text: str = Field(
        ...,
        min_length=SEMANTIC_ANCHOR_CUSTOM_MIN_LENGTH,
        max_length=SEMANTIC_ANCHOR_CUSTOM_MAX_LENGTH,
        description="User-written link to the word (required)",
    )
    context_choice_index: int = Field(
        ...,
        ge=0,
        le=2,
        description="Index of the chosen sentence from context_variants",
    )

    @field_validator("custom_anchor_text", mode="before")
    @classmethod
    def strip_custom_anchor(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class SemanticAnchorSubmitResult(BaseModel):
    is_context_correct: bool
    accepted_anchor_text: str
    correct_context_sentence: str
    selected_context_sentence: str | None = None
    feedback_message: str


class DoubleRecallExercise(BaseModel):
    exercise_id: int
    word_id: int
    word_text: str
    translation_prompt: str
    min_synonyms: int = 1
    example_sentences: list[str]
    total_steps: int = 5
    current_step: int = 0


class DoubleRecallTranslationSubmitRequest(BaseModel):
    exercise_id: int
    translation_answer: str


class DoubleRecallTranslationResult(BaseModel):
    correct: bool
    current_step: int


class DoubleRecallGlossSubmitRequest(BaseModel):
    """Step 1: recall translation/meaning from the English word."""

    exercise_id: int
    gloss_answer: str


class DoubleRecallGlossResult(BaseModel):
    correct: bool
    current_step: int


class DoubleRecallSynonymsSubmitRequest(BaseModel):
    exercise_id: int
    synonyms_answer: list[str]
    skip: bool = False


class DoubleRecallSynonymsResult(BaseModel):
    correct: bool
    current_step: int


class DoubleRecallExampleSubmitRequest(BaseModel):
    exercise_id: int
    selected_example_index: int


class DoubleRecallExampleResult(BaseModel):
    correct: bool
    current_step: int


class DoubleRecallOwnSentenceSubmitRequest(BaseModel):
    exercise_id: int
    sentence: str = Field(..., min_length=12, max_length=500)


class DoubleRecallFinishResult(BaseModel):
    """Double-recall summary: overall_correct means all steps passed (synonym skip ignored)."""

    translation_correct: bool
    gloss_recall_correct: bool
    synonyms_correct: bool
    synonyms_skipped: bool = False
    example_correct: bool
    own_sentence_correct: bool
    overall_correct: bool
    correct_word: str
    matched_synonyms: list[str]
    missed_synonyms: list[str]


class AntiConfusionExercise(BaseModel):
    exercise_id: int
    word_id: int
    question: str
    context_sentence: str
    options: list[str]
    confusion_pair_focus: bool = False
    confusion_partner_word: str | None = None


class AntiConfusionSubmitRequest(BaseModel):
    exercise_id: int
    selected_index: int


class AntiConfusionSubmitResult(BaseModel):
    is_correct: bool
    selected_option: str | None = None
    correct_option: str | None
    explanation: str | None
    pair_hint: str | None = None
    suggest_retry: bool = False


class AssociationRecallExercise(BaseModel):
    word_id: int
    cue_text: str


class AssociationRecallSubmitRequest(BaseModel):
    answer: str


class AssociationRecallResult(BaseModel):
    correct: bool
    correct_word: str
    cue_text: str



