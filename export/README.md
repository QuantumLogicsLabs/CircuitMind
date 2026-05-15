# Export Module

## What This Module Does
Takes circuit JSON as input and converts it into:
- Structured JSON output
- SPICE netlist format (.sp file)
- Readable text format (.txt file)

## Input Format
```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
```

## Output Format
```json
{
  "status": "success",
  "circuit_name": "LED Circuit",
  "components": "battery, resistor, led",
  "connections": "battery → resistor → led",
  "spice_netlist": "LED Circuit\nV1 1 2 9V\nR2 2 3 330ohm\nD3 3 4 LED\n.end"
}
```

## SPICE Netlist Output
LED Circuit
V1 1 2 9V
R2 2 3 330ohm
D3 3 4 LED
.end
## Component Mapping
| Component | SPICE Symbol | Value |
|-----------|-------------|-------|
| battery | V | 9V |
| resistor | R | 330ohm |
| led | D | LED |
| capacitor | C | 100uF |
| switch | S | SW |
| motor | M | MOTOR |

## Error Handling
| Case | Response |
|------|----------|
| Empty input | status: error |
| Invalid JSON | status: error |
| Missing fields | status: error |

## Files
| File | Purpose |
|------|---------|
| export-module.py | Main export logic |
| testcases.py | 5 test circuits |
| TestResults.json | Saved test outputs |

## How to Use
```python
from export_module import export_module

result = export_module(json_input, save_to_file=True)
print(result)
```

## Test Cases Covered
1. LED Circuit
2. Motor Circuit
3. Fan Circuit
4. Empty input (error)
5. Invalid JSON (error)
