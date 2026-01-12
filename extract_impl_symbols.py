#!/usr/bin/env python3
"""Extract impl symbols for neg() and mul() from SCIP JSON files."""

import json
import os
import sys
from collections import defaultdict


def extract_impl_symbols(json_file, functions_only=True):
    """Extract impl-related symbols from a SCIP JSON file with line numbers.
    
    Returns:
        tuple: (symbol_lines dict, error_message or None)
    """
    # Check if file exists
    if not os.path.exists(json_file):
        return None, f"File not found: {json_file}"
    
    # Check if file is empty
    if os.path.getsize(json_file) == 0:
        return None, f"File is empty: {json_file}"
    
    # Try to load JSON
    try:
        with open(json_file) as f:
            # Peek at first few bytes to detect non-JSON content
            first_bytes = f.read(100)
            f.seek(0)
            
            # Check for ANSI escape codes (colored debug output)
            if '\x1b[' in first_bytes or '[0m' in first_bytes:
                return None, (
                    f"File contains ANSI escape codes (not valid JSON): {json_file}\n"
                    "  This looks like colored debug output, not JSON.\n"
                    "  Try: scip print --json <file.scip> > output.json"
                )
            
            # Check for Go-style struct output
            if first_bytes.startswith('&scip.'):
                return None, (
                    f"File contains Go struct format (not valid JSON): {json_file}\n"
                    "  This looks like 'scip print' output without --json flag.\n"
                    "  Try: scip print --json <file.scip> > output.json"
                )
            
            data = json.load(f)
            
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {json_file}: {e}"
    except PermissionError:
        return None, f"Permission denied: {json_file}"
    except Exception as e:
        return None, f"Error reading {json_file}: {e}"
    
    # Validate expected structure
    if not isinstance(data, dict):
        return None, f"Expected JSON object, got {type(data).__name__}: {json_file}"
    
    if 'documents' not in data:
        return None, f"Missing 'documents' key in JSON (not a SCIP file?): {json_file}"
    
    # First pass: collect matching symbols
    matching_symbols = set()
    for doc in data.get('documents', []):
        for sym in doc.get('symbols', []):
            s = sym.get('symbol', '')
            # Look for impl symbols containing neg or mul
            if ('neg' in s.lower() or 'mul' in s.lower()) and '#' in s:
                # Skip local variables, test functions, and core library
                if s.startswith('local ') or 'tests/' in s or '/core ' in s:
                    continue
                # Optionally filter to just function symbols (ending in parentheses)
                if functions_only and not s.endswith('().'):
                    continue
                matching_symbols.add(s)
    
    # Second pass: find line numbers for symbol DEFINITIONS only (not references)
    # Look for lines with "symbol": "..." pattern
    symbol_lines = defaultdict(list)
    with open(json_file) as f:
        for line_num, line in enumerate(f, 1):
            if '"symbol":' not in line:
                continue
            for symbol in matching_symbols:
                if f'"{symbol}"' in line:
                    symbol_lines[symbol].append(line_num)
    
    return symbol_lines, None


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_impl_symbols.py <json_file> [json_file2 ...]")
        print("\nExtracts impl-related symbols (neg/mul) from SCIP JSON files.")
        print("Use 'scip print --json <file.scip>' to convert .scip to JSON first.")
        sys.exit(1)
    
    exit_code = 0
    
    for json_file in sys.argv[1:]:
        print(f"\n=== {json_file} ===")
        
        symbol_lines, error = extract_impl_symbols(json_file)
        
        if error:
            print(f"ERROR: {error}", file=sys.stderr)
            exit_code = 1
            continue
        
        if not symbol_lines:
            print("No matching symbols found (neg/mul impl functions).")
            continue
        
        # Count how many impl blocks produce each symbol
        for s in sorted(symbol_lines.keys()):
            lines = symbol_lines[s]
            first_line = lines[0]
            # For duplicates, show all lines where the same symbol is defined
            if len(lines) > 2:  # More than expected (def + metadata)
                # This means the same symbol string is used for multiple impls
                print(f"L{first_line}: {s}  (DUPLICATE! also at L{', '.join(str(l) for l in lines[1:])})")
            else:
                print(f"L{first_line}: {s}")
        
        unique_symbols = len(symbol_lines)
        print(f"\nUnique symbols: {unique_symbols}")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
