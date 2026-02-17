import json

cov = json.load(open('coverage.json'))

# Get source files
src_files = [(f, d['summary']) for f, d in cov['files'].items() if f.startswith('src')]

src_files.sort(key=lambda x: x[1]['percent_covered'])

print(f'Total source files: {len(src_files)}')
total_covered = sum(s[1]['covered_lines'] for s in src_files)
total_statements = sum(s[1]['num_statements'] for s in src_files)
print(f'Source coverage: {total_covered/max(total_statements,1)*100:.1f}%')
print()

# Group by module
modules = {}
for f, s in src_files:
    parts = f.replace('/', '\\').split('\\')
    if len(parts) > 1 and parts[0] == 'src':
        module = parts[1] if len(parts) > 2 else 'root'
        if module not in modules:
            modules[module] = {'covered': 0, 'total': 0, 'files': 0}
        modules[module]['covered'] += s['covered_lines']
        modules[module]['total'] += s['num_statements']
        modules[module]['files'] += 1

print('=== COVERAGE BY MODULE ===')
for module in sorted(modules.keys(), key=lambda m: modules[m]['covered']/max(modules[m]['total'],1)):
    m = modules[module]
    pct = m['covered'] / max(m['total'], 1) * 100
    status = 'FAIL' if pct < 80 else 'OK  '
    print(f'{module:20s}: {pct:5.1f}% ({m["covered"]:4d}/{m["total"]:4d} lines, {m["files"]:2d} files) [{status}]')

print('\n=== UNCOVERED CRITICAL FILES (<50%) ===')
uncovered = [(f, s) for f, s in src_files if s['percent_covered'] < 50]
for f, s in uncovered[:15]:
    print(f'{s["percent_covered"]:5.1f}% - {f}')
