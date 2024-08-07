from goldenverba.components.generation.GPT4Generator import GPT4Generator
import os

class OpenrouterGenerator(GPT4Generator):
    """
    Openrouter Generator.
    """

    def __init__(self):
        super().__init__()
        self.name = "Openrouter"
        self.description = "Generator using Openrouter suppported model"
        self.model_name = os.getenv("Openrouter_MODEL")
        self.requires_library = ["openai"]
        self.requires_env = ["OPENROUTER_API_KEY"]
        self.streamable = True
        self.context_window = 8000
        print("MODEL :: ",self.model_name)

    async def generate_stream(
        self,
        queries: list[str],
        context: list[str],
        conversation: dict = None,
    ):
        """Generate a stream of response dicts based on a list of queries and list of contexts, and includes conversational context
        @parameter: queries : list[str] - List of queries
        @parameter: context : list[str] - List of contexts
        @parameter: conversation : dict - Conversational context
        @returns Iterator[dict] - Token response generated by the Generator in this format {system:TOKEN, finish_reason:stop or empty}.
        """

        url = os.environ.get("OPENROUTER_API_KEY", "")
        if url == "":
            yield {
                "message": "Missing Openrouter API Key",
                "finish_reason": "stop",
            }

        if conversation is None:
            conversation = {}
        messages = self.prepare_messages(queries, context, conversation)

        try:
            import openai

            openai.api_key = os.getenv("OPENROUTER_API_KEY")
            #base_url = os.environ.get("OPENAI_BASE_URL", "")
            base_url = "https://openrouter.ai/api/v1"
            if base_url:
                openai.api_base = base_url

            if "OPENAI_API_TYPE" in os.environ:
                openai.api_type = os.getenv("OPENAI_API_TYPE")
            if "OPENAI_API_BASE" in os.environ:
                openai.api_base = os.getenv("OPENAI_API_BASE")
            if "OPENAI_API_VERSION" in os.environ:
                openai.api_version = os.getenv("OPENAI_API_VERSION")

            chat_completion_arguments = {
                "model": self.model_name,
                "messages": messages,
                "stream": True,
                "temperature": 0.0,
            }

            completion = await openai.ChatCompletion.acreate(
                **chat_completion_arguments
            )

            try:
                while True:
                    chunk = await completion.__anext__()
                    if len(chunk["choices"]) > 0:
                        if "content" in chunk["choices"][0]["delta"]:
                            yield {
                                "message": chunk["choices"][0]["delta"]["content"],
                                "finish_reason": chunk["choices"][0]["finish_reason"],
                            }
                        else:
                            yield {
                                "message": "",
                                "finish_reason": chunk["choices"][0]["finish_reason"],
                            }
            except StopAsyncIteration:
                pass

        except Exception:
            raise    
        
        
    def prepare_messages(
        self, queries: list[str], context: list[str], conversation: dict[str, str]
    ) -> dict[str, str]:
        """
        Prepares a list of messages formatted for a Retrieval Augmented Generation chatbot system, including system instructions, previous conversation, and a new user query with context.

        @parameter queries: A list of strings representing the user queries to be answered.
        @parameter context: A list of strings representing the context information provided for the queries.
        @parameter conversation: A list of previous conversation messages that include the role and content.

        @returns A list of message dictionaries formatted for the chatbot. This includes an initial system message, the previous conversation messages, and the new user query encapsulated with the provided context.

        Each message in the list is a dictionary with 'role' and 'content' keys, where 'role' is either 'system' or 'user', and 'content' contains the relevant text. This will depend on the LLM used.
        """
        messages = [
            {
                "role": "system",
                "content": "You are Verba, The Golden RAGtriever, a chatbot for Retrieval Augmented Generation (RAG). You will receive a user query and context pieces that have a semantic similarity to that specific query. Please answer these user queries only their provided context. If the provided documentation does not provide enough information, say so. If the user asks questions about you as a chatbot specifially, answer them naturally. If the answer requires code examples encapsulate them with ```programming-language-name ```. Don't do pseudo-code.",
            }
        ]

        for message in conversation:
            messages.append({"role": message.type, "content": message.content})

        query = " ".join(queries)
        user_context = " ".join(context)

        messages.append(
            {
                "role": "user",
                "content": f"Please answer this query: '{query}' with this provided context: {user_context}",
            }
        )

        return messages
