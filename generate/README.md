# Generate Module

**Developer:** M-Haseeb  
**Task:** Convert user text into Circuit JSON

## What it does
User types: `make me a LED circuit`  
Module returns:
```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"],
  "confidence": "high",
  "description": "Basic LED circuit with current limiting resistor",
  "source": "llm"
}
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Groq API Key

Get your free API key from: https://console.groq.com

**Windows:**
```bash
set GROQ_API_KEY=your_key_here
```

**Mac/Linux:**
```bash
export GROQ_API_KEY=your_key_here
```

### 3. Run
```bash
cd generate
python test_manual.py
```

## How it works
1. User input is validated first
2. Groq AI (Llama 3.3) generates circuit JSON
3. If LLM fails → rule-based fallback kicks in automatically
4. Clean JSON is returned every time — no crashes

## Supported Circuits (rule-based fallback)
- LED Circuit
- Motor Circuit
- Buzzer Circuit
- Fan Circuit
- Temperature Sensor Circuit
- Solar Charging Circuit
