import re
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv


class TagExtractor:
    def __init__(self):
        load_dotenv()
        self.ollama_host = os.getenv("OLLAMA_HOST")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "default-model")
        self.candidate_tags = {
            "Business": ["Walter","business", "economy", "enterprise"],
            "Marketing": ["Walter","advertising", "sales", "branding"],
            "Climate": ["Julia","environment", "global warming", "green energy"],
            "Ethics": ["Lynda","Linda","fairness", "transparency", "AI governance"],
            "AI": ["artificial intelligence", "machine learning", "automation"],
            "Technology": ["tech", "innovation", "gadgets"],
            "Healthcare": ["Alex","medicine", "health", "biotech"],
            "Renewable Energy": ["solar", "wind energy", "clean energy"],
            "Sustainability": ["eco-friendly", "recycling", "carbon footprint"],
        }

    def keyword_based_extraction(self, message):
        tags = []
        for tag, keywords in self.candidate_tags.items():
            if any(re.search(rf"\b{keyword}\b", message, re.IGNORECASE) for keyword in keywords):
                tags.append(tag)
        return tags

    def cosine_similarity_extraction(self, message):
        vectorizer = TfidfVectorizer()
        corpus = [message] + list(self.candidate_tags.keys())
        tfidf_matrix = vectorizer.fit_transform(corpus)

        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        threshold = 0.15
        relevant_tags = [tag for tag, similarity in zip(self.candidate_tags.keys(), similarities) if similarity >= threshold]

        return relevant_tags

    def ollama_based_extraction(self, message):
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": (
                    f"Analyze the message: '{message}' and match it with relevant tags "
                    f"from the following list: {', '.join(self.candidate_tags.keys())}. "
                    f"Return only the most relevant tags."
                ),
            }

            response = requests.post(f"{self.ollama_host}/api/v1/completions", json=payload)
            response.raise_for_status()

            tags = response.json().get("choices", [{}])[0].get("text", "").strip().split(", ")
            return [tag.strip() for tag in tags if tag.strip() in self.candidate_tags.keys()]
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return []

    def extract_tags(self, message, method="hybrid"):
        if method == "keyword":
            return self.keyword_based_extraction(message)
        elif method == "cosine":
            return self.cosine_similarity_extraction(message)
        elif method == "ollama":
            return self.ollama_based_extraction(message)
        elif method == "hybrid":
            tags = self.keyword_based_extraction(message)
            if not tags:
                tags = self.cosine_similarity_extraction(message)
            if not tags:
                tags = self.ollama_based_extraction(message)
            return tags
        else:
            raise ValueError(f"Invalid method '{method}'.")

    def build_metadata(self, message, method="hybrid"):
        tags = self.extract_tags(message, method)
        return {"message": message, "tags": tags}