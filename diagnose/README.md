# Diagnose Module
# 🔍 Diagnose Module

The Diagnose Module is part of the CircuitMind project. It takes a circuit in JSON format as input, runs a series of electrical checks, and returns clear error and warning messages if any issues are found.

---

## 📁 File

```
diagnose/
└── diagnose_module.py
```

---

## 🧠 What It Does

Given a circuit JSON, the module checks for the following issues:

| # | Check | Type |
|---|-------|------|
| 1 | Missing power source | Error |
| 2 | LED/Diode without current-limiting component | Warning |
| 3 | No connections defined | Error |
| 4 | Short circuit (power reaches ground with no load) | Error |
| 5 | Floating (disconnected) components | Warning |
| 6 | Capacitor polarity not indicated | Info |

---

## 📥 Input Format

The module accepts a circuit as a Python dictionary (or parsed JSON):

```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `circuit_name` | string | No | Name of the circuit |
| `components` | list of strings | Yes | All components in the circuit |
| `connections` | list of strings | Yes | Connections using `->` or `--` |

---

## 📤 Output Format

The module returns a dictionary:

```python
{
  "circuit_name": "LED Circuit",
  "issues": [],          # list of error/warning strings
  "passed": True         # True if no issues found
}
```

### Issue Prefixes

| Prefix | Meaning |
|--------|---------|
| `Error:` | Critical problem — circuit will not work |
| `Warning:` | Potential problem — circuit may be damaged |
| `Info:` | Suggestion — good practice to follow |

---

## 💡 Supported Components

### Power Sources
`battery`, `power_supply`, `solar_cell`

### Current Limiters
`resistor`, `potentiometer`, `mosfet`, `transistor`, `npn_transistor`, `pnp_transistor`

### Components Needing Current Limit
`led`, `diode`, `zener_diode`

---

## 🔌 Usage

```python
from diagnose_module import diagnose_circuit, pretty_print

circuit = {
    "circuit_name": "LED Circuit",
    "components": ["battery", "led"],
    "connections": ["battery -> led"]
}

result = diagnose_circuit(circuit)
pretty_print(result)
```

### Output

```
============================================================
Diagnosing: LED Circuit
------------------------------------------------------------
⚠️  Warning: 'led' detected without a current-limiting component. Add a resistor to prevent burnout.
```

---

## ✅ Example Test Cases

### 1 — Valid Circuit (No Issues)
```python
{
  "circuit_name": "Valid LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
# Output: ✅ No issues found. Circuit looks valid.
```

### 2 — LED Without Resistor
```python
{
  "circuit_name": "LED Without Resistor",
  "components": ["battery", "led"],
  "connections": ["battery -> led"]
}
# Output: ⚠️ Warning: 'led' detected without a current-limiting component.
```

### 3 — Short Circuit (Multi-Node)
```python
{
  "circuit_name": "Short Circuit",
  "components": ["battery", "wire", "ground"],
  "connections": ["battery -> wire -> ground"]
}
# Output: ❌ Error: Short circuit detected — power reaches ground with no load.
```

### 4 — No Power Source
```python
{
  "circuit_name": "No Power",
  "components": ["resistor", "led"],
  "connections": ["resistor -> led"]
}
# Output: ❌ Error: No power source found. Add a battery or power supply.
```

---

## ⚙️ How Short Circuit Detection Works

Unlike a simple 2-node check, this module uses a **BFS (Breadth-First Search)** algorithm to detect short circuits across paths of any length:

```
battery -> ground              ✅ detected (2 nodes)
battery -> wire -> ground      ✅ detected (3 nodes)
battery -> n1 -> n2 -> gnd    ✅ detected (4+ nodes)
```

Pure wire/net labels (`wire`, `node`, `net`, `trace`) are not counted as load components.

---

## 🔗 Consistency with Explain Module

This module shares the same constants as `explain/explain_module.py`:

```python
POWER_SOURCES       = {"battery", "power_supply", "solar_cell"}
NEEDS_CURRENT_LIMIT = {"led", "diode", "zener_diode"}
CURRENT_LIMITERS    = {"resistor", "potentiometer", "mosfet", "transistor",
                       "npn_transistor", "pnp_transistor"}
```

Component names use **underscore** format: `op_amp`, `npn_transistor`, `power_supply`.

---

## 👤 Author

Ubaidullah — CircuitMind Internship, Quantum Logics Labs
