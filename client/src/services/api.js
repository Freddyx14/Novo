const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const analyzeProfile = async (profile) => {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ profile }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.details || 'Failed to analyze profile');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};
