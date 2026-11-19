"""python tr/fill_runs.py tr/lay00_runs.txt tr/lay00_ko.txt
Put one KO per line (same order as runs file; '=' keeps JP) into column 5.
If the JP run ends with spaces (alignment), pad KO with spaces up to the JP width."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from layruns import width
runs = [l.rstrip('\n').split('\t') for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
ko = [l.rstrip('\n') for l in open(sys.argv[2], encoding='utf-8')]
ko = [k for k in ko if k != '']
assert len(ko) == len(runs), (len(ko), len(runs))
out = []
for r, k in zip(runs, ko):
    r = r[:4]
    if k == '=':
        k = ''
    elif r[2].endswith(' ') or r[2].startswith(' '):
        lead = ' ' if r[2].startswith(' ') and not k.startswith(' ') else ''
        k = lead + k
        while width(k) + 8 <= int(r[3]):
            k += ' '
    out.append('\t'.join(r + [k]))
open(sys.argv[1], 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
