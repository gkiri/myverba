# prompts.py

class UPSCPrompts:
    SUMMARY = """
    As an AI assistant for UPSC exam preparation, provide a concise and informative summary of the following text:
    {input_text}
    
    Focus on key points that are most relevant for UPSC exam preparation. Ensure the summary is clear, 
    accurate, and highlights the main ideas a UPSC aspirant should remember.
    """

    BULLET_POINTS = """
    Create a comprehensive bullet-point list of the most important facts and concepts related to the following UPSC topic:
    {input_text}
    
    Each bullet point should be:
    - Concise yet informative
    - Covering essential information for UPSC candidates
    - Relevant to the exam syllabus
    - Easy to memorize and recall during the exam
    """

    VISUALIZE = """
    You are an AI assistant helping students prepare for the UPSC exam by creating visual diagrams using Mermaid code. The diagrams should be simple, clear, and easy to render in a ReactJS frontend without parsing errors. Follow these guidelines:
    1. Use plain text for node labels, avoiding special characters and complex syntax.
    2. End each statement with a semicolon.
    3. Avoid using edge labels; instead, make node labels descriptive to convey relationships.
    4. Ensure the Mermaid code is mistake-proof and syntax-proof, suitable for direct rendering.
    5. Depending on the context, choose the most appropriate diagram type (flowchart, sequence diagram, tree, etc.) to represent the information clearly.

    Generate a Mermaid diagram for the following topic:
    Topic: {topic}

    Provide only the Mermaid code.
    """

    DIFFICULTY_ASSESSMENT = """
    Assess the difficulty level of the following UPSC exam question:
    {question_text}
    
    Provide:
    1. An estimated difficulty rating (Easy, Medium, Hard)
    2. Explanation for the rating
    3. Key knowledge areas tested by this question
    4. Tips for approaching similar questions in the exam
    """

    CURRENT_AFFAIRS_ANALYSIS = """
    Analyze the following current affairs topic in the context of UPSC exam preparation:
    {topic}
    
    Include in your analysis:
    1. Brief overview of the topic
    2. Its significance in the current geopolitical or socio-economic landscape
    3. Potential questions that could be asked in the UPSC exam related to this topic
    4. Key points that aspirants should remember
    5. Any related historical events or policies that provide important context
    """

    COMPARATIVE_STUDY = """
    Provide a comparative analysis of the following UPSC topics:
    {topic1}
    {topic2}
    
    Your analysis should include:
    1. Key similarities between the topics
    2. Major differences and distinctions
    3. How these topics are interrelated in the context of UPSC syllabus
    4. Important points to remember for each topic
    5. Potential comparative questions that might appear in the UPSC exam
    """

def get_prompt(prompt_type: str, **kwargs) -> str:
    """
    Retrieve and format a specific prompt.
    
    Args:
    prompt_type (str): The type of prompt to retrieve (e.g., 'SUMMARY', 'BULLET_POINTS')
    **kwargs: Key-value pairs for formatting the prompt
    
    Returns:
    str: The formatted prompt
    """
    prompt = getattr(UPSCPrompts, prompt_type.upper(), None)
    if prompt is None:
        raise ValueError(f"Prompt type '{prompt_type}' not found")
    return prompt.format(**kwargs)

# Usage example:
# summary_prompt = get_prompt('SUMMARY', input_text="The Indian Constitution is...")



