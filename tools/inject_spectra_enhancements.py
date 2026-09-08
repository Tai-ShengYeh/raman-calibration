from pathlib import Path

FILES = [
    Path('raman_calibration_tutorial.html'),
    Path('raman_calibration_unit1b.html'),
    Path('raman_food_additives_tutorial.html'),
]
CSS = '<link rel="stylesheet" href="spectra-enhance.css">'
JS = '<script src="spectra-enhance.js" defer></script>'

for path in FILES:
    text = path.read_text(encoding='utf-8')
    original = text
    if 'spectra-enhance.css' not in text:
        text = text.replace('</head>', CSS + '\n</head>', 1)
    if 'spectra-enhance.js' not in text:
        text = text.replace('</body>', JS + '\n</body>', 1)
    if text != original:
        path.write_text(text, encoding='utf-8')
        print('updated', path)
    else:
        print('already enhanced', path)
