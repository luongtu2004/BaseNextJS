const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Sample Route
app.get('/', (req, res) => {
  res.json({ message: 'Welcome to the Node.js Backend API' });
});

// Health Check
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
