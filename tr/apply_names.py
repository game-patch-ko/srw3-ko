"""Pair tr/<sys>.txt lines (one per non-empty name, '=' keeps original) with script order and write KO lines."""
import re, sys
sys.path.insert(0, 'build')
import setko
pairs = []
for f in ('sys10', 'sys11', 'sys12'):
    segs = []; l = None
    for ln in open('script/%s.txt' % f, encoding='utf-8'):
        m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
        if m: l = m.group(1)
        elif ln.startswith('JP:'):
            jp = ln[4:].rstrip('\n').replace('{END}', '')
            if jp and jp != 'ーーーー': segs.append((l, jp))
    ko = [x.rstrip('\n') for x in open('tr/%s.txt' % f, encoding='utf-8') if x.strip()]
    assert len(ko) == len(segs), (f, len(ko), len(segs))
    for (l, jp), k in zip(segs, ko):
        if '-v' in sys.argv: print(f, l, jp, '=>', k)
        pairs.append((l, '' if k == '=' else k + '{END}'))
setko.set_many(pairs)
