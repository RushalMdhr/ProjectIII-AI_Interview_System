from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams, SingleTurnParams
from deepeval.models import OllamaModel
from deepeval.metrics.g_eval import Rubric
import json
# import pandas as pd
# import ollama
# from .request_ollama import ollama_client
import ast

ollama_model = OllamaModel(
    model="llama3.2",  # use a model tag installed in Ollama
    base_url="http://host.docker.internal:11434",
    temperature=0,
)

SCORING_RUBRIC = [
    Rubric(
        score_range=(0, 2),
        expected_outcome=(
            "Very poor answer. Required evidence is absent, "
            "irrelevant, or fundamentally incorrect."
        )
    ),
    Rubric(
        score_range=(3, 4),
        expected_outcome=(
            "Poor answer. Shows limited understanding, "
            "with major missing information or vague explanations."
        )
    ),
    Rubric(
        score_range=(5, 6),
        expected_outcome=(
            "Average answer. Demonstrates partial understanding "
            "but lacks sufficient detail, evidence, or completeness."
        )
    ),
    Rubric(
        score_range=(7, 8),
        expected_outcome=(
            "Good answer. Demonstrates clear understanding, "
            "relevant evidence, and mostly complete explanations."
        )
    ),
    Rubric(
        score_range=(9, 10),
        expected_outcome=(
            "Excellent answer. Demonstrates strong understanding, "
            "specific evidence, completeness, and clear reasoning."
        )
    )
]
EVALUATION_DIMENSIONS_SOFT = {

    "introduction": {
        "name": "Introduction Completeness",
        "use_ideal": False,
        "steps": [
            "Evaluate the candidate's introduction as if you are a friendly interviewer.",
            "See if they mentioned their educational background, or their current role / relevant experience.",
            "See if they shared at least one relevant skill, interest, or achievement.",
            "It is perfectly fine if they are a student without work experience — academic projects count.",
            "Give a higher score if they provide specific, relevant details rather than generic statements.",
            "It is okay if the introduction is personal — there is no single correct way to introduce oneself.",
        ]
    },

    "experience": {
        "name": "Experience and Ownership",
        "use_ideal": True,
        "steps": [
            "Understand the candidate's actual experience related to the question.",
            "Check if they explained their personal contribution (what 'I' did) versus the team's.",
            "Look for specific tools, technologies, or responsibilities they mentioned.",
            "See if they showed practical involvement rather than just theoretical knowledge.",
            "Reward specific examples, even if they come from academic or personal projects (not only professional work).",
            "Use the expected answer as a rough guide for depth, but they do not need to mention the exact same tools or projects.",
        ]
    },

    "behavioral": {
        "name": "Behavioral STAR Evaluation",
        "use_ideal": False,
        "steps": [
            "Check if the candidate described a specific past Situation or Task.",
            "See if they explained the Action they personally took.",
            "Look for the Result or outcome of their actions.",
            "Give a high score if they showed reflection or learning from the experience.",
            "Reward specific, believable stories over generic claims.",
            "It is okay if the story is not perfectly formatted as STAR, as long as the core details are there.",
            "If they only gave a generic opinion instead of a real past example, give a lower score (because this is a behavioral question), but do not give a zero.",
            "Do not compare against an expected answer — personal stories are unique.",
        ]
    },

    "situational": {
        "name": "Situational Reasoning",
        "use_ideal": True,
        "steps": [
            "Check if the candidate understood the hypothetical problem and its constraints.",
            "See if they considered relevant stakeholders, risks, or trade-offs.",
            "Evaluate if their proposed actions are practical and actionable.",
            "Look for clear reasoning and the 'why' behind their decisions.",
            "Reward realistic, well-justified decisions.",
            "It is okay if their approach differs from the expected answer, as long as it is valid.",
            "If they only told a past story without addressing the hypothetical scenario, give a lower score (because this is a situational question), but do not give a zero.",
            "Use the expected answer as a rough guide for the quality of reasoning, but accept alternative approaches.",
        ]
    },

    "technical": {
        "name": "Technical Understanding",
        "use_ideal": True,
        "steps": [
            "Evaluate the factual and conceptual correctness of the answer.",
            "Check if they demonstrated understanding rather than just dropping technical buzzwords.",
            "See if they included relevant technical details or practical solutions.",
            "Reward understanding of trade-offs, limitations, or alternatives.",
            "If they confidently state a wrong fact, give a lower score — accuracy matters.",
            "Accept technically valid alternative approaches; they do not need to exactly match the expected answer.",
            "Use the expected answer as a reference for key concepts, but do not require the exact same wording.",
        ]
    }
}

