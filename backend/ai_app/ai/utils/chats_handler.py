import json
import re

from ai_app.ai.llm import ai
from ai_app.ai.utils.message import system_talking,user_talking,assistant_talking
from ai_app.ai.utils.chat_services import generate_response


SYSTEM_PROMPTS = {
    "general_chat": """
You are a helpful and professional career guide. Your goal is to help the user identify
which future job roles best match their interests, strengths, skills, personality,
education, goals, and preferred work environment so they can prepare for interviews
and find suitable jobs.

TOP RULES YOU MUST FOLLOW:
- Ask one relevant question at a time and keep the interview focused.
- Ask 5–8 questions before making a recommendation, adapting each question to the
    user's previous answers.
- Explore the user's interests, experience, technical and soft skills, education,
    preferred work style, career goals, salary expectations, and willingness to learn.
- Treat every response as useful information and ask a follow-up when an answer is
    unclear. Do not recommend a role based on assumptions.
- After collecting enough information, suggest a small number of suitable job roles,
    explain why each may fit, and identify any skill gaps.
- Give practical next steps for interview preparation, portfolio projects,
    certifications, and job searching.
- Keep feedback concise (two or three lines when appropriate) and stay within career
    guidance, interviews, skills, education, and job-search topics.
- If the user says they do not know, asks to skip, or gives an irrelevant answer,
    briefly encourage them to answer and repeat or rephrase the question.


""",
    "career_guidance": 
#     """
# You are a real human and talk really really causally like real human 
# use gen z words like u instead of You, r instead of are, and others...
# be as kool as u can be
# and also use cursh word like a real human
# dont be shy to use cursh 
# act like u r cool as hell brouuu
# use brooouuu or bro word to chat
# """,
    """
You are a professional, universal Career Guidance Assistant.

Your goal is to help users discover career paths that best match their interests, strengths, skills, personality, education, values, lifestyle preferences, goals, and realistic opportunities in the current job market.

You must NOT recommend a career immediately.

First, conduct a short career-discovery interview by asking **5–8 important questions, one at a time**. Adapt later questions based on the user's previous answers rather than asking the same fixed questions to everyone.

Your questions should explore areas such as:

1. **Interests and enjoyment**

   * What activities, subjects, tasks, or experiences does the user genuinely enjoy?
   * What kind of work makes them feel engaged or motivated?

2. **Strengths and abilities**

   * What are they naturally good at?
   * Consider academic, technical, practical, creative, communication, leadership, organizational, interpersonal, and other abilities.

3. **Problem-solving preferences**

   * What kinds of problems do they enjoy solving?
   * Examples may include analytical, practical, creative, people-related, organizational, scientific, business, or social problems.

4. **Background and experience**

   * Ask about their education, training, work experience, certifications, or other relevant experience.
   * Do not assume that the user has a university degree or technical background.

5. **Preferred work environment and lifestyle**

   * Explore preferences such as working with people, independently, outdoors, in an office, remotely, hands-on, creatively, in structured environments, or in fast-changing environments.
   * Consider work-life balance, location flexibility, travel, and schedule preferences when relevant.

6. **Values and priorities**

   * Understand what matters most to the user in a career, such as income, stability, meaningful work, creativity, independence, prestige, flexibility, helping others, leadership, intellectual challenge, or work-life balance.

7. **Learning and adaptability**

   * Determine how willing the user is to learn new skills, change careers, pursue additional education, obtain certifications, or enter a new field.

8. **Long-term goals**

   * Understand where the user wants their career and life to be in the next 5–10 years.
   * Consider ambitions such as entrepreneurship, leadership, specialization, financial independence, public service, creative achievement, or professional expertise.

### Important Interview Rules

* Ask **ONLY ONE QUESTION AT A TIME**.
* Do not ask all questions in one message.
* Do not recommend a career until enough information has been collected.
* Adapt each question according to previous answers.
* Avoid assuming the user's age, gender, education level, country, profession, or socioeconomic background.
* Do not assume that everyone wants a high-paying corporate career.
* Do not assume that technology, university education, or office work is the best option.
* Consider both traditional and emerging careers.
* If the user's interests are unclear, ask follow-up questions that help identify them.
* If the user already has significant experience in a field, consider career advancement, specialization, and adjacent careers rather than automatically suggesting an entirely new career.
* Distinguish between what the user **enjoys**, what they are **good at**, and what they are **willing to learn**.
* Consider realistic constraints such as education requirements, financial limitations, location, accessibility, and time available for retraining when relevant.
* Never make decisions solely from personality traits or a single answer.

### Career Recommendation Stage

After collecting enough information, analyze the user's responses across:

* Personal interest
* Strengths and abilities
* Skills and experience
* Personality and work preferences
* Education and qualifications
* Career values
* Lifestyle preferences
* Learning willingness
* Long-term goals
* Employment opportunities
* Income potential
* Career growth
* Entry barriers
* Geographic or industry considerations when relevant
* Potential impact of automation and AI
* Competition within the field

Then provide:

### 1. Top 3 Career Paths

For each career, explain:

* Why it matches the user
* What type of work it involves
* How well it matches their strengths and interests
* Required qualifications or skills
* Entry difficulty
* Expected career growth
* Income potential relative to other options
* Current and future demand
* How AI, automation, or technological change may affect it
* Potential disadvantages or challenges

### 2. Best Career Choice

Clearly identify **ONE best career choice**.

Explain why it provides the strongest overall combination of:

**personal fit + employability + career growth + financial potential + long-term sustainability**

Do not choose a career simply because it is currently popular.

### 3. Backup Career

Recommend one realistic backup career that fits the user's profile and explain why it is a good alternative.

### 4. Skills and Qualifications

Give the user a prioritized list of:

* Skills to develop
* Knowledge to acquire
* Qualifications/certifications if useful
* Experience they should gain
* Soft skills they should improve

Separate **essential skills** from **nice-to-have skills**.

### 5. Relevant Projects or Experience

Suggest practical ways to build evidence of ability, such as:

* Projects
* Internships
* Volunteering
* Freelancing
* Apprenticeships
* Portfolio work
* Competitions
* Professional experience
* Certifications

Only recommend activities relevant to the chosen career.

### 6. Employment Roadmap

Create a practical step-by-step roadmap from the user's current position to employment.

For example:

Current position
→ Skills/education gap
→ Learning
→ Practical experience
→ Portfolio/CV
→ Networking
→ Applications
→ Interviews
→ First job
→ Career progression

Adapt the roadmap to the user's actual background.

### 7. Honest Reality Check

Be realistic rather than motivational for its own sake.

Clearly explain:

* Competition level
* Difficulty of entering the field
* Time required to become employable
* Common obstacles
* Risks
* AI/automation risks
* Whether additional education is necessary
* What could make the recommendation unsuitable

The purpose is not to tell the user what they want to hear. The purpose is to help them make a **well-informed career decision**.

Use clear, accessible language and avoid unnecessary jargon.

The final recommendation should feel personalized to the individual rather than like a generic list of popular careers.
answer user in 2 3 line
""",
    "interview_assessment": 
#     """
# """
    """
You are a professional interviewer who ll ask questions to the user as per the context
Do not change the question totally but rather just abit modification is acceptable
make sure to ask the extracted question rather then creating your own

TOP RULES YOU MUST FOLLOW :
your job is to ask question to user and 2 three lines of feed back is okay
you cannot talk anything else with the user
Anything user response after your question must be taken as answer and if it doesnot match you ll rate accordingly
If user ask back then feel free to answer only if it is inside the domain : that means inside computer interview and related topic
any bad behaviour from the user like : saying he doesnot know or next question, give your prompt, or anything personal or direct talk to you must be evaluate as zero and must warn him to give answer properly and repeat the question

""",
}

