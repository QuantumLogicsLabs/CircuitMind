# Generate Module

**Developer:** M-Haseeb  
**Task:** Convert user text into Circuit JSON

---

## What it does

User types anything like:
- `make me a LED circuit`
- `temperature sensor circuit banao`
- `bluetooth speaker circuit`

Module returns a clean Circuit JSON:

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

---

## How it works

User Input (text)
↓
Validate Input
↓
Try Groq AI (LLM)
↓
Success?
YES → return LLM JSON
NO  → Rule-based Fallback
↓
Clean Circuit JSON always returned
No crashes ever

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get free Groq API Key
- Go to **https://console.groq.com**
- Sign up with Google (free)
- Click API Keys → Create API Key
- Copy your key

### 3. Create `.env` file in root folder
GROQ_API_KEY=your_key_here



### 4. Run tests
```bash
cd generate
python test_manual.py
```

---

## Supported Circuits (rule-based fallback)

| Circuit | Keywords |
|---------|----------|
| LED Circuit | led, light |
| Motor Circuit | motor |
| Buzzer Circuit | buzzer |
| Fan Circuit | fan |
| Temperature Sensor | temperature, sensor |
| Solar Charging | solar |
| 555 Timer | 555, timer |
| RC Filter | rc, filter |

---

## Features

- ✅ Groq AI (Llama 3.3) for smart generation
- ✅ Rule-based fallback — works without internet
- ✅ Input validation — no crashes
- ✅ Safe JSON parsing with try-catch
- ✅ API key loaded from .env — never hardcoded
- ✅ Works on any system with or without API key

---

## Error Handling

| Situation | Result |
|-----------|--------|
| Empty input | Error: Input cannot be empty |
| Too short (< 3 chars) | Error: Input too short |
| Too long (> 1000 chars) | Error: Input too long |
| LLM fails | Rule-based fallback kicks in |
| No API key | Rule-based fallback kicks in |
| Groq not installed | Rule-based fallback kicks in |

---

## Files

| File | Purpose |
|------|---------|
| `generate.py` | Main module code |
| `test_manual.py` | Manual test runner |
| `README.md` | This file |

---

## Progress


- Basic rule-based generate function 
- Input validation, more circuits, confidence score 
- Groq LLM integration, .env support, safe JSON parsing 