EVALUATION_DIMENSIONS = {

    "introduction": {
        "name": "Introduction Completeness",
        "use_ideal": False,   # ← each candidate's intro is personal
        "steps": [
            "Evaluate whether the candidate introduced themselves appropriately for an interview context.",
            "Check whether relevant educational background was mentioned (degree, field, institution).",
            "Check whether current employment or relevant experience was mentioned, if applicable.",
            "Check whether at least one relevant skill, interest, or achievement was provided.",
            "Check whether the introduction stayed focused and did not drift into unrelated personal detail.",
            "Do not penalize candidates for not having work experience — students are valid candidates.",
            "Reward relevant and specific information rather than unnecessary personal details.",
            "Do not compare against an expected answer — introductions are personal and there is no single correct version.",
        ]
    },

    "experience": {
        "name": "Experience and Ownership",
        "use_ideal": True,
        "steps": [
            "Identify the candidate's actual experience relevant to the question.",
            "Check whether the candidate clearly explained their personal contribution versus the team's.",
            "Check whether specific tools, technologies, or responsibilities were mentioned when relevant.",
            "Evaluate whether the candidate demonstrated practical involvement rather than merely describing theoretical knowledge.",
            "Check whether outcomes or results of the experience were described.",
            "Reward specific examples and evidence of genuine involvement over generic claims.",
            "Do not assume that a candidate lacks experience simply because they have no professional employment history — personal and academic projects are valid evidence.",
            "Use the expected answer as a reference for the level of depth and specificity expected, but do not require the candidate to mention the same tools or projects.",
        ]
    },

    "behavioral": {
        "name": "Behavioral STAR Evaluation",
        "use_ideal": False,   # personal stories differ
        "steps": [
            "Check whether the candidate described a specific past Situation or Task (not a hypothetical one).",
            "Check whether the candidate explained the Action they personally took.",
            "Distinguish individual contributions from actions performed by the entire team.",
            "Check whether the candidate explained the Result or outcome.",
            "Check whether the candidate demonstrated reflection or learning when relevant.",
            "Reward specific and believable examples.",
            "Do not require a rigid STAR format if the candidate communicates all important information naturally.",
            "Boundary rule: if the candidate answers with a generic opinion or a purely hypothetical scenario instead of a real past experience, penalize the answer because behavioral questions require a past example.",
            "Do not compare against an expected answer — personal stories are unique and there is no single correct response.",
        ]
    },

    "situational": {
        "name": "Situational Reasoning",
        "use_ideal": True,
        "steps": [
            "Check whether the candidate understood the problem and identified important constraints.",
            "Check whether relevant stakeholders or risks were considered.",
            "Evaluate whether the proposed actions are specific and practical.",
            "Check whether the candidate explained their reasoning and the 'why' behind their decision.",
            "Evaluate whether trade-offs or alternative approaches were considered.",
            "Reward realistic, actionable and well-justified decisions.",
            "Do not penalize a valid alternative approach simply because it differs from an expected approach.",
            "Boundary rule: if the candidate only tells a past story without addressing the hypothetical scenario, penalize the answer because situational questions require a hypothetical decision.",
            "Use the expected answer as a reference for the quality of reasoning expected, but accept any well-justified alternative approach.",
        ]
    },

    "technical": {
        "name": "Technical Understanding",
        "use_ideal": True,
        "steps": [
            "Evaluate the factual and conceptual correctness of the answer.",
            "Check whether the candidate demonstrated understanding rather than merely mentioning technical terminology.",
            "Evaluate whether the explanation includes relevant technical details.",
            "Check whether the proposed implementation or solution is practical and complete.",
            "Evaluate whether relevant trade-offs, limitations, or alternatives were understood.",
            "Penalize confidently stated technical misconceptions — a confidently wrong answer is worse than an uncertain correct one.",
            "Do not require an exact match with the expected answer — accept technically valid alternative approaches.",
            "Use the expected answer as a reference for key concepts that should be covered, but do not require the exact same wording or examples.",
        ]
    }
}

