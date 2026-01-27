# import pandas as pd
# import numpy as np
# import re
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

# # Define the function structure for Django
# def preprocess_text(text):
#     text = str(text).lower()
#     text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
#     return text

# # Load and process data
# file_path = r"C:\Users\LENOVO\Desktop\jobportal\backend\chat_bot\data.csv"
# df = pd.read_csv(file_path)
# df['Question'] = df['Question'].apply(preprocess_text)

# vectorizer = TfidfVectorizer()
# tfidf_matrix = vectorizer.fit_transform(df['Question'])

# class ChatBot:
#     def __init__(self, threshold=0.2):
#         self.threshold = threshold
        
#     def get_response(self, user_input):
#         user_input = preprocess_text(user_input)
#         user_tfidf = vectorizer.transform([user_input])
#         similarities = cosine_similarity(user_tfidf, tfidf_matrix)

#         best_match_idx = np.argmax(similarities)
#         best_score = similarities[0, best_match_idx]

#         if best_score < self.threshold:
#             return "I'm sorry, I didn't understand. Can you rephrase your question?"

#         return df.iloc[best_match_idx]['Answer']

# # Create a global chatbot instance
# chatbot = ChatBot()

# def get_chat_response(message):
#     """Wrapper function for Django views"""
#     return chatbot.get_response(message)

# # Test code (remove this in production/Django)
# if __name__ == "__main__":
#     print("workforce Chatbot: Hi! Ask me a medical question. (type 'exit' to quit)")
#     while True:
#         user_query = input("You: ")
#         if user_query.lower() in ['exit', 'quit']:
#             print("workforce chatbot: Goodbye!")
#             break
#         response = get_chat_response(user_query)
#         print("workforce Chatbot:", response)






import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
import difflib
# from rapidfuzz import process, fuzz as rfuzz

# Define the function structure for Django
def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    return text

def clean_text(text):
    """Enhanced text cleaning"""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text.strip()

# Load and process data
file_path = r"C:\Users\LENOVO\Desktop\jobportal\backend\chat_bot\data.csv"
df = pd.read_csv(file_path)

# Create cleaned versions for better matching
df['Question_cleaned'] = df['Question'].apply(clean_text)
df['Question_original'] = df['Question']  # Keep original

vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
tfidf_matrix = vectorizer.fit_transform(df['Question_cleaned'])

class ChatBot:
    def __init__(self, threshold=0.15):  # Lower threshold for fuzzy matching
        self.threshold = threshold
        self.questions_list = df['Question_cleaned'].tolist()
        self.original_questions = df['Question'].tolist()
        self.answers = df['Answer'].tolist()
        
    def get_response(self, user_input):
        # Clean user input
        user_cleaned = clean_text(user_input)
        

        # Method 1: Fuzzy string matching (handles spelling mistakes)
        fuzzy_scores = []
        for question in self.questions_list:
            # Use multiple fuzzy matching techniques
            ratio1 = fuzz.ratio(user_cleaned, question)
            ratio2 = fuzz.partial_ratio(user_cleaned, question)
            ratio3 = fuzz.token_sort_ratio(user_cleaned, question)
            ratio4 = fuzz.token_set_ratio(user_cleaned, question)
            
            # Weighted average
            weighted_score = (ratio1 * 0.2 + ratio2 * 0.3 + ratio3 * 0.25 + ratio4 * 0.25)
            fuzzy_scores.append(weighted_score)

        # Method 2: TF-IDF cosine similarity
        user_tfidf = vectorizer.transform([user_cleaned])
        tfidf_similarities = cosine_similarity(user_tfidf, tfidf_matrix)[0]
        
        # Method 3: Use difflib for close matches
        close_matches = difflib.get_close_matches(
            user_cleaned, 
            self.questions_list, 
            n=3, 
            cutoff=0.6
        )

        # Method 4: RapidFuzz for fast fuzzy matching
        # rapid_matches = process.extract(
        #     user_cleaned,
        #     self.questions_list,
        #     scorer=rfuzz.WRatio,
        #     limit=3
        # )
        rapid_matches = []
        
        # Combine scores (weighted)
        combined_scores = []
        for i in range(len(self.questions_list)):
            # Weighted combination of different methods
            combined = (
                tfidf_similarities[i] * 0.4 +  # TF-IDF weight
                (fuzzy_scores[i] / 100) * 0.4 +  # Fuzzy weight
                (1 if any(self.questions_list[i] in match[0] for match in rapid_matches) else 0) * 0.2
            )
            combined_scores.append(combined)
        
        # Find best match
        best_match_idx = np.argmax(combined_scores)
        best_score = combined_scores[best_match_idx]
        
        print(f"Best score: {best_score}, Threshold: {self.threshold}")
        
        # Check threshold
        if best_score < self.threshold:
            # Try partial matching as fallback
            for i, question in enumerate(self.questions_list):
                if user_cleaned in question or question in user_cleaned:
                    return self.answers[i]
            
            # Try keyword matching
            user_words = set(user_cleaned.split())
            for i, question in enumerate(self.questions_list):
                question_words = set(question.split())
                common_words = user_words.intersection(question_words)
                if len(common_words) >= 2:  # At least 2 common words
                    return self.answers[i]
            
            return "I'm sorry, I couldn't find an exact match. Could you rephrase your question or try asking about: job search, registration, account help, or contact support?"
        
        return self.answers[best_match_idx]
    
    def get_suggestions(self, user_input, n_suggestions=3):
        """Get similar question suggestions"""
        user_cleaned = clean_text(user_input)
        suggestions = []
        
        # Find similar questions
        for i, question in enumerate(self.questions_list):
            similarity = fuzz.token_set_ratio(user_cleaned, question)
            if similarity > 60:  # 60% similarity threshold
                suggestions.append({
                    'question': self.original_questions[i],
                    'similarity': similarity
                })
        
        # Sort by similarity and get top N
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        return [s['question'] for s in suggestions[:n_suggestions]]

