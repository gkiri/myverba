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