def create_evaluator(dimension, model):
    config = EVALUATION_DIMENSIONS_SOFT[dimension]
    return GEval(
        name=config["name"],
        evaluation_steps=config["steps"],
        evaluation_params=[
            SingleTurnParams.INPUT,           # question
            SingleTurnParams.ACTUAL_OUTPUT,   # candidate answer
            SingleTurnParams.EXPECTED_OUTPUT, # ideal answer  ← NEW
        ],
        rubric=SCORING_RUBRIC,
        model=model,
        threshold=None,
        async_mode=False,
        verbose_mode=False,
    )

def evaluate_interview_answer(
    question,
    answer,
    ideal_answer,          # ← NEW parameter
    dimensions,
    model,
    use_ideal_per_dimension=None,
):
    """
    use_ideal_per_dimension: optional dict mapping dimension → bool.
    If None, ideal_answer is used for ALL dimensions.
    """
    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        expected_output=ideal_answer,   # ← passed to GEval
    )

    results = {}
    weighted_score = 0.0
    check=False
    if len(dimensions) > 1:
        check=True
    
    for dimension in dimensions:
        key    = dimension["label"]      # ← was dimension["key"]
        weight = float(dimension["score"])  # ← was dimension["weight"]

        evaluator = create_evaluator(dimension=key, model=model)
        evaluator.measure(test_case)

        score = evaluator.score * 10
        print("score : ",score)

        if score < 1:
            return {'overall_score': score, 'dimension_scores': {'suspicious_break': {'score': 0.0, 'weight': 1.0, 'reason': evaluator.reason}}}

        results[key] = {
            "score":  round(score, 2),
            "weight": weight,
            "reason": evaluator.reason,
        }
        weighted_score += score * weight

    return {
        "overall_score":    round(weighted_score, 2),
        "dimension_scores": results,
    }


# In 5th sem we chose a unique project and with unknown dev language where i have to learn whole full stack and MERN in 3 month and time was so short that i thought i might not be able to make it out but guess what we created really great e commerce with multi vendor system

def evaluate_candidate_answer(asked_question,candidate_answer,expected_answer,dimensions):
    print("[ INSIDE G EVAL ] : ",flush=True)
    print("asked_question  : ",asked_question,flush=True)
    print("candidate_answer  : ",candidate_answer,flush=True)
    print("expected_answer  : ",expected_answer,flush=True)
    print("dimensions  : ",dimensions,flush=True)
    if asked_question and candidate_answer and expected_answer and dimensions:
        print("everythings fine ! ")
    else:
        return {'overall_score': 2.0, 'dimension_scores': {'suspicious_break': {'score': 0.0, 'weight': 1.0, 'reason': "review by yourself"}}}
    if isinstance(dimensions, str):
        try:
            dimensions = json.loads(dimensions)
        except json.JSONDecodeError:
            dimensions = ast.literal_eval(dimensions)
    result = evaluate_interview_answer(
        question=asked_question,
        answer=candidate_answer,
        ideal_answer=expected_answer,
        dimensions=dimensions,
        model=ollama_model,
    )
    print("G EVAL RESULT : ",json.dumps(result, indent=2, default=str))
    return result