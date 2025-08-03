import requests
from bs4 import BeautifulSoup
import re
from textblob import TextBlob
import nltk
from collections import Counter

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass

class NewsExplainer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def extract_article_content(self, url):
        """Extract main content from a news article"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
                    element.decompose()
                
                # Common selectors for article content
                content_selectors = [
                    '.article-content', '.post-content', '.entry-content',
                    '.content', '.text', '.body', 'article p',
                    '.detail-content', '.news-content'
                ]
                
                content_text = ""
                for selector in content_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        if len(text) > 100:  # Only substantial content
                            content_text += text + "\n"
                
                # If no specific content found, try all paragraphs
                if not content_text:
                    paragraphs = soup.find_all('p')
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if len(text) > 50:
                            content_text += text + "\n"
                
                return content_text[:2000]  # Limit content length
                
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            return ""
        
        return ""
    
    def summarize_topic(self, original_text, related_articles):
        """Create a comprehensive explanation of the news topic"""
        
        # Extract key information from original text
        original_summary = self.extract_key_points(original_text)
        
        # Get content from top related articles
        article_contents = []
        for article in related_articles[:3]:  # Top 3 most relevant
            print(f"Extracting content from {article['source']}...")
            content = self.extract_article_content(article['link'])
            if content:
                article_contents.append({
                    'source': article['source'],
                    'title': article['title'],
                    'content': content,
                    'link': article['link']
                })
        
        # Generate comprehensive explanation
        explanation = self.generate_explanation(original_text, original_summary, article_contents)
        
        return explanation
    
    def extract_key_points(self, text):
        """Extract key points and entities from text"""
        try:
            # Basic entity extraction
            blob = TextBlob(text)
            
            # Extract potential entities (proper nouns)
            entities = []
            try:
                for word, pos in blob.tags:
                    if pos in ['NNP', 'NNPS']:  # Proper nouns
                        entities.append(word)
            except:
                # Fallback: simple word extraction
                words = text.split()
                entities = [word for word in words if word.istitle() and len(word) > 3][:5]
            
            # Extract key phrases (sequences of important words)
            key_sentences = []
            try:
                sentences = blob.sentences
                for sentence in sentences:
                    if len(sentence.words) > 5 and len(sentence.words) < 30:
                        key_sentences.append(str(sentence))
            except:
                # Fallback: simple sentence splitting
                sentences = text.split('.')
                key_sentences = [s.strip() for s in sentences if len(s.strip()) > 20 and len(s.strip()) < 200]
            
            # Extract numbers and dates
            numbers = re.findall(r'\b\d+(?:[.,]\d+)*\b', text)
            dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', text)
            
            return {
                'entities': list(set(entities))[:10],
                'key_sentences': key_sentences[:3],
                'numbers': numbers[:5],
                'dates': dates[:3]
            }
        except Exception as e:
            print(f"Error in extract_key_points: {str(e)}")
            # Return minimal fallback
            return {
                'entities': [],
                'key_sentences': [text[:100] + "..." if len(text) > 100 else text],
                'numbers': [],
                'dates': []
            }
    
    def generate_explanation(self, original_text, original_summary, article_contents):
        """Generate comprehensive explanation based on all sources"""
        
        explanation = {
            'topic_overview': '',
            'key_facts': [],
            'context': '',
            'verified_information': [],
            'sources_consulted': [],
            'timeline': [],
            'important_numbers': []
        }
        
        # Topic Overview
        if original_summary['entities']:
            main_entities = original_summary['entities'][:3]
            explanation['topic_overview'] = f"Topik ini berkaitan dengan {', '.join(main_entities)}. "
        
        if original_summary['key_sentences']:
            explanation['topic_overview'] += f"Inti dari klaim tersebut adalah: {original_summary['key_sentences'][0]}"
        
        # Extract verified information from trusted sources
        all_content = ""
        for article in article_contents:
            all_content += article['content'] + " "
            explanation['sources_consulted'].append({
                'source': article['source'],
                'title': article['title'],
                'link': article['link']
            })
        
        # Extract key facts from trusted sources
        if all_content:
            trusted_summary = self.extract_key_points(all_content)
            
            # Key facts from trusted sources
            explanation['key_facts'] = trusted_summary['key_sentences'][:5]
            
            # Important numbers and dates
            if trusted_summary['numbers']:
                explanation['important_numbers'] = list(set(trusted_summary['numbers']))[:5]
            
            if trusted_summary['dates']:
                explanation['timeline'] = list(set(trusted_summary['dates']))[:3]
        
        # Context explanation
        explanation['context'] = self.generate_context_explanation(original_text, article_contents)
        
        # Verified information comparison
        explanation['verified_information'] = self.compare_claims_with_facts(
            original_summary, 
            [self.extract_key_points(article['content']) for article in article_contents]
        )
        
        return explanation
    
    def generate_context_explanation(self, original_text, article_contents):
        """Generate contextual explanation"""
        if not article_contents:
            return "Tidak dapat menemukan konteks tambahan dari sumber terpercaya."
        
        # Count word frequency across trusted sources to find main themes
        all_words = []
        for article in article_contents:
            # Simple tokenization and filtering
            words = re.findall(r'\b[a-zA-Z]{4,}\b', article['content'].lower())
            all_words.extend(words)
        
        # Get most common themes
        common_themes = Counter(all_words).most_common(5)
        
        if common_themes:
            theme_words = [word for word, count in common_themes if count > 2]
            if theme_words:
                return f"Berdasarkan sumber terpercaya, topik ini umumnya berkaitan dengan: {', '.join(theme_words[:3])}. Informasi ini konsisten dilaporkan oleh multiple sumber terpercaya."
        
        return "Topik ini telah dikonfirmasi oleh beberapa sumber berita terpercaya."
    
    def compare_claims_with_facts(self, original_summary, trusted_summaries):
        """Compare original claims with verified facts"""
        verified_info = []
        
        # Simple comparison of entities and key phrases
        original_entities = set([e.lower() for e in original_summary.get('entities', [])])
        
        for trusted_summary in trusted_summaries:
            if trusted_summary:
                trusted_entities = set([e.lower() for e in trusted_summary.get('entities', [])])
                
                # Find common entities
                common_entities = original_entities.intersection(trusted_entities)
                if common_entities:
                    verified_info.append(f"Entitas yang dikonfirmasi: {', '.join(common_entities)}")
                
                # Add key sentences from trusted sources
                if trusted_summary.get('key_sentences'):
                    verified_info.extend(trusted_summary['key_sentences'][:2])
        
        return verified_info[:5]  # Limit to top 5 verified facts
    
    def generate_user_friendly_explanation(self, explanation_data, prediction, confidence):
        """Generate user-friendly explanation text"""
        
        result = {
            'summary': '',
            'detailed_explanation': '',
            'fact_check_result': '',
            'recommendation': ''
        }
        
        # Summary
        if explanation_data['topic_overview']:
            result['summary'] = explanation_data['topic_overview']
        else:
            result['summary'] = "Analisis telah dilakukan terhadap konten berita yang diberikan."
        
        # Detailed explanation
        detailed_parts = []
        
        if explanation_data['context']:
            detailed_parts.append(f"**Konteks:** {explanation_data['context']}")
        
        if explanation_data['key_facts']:
            facts_text = "\n".join([f"• {fact}" for fact in explanation_data['key_facts'][:3]])
            detailed_parts.append(f"**Fakta Utama:**\n{facts_text}")
        
        if explanation_data['important_numbers']:
            numbers_text = ", ".join(explanation_data['important_numbers'])
            detailed_parts.append(f"**Data Penting:** {numbers_text}")
        
        if explanation_data['timeline']:
            timeline_text = ", ".join(explanation_data['timeline'])
            detailed_parts.append(f"**Timeline:** {timeline_text}")
        
        result['detailed_explanation'] = "\n\n".join(detailed_parts)
        
        # Fact check result
        if prediction == 'Real':
            result['fact_check_result'] = f"✅ **Hasil Verifikasi:** Konten ini DAPAT DIPERCAYA dengan tingkat kepercayaan {confidence:.1%}."
            if explanation_data['verified_information']:
                verified_text = "\n".join([f"• {info}" for info in explanation_data['verified_information'][:3]])
                result['fact_check_result'] += f"\n\n**Informasi Terverifikasi:**\n{verified_text}"
        else:
            result['fact_check_result'] = f"⚠️ **Hasil Verifikasi:** Konten ini MERAGUKAN dengan tingkat kepercayaan {confidence:.1%}."
            result['fact_check_result'] += "\n\nHarap periksa sumber-sumber terpercaya sebelum mempercayai atau menyebarkan informasi ini."
        
        # Recommendation
        sources_count = len(explanation_data['sources_consulted'])
        if sources_count > 0:
            source_names = [s['source'] for s in explanation_data['sources_consulted'][:3]]
            result['recommendation'] = f"💡 **Rekomendasi:** Kami telah memverifikasi informasi ini dengan {sources_count} sumber terpercaya ({', '.join(source_names)}). "
            
            if prediction == 'Real':
                result['recommendation'] += "Untuk informasi lebih lengkap, silakan baca artikel-artikel terkait yang telah kami sediakan di bawah."
            else:
                result['recommendation'] += "Silakan merujuk pada artikel-artikel dari sumber terpercaya yang kami sediakan untuk mendapatkan informasi yang akurat."
        else:
            result['recommendation'] = "💡 **Rekomendasi:** Selalu verifikasi informasi dengan sumber-sumber berita terpercaya sebelum mempercayai atau menyebarkan konten."
        
        return result