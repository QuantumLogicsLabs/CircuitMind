"""
CircuitMind - Diagnose Module
diagnose/test_cases.py

Test cases for diagnose_module.py
"""

from diagnose_module import diagnose_circuit
import json

test_cases = [
    {
        "test_id": "TC01",
        "description": "Valid LED circuit — should pass with no issues",
        "input": {
            "circuit_name": "Valid LED Circuit",
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"]
        },
        "expected_passed": True,
        "expected_issues": []
    },
    {
        "test_id": "TC02",
        "description": "LED without resistor — should warn",
        "input": {
            "circuit_name": "LED Without Resistor",
            "components": ["battery", "led"],
            "connections": ["battery -> led"]
        },
        "expected_passed": False,
        "expected_issues": ["Warning"]
    },
    {
        "test_id": "TC03",
        "description": "No power source — should error",
        "input": {
            "circuit_name": "No Power Source",
            "components": ["resistor", "led"],
            "connections": ["resistor -> led"]
        },
        "expected_passed": False,
        "expected_issues": ["Error"]
    },
    {
        "test_id": "TC04",
        "description": "Short circuit 2 nodes — should error",
        "input": {
            "circuit_name": "Short Circuit 2 Nodes",
            "components": ["battery", "ground"],
            "connections": ["battery -> ground"]
        },
        "expected_passed": False,
        "expected_issues": ["Error"]
    },
    {
        "test_id": "TC05",
        "description": "Short circuit 3 nodes — should error",
        "input": {
            "circuit_name": "Short Circuit 3 Nodes",
            "components": ["battery", "wire", "ground"],
            "connections": ["battery -> wire -> ground"]
        },
        "expected_passed": False,
        "expected_issues": ["Error"]
    },
    {
        "test_id": "TC06",
        "description": "Short circuit 4 nodes — should error",
        "input": {
            "circuit_name": "Short Circuit 4 Nodes",
            "components": ["battery", "node1", "node2", "gnd"],
            "connections": ["battery -> node1 -> node2 -> gnd"]
        },
        "expected_passed": False,
        "expected_issues": ["Error"]
    },
    {
        "test_id": "TC07",
        "description": "No connections — should error",
        "input": {
            "circuit_name": "Empty Connections",
            "components": ["battery", "resistor", "led"],
            "connections": []
        },
        "expected_passed": False,
        "expected_issues": ["Error"]
    },
    {
        "test_id": "TC08",
        "description": "Floating component — should warn",
        "input": {
            "circuit_name": "Floating Motor",
            "components": ["battery", "resistor", "led", "motor"],
            "connections": ["battery -> resistor -> led"]
        },
        "expected_passed": False,
        "expected_issues": ["Warning"]
    },
    {
        "test_id": "TC09",
        "description": "Capacitor without polarity — should info",
        "input": {
            "circuit_name": "Capacitor No Polarity",
            "components": ["battery", "resistor", "capacitor"],
            "connections": ["battery -> resistor -> capacitor"]
        },
        "expected_passed": False,
        "expected_issues": ["Info"]
    },
    {
        "test_id": "TC10",
        "description": "LED with npn_transistor — should pass",
        "input": {
            "circuit_name": "LED with NPN Transistor",
            "components": ["battery", "npn_transistor", "led"],
            "connections": ["battery -> npn_transistor -> led"]
        },
        "expected_passed": True,
        "expected_issues": []
    },
    {
        "test_id": "TC11",
        "description": "LED with pnp_transistor — should pass",
        "input": {
            "circuit_name": "LED with PNP Transistor",
            "components": ["battery", "pnp_transistor", "led"],
            "connections": ["battery -> pnp_transistor -> led"]
        },
        "expected_passed": True,
        "expected_issues": []
    },
]


def run_tests():
    results = []
    passed_count = 0
    failed_count = 0

    print("\n" + "=" * 60)
    print("  CircuitMind — Diagnose Module Test Suite")
    print("=" * 60)

    for tc in test_cases:
        result = diagnose_circuit(tc["input"])
        actual_passed = result["passed"]
        expected_passed = tc["expected_passed"]

        issues_ok = True
        for expected_type in tc["expected_issues"]:
            if not any(expected_type in issue for issue in result["issues"]):
                issues_ok = False

        test_passed = (actual_passed == expected_passed) and issues_ok
        status = "PASS" if test_passed else "FAIL"

        if test_passed:
            passed_count += 1
        else:
            failed_count += 1

        print(f"\n[{tc['test_id']}] {'✅' if test_passed else '❌'} {status} — {tc['description']}")
        if not test_passed:
            print(f"  Expected passed={expected_passed}, Got passed={actual_passed}")
            print(f"  Issues: {result['issues']}")

        results.append({
            "test_id":       tc["test_id"],
            "description":   tc["description"],
            "status":        status,
            "input":         tc["input"],
            "actual_issues": result["issues"],
            "passed":        result["passed"]
        })

    print("\n" + "=" * 60)
    print(f"  Results: {passed_count} passed, {failed_count} failed out of {len(test_cases)} tests")
    print("=" * 60)

    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n  Results saved to test_results.json\n")

    return results


if __name__ == "__main__":
    run_tests()
