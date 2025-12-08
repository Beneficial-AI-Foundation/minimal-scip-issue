#!/usr/bin/env python3
"""Extract impl symbols for neg() and mul() from SCIP JSON files."""

import json
import re
import sys
from collections import defaultdict

def extract_impl_symbols(json_file, functions_only=True):
    """Extract impl-related symbols from a SCIP JSON file with line numbers."""
    with open(json_file) as f:
        data = json.load(f)
    
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
    
    return symbol_lines

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_impl_symbols.py <json_file> [json_file2 ...]")
        sys.exit(1)
    
    for json_file in sys.argv[1:]:
        print(f"\n=== {json_file} ===")
        symbol_lines = extract_impl_symbols(json_file)
        
        # Count how many impl blocks produce each symbol
        # Each impl block should have exactly one definition, so count first occurrences
        symbol_count = {s: len(lines) for s, lines in symbol_lines.items()}
        
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

if __name__ == '__main__':
    main()

