/**
 * Centralized AI Server Configuration
 * Handles environment variables with defaults for consistency across API routes.
 */
export const AI_CONFIG = {
  baseUrl: process.env.AI_BASE_URL || 'http://113.160.201.164:8003/v1',
  apiKey: process.env.AI_API_KEY,
  model: process.env.AI_MODEL || 'local-pro',
};
