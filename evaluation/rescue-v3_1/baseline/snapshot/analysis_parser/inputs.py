"""Input fidelity and Unicode span mapping; never opens evaluation resources."""
import copy
import hashlib
import json
import re

NUMERALS = '零〇一二三四五六七八九十百千萬万兩两'
NUMBER = '[' + NUMERALS + '0-9]+'

def number(text):
    if text.isdecimal():
        return int(text)
    digits = dict(zip('零一二三四五六七八九', range(10)))
    digits.update({'〇':0, '兩':2, '两':2})
    total = section = digit = 0
    for char in text:
        if char in digits:
            digit = digits[char]
        elif char in '十百千':
            section += (digit or 1) * {'十':10, '百':100, '千':1000}[char]
            digit = 0
        elif char in '萬万':
            total += (section + digit or 1) * 10000
            section = digit = 0
        else:
            raise ValueError('Not a numeric literal: ' + text)
    return total + section + digit

def load_primary_packet(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)

def documents(packet):
    output = []
    for category in ('primary_documents','context_documents'):
        for original in packet.get(category, []):
            doc = copy.deepcopy(original)
            doc['category'] = category
            doc.setdefault('reading_id', doc['doc_id'] + '.declared')
            doc['actual_sha256'] = hashlib.sha256(doc['text'].encode()).hexdigest()
            doc['reconstruction_limitations'] = []
            v3_edits = doc.get('edition_edits')
            edits = ([dict(e, transcription_range=[e['edition_start'],e['edition_end']], reading_range=[e['reading_start'],e['reading_end']]) for e in v3_edits] if v3_edits is not None else doc.get('editorial_trace', []))
            raw = doc['text']
            delta = 0
            normalized = []
            # Ranges are transcription coordinates: subtract prior length deltas.
            for edit in sorted(edits, key=lambda e:e.get('transcription_range',[0])[0]):
                old,new = edit.get('old',''),edit.get('new','')
                rr = edit.get('transcription_range')
                pos = edit['reading_range'][0] if 'reading_range' in edit else (rr[0] - delta) if rr else -1
                if pos < 0 or doc['text'][pos:pos+len(new)] != new:
                    occurrences = [m.start() for m in re.finditer(re.escape(new), doc['text'])] if new else []
                    if len(occurrences) == 1:
                        pos = occurrences[0]
                    else:
                        doc['reconstruction_limitations'].append({'edit':edit,'reason':'declared range cannot be uniquely reconciled'})
                        delta += len(old)-len(new)
                        continue
                normalized.append(dict(edit, reading_range=[pos,pos+len(new)]))
                delta += len(old)-len(new)
            for edit in sorted(normalized,key=lambda e:e['reading_range'][0], reverse=True):
                a,b=edit['reading_range'];raw=raw[:a]+edit['old']+raw[b:]
            doc['reconstructed_transcription'] = raw
            if v3_edits is not None:
                doc['edition_actual_sha256'] = hashlib.sha256(doc.get('edition_transcription',raw).encode()).hexdigest()
                if raw != doc.get('edition_transcription',raw):
                    doc['reconstruction_limitations'].append({'reason':'edition edit reconstruction differs from supplied edition transcription'})
            doc['editorial_mapping'] = normalized
            # Source reconstruction is derived, never represented as an original witness.
            doc['transcription_status'] = 'supplied_modern_edition_transcription' if v3_edits is not None else 'derived_from_declared_trace'
            mapping=[]; delta=0
            for i,char in enumerate(doc['text']):
                overlapping=[e for e in normalized if e['reading_range'][0] <= i < e['reading_range'][1]]
                previous=[e for e in normalized if e['reading_range'][1] <= i]
                shift=sum(len(e['old'])-len(e['new']) for e in previous)
                mapping.append({'reading_offset':i,'transcription_offset':None if overlapping else i+shift,'editorial':bool(overlapping)})
            doc['character_map']=mapping
            raw_mode=packet.get('input_mode')=='edition_transcription_only'
            omitted=set();doc['excluded_editorial_spans']=[]
            for markup in re.finditer(r'\[[^\]]*\]|\([^)]*\)',doc['text']):
                is_supplement=markup.group().startswith('[')
                omit_content=is_supplement if raw_mode else not is_supplement
                if omit_content:
                    omitted.update(range(markup.start(),markup.end()))
                    doc['excluded_editorial_spans'].append({'start':markup.start(),'end':markup.end(),'quote':markup.group(),'reason':'unadopted_editorial_supplement' if is_supplement else 'declared_editorial_deletion'})
                else:
                    omitted.update((markup.start(),markup.end()-1))
            retained=[(i,c) for i,c in enumerate(doc['text']) if i not in omitted and not c.isspace()]
            doc['analysis_text']=''.join(c for _,c in retained)
            doc['analysis_to_source']=[i for i,_ in retained]
            output.append(doc)
    return output

def span(doc, start, end):
    result={'doc_id':doc['doc_id'],'reading_id':doc['reading_id'],'start':start,'end':end,'quote':doc['text'][start:end]}
    edits=[e for e in doc.get('editorial_mapping',[]) if e['reading_range'][0]<end and e['reading_range'][1]>start]
    if edits:
        result['editorial_provenance']=edits
    return result

def clauses(doc):
    # Whitespace is a presentation layer; source indices remain Unicode offsets.
    text=doc.get('analysis_text',doc['text'])
    mapping=doc.get('analysis_to_source',list(range(len(text))))
    for match in re.finditer(r'[^，,；;．。.!！?？]+',text):
        yield match.group(),mapping[match.start():match.end()]
