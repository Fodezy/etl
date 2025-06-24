"""
programs_with_sections_parser.py

Cleans and normalizes the raw programs_with_sections data into nested sections.
"""
import re
from typing import List, Dict, Any, Union

# Helpers
def normalize_text(text: Any) -> str:
    if not isinstance(text, str): return ''
    clean = text.replace("\u200b", "").strip()
    return re.sub(r"\s+", " ", clean)

# Regex to match course lines: CODE*#### Title Credits
COURSE_LINE_RE = re.compile(
    r"^(?P<code>[A-Z]{2,}\*[0-9]+)\s+(?P<title>.+?)\s+(?P<credits>[0-9]+(?:\.[0-9]+)?)$"
)
# Regex to match numeric electives lines: Credits Title Credits
NUM_ELECTIVE_RE = re.compile(
    r"^(?P<credits>[0-9]+(?:\.[0-9]+)?)\s+(?P<title>.+?)\s+(?P=credits)$"
)

SECTION_HEADERS_RE = re.compile(r"^(?P<section>.+?) Requirements(?: \((?P<type>.+)\))?$")
TOTAL_CRED_RE = re.compile(r"^\((?P<total>[0-9]+(?:\.[0-9]+)?) Total Credits\)$")


def parse_programs_with_sections(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []

    for prog in raw:
        name = normalize_text(prog.get('name'))
        degree = normalize_text(prog.get('degree'))
        url = normalize_text(prog.get('calendar_url'))
        sections_raw = prog.get('sections', {}) or {}

        sections: Dict[str, Any] = {}
        for sec_name, content in sections_raw.items():
            if content is None: continue
            # Overview unchanged
            if sec_name == 'Overview' and isinstance(content, dict):
                paras = [normalize_text(p) for p in content.get('paragraphs', []) if normalize_text(p)]
                coll = []
                for grp in content.get('collapsibles', []):
                    hdr = normalize_text(grp.get('header'))
                    txt = '\n'.join(
                        normalize_text(ln) for ln in grp.get('content','').splitlines() if normalize_text(ln)
                    )
                    if hdr and txt: coll.append({'header': hdr, 'content': txt})
                if paras or coll:
                    sections['Overview'] = {'paragraphs': paras, 'collapsibles': coll}
                continue

            if isinstance(content, list):
                lines = [normalize_text(ln) for ln in content if normalize_text(ln)]
                idx, n = 0, len(lines)
                sect: Dict[str, Any] = {}

                # Requirements block
                m = SECTION_HEADERS_RE.match(lines[idx])
                if m:
                    sect['requirements'] = {
                        'title': normalize_text(m.group('section')),
                        'type': normalize_text(m.group('type') or ''),
                        'description': normalize_text(lines[idx+1]) if idx+1<n else ''
                    }
                    idx += 2

                # Credit summary
                while idx<n and lines[idx] != 'Credit Summary': idx+=1
                if idx<n and lines[idx]=='Credit Summary': idx+=1
                total, breakdown = None, {}
                if idx<n:
                    m2 = TOTAL_CRED_RE.match(lines[idx])
                    if m2:
                        total = float(m2.group('total'))
                        idx+=1
                        while idx<n and lines[idx] != 'Course List':
                            parts = lines[idx].rsplit(' ',1)
                            if len(parts)==2 and re.match(r'^[0-9]+(?:\.[0-9]+)?$', parts[1]):
                                breakdown[parts[0]] = float(parts[1])
                            idx+=1
                if total is not None or breakdown:
                    sect['credit_summary'] = {'total_credits': total, 'breakdown': breakdown}

                # Skip to courses
                while idx<n and (lines[idx]=='Course List' or lines[idx].startswith('Code')): idx+=1

                # Sequence parsing
                seq: Dict[str, List[Any]] = {}
                current = None
                notes: List[str] = []
                electives: List[str] = []
                while idx<n:
                    ln = lines[idx]
                    if ln.startswith('Semester') or ln.startswith('Year'):
                        current = ln
                        seq[current] = []
                    else:
                        cm = COURSE_LINE_RE.match(ln)
                        if cm and current:
                            entry = {
                                'course_code': cm.group('code'),
                                'title': cm.group('title'),
                                'credits': float(cm.group('credits'))
                            }
                            seq[current].append(entry)
                        else:
                            ne = NUM_ELECTIVE_RE.match(ln)
                            if ne and current:
                                entry = {
                                    'title': ne.group('title'),
                                    'credits': float(ne.group('credits'))
                                }
                                seq[current].append(entry)
                            elif ln.startswith('Select'):
                                electives.append(ln)
                            else:
                                notes.append(ln)
                    idx+=1

                if seq: sect['program_sequence'] = seq
                if electives: sect['elective_options'] = electives
                if notes: sect['notes'] = notes

                if sect:
                    sections[sec_name] = sect

        cleaned.append({'name': name, 'degree': degree, 'calendar_url': url, 'sections': sections})

    return cleaned