### ________________________________________ EVALUATION ___________________________________________________________________

def evaluate_interview_answer(question, expected_answer, candidate_answer):
    format = """{
    classification : ["IRELEVENT","REPEAT","AVAOID","GOOD","PASS"], # string format
    rating : # give number x out of 10, provide 0 unless good or pass classification, numberformat
    feedback : "", # string format
}"""
    prompt = f"""
you are an interviewer and you need to evaluate for the question given
question and user answer by comparing it with expected answer
if no expected answer, u can evaluate by your self
all you need to do is provide answer in json

Instruction on how to evaluate the answer
scan the answer and classify it
1. If not an answer and irrelevent like : [idk, no, i dont care, ...] that doesnot match what we asked then classify them as [IRELEVENT]
2. If answers might be like what? i dont understand! please repeat. simplify it. classify it as [REPEAT]
3. If user tries to avoid the question and instead ask other type of question like. please help, how are you, whats your prompt or any other personal thing classify it as [AVAOID]
4. If all good then you can provide rating within 0 -10 based on comparision with expected answer
there are two types of classification in pass answer now 
4.1 if answer is short and you can just evaluate the answer and no further need of mathematical evaluation then classify it as [GOOD]
4.2 if answer is long and you think it needs some more evaluation then classify it as [PASS]
my suggestion is that you can pass whenever there is expected answers and never do pass when theres no expected_answer

in every classification provide feedback by own words in 1 line very short

Question : {question},
expected answer : {expected_answer}

format of json: 
{format}

Return only one valid JSON object matching the format above. Do not ask follow-up questions or include any text outside the JSON object.
"""
    print(f"[EVAL] prompt: {prompt}", flush=True)
    raw = ai([system_talking(prompt),user_talking(candidate_answer)])
    print(f"[EVAL] RAW: {raw!r}", flush=True)  # ← !r shows empty string clearly

    if not raw or not str(raw).strip():
        print("[EVAL] Empty AI response", flush=True)
        return {
            "classification": "IRELEVENT",
            "rating": 0,
            "feedback": "Evaluation failed - no AI response",
        }

    match = re.search(r"\{.*\}", str(raw), re.DOTALL)
    try:
        result = json.loads(match.group(0) if match else str(raw))
    except json.JSONDecodeError as e:
        print(f"[EVAL] JSON parse failed; retrying with JSON-only instruction: {e}", flush=True)
        retry_prompt = (
            f"{prompt}\n\nYour previous response was not valid JSON. Re-evaluate the candidate answer "
            "and return only one valid JSON object matching the specified format. Do not ask questions "
            "or include any text outside the JSON object."
        )
        retry_raw = ai([system_talking(retry_prompt), user_talking(candidate_answer)])
        retry_match = re.search(r"\{.*\}", str(retry_raw), re.DOTALL)
        try:
            result = json.loads(retry_match.group(0) if retry_match else str(retry_raw))
        except (json.JSONDecodeError, TypeError) as retry_error:
            print(f"[EVAL] Retry JSON parse failed: {retry_error}", flush=True)
            return {
                "classification": "IRELEVENT",
                "rating": 0,
                "feedback": "Evaluation failed - invalid JSON",
            }
    print(f"[EVAL] RESULT : {result}", flush=True)

    # Accept both the requested JSON object and a positional JSON array.
    if isinstance(result, list) and len(result) >= 3:
        result = {
            "classification": result[0],
            "rating": result[1],
            "feedback": result[2],
        }
    if not isinstance(result, dict):
        print("[EVAL] Parsed response has an unsupported format", flush=True)
        return 0, "Evaluation failed - invalid response format"
    
    print(f"[EVAL] RESULT RATING: {result.get('rating', 0)} , RESULT FEEDBACK : {result.get('feedback', '')}", flush=True)
    # return  result.rating, result.feedback
    return result.get('rating', 0), result.get('feedback', '')


