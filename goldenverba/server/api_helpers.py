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
    pyqs_data = (
        manager.client.query
        .get("PYQS", ["question", "options", "answer_key", "description", "year"])
        .with_hybrid(query=subtopic_content, alpha=0.7, properties=["question", "description"])
        .with_limit(limit)
        .with_additional(["score"])
        .do()
    )
    
    return pyqs_data.get("data", {}).get("Get", {}).get("PYQS", [])


def sort_pyqs_by_score(pyqs_data: list, top_n: int = 50) -> list:
    """
    Sort the returned PYQS data by descending score, then truncate to top_n items.
    """
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
    return sorted_pyqs[:top_n]


def build_filter_prompt(subtopic_content: str, sorted_pyqs: list) -> str:
    """Create a prompt for filtering relevant PYQs using the standardized template"""
    hybrid_results = [
        f"Q{i+1}: {q['question']}\nExplanation: {q['explanation']}"
        for i, q in enumerate(sorted_pyqs)
    ]
    
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

    try:
        llm_response = await generate_gemini_response(prompt, "") #2nd arg is null because subtopic and questiosn already in prompt
        selected_ids = re.findall(r"Q\d+", llm_response)
        
        return [
            q for i, q in enumerate(sorted_pyqs)
            if f"Q{i+1}" in selected_ids
        ][:10] or sorted_pyqs[:10]

    except Exception as e:
        msg.warn(f"Gemini filtering failed: {str(e)}")
        return sorted_pyqs[:10]

