"""Run make_laychain over many targets, skipping layouts that hang the game.

  python tools/rt/run_laychain.py <outdir> "<table:first-last,...>" [chunk]

Runs Mesen in chunks (default 25 targets, 120 s). If a chunk stops early, the next target is
recorded as HANG in <outdir>/hang.txt and the run continues after it.
"""
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
outdir, spec = sys.argv[1:3]
chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 25
targets = []
for part in spec.split(','):
    t, r = part.split(':')
    a, b = r.split('-')
    targets += [(int(t), k) for k in range(int(a), int(b) + 1)]
os.makedirs(outdir, exist_ok=True)
done_log = open(os.path.join(outdir, 'all.txt'), 'w')
hang = open(os.path.join(outdir, 'hang.txt'), 'w')
i = 0
while i < len(targets):
    part = targets[i:i + chunk]
    sub = os.path.join(outdir, 'part')
    lua = os.path.join(ROOT, 'tools', 'rt', '_laypart.lua')
    spec2 = ','.join('%d:%d-%d' % (t, k, k) for t, k in part)
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'rt', 'make_laychain.py'), outdir, lua, spec2],
                   check=True, capture_output=True)
    open(os.path.join(outdir, 'lay.txt'), 'w').close()
    subprocess.run([os.path.join(ROOT, 'tools', 'mesen', 'Mesen.exe'), '--testrunner', '--timeout=120',
                    os.environ.get('LAYROM', os.path.join(ROOT, 'out', 'srw3_auto.smc')), lua], cwd=ROOT)
    got = [l.split()[0] for l in open(os.path.join(outdir, 'lay.txt'), encoding='utf-8') if l.endswith(('\n',)) and l[0].isdigit()]
    for l in open(os.path.join(outdir, 'lay.txt'), encoding='utf-8'):
        if l[0].isdigit():
            done_log.write(l)
    done_log.flush()
    n = len(got)
    if n < len(part):
        t, k = part[n]
        hang.write('%d_%02X\n' % (t, k)); hang.flush()
        print('hang at %d_%02X' % (t, k), flush=True)
        i += n + 1
    else:
        i += n
    print('%d/%d' % (i, len(targets)), flush=True)
