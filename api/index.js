const express = require('express');
const cors = require('cors');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();

app.use(cors());
app.use(express.json());

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

app.post('/api/analyze', async (req, res) => {
  try {
    const { profile } = req.body;

    if (!profile) {
      return res.status(400).json({ error: 'Profile data is required' });
    }

    const prompt = `Analyze the following student profile and provide personalized recommendations for university opportunities in Mexico:

Student Profile:
- Academic Level: ${profile.academicLevel}
- Field of Study: ${profile.fieldOfStudy}
- GPA: ${profile.gpa}
- Interests: ${profile.interests}
- Skills: ${profile.skills}
- Career Goals: ${profile.careerGoals}
- Location Preference: ${profile.locationPreference}
- Budget: ${profile.budget}

Please provide:
1. Top 5 recommended universities in Mexico with brief explanations
2. Relevant scholarship opportunities
3. Career pathway suggestions
4. Skills to develop
5. Networking opportunities

Format the response in a clear, structured way.`;

    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 2048,
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    });

    const recommendations = message.content[0].text;

    res.json({
      recommendations,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error analyzing profile:', error);
    res.status(500).json({
      error: 'Failed to analyze profile',
      details: error.message,
    });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

module.exports = app;
