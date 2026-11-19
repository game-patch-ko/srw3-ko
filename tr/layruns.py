"""Translate window-layout segments run by run, keeping every tag from JP.

  python tr/layruns.py export lay00 > tr/lay00_runs.txt
      one line per text run that contains kana/kanji:  LABEL<TAB>runno<TAB>JP run<TAB>widthpx<TAB>
      (fill the 5th column with Korean; leave it empty to keep the JP run)
  python tr/layruns.py build tr/lay00_runs.txt tr/lay00.tsv
      writes label<TAB>KO segment lines (JP with the runs replaced) and reports runs wider than JP
A run is the text between two tags; {n} splits runs.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TAG = re.compile(r'(\{[^}]*\})')
JPCH = re.compile(r'[ぁ-ヿ一-鿿]')


def todo(name, all_segments=False):
    """(label, JP) pairs; export uses untranslated ones only, build uses every segment"""
    if not all_segments:
        out = subprocess.run([sys.executable, os.path.join(HERE, 'export_todo.py'), name], capture_output=True).stdout
        return [l.split('\t', 1) for l in out.decode('utf-8').splitlines()]
    res, lab = [], None
    for ln in open(os.path.join(HERE, '..', 'script', name + '.txt'), encoding='utf-8'):
        m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
        if m:
            lab = m.group(1)
        elif ln.startswith('JP:') and lab:
            res.append([lab, ln[4:].rstrip('\n')])
    return res


def width(s):
    return sum(12 if ('가' <= c <= '힣' or '一' <= c <= '鿿') else 8 for c in s)


def limits(jp):
    """per run index: room in its window = (F8 width - FC column) * 8px, at least the JP run width"""
    W = None; x = 0; out = {}
    for i, p in enumerate(TAG.split(jp)):
        if i % 2:
            m = re.fullmatch(r'\{F8:([0-9A-F]{2}):[^}]*\}', p)
            if m:
                W = int(m.group(1), 16); x = 0
            m = re.fullmatch(r'\{FC:([0-9A-F]{2}):([0-9A-F]{2})\}', p)
            if m:
                v = int(m.group(1), 16); x = v if v < 0x80 else 0
        else:
            room = (W - x) * 8 if W is not None else 0
            out[i] = max(room, width(p))
    return out


def runs(jp):
    parts = TAG.split(jp)
    return [(i, p) for i, p in enumerate(parts) if i % 2 == 0 and JPCH.search(p)], parts


def main():
    if sys.argv[1] == 'export':
        for lab, jp in todo(sys.argv[2]):
            rs, _ = runs(jp)
            for i, p in rs:
                sys.stdout.buffer.write(('%s\t%d\t%s\t%d\t\n' % (lab, i, p, width(p))).encode('utf-8'))
    else:
        src, dst = sys.argv[2], sys.argv[3]
        name = re.match(r'(lay[0-9A-F]+)', os.path.basename(src)).group(1)
        jpmap = dict(todo(name, all_segments=True))
        rep = {}
        for ln in open(src, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip():
                continue
            lab, i, jprun, w, ko = (ln.split('\t') + [''])[:5]
            if ko:
                rep.setdefault(lab, {})[int(i)] = (jprun, ko)
        rows = []
        for lab, jp in jpmap.items():
            if lab not in rep:
                continue
            _, parts = runs(jp)
            lim = limits(jp)
            for i, (jprun, ko) in rep[lab].items():
                assert parts[i] == jprun, (lab, i, parts[i], jprun)
                if width(ko) > lim[i]:
                    print('OVER window %3d > %3d  %s  %s -> %s' % (width(ko), lim[i], lab, jprun, ko))
                parts[i] = ko
            rows.append(lab + '\t' + ''.join(parts))
        open(dst, 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
        print(len(rows), 'rows')


if __name__ == '__main__':
    main()
