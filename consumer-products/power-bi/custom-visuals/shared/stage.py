"""Stage a built private visual into the source PBIP and an isolated QA copy.

Staging is additive: each visual registers its own resource package, so several
visuals accumulate in the same report without displacing one another.
"""
import json
import shutil
import zipfile
from pathlib import Path

from nexus_build import DELIVERY, PBIP, POWERBI, REPORT

C2_PLACEHOLDER = 'C:\\C2\\Q-FINANCE-C2-V1'


def stage(here, qa_folder):
    packages = list((Path(here) / 'dist').glob('*.pbiviz'))
    assert len(packages) == 1, 'Build exactly one visual package first.'
    with zipfile.ZipFile(packages[0]) as z:
        package = json.loads(z.read('package.json'))
        guid = package['visual']['guid']
        target = REPORT / 'CustomVisuals' / guid
        target.mkdir(parents=True, exist_ok=True)
        for member in z.namelist():
            destination = (target / member).resolve()
            assert destination.is_relative_to(target.resolve()), 'Unsafe archive path'
        z.extractall(target)
    metadata = list((target / 'resources').glob('*.pbiviz.json'))
    assert len(metadata) == 1
    p = REPORT / 'definition/report.json'
    r = json.loads(p.read_text())
    r['resourcePackages'] = [v for v in r['resourcePackages'] if v['name'] != guid] + [
        {'name': guid, 'type': 'CustomVisual', 'items': [{'name': metadata[0].name, 'path': metadata[0].name, 'type': 'CustomVisualMetadata'}]}]
    p.write_text(json.dumps(r, indent=2) + '\n')
    qa = POWERBI / 'work' / qa_folder
    registered = {pkg['name'] for pkg in r['resourcePackages'] if pkg['type'] == 'CustomVisual'}

    def ignore(path, names):
        if Path(path) == REPORT / 'CustomVisuals':
            return set(names) - registered
        return {'.pbi'} & set(names)

    shutil.copytree(PBIP, qa, dirs_exist_ok=True, ignore=ignore)
    p = qa / 'NexusFinance.SemanticModel/definition/expressions.tmdl'
    p.write_text(p.read_text().replace(C2_PLACEHOLDER, str(DELIVERY)))
    return qa / 'NexusFinance.pbip'
