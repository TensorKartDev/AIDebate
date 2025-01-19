import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

class TagExtractor:
    def __init__(self, personas):
        """
        Initialize TagExtractor with personas.
        """
        self.candidate_tags = {
            persona: data.get("relevant_tags", []) for persona, data in personas.items()
        }
        print(self.candidate_tags)

    def keyword_based_extraction(self, message):
        tags = {}
        for persona, keywords in self.candidate_tags.items():
            matched_tags = [keyword for keyword in keywords if re.search(rf"\b{keyword}\b", message, re.IGNORECASE)]
            if matched_tags:
                tags[persona] = matched_tags
        logging.debug(f"Extracted tags: {tags} for message: '{message}'")
        return tags

    def cosine_similarity_extraction(self, message):
        vectorizer = TfidfVectorizer()
        corpus = [message] + list(self.candidate_tags.keys())
        tfidf_matrix = vectorizer.fit_transform(corpus)

        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return [tag for tag, sim in zip(self.candidate_tags.keys(), similarities) if sim > 0.15]

    def extract_tags(self, message, method="hybrid"):
        if method == "keyword":
            return self.keyword_based_extraction(message)
        elif method == "cosine":
            return self.cosine_similarity_extraction(message)
        elif method == "hybrid":
            tags = self.keyword_based_extraction(message)
            return tags or self.cosine_similarity_extraction(message)