from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from news_analyzer import NewsAnalyzer

app = Flask(__name__)
CORS(app)

analyzer = NewsAnalyzer()

def init_db():
    conn = sqlite3.connect('hoax_detection.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_text TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/analyze', methods=['POST'])
def analyze_news():
    try:
        data = request.get_json()
        news_text = data.get('text', '')
        
        if not news_text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = analyzer.analyze(news_text)
        
        # Store in database
        conn = sqlite3.connect('hoax_detection.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_history (news_text, prediction, confidence)
            VALUES (?, ?, ?)
        ''', (news_text, result['prediction'], result['confidence']))
        conn.commit()
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error in analyze_news: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect('hoax_detection.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, SUBSTR(news_text, 1, 100) as preview, prediction, confidence, timestamp 
            FROM analysis_history 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        history = cursor.fetchall()
        conn.close()
        
        return jsonify([{
            'id': row[0],
            'preview': row[1],
            'prediction': row[2],
            'confidence': row[3],
            'timestamp': row[4]
        } for row in history])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)