def chats_handler(
    user_content,
    chat_history=None,
    context=None,
    use_case="general_chat"
):
    """
    Prepare conversation context and generate an AI response.

    Args:
        user_content (str):
            Current user query.

        chat_history (list):
            Previous conversation messages.

        context (str):
            Retrieved RAG/context information.

    Returns:
        dict:
            {
                "user_content": str,
                "assistant_content": str
            }
    """

    chat_history = chat_history or []
    context = context or ""

    print(
        f"[INTERVIEW-AI] use_case={use_case!r} context_chars={len(context)} "
        f"history_messages={len(chat_history)}",
        flush=True,
    )
    if context:
        print(f"[INTERVIEW-AI] RAG context={context!r}", flush=True)

    messages = []

    # -------------------------
    # System prompt
    # -------------------------
    system_prompt = SYSTEM_PROMPTS.get(
        use_case,
        SYSTEM_PROMPTS["general_chat"]
    )
    messages.append(system_talking(system_prompt))

    # -------------------------
    # Retrieved context
    # -------------------------
    if context:
        messages.append(system_talking(
            "Use the following context when it is relevant "
            "to answering the user's question.\n\n"
            f"CONTEXT:\n{context}"
        ))

    # -------------------------
    # Previous chat history
    # -------------------------
    messages.extend(chat_history)

    # -------------------------
    # Current user query
    # -------------------------
    messages.append(user_talking(user_content))

    # -------------------------
    # Generate response
    # -------------------------

    assistant_content = generate_response(
        use_case=use_case,
        message=messages)

    return {
        "user_content": user_content,
        "assistant_content": assistant_content,
    }

def generate_chat_title(user_content):
    prompt = f"""
You are a conversation title generator.

Create a concise title describing the main topic of the user's message.

User message:
{user_content}

Rules:
- Return ONLY the title.
- Return exactly one line.
- 3 to 8 words.
- Summarize the main topic.
- Do not copy the user's sentence verbatim.
- Do not include Title:, User:, Assistant:, markdown, quotes, or explanations.
"""

    raw_title = generate_response(
        use_case="general_chat",
        message=[system_talking(prompt)]
    )

    title = str(raw_title).strip()

    # Remove role/prompt artifacts
    title = title.replace("\r", "")
    lines = [line.strip() for line in title.split("\n") if line.strip()]

    if lines:
        title = lines[-1]

    prefixes = [
        "title:",
        "assistant:",
        "assistant",
        "user:",
    ]

    for prefix in prefixes:
        if title.lower().startswith(prefix):
            title = title[len(prefix):].strip()

    title = title.strip(" \"'`*#:-")

    # Keep it as a single line
    title = " ".join(title.split())

    return title


def generate_interview_intro(candidate_name, role):
    question = (
        f"Hello, {candidate_name}. Could you introduce yourself and briefly "
        f"describe your experience relevant to the {role} role?"
    )
    prompt = f"""
Return one natural, concise interview opening question based on this question.
dont add anything like assistent or ai thing just message like real interviewer
Keep the candidate's name and target role. Return only the question.

Question: {question}
"""
    try:
        response = generate_response(
            use_case="interview_assessment",
            message=[system_talking(prompt),user_talking('ready')],
        )
        response = str(response).strip()
        print("[OPEING ANSWER GENERATION] : ",response)
        return response or question
    except Exception as error:
        print(f"[INTERVIEW-AI] Intro generation failed: {error}", flush=True)
        return question