# Create a global chatbot instance
chatbot = ChatBot()

def get_chat_response(message):
    """Wrapper function for Django views"""
    return chatbot.get_response(message)














# import pandas as pd
# import numpy as np
# import re
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from fuzzywuzzy import fuzz
# import difflib
# from rapidfuzz import process, fuzz as rfuzz
# import nltk
# from nltk.corpus import stopwords
# from nltk.stem import PorterStemmer
# from collections import Counter
# import itertools

# # Download NLTK data if not already downloaded
# try:
#     nltk.data.find('corpora/stopwords')
# except LookupError:
#     nltk.download('stopwords')

# # Initialize stemmer
# stemmer = PorterStemmer()
# stop_words = set(stopwords.words('english'))

# def enhanced_clean_text(text):
#     """More comprehensive text cleaning with stemming"""
#     text = str(text).lower()
    
#     # Remove special characters but keep important ones
#     text = re.sub(r'[^\w\s\-]', '', text)
    
#     # Remove extra spaces
#     text = re.sub(r'\s+', ' ', text)
    
#     # Tokenize and stem
#     words = text.split()
    
#     # Remove stopwords and apply stemming
#     filtered_words = []
#     for word in words:
#         if word not in stop_words and len(word) > 2:  # Remove very short words
#             stemmed_word = stemmer.stem(word)
#             filtered_words.append(stemmed_word)
    
#     return ' '.join(filtered_words).strip()

# def preprocess_text(text):
#     text = str(text).lower()
#     text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
#     return text

# def clean_text(text):
#     """Enhanced text cleaning"""
#     text = str(text).lower()
#     text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
#     text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
#     return text.strip()

# # Load and process data
# file_path = r"C:\Users\LENOVO\Desktop\jobportal\backend\chat_bot\data.csv"
# df = pd.read_csv(file_path)

# # Create multiple cleaned versions for better matching
# df['Question_cleaned'] = df['Question'].apply(clean_text)
# df['Question_stemmed'] = df['Question'].apply(enhanced_clean_text)
# df['Question_original'] = df['Question']  # Keep original

# # Create TF-IDF vectorizers for different text versions
# vectorizer_basic = TfidfVectorizer(stop_words='english', ngram_range=(1, 3))
# vectorizer_stemmed = TfidfVectorizer(stop_words='english', ngram_range=(1, 3))

# tfidf_matrix_basic = vectorizer_basic.fit_transform(df['Question_cleaned'])
# tfidf_matrix_stemmed = vectorizer_stemmed.fit_transform(df['Question_stemmed'])

# class ChatBot:
#     def __init__(self, threshold=0.25):  # Adjusted threshold
#         self.threshold = threshold
#         self.questions_cleaned = df['Question_cleaned'].tolist()
#         self.questions_stemmed = df['Question_stemmed'].tolist()
#         self.original_questions = df['Question'].tolist()
#         self.answers = df['Answer'].tolist()
        
#         # Precompute question keywords for faster matching
#         self.question_keywords = []
#         for q in self.questions_cleaned:
#             words = set(q.split())
#             self.question_keywords.append(words)
    
#     def calculate_semantic_similarity(self, user_cleaned, user_stemmed):
#         """Calculate multiple similarity scores"""
#         similarities = {
#             'tfidf_basic': 0,
#             'tfidf_stemmed': 0,
#             'fuzzy_weighted': 0,
#             'rapidfuzz': 0,
#             'jaccard': 0
#         }
        
#         user_words = set(user_cleaned.split())
#         user_words_stemmed = set(user_stemmed.split())
        
#         # TF-IDF similarities
#         user_tfidf_basic = vectorizer_basic.transform([user_cleaned])
#         tfidf_sim_basic = cosine_similarity(user_tfidf_basic, tfidf_matrix_basic)[0]
        
#         user_tfidf_stemmed = vectorizer_stemmed.transform([user_stemmed])
#         tfidf_sim_stemmed = cosine_similarity(user_tfidf_stemmed, tfidf_matrix_stemmed)[0]
        
#         # Get best fuzzy matches
#         rapid_matches = process.extract(
#             user_cleaned,
#             self.questions_cleaned,
#             scorer=rfuzz.WRatio,
#             limit=5
#         )
        
