from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from typing import Dict, Any
import logging

class HuggingFaceDetector:
    def __init__(self, model_name: str = "jy46604790/Fake-News-Bert-Detect"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_model()
    
    def load_model(self):
        try:
            logging.info(f"Loading Hugging Face model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise
    
    def predict(self, text: str) -> Dict[str, Any]:
        try:
            # Truncate text to max 512 tokens
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=512
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
                
            # Get prediction
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = torch.max(probabilities).item()
            
            # Map class to label (0: Real, 1: Fake)
            prediction = "FAKE" if predicted_class == 1 else "REAL"
            
            return {
                "prediction": prediction,
                "confidence": confidence,
                "model": self.model_name,
                "probabilities": {
                    "real": probabilities[0][0].item(),
                    "fake": probabilities[0][1].item() if probabilities.shape[1] > 1 else 1 - probabilities[0][0].item()
                }
            }
            
        except Exception as e:
            logging.error(f"Error in prediction: {str(e)}")
            return {
                "prediction": "ERROR",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def batch_predict(self, texts: list) -> list:
        results = []
        for text in texts:
            results.append(self.predict(text))
        return results

class MultiModelDetector:
    def __init__(self):
        self.models = {
            "bert_news": HuggingFaceDetector("jy46604790/Fake-News-Bert-Detect"),
            "roberta_news": HuggingFaceDetector("winterForestStump/Roberta-fake-news-detector")
        }
    
    def predict_ensemble(self, text: str) -> Dict[str, Any]:
        results = {}
        predictions = []
        confidences = []
        
        for model_name, model in self.models.items():
            try:
                result = model.predict(text)
                results[model_name] = result
                
                if result["prediction"] != "ERROR":
                    predictions.append(1 if result["prediction"] == "FAKE" else 0)
                    confidences.append(result["confidence"])
            except Exception as e:
                logging.error(f"Error with model {model_name}: {str(e)}")
                results[model_name] = {"prediction": "ERROR", "error": str(e)}
        
        if not predictions:
            return {
                "prediction": "ERROR",
                "confidence": 0.0,
                "individual_results": results,
                "error": "All models failed"
            }
        
        # Ensemble prediction (majority vote with confidence weighting)
        weighted_pred = np.average(predictions, weights=confidences)
        ensemble_pred = "FAKE" if weighted_pred > 0.5 else "REAL"
        ensemble_confidence = np.mean(confidences)
        
        return {
            "prediction": ensemble_pred,
            "confidence": ensemble_confidence,
            "weighted_score": weighted_pred,
            "individual_results": results,
            "method": "ensemble"
        }