"""Join spaced technique names in dialogue so they match the weapon tables (sys13, sys14-15-16).

  python tr/join_names.py            # report only
  python tr/join_names.py --apply    # rewrite KO: lines in script/dlg*.txt and tr/dlg*.tsv
Matches a weapon name with one or more single spaces between its letters (not across {n}).
Only names of 4+ letters are used, to avoid false hits.
"""
import glob, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def names():
    out = set()
    for f in ('script/sys13.txt', 'script/sys14-15-16.txt'):
        for line in open(f, encoding='utf-8'):
            if line.startswith('KO:'):
                n = line[3:].strip().replace('{END}', '')
                if len(n) >= 4 and ' ' not in n and '{' not in n:
                    out.add(n)
    return sorted(out, key=len, reverse=True)

def pattern(n):
    return re.compile(' ?'.join(re.escape(c) for c in n))

def main():
    apply = '--apply' in sys.argv
    pats = [(n, pattern(n)) for n in names()]
    hits = {}
    files = sorted(glob.glob('script/dlg*.txt')) + sorted(glob.glob('tr/dlg*.tsv'))
    for f in files:
        lines = open(f, encoding='utf-8').read().split('\n')
        changed = False
        for i, line in enumerate(lines):
            if f.endswith('.txt') and not line.startswith('KO:'):
                continue
            new = line
            for n, p in pats:
                def rep(m):
                    s = m.group(0)
                    if ' ' in s:
                        hits.setdefault(s, set()).add(n)
                        return n
                    return s
                new = p.sub(rep, new)
            if new != line:
                changed = True
                lines[i] = new
        if apply and changed:
            open(f, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
    for s, ns in sorted(hits.items()):
        print(f'{s!r} -> {sorted(ns)}')
    print(len(hits), 'distinct spaced forms')

main()
