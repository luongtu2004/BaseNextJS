import fetch from 'node-fetch';

const baseUrl = 'http://113.160.201.164:4020/api/agent-openai/v1';
const apiKey = 'ask_IT-THANG_9f1fa5b24b88525fde7917c2f0dcce961a0e';

async function checkModels() {
  try {
    const response = await fetch(`${baseUrl}/models`, {
      headers: { 'Authorization': `Bearer ${apiKey}` }
    });
    const data = await response.json();
    console.log('Status:', response.status);
    console.log('Models:', JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('Error:', error.message);
  }
}

checkModels();
