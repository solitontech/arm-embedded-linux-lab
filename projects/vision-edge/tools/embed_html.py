#!/usr/bin/env python3
"""Convert a file to a C header with an embedded byte array."""
import sys

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input> <output.h>", file=sys.stderr)
        sys.exit(1)

    data = open(sys.argv[1], 'rb').read()
    with open(sys.argv[2], 'w') as f:
        f.write('// Auto-generated from web/dashboard.html — do not edit.\n')
        f.write('static const unsigned char dashboard_html[] = {\n')
        for i in range(0, len(data), 12):
            chunk = ', '.join('0x%02x' % b for b in data[i:i+12])
            f.write(f'  {chunk},\n')
        f.write('};\n')
        f.write(f'static const unsigned int dashboard_html_len = {len(data)};\n')

if __name__ == '__main__':
    main()