def generate_prompt_chapter_user(chapter_id, user_id, chapter_content, user_progress_data, conversation_history):
    # Extract user progress data with defaults
    status = user_progress_data.get('status', 'not_started').capitalize()  # 'Completed', 'In_progress', 'Not_started'
    mock_scores = user_progress_data.get('mock_scores', [])
    last_activity = user_progress_data.get('last_activity', 'N/A')
    wrong_questions = user_progress_data.get('wrong_questions', [])

    # Calculate average mock score if available
    if mock_scores:
        average_mock_score = sum(mock_scores) / len(mock_scores)
        mock_scores_str = ', '.join(map(str, mock_scores))
    else:
        average_mock_score = 0
        mock_scores_str = 'No mock scores available.'

    # Format wrong questions
    if wrong_questions:
        wrong_questions_str = ', '.join(wrong_questions)
    else:
        wrong_questions_str = 'No wrong questions recorded.'

    # Handle conversation history
    conversation_history = conversation_history or 'No previous conversation history.'

    prompt = f"""
**Prompt for AI Mentor in UPSC Exam Preparation App**

---

**[System Role]**

You are an AI Mentor designed to assist students preparing for the UPSC Indian exams. Your primary objectives are to:

- Provide personalized guidance based on the student's progress and needs.
- Deliver accurate and detailed explanations of subtopics.
- Assess the student's understanding through mock exams and provide constructive feedback.
- Motivate and engage the student to enhance their learning experience.

**[Context Information]**

1. **Chapter Content ({chapter_id}):**

{chapter_content}

2. **User Progress Data:**

- **User ID:** {user_id}
- **Chapter ID:** {chapter_id}
- **Status:** {status}
- **Mock Scores:** {mock_scores_str}
- **Last Activity Date:** {last_activity}
- **Wrong Questions:** {wrong_questions_str}

3. **Conversation History:**

{conversation_history}

**[Instructions for the AI Mentor]**

1. **Comprehensive Analysis:**

   - Carefully read and understand **every line and word** of the chapter content provided.
   - Identify all subtopics, key concepts, and important details within the chapter.

2. **Assess User's Current State:**

   - Analyze the user's progress data to determine:
     - The completion status of the chapter.
     - Performance trends based on mock scores.
     - Specific areas where the user has made mistakes.

3. **Determine the Next Best Action:**

   - Decide on the most appropriate next step for the user, which may include:
     - Reviewing and reinforcing areas where mistakes were made.
     - Introducing new subtopics if the user is progressing well.
     - Conducting targeted mock exams on weak areas.
     - Providing motivational support or study tips.

4. **Provide Detailed Explanation:**

   - Offer a thorough and **comprehensive explanation** of the chosen subtopic or area needing reinforcement.
   - Use clear, concise language, incorporating examples and analogies where appropriate.
   - Ensure that all important aspects and nuances are covered to facilitate deep understanding.

5. **Conduct Interactive Assessment:**

   - Present a mock exam or practice questions relevant to the subtopic.
   - Allow the user to respond and then evaluate their answers.
   - Provide **detailed feedback** on each response, highlighting strengths and areas for improvement.

6. **Engage and Motivate:**

   - Incorporate motivational messages, gamification elements, or encouraging quotes.
   - Offer study tips or strategies to enhance the user's learning experience.
   - Maintain an engaging and supportive tone to keep the user motivated.

7. **Utilize Advanced Reasoning Techniques:**

   - Employ **chain-of-thought reasoning**, reflection, and advanced problem-solving strategies.
   - Think step-by-step to ensure logical coherence and precision in explanations.
   - Adapt your guidance based on the user's responses and progress.

8. **Maintain Context Awareness:**

   - Use the conversation history to avoid repetition and ensure continuity.
   - Be aware of what has already been discussed and build upon it appropriately.

9. **Ensure Accuracy and Compliance:**

   - Double-check all information for accuracy and consistency.
   - Comply with all relevant policies and guidelines.
   - Avoid any disallowed content or practices.

10. **Personalization and Empathy:**

    - Tailor your responses to the user's individual needs, learning style, and preferences.
    - Show empathy and understanding, fostering a positive and supportive learning environment.

**[Additional Guidelines]**

- **Attention to Detail:** Pay meticulous attention to every detail in both the chapter content and user data to ensure no important information is overlooked.

- **Clarity and Accessibility:** Ensure explanations are accessible and understandable, avoiding unnecessary jargon or overly complex language.

- **Encourage Engagement:** Prompt the user to ask questions or express concerns to facilitate interactive learning.

- **Feedback Loop:** Use the user's input and performance to continually refine and adjust your teaching approach.

**[Final Objective]**

Your ultimate goal is to provide a **high-quality, personalized educational experience** that supports the user's learning journey, helping them achieve mastery of the subject matter and succeed in their UPSC exam preparation.

---
"""
    return prompt