#         # Create fuzzy score mapping
#         fuzzy_scores_dict = {match[0]: match[1] for match in rapid_matches}
        
#         all_scores = []
#         for i in range(len(self.questions_cleaned)):
#             # Get individual scores
#             tfidf_basic_score = tfidf_sim_basic[i]
#             tfidf_stemmed_score = tfidf_sim_stemmed[i]
            
#             # Fuzzy scores
#             fuzzy_ratio = fuzz.ratio(user_cleaned, self.questions_cleaned[i])
#             fuzzy_partial = fuzz.partial_ratio(user_cleaned, self.questions_cleaned[i])
#             fuzzy_token = fuzz.token_set_ratio(user_cleaned, self.questions_cleaned[i])
#             weighted_fuzzy = (fuzzy_ratio * 0.2 + fuzzy_partial * 0.35 + fuzzy_token * 0.45)
            
#             # RapidFuzz score
#             rapid_score = fuzzy_scores_dict.get(self.questions_cleaned[i], 0)
            
#             # Jaccard similarity
#             jaccard_sim = len(user_words.intersection(self.question_keywords[i])) / len(user_words.union(self.question_keywords[i])) if len(user_words.union(self.question_keywords[i])) > 0 else 0
            
#             # Weighted combination - adjusted weights
#             combined = (
#                 tfidf_basic_score * 0.25 + 
#                 tfidf_stemmed_score * 0.20 + 
#                 (weighted_fuzzy / 100) * 0.30 +
#                 (rapid_score / 100) * 0.15 +
#                 jaccard_sim * 0.10
#             )
            
#             all_scores.append(combined)
        
#         return np.array(all_scores)
    
#     def get_response(self, user_input):
#         # Clean user input in multiple ways
#         user_cleaned = clean_text(user_input)
#         user_stemmed = enhanced_clean_text(user_input)
        
#         # Calculate combined similarity scores
#         combined_scores = self.calculate_semantic_similarity(user_cleaned, user_stemmed)
        
#         # Find best match
#         best_match_idx = np.argmax(combined_scores)
#         best_score = combined_scores[best_match_idx]
        
#         print(f"Debug - Best score: {best_score:.4f}, Question: {self.original_questions[best_match_idx][:50]}...")
        
#         # Multi-level fallback strategy
#         if best_score < self.threshold:
#             # Level 1: Check for exact substring matches
#             for i, question in enumerate(self.questions_cleaned):
#                 if (user_cleaned in question and len(user_cleaned) > 3) or \
#                    (question in user_cleaned and len(question) > 3):
#                     print(f"Debug - Substring match found at index {i}")
#                     return self.answers[i]
            
#             # Level 2: Check for keyword overlap with stemming
#             user_words_stemmed = set(user_stemmed.split())
#             for i, question_stemmed in enumerate(self.questions_stemmed):
#                 question_words = set(question_stemmed.split())
#                 common_words = user_words_stemmed.intersection(question_words)
#                 if len(common_words) >= 2:
#                     print(f"Debug - Keyword match with {len(common_words)} common words at index {i}")
#                     return self.answers[i]
            
#             # Level 3: Check for partial word matches
#             for i, question in enumerate(self.questions_cleaned):
#                 user_words = user_cleaned.split()
#                 question_words = question.split()
                
#                 # Check if any user word starts with any question word or vice versa
#                 matches = 0
#                 for uw in user_words:
#                     for qw in question_words:
#                         if (uw.startswith(qw) or qw.startswith(uw)) and len(uw) > 3 and len(qw) > 3:
#                             matches += 1
#                             break
                
#                 if matches >= 2:
#                     print(f"Debug - Partial word match with {matches} matches at index {i}")
#                     return self.answers[i]
            
#             # Level 4: Get similar questions for suggestions
#             suggestions = self.get_suggestions(user_input, n_suggestions=3)
#             suggestion_text = "\n".join([f"- {s}" for s in suggestions])
            
#             return f"I'm sorry, I couldn't find an exact match. Here are some similar questions:\n{suggestion_text}\n\nOr try asking about: job search, registration, account help, or contact support."
        
#         return self.answers[best_match_idx]
    
#     def get_suggestions(self, user_input, n_suggestions=5):
#         """Get similar question suggestions"""
#         user_cleaned = clean_text(user_input)
#         suggestions = []
        
#         # Calculate similarities for all questions
#         similarities = []
#         for i, question in enumerate(self.questions_cleaned):
#             # Use multiple similarity measures
#             token_set = fuzz.token_set_ratio(user_cleaned, question)
#             partial = fuzz.partial_ratio(user_cleaned, question)
#             avg_similarity = (token_set + partial) / 2
            
#             if avg_similarity > 50:  # Lower threshold for suggestions
#                 similarities.append((i, avg_similarity))
        
#         # Sort by similarity
#         similarities.sort(key=lambda x: x[1], reverse=True)
        
#         # Return top N suggestions
#         return [self.original_questions[idx] for idx, _ in similarities[:n_suggestions]]

# # Create a global chatbot instance
# chatbot = ChatBot()

# def get_chat_response(message):
#     """Wrapper function for Django views"""
#     return chatbot.get_response(message)
