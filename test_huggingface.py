#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from huggingface_detector import HuggingFaceDetector, MultiModelDetector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_single_model():
    print("=== Testing Single Hugging Face Model ===")
    try:
        detector = HuggingFaceDetector("jy46604790/Fake-News-Bert-Detect")
        
        # Test cases
        test_cases = [
            "BREAKING: Scientists Discover Miracle Cure That Doctors Don't Want You to Know!",
            "The Federal Reserve announced a 0.25% interest rate increase following today's meeting.",
            "SHOCKING: This One Weird Trick Will Make You Rich Overnight!",
            "Local authorities report a 15% decrease in traffic accidents after implementing new safety measures."
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\nTest {i}: {text[:50]}...")
            result = detector.predict(text)
            print(f"Prediction: {result['prediction']}")
            print(f"Confidence: {result['confidence']:.3f}")
            print(f"Probabilities: Real={result['probabilities']['real']:.3f}, Fake={result['probabilities']['fake']:.3f}")
            
    except Exception as e:
        print(f"Error testing single model: {str(e)}")
        return False
    
    return True

def test_multi_model():
    print("\n=== Testing Multi-Model Ensemble ===")
    try:
        detector = MultiModelDetector()
        
        # Test cases
        test_cases = [
            "Government Hiding Alien Technology in Area 51, Whistleblower Reveals!",
            "The stock market closed mixed today with technology shares leading gains."
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\nEnsemble Test {i}: {text[:50]}...")
            result = detector.predict_ensemble(text)
            print(f"Final Prediction: {result['prediction']}")
            print(f"Final Confidence: {result['confidence']:.3f}")
            print(f"Weighted Score: {result['weighted_score']:.3f}")
            print("Individual Results:")
            for model_name, model_result in result['individual_results'].items():
                print(f"  {model_name}: {model_result['prediction']}")
                
    except Exception as e:
        print(f"Error testing multi-model: {str(e)}")
        return False
    
    return True

def test_news_analyzer_integration():
    print("\n=== Testing NewsAnalyzer Integration (Hugging Face Only) ===")
    try:
        from news_analyzer import NewsAnalyzer
        
        # Test new Hugging Face only system
        analyzer = NewsAnalyzer()
        
        test_cases = [
            "VIRAL: Celebrity Admits to Fake Moon Landing Conspiracy!",
            "The Federal Reserve announced a 0.25% interest rate increase following today's meeting."
        ]
        
        for i, test_text in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_text[:50]}...")
            
            result = analyzer.analyze(test_text)
            print(f"Final Prediction: {result['prediction']}")
            print(f"Final Confidence: {result['confidence']:.3f}")
            print(f"Decision Basis: {result['decision_basis']}")
            
            if 'huggingface_details' in result and result['huggingface_details']:
                print(f"Hugging Face Details: {result['huggingface_details']['prediction']} "
                      f"(confidence: {result['huggingface_details']['confidence']:.3f})")
            
            print("Model Predictions:")
            for name, pred in result['individual_predictions'].items():
                print(f"  {name}: {pred['prediction']} ({pred['confidence']:.3f})")
            
    except Exception as e:
        print(f"Error testing NewsAnalyzer integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("Testing Hugging Face Integration for Fake News Detection")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    if test_single_model():
        success_count += 1
        print("✅ Single model test passed")
    else:
        print("❌ Single model test failed")
    
    if test_multi_model():
        success_count += 1
        print("✅ Multi-model test passed")
    else:
        print("❌ Multi-model test failed")
    
    if test_news_analyzer_integration():
        success_count += 1
        print("✅ NewsAnalyzer integration test passed")
    else:
        print("❌ NewsAnalyzer integration test failed")
    
    print(f"\n=== Test Results: {success_count}/{total_tests} tests passed ===")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Hugging Face integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")