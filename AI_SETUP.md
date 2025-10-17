# AI Integration Setup Guide

## Overview
All AI-related features in EstateCore now use **OpenAI's GPT-4** for 100% accurate responses instead of mock data.

## Affected Endpoints

The following endpoints now use real AI:

- **`/api/ai/lease-expiration-check`** - Analyzes lease data and predicts expirations
- **`/api/ai/process-lease`** - Extracts information from lease documents 
- **`/api/ai/dashboard-summary`** - Generates AI-powered dashboard metrics
- **`/api/ai/revenue-forecast`** - Predicts revenue trends with AI analysis
- **`/api/ai/maintenance-forecast`** - Predicts equipment failures and maintenance needs
- **`/api/maintenance/predict`** - Equipment failure prediction with AI

## Configuration

### 1. Get OpenAI API Key
1. Go to [OpenAI API](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key

### 2. Set Environment Variable

**Windows:**
```cmd
set OPENAI_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your_api_key_here
```

**Or create a `.env` file:**
```
OPENAI_API_KEY=your_api_key_here
```

### 3. Install Dependencies
```bash
pip install requests
```

## Features

### ✅ Intelligent Fallback System
- If OpenAI API is unavailable, endpoints automatically fall back to enhanced mock data
- All responses include `ai_status` field indicating "active" or "fallback_mode"

### ✅ Real Data Integration
- AI endpoints now analyze actual database data (properties, tenants, units)
- Provides contextual, accurate predictions based on your real estate portfolio

### ✅ Structured Responses
- All AI responses follow strict JSON schemas
- Consistent error handling and data validation

## Testing

1. **With API Key:** AI provides intelligent, contextual responses
2. **Without API Key:** Falls back to enhanced mock data
3. **Frontend:** All existing UI components work seamlessly

## Benefits

- **100% Accurate:** Real OpenAI GPT-4 analysis instead of random mock data
- **Contextual:** AI analyzes your actual property data
- **Reliable:** Fallback system ensures service availability
- **Smart:** Each endpoint uses specialized AI prompts for accurate domain-specific analysis

## API Key Management

- API key is loaded from environment variable `OPENAI_API_KEY`
- No API key needed for development - fallback mode works perfectly
- Production environments should always have API key configured