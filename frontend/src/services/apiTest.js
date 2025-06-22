import api from './api';

/**
 * Test the connection to the RAG service API
 * @returns {Promise<boolean>} True if connection successful, false otherwise
 */
export async function testRagServiceConnection() {
  console.log('Testing connection to RAG service...');
  
  try {
    // Simple health check endpoint - modify this to match your actual API health check endpoint
    const response = await api.get('/health');
    
    console.log('RAG service health check response:', response.data);
    return true;
  } catch (error) {
    console.error('Failed to connect to RAG service:', error);
    return false;
  }
}

/**
 * Test the quiz generation endpoint
 * @param {string} topic - The quiz topic
 * @returns {Promise<Object|null>} Quiz data if successful, null otherwise
 */
export async function testQuizGeneration(topic = 'Python basics') {
  console.log(`Testing quiz generation for topic: ${topic}`);
  
  try {
    const response = await api.post('/quiz/generate', {
      topic,
      num_questions: 3,
      num_alternatives: 4
    });
    
    console.log('Quiz generation response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to generate quiz:', error);
    console.error('Error details:', error.response ? error.response.data : error.message);
    return null;
  }
}

/**
 * Debug the quiz generation API by directly fetching from the backend
 * @param {string} topic - The quiz topic
 */
export async function debugQuizGeneration(topic = 'Python basics') {
  console.log(`Debug: Testing quiz generation with direct fetch for topic: ${topic}`);
  
  try {
    // Try direct fetch to diagnose CORS or proxy issues
    const apiUrl = '/api/quiz/generate';
    console.log(`Fetching from: ${apiUrl}`);
    
    const rawResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        topic,
        num_questions: 3,
        num_alternatives: 4
      })
    });
    
    if (!rawResponse.ok) {
      const errorText = await rawResponse.text();
      throw new Error(`HTTP Error ${rawResponse.status}: ${errorText}`);
    }
    
    const data = await rawResponse.json();
    console.log('Direct fetch quiz generation response:', data);
    return data;
  } catch (error) {
    console.error('Direct fetch error:', error);
    return null;
  }
} 