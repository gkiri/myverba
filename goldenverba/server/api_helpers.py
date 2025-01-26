from fastapi import HTTPException
#from goldenverba import verba_manager
from wasabi import msg
import goldenverba.server.prompts as prompts  # Add this import
import re
from goldenverba.verba_manager import VerbaManager

def fetch_subtopic_content(manager: VerbaManager, subtopic_id: str) -> str:
    """
    Retrieve subtopic content from Weaviate
    """
    subtopic_data = (
        manager.client.query
        .get("VERBA_Syllabus_Subtopics", ["subtopic_content"])
        .with_where({"path": ["subtopic_id"], "operator": "Equal", "valueString": subtopic_id})
        .with_limit(1)
        .do()
    )

    if not subtopic_data["data"]["Get"]["VERBA_Syllabus_Subtopics"]:
        raise HTTPException(status_code=404, detail="Subtopic not found")
        
    return subtopic_data["data"]["Get"]["VERBA_Syllabus_Subtopics"][0].get("subtopic_content", "")

def perform_pyqs_search(manager: VerbaManager, subtopic_content: str, limit: int = 50) -> list:
    """
    Perform a hybrid search in Weaviate's PYQS class using the subtopic content.
    Returns a list of top 'limit' results, each item containing question data.
    """
    try:
        # First, let's log the input parameters
        msg.info(f"Performing PYQS search for content length: {len(subtopic_content)} chars, limit: {limit}")
        
        # Perform the hybrid search
        pyqs_data = (
            manager.client.query
            .get("PYQS", ["question", "options", "answer_key", "description", "year"])
            .with_hybrid(
                query=subtopic_content[:1000],  # Limit query length to avoid potential issues
                alpha=0.7,
                properties=["question", "description"]
            )
            .with_limit(limit)
            .with_additional(["score"])
            .do()
        )
        
        # Log the raw response for debugging
        #msg.info(f"Raw Weaviate response: {pyqs_data}")
        
        # Validate response structure
        if not isinstance(pyqs_data, dict):
            msg.warn(f"Unexpected response type: {type(pyqs_data)}")
            return []
            
        if 'data' not in pyqs_data:
            msg.warn("No 'data' field in response")
            return []
            
        pyqs_results = pyqs_data.get('data', {}).get('Get', {}).get('PYQS', [])
        
        if not pyqs_results:
            msg.warn("No PYQS results found")
            return []
            
        # Transform and return results
        processed_results = [
            {
                "question": item["question"],
                "answer": item["answer_key"],
                "hybrid_score": float(item["_additional"].get("score", 0.0)),
                "explanation": item["description"],
                "year": item["year"]
            }
            for item in pyqs_results
        ]
        
        #msg.good(f"Successfully retrieved {len(processed_results)} PYQS results")
        return processed_results

    except Exception as e:
        msg.fail(f"Error in perform_pyqs_search: {str(e)}")
        # Log the full exception for debugging
        import traceback
        msg.warn(f"Full traceback: {traceback.format_exc()}")
        return []


def sort_pyqs_by_score(pyqs_data: list, top_n: int = 50) -> list:
    """
    Sort the returned PYQS data by descending score, then truncate to top_n items.
    """
    
    if not isinstance(pyqs_data, list):
        msg.warn(f"Error:sort_pyqs_by_score failed: pyqs_data not list")
        return []

    sorted_pyqs = sorted(
        [
            {
                "question": p["question"],
                "options": p.get("options", []),
                "answer": p["answer_key"],
                "year": p.get("year", "Unknown"),
                "score": float(p["_additional"].get("score", 0.0)),
                "explanation": p.get("description", "")
            }
            for p in pyqs_data
        ],
        key=lambda x: x["score"],
        reverse=True
    )
    #msg.info(f"sorted_pyqs:: {sorted_pyqs}")
    return sorted_pyqs[:top_n]


def build_filter_prompt(subtopic_content: str, sorted_pyqs: list) -> str:
    """Create a prompt for filtering relevant PYQs using the standardized template"""
    hybrid_results = [
        f"Q{i+1}: {q['question']}\nExplanation: {q['explanation']}"
        for i, q in enumerate(sorted_pyqs)
    ]

    #msg.info(f"build_filter_prompt sorted hybrid_results:: {hybrid_results}")  # Add logging
    
    return prompts.get_prompt(
        "PYQS",
        subtopic_content=subtopic_content,
        hybrid_results="\n".join(hybrid_results)
    )


async def filter_top_pyqs_with_llm(sorted_pyqs: list, subtopic_content: str) -> list:
    """
    Use Gemini LLM to select the 10 most relevant questions from sorted_pyqs.
    If the LLM fails or returns fewer than 10, fallback to the top-10 by score.
    """
    from goldenverba.server.api import generate_gemini_response  # Local import to avoid circular dependency

    prompt = build_filter_prompt(subtopic_content, sorted_pyqs)
    #msg.info(f"filter_top_pyqs_with_llm sorted prompt:: {prompt}")
    #msg.info(f"filter_top_pyqs_with_llm sorted_pyqs:: {sorted_pyqs}")

    try:
        # Generate LLM response - subtopic and questions already in prompt
        llm_response = await generate_gemini_response(prompt, "")
        
        # Extract question IDs (e.g., Q1, Q2) from LLM response
        selected_question_ids = re.findall(r"\bQ\d+\b", llm_response)
        msg.info(f"selected_ids:: {selected_question_ids}")

        # Filter questions based on selected IDs
        filtered_questions = [
            question 
            for index, question in enumerate(sorted_pyqs)
            if f"Q{index+1}" in selected_question_ids
        ]

        msg.info(f"filtered_questions:: {filtered_questions}")
        # Return top 10 filtered questions or fallback to score-based top 10
        return filtered_questions[:10] or sorted_pyqs[:10]

    except Exception as e:
        msg.warn(f"Gemini filtering failed: {str(e)}")
        # Fallback to top 10 questions by score
        return sorted_pyqs[:10]

