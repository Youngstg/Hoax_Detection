import re
import nltk
import pandas as pd
import numpy as np
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
from real_time_checker import RealTimeNewsChecker
from news_explainer import NewsExplainer
from huggingface_detector import HuggingFaceDetector, MultiModelDetector
import logging

class NewsAnalyzer:
    def __init__(self):
        self.trusted_sources = [
            'reuters.com', 'ap.org', 'bbc.com', 'cnn.com', 'npr.org',
            'kompas.com', 'detik.com', 'tempo.co', 'antara.id', 'liputan6.com'
        ]
        self.real_time_checker = RealTimeNewsChecker()
        self.news_explainer = NewsExplainer()
        
        # Initialize Hugging Face models
        try:
            logging.info("Initializing Hugging Face models...")
            self.hf_detector = MultiModelDetector()
            logging.info("Hugging Face models loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Hugging Face models: {str(e)}")
            raise Exception(f"Cannot initialize Hugging Face models: {str(e)}")
    
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
    
    
    def check_trusted_sources(self, text):
        # Simple check for domain mentions
        trusted_mentions = 0
        for source in self.trusted_sources:
            if source.lower() in text.lower():
                trusted_mentions += 1
        
        return trusted_mentions / len(self.trusted_sources) if self.trusted_sources else 0
    
    def analyze(self, text):
        print("Starting analysis...")
        
        # Get Hugging Face model predictions
        print("Getting Hugging Face model predictions...")
        hf_result = self.hf_detector.predict_ensemble(text)
        
        if hf_result['prediction'] == 'ERROR':
            raise Exception(f"Hugging Face prediction failed: {hf_result.get('error', 'Unknown error')}")
        
        print(f"Hugging Face prediction: {hf_result['prediction']} (confidence: {hf_result['confidence']:.3f})")
        
        # Use Hugging Face results as primary prediction
        ml_prediction = hf_result['prediction']
        avg_confidence = hf_result['confidence']
        
        # Individual predictions for detailed results
        predictions = {
            'huggingface_ensemble': {
                'prediction': hf_result['prediction'],
                'confidence': hf_result['confidence']
            }
        }
        
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
        decision_basis = "Hugging Face Transformer Models"
        if verification_weight >= 0.6:
            decision_basis = "Real-time Verification from Trusted Sources"
        elif verification_weight >= 0.4:
            decision_basis = "Fact-checker Verification"
        elif verification_weight >= 0.2:
            decision_basis = "Combined Transformer + Source Verification"
        
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
            'huggingface_details': hf_result,
            'features': features,
            'analysis': {
                'word_count': features['word_count'],
                'sentiment': 'Positive' if features['sentiment_polarity'] > 0 else 'Negative' if features['sentiment_polarity'] < 0 else 'Neutral',
                'suspicious_indicators': features['suspicious_word_count']
            }
        }
        
        return result