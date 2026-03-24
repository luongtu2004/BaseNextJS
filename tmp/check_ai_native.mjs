const baseUrl = 'http://113.160.201.164:4020/api/agent-openai/v1';
const apiKey = 'sk_local_7fN3qL9vX2mK8pR4dT1yH6wZcB5uJ0aQmE8sV2nP4xK7rL1tY9';

async function checkModels() {
  try {
    const response = await fetch(`${baseUrl}/models`, {
      headers: { 'Authorization': `Bearer ${apiKey}` }
    });
    const data = await response.json();
    console.log('Status:', response.status);
    console.log('Models JSON:', JSON.stringify(data));
  } catch (error) {
    console.error('Error:', error.message);
  }
}

checkModels();
