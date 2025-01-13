import re
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv

class TagExtractor:
    """
    A class to generate tags or metadata for messages or topics.
    Supports keyword-based and cosine similarity approaches, with Ollama for advanced extraction.
    """

    def __init__(self):
        # Load environment variables for Ollama configuration
        load_dotenv()
        self.ollama_host = os.getenv("OLLAMA_HOST")
        self.ollama_model = os.getenv("OLLAMA_MODEL")  # Set the default Ollama model name

        # Default candidate tags (can be extended dynamically)
        self.candidate_tags = [
            "Business",
            "Marketing", 
            "climate",
            "ethics",
            "policy",
            "AI",
            "technology",
            "healthcare",
            "renewable energy",
            "sustainability",
            "environment"
        ]

    def keyword_based_extraction(self, message):
        """
        Extract tags from the message using predefined keywords.
        """
        keywords_to_tags = {tag: tag for tag in self.candidate_tags}
        tags = []
        for keyword, tag in keywords_to_tags.items():
            if re.search(rf"\b{keyword}\b", message, re.IGNORECASE):
                tags.append(tag)
        return tags

    def cosine_similarity_extraction(self, message):
        """
        Extract tags using cosine similarity between message and predefined tags.
        """
        vectorizer = TfidfVectorizer()
        corpus = [message] + self.candidate_tags
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Compute cosine similarity
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # Filter tags with a similarity threshold
        threshold = 0.1  # Adjust threshold based on experimentation
        relevant_tags = [tag for tag, similarity in zip(self.candidate_tags, similarities) if similarity >= threshold]

        return relevant_tags

    def ollama_based_extraction(self, message):
        """
        Extract tags using a locally hosted Ollama model.
        """
        try:
            # Build the request payload
            payload = {
                "model": self.ollama_model,
                "prompt": f"Message: \"{message}\"\nCandidate Tags: {', '.join(self.candidate_tags)}\nIdentify the relevant tags from the candidate list based on the message context."
            }

            # Send the request to Ollama
            response = requests.post(f"{self.ollama_host}/api/v1/completions", json=payload)
            response.raise_for_status()  # Raise error for HTTP errors

            # Extract and parse tags from the response
            tags = response.json().get("choices", [{}])[0].get("text", "").strip().split(", ")
            return [tag.strip() for tag in tags if tag.strip() in self.candidate_tags]

        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return []

    def extract_tags(self, message, method="hybrid"):
        """
        Extract tags from the message using the specified method.
        Options: "keyword", "cosine", "ollama", "hybrid".
        """
        if method == "keyword":
            return self.keyword_based_extraction(message)
        elif method == "cosine":
            return self.cosine_similarity_extraction(message)
        elif method == "ollama":
            return self.ollama_based_extraction(message)
        elif method == "hybrid":
            # Use keyword-based first, fallback to cosine similarity if no tags found
            tags = self.keyword_based_extraction(message)
            if not tags:
                tags = self.cosine_similarity_extraction(message)
            # Fallback to Ollama if advanced tagging is needed
            if not tags:
                tags = self.ollama_based_extraction(message)
            return tags
        else:
            raise ValueError(f"Invalid method '{method}'. Choose from 'keyword', 'cosine', 'ollama', 'hybrid'.")

    def build_metadata(self, message, method="keyword"):
        """
        Build metadata for the given message.
        Returns a dictionary with tags and the original message.
        """
        tags = self.extract_tags(message, method)
        return {
            "message": message,
            "tags": tags
        }