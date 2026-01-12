#!/usr/bin/env python3
"""Extract impl symbols for neg() and mul() from SCIP JSON files.

This script analyzes SCIP index files (in JSON format) to find impl-related
symbols and detect collisions where multiple impl blocks produce the same
symbol string.
"""

import argparse
import json
import os
import sys
from collections import defaultdict


def extract_impl_symbols(json_file, patterns=None, functions_only=True):
    """Extract impl-related symbols from a SCIP JSON file with line numbers.
    
    Args:
        json_file: Path to the SCIP JSON file
        patterns: List of patterns to search for (default: ['neg', 'mul'])
        functions_only: If True, only match function symbols ending in '().'
    
    Returns:
        tuple: (symbol_lines dict, error_message or None)
    """
    if patterns is None:
        patterns = ['neg', 'mul']
    
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
            # Look for impl symbols containing any of the patterns
            if any(p in s.lower() for p in patterns) and '#' in s:
                # Skip local variables, test functions, and core library
                if s.startswith('local ') or 'tests/' in s or '/core ' in s:
                    continue
                # Optionally filter to just function symbols (ending in parentheses)
                if functions_only and not s.endswith('().'):
                    continue
                matching_symbols.add(s)
    
    # Second pass: find line numbers for symbol occurrences
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
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  %(prog)s index.json

  # Compare multiple files
  %(prog)s index-ra.json index-va.json

  # Search for different patterns
  %(prog)s --pattern add --pattern sub index.json

  # Include non-function symbols (Output types, etc.)
  %(prog)s --all index.json

Converting SCIP to JSON:
  scip print --json index.scip > index.json

What this script detects:
  - Symbol collisions: Multiple impl blocks producing the same symbol
  - Missing type info: impl for &Type producing different symbol than impl for Type
  - Format differences: Between different SCIP generators (rust-analyzer vs verus-analyzer)
""",
    )
    
    parser.add_argument(
        'files',
        metavar='JSON_FILE',
        nargs='+',
        help='SCIP JSON file(s) to analyze',
    )
    
    parser.add_argument(
        '-p', '--pattern',
        action='append',
        dest='patterns',
        metavar='PATTERN',
        help='Pattern to search for in symbol names (default: neg, mul). Can be specified multiple times.',
    )
    
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        dest='all_symbols',
        help='Include all matching symbols, not just functions (ending in "().")',
    )
    
    args = parser.parse_args()
    
    patterns = args.patterns if args.patterns else ['neg', 'mul']
    functions_only = not args.all_symbols
    
    exit_code = 0
    
    for json_file in args.files:
        print(f"\n=== {json_file} ===")
        
        symbol_lines, error = extract_impl_symbols(
            json_file,
            patterns=patterns,
            functions_only=functions_only,
        )
        
        if error:
            print(f"ERROR: {error}")
            exit_code = 1
            continue
        
        if not symbol_lines:
            print(f"No matching symbols found (patterns: {', '.join(patterns)}).")
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
