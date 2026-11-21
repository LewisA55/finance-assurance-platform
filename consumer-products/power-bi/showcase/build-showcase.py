"""Complete the native Cover and Objective pages over the checked-in artwork."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'custom-visuals' / 'shared'))
import nexus_build as nb

COVER = 'a94cf4bc9826f41a6f51'
OBJECTIVE = '8f6b87377994a7e133fc'
FINANCIAL = '8c5d16b8f8a74d18ac85'
PAGE_ROOT = nb.REPORT / 'definition' / 'pages'


def literal(value):
    return {'expr': {'Literal': {'Value': value}}}


def label(text):
    return literal("'" + text.replace("'", "''") + "'")


def colour(hex_code):
    return {'solid': {'color': label(hex_code)}}


def button(visual_id, title, target, position):
    spec = nb.visual(visual_id, 'actionButton', *position)
    spec['position'].update(z=1000, tabOrder=1000 + position[1] * 1600 + position[0])
    spec['visual']['objects'] = {
        'icon': [{'properties': {'shapeType': label('blank')}, 'selector': {'id': 'default'}}],
        'fill': [
            {'properties': {'show': literal('true')}},
            {'properties': {'fillColor': colour('#1C4661'), 'transparency': literal('0D')},
             'selector': {'id': 'default'}},
        ],
        'outline': [{'properties': {'show': literal('false')}}],
        'text': [
            {'properties': {'show': literal('true')}},
            {'properties': {'text': label(title), 'fontColor': colour('#FFFFFF'),
                            'fontFamily': label('Segoe UI Semibold'), 'fontSize': literal('16D')},
             'selector': {'id': 'default'}},
        ],
    }
    spec['visual']['visualContainerObjects'] = {
        'visualLink': [{'properties': {'show': literal('true'), 'type': label('PageNavigation'),
                                      'navigationSection': label(target)}}],
        'general': [{'properties': {'altText': label(title)}}],
    }
    return spec


def textbox(visual_id, position, lines):
    spec = nb.visual(visual_id, 'textbox', *position)
    spec['visual']['objects'] = {'general': [{'properties': {'paragraphs': [
        {'textRuns': [{'value': text, 'textStyle': {'fontFamily': font, 'fontSize': size, 'color': ink}}]}
        for text, font, size, ink in lines
    ]}}]}
    return spec


nb.write_visual(COVER, button('c8dbf1939f03011fd3de', 'View objective', OBJECTIVE, (86, 694, 218, 56)))
nb.write_visual(COVER, button('3125f4938ee634d2bc77', 'Open report', FINANCIAL, (326, 694, 218, 56)))

page_file = PAGE_ROOT / OBJECTIVE / 'page.json'
page = json.loads(page_file.read_text(encoding='utf-8-sig'))
page['displayOption'] = 'FitToPage'
nb.write_json(page_file, page)

nb.write_visual(OBJECTIVE, textbox('d0fd6d54758477d41585', (86, 214, 1390, 180), [
    ('From financial performance to reporting evidence', 'Georgia', '43px', '#162C43'),
    ('Review Nexus Group results, see what moved cash, and trace reported figures back to their close and reconciliation evidence.',
     'Segoe UI', '22px', '#355064'),
    ('Synthetic data | June 2026 close | Q-FINANCE-C2@v1', 'Segoe UI Semibold', '17px', '#1C4661'),
]))

nb.write_visual(OBJECTIVE, button('c51d83aa468c4cfb8900', 'View report', FINANCIAL, (1322, 62, 192, 56)))
sections = (
    ('3b6960bcb333930b5786', 'd0fd6d54758477d41586', 'Financial results',
     'Compare the income statement, balance sheet and cash flow against the prior month.',
     'Statutory statements', 'c3a9f57e1b6d4a28b904'),
    ('f025a3d414eb91fb51b9', 'd0fd6d54758477d41587', 'Close and controls',
     'Inspect close status, reconciliation results and exposure observations.',
     'Assurance controls', 'd4b82e6a1c7f49538a0d'),
    ('6834855d0538c06b0f5f', 'd0fd6d54758477d41588', 'Data and lineage',
     'Follow declared dataset dependencies through the governed delivery.',
     'Dataset lineage', 'f18d6c40a932e5b74c81'),
)
for index, (text_id, button_id, title, description, action, target) in enumerate(sections):
    x = 86 + index * 483
    nb.write_visual(OBJECTIVE, textbox(text_id, (x, 457, 430, 165), [
        (title, 'Georgia', '28px', '#162C43'),
        (description, 'Segoe UI', '20px', '#355064'),
    ]))
    nb.write_visual(OBJECTIVE, button(button_id, action, target, (x, 635, 245, 56)))

nb.write_visual(OBJECTIVE, button('543cf5e4889d4d7f9e10', 'Planning variance',
    '3092b6abee574a1a90a1', (86, 710, 245, 56)))
nb.write_visual(OBJECTIVE, button('543cf5e4889d4d7f9e11', 'Restatements',
    '3092b6abee574a1a90a2', (569, 710, 245, 56)))

pages_file = PAGE_ROOT / 'pages.json'
pages = json.loads(pages_file.read_text(encoding='utf-8-sig'))
pages['pageOrder'] = [COVER, OBJECTIVE] + [item for item in pages['pageOrder'] if item not in {COVER, OBJECTIVE}]
pages['activePageName'] = COVER
nb.write_json(pages_file, pages)
print('Cover and Objective pages are ready.')
