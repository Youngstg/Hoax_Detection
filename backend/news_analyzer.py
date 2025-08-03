import re
import nltk
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import pickle
import os
from real_time_checker import RealTimeNewsChecker
from news_explainer import NewsExplainer

class NewsAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'naive_bayes': MultinomialNB(),
            'logistic_regression': LogisticRegression(random_state=42)
        }
        self.trained = False
        self.trusted_sources = [
            'reuters.com', 'ap.org', 'bbc.com', 'cnn.com', 'npr.org',
            'kompas.com', 'detik.com', 'tempo.co', 'antara.id', 'liputan6.com'
        ]
        self.real_time_checker = RealTimeNewsChecker()
        self.news_explainer = NewsExplainer()
        self.load_or_train_models()
    
    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_features(self, text):
        features = {}
        
        # Basic text features
        features['word_count'] = len(text.split())
        features['char_count'] = len(text)
        features['avg_word_length'] = np.mean([len(word) for word in text.split()])
        
        # Sentiment analysis
        blob = TextBlob(text)
        features['sentiment_polarity'] = blob.sentiment.polarity
        features['sentiment_subjectivity'] = blob.sentiment.subjectivity
        
        # Suspicious patterns
        suspicious_words = ['viral', 'shocking', 'unbelievable', 'must read', 'breaking']
        features['suspicious_word_count'] = sum(1 for word in suspicious_words if word in text.lower())
        
        # Capitalization patterns
        features['caps_ratio'] = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        
        return features
    
    def generate_training_data(self):
        # Sample training data - in production, you'd use a larger dataset
        fake_news = [
            "BREAKING: Scientists Discover Miracle Cure That Doctors Don't Want You to Know!",
            "SHOCKING: This One Weird Trick Will Make You Rich Overnight!",
            "VIRAL: Celebrity Admits to Fake Moon Landing Conspiracy!",
            "Government Hiding Alien Technology in Area 51, Whistleblower Reveals!",
            "Doctors Hate This Simple Trick to Lose Weight Fast!",
            "Breaking: Vaccine Contains Microchips for Mind Control!",
            "Shocking Discovery: Earth is Actually Flat, Scientists Confirm!",
            "This Miracle Food Cures Cancer in 24 Hours!"
        ]
        
        real_news = [
            "The Federal Reserve announced a 0.25% interest rate increase following today's meeting.",
            "Local authorities report a 15% decrease in traffic accidents after implementing new safety measures.",
            "The stock market closed mixed today with technology shares leading gains.",
            "Researchers at the university published findings on climate change impacts in coastal regions.",
            "The city council approved the new infrastructure budget for road maintenance projects.",
            "Health officials recommend continued vaccination efforts amid seasonal flu concerns.",
            "Economic indicators show steady growth in the manufacturing sector this quarter.",
            "Scientists announce breakthrough in renewable energy storage technology."
        ]
        
        # Create training dataset
        texts = fake_news + real_news
        labels = [0] * len(fake_news) + [1] * len(real_news)  # 0 = fake, 1 = real
        
        return texts, labels
    
    def train_models(self):
        texts, labels = self.generate_training_data()
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        # Vectorize texts
        X = self.vectorizer.fit_transform(processed_texts)
        
        # Train models
        for name, model in self.models.items():
            model.fit(X, labels)
        
        self.trained = True
        self.save_models()
    
    def save_models(self):
        model_dir = 'models'
        os.makedirs(model_dir, exist_ok=True)
        
        # Save vectorizer
        with open(f'{model_dir}/vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        # Save models
        for name, model in self.models.items():
            with open(f'{model_dir}/{name}.pkl', 'wb') as f:
                pickle.dump(model, f)
    
    def load_models(self):
        model_dir = 'models'
        
        try:
            # Load vectorizer
            with open(f'{model_dir}/vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            # Load models
            for name in self.models.keys():
                with open(f'{model_dir}/{name}.pkl', 'rb') as f:
                    self.models[name] = pickle.load(f)
            
            self.trained = True
            return True
        except FileNotFoundError:
            return False
    
    def load_or_train_models(self):
        if not self.load_models():
            print("Training new models...")
            self.train_models()
            print("Models trained and saved.")
    
    def check_trusted_sources(self, text):
        # Simple check for domain mentions
        trusted_mentions = 0
        for source in self.trusted_sources:
            if source.lower() in text.lower():
                trusted_mentions += 1
        
        return trusted_mentions / len(self.trusted_sources) if self.trusted_sources else 0
    
    def analyze(self, text):
        if not self.trained:
            raise Exception("Models not trained")
        
        print("Starting analysis...")
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Vectorize
        X = self.vectorizer.transform([processed_text])
        
        # Get predictions from all models
        predictions = {}
        for name, model in self.models.items():
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0]
            predictions[name] = {
                'prediction': 'Real' if pred == 1 else 'Fake',
                'confidence': max(prob)
            }
        
        # Ensemble prediction (majority vote)
        fake_votes = sum(1 for p in predictions.values() if p['prediction'] == 'Fake')
        real_votes = len(predictions) - fake_votes
        
        ml_prediction = 'Real' if real_votes > fake_votes else 'Fake'
        
        # Calculate ML confidence
        avg_confidence = np.mean([p['confidence'] for p in predictions.values()])
        
        # Check trusted sources (old method)
        trusted_score = self.check_trusted_sources(text)
        
        # Real-time verification with trusted sources
        print("Performing real-time verification...")
        verification_result = self.real_time_checker.verify_with_trusted_sources(text)
        
        # Get related authentic news articles
        print("Searching for related authentic news...")
        related_news = self.real_time_checker.get_related_authentic_news(text, max_articles=5)
        
        # Generate comprehensive explanation
        print("Generating comprehensive explanation...")
        explanation = None
        user_explanation = None
        
        try:
            if related_news and related_news['related_articles']:
                explanation = self.news_explainer.summarize_topic(text, related_news['related_articles'])
                user_explanation = self.news_explainer.generate_user_friendly_explanation(
                    explanation, final_prediction, final_confidence
                )
        except Exception as e:
            print(f"Error generating explanation: {str(e)}")
            # Continue without explanation rather than failing completely
        
        # PRIORITIZE REAL-TIME VERIFICATION over ML models
        final_prediction = ml_prediction
        final_confidence = avg_confidence
        verification_weight = 0.0
        
        # Handle suspicious geopolitical claims
        if verification_result.get('claim_type') == 'suspicious_geopolitical_claim':
            final_prediction = 'Fake'
            final_confidence = 0.9  # High confidence this is false
            verification_weight = 0.9
            print("SUSPICIOUS GEOPOLITICAL CLAIM DETECTED - Marked as Fake with high confidence")
        
        # Strong evidence from multiple trusted sources
        elif verification_result['total_sources_found'] >= 3:
            final_prediction = 'Real'
            final_confidence = 0.9 + (verification_result['verification_score'] * 0.1)
            verification_weight = 0.8
            print(f"HIGH CONFIDENCE: Found {verification_result['total_sources_found']} trusted sources")
        
        # Moderate evidence from trusted sources    
        elif verification_result['total_sources_found'] >= 1:
            final_prediction = 'Real'
            final_confidence = 0.7 + (verification_result['verification_score'] * 0.2)
            verification_weight = 0.6
            print(f"MODERATE CONFIDENCE: Found {verification_result['total_sources_found']} trusted source(s)")
        
        # Evidence from fact-checkers (even without trusted news sources)
        elif len(verification_result['fact_checks']) > 0:
            # Fact-checkers found - likely debunking false claims
            final_prediction = 'Fake'
            final_confidence = 0.8
            verification_weight = 0.7
            print(f"FACT-CHECK FOUND: {len(verification_result['fact_checks'])} fact-check(s) available - likely debunking")
        
        # No verification found - rely more on ML but with lower confidence
        elif verification_result['verification_score'] == 0 and len(verification_result['keywords_used']) > 0:
            # Keywords found but no trusted sources - suspicious
            if ml_prediction == 'Real':
                final_prediction = 'Fake'
                final_confidence = max(0.4, avg_confidence - 0.3)
                verification_weight = 0.3
                print("SUSPICIOUS: No trusted sources found despite relevant keywords")
            else:
                final_confidence = min(0.8, avg_confidence + 0.2)  # More confident in Fake prediction
                verification_weight = 0.2
        
        # Combine with related authentic news findings
        if related_news and related_news['total_found'] >= 2:
            # Multiple related authentic articles found - strong indicator of real news
            if verification_weight < 0.6:  # Only adjust if not already high confidence
                final_prediction = 'Real'
                final_confidence = min(0.95, final_confidence + 0.2)
                verification_weight = max(verification_weight, 0.5)
                print(f"AUTHENTIC NEWS FOUND: {related_news['total_found']} related articles from trusted sources")
        
        # Extract additional features
        features = self.extract_features(text)
        
        # Determine decision basis
        decision_basis = "Machine Learning Model"
        if verification_weight >= 0.6:
            decision_basis = "Real-time Verification from Trusted Sources"
        elif verification_weight >= 0.4:
            decision_basis = "Fact-checker Verification"
        elif verification_weight >= 0.2:
            decision_basis = "Combined ML + Source Verification"
        
        result = {
            'prediction': final_prediction,
            'confidence': float(final_confidence),
            'decision_basis': decision_basis,
            'verification_weight': float(verification_weight),
            'ml_prediction': ml_prediction,
            'ml_confidence': float(avg_confidence),
            'trusted_sources_score': float(trusted_score),
            'real_time_verification': verification_result,
            'related_authentic_news': related_news,
            'comprehensive_explanation': explanation,
            'user_explanation': user_explanation,
            'individual_predictions': predictions,
            'features': features,
            'analysis': {
                'word_count': features['word_count'],
                'sentiment': 'Positive' if features['sentiment_polarity'] > 0 else 'Negative' if features['sentiment_polarity'] < 0 else 'Neutral',
                'suspicious_indicators': features['suspicious_word_count']
            }
        }
        
        return result