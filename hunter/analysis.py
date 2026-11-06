"""Conservative versioned candidate extraction from stored provider excerpts.

This is deterministic pattern matching, not an AI model or eligibility verdict.
Provider content stays untrusted: it cannot authorize actions or execute tools.
"""
import re
import math
import time
from hunter.sources import FRESH_SECONDS

EXTRACTOR_VERSION='github-education-checklist-v1'
FIELDS=('minimum_age','enrollment_required','student_status_evidence_required','personal_account_required')
HEADING='## Do I qualify for GitHub Education?'
EXACT_BULLETS={
    '* Are enrolled in a degree- or diploma-granting program, such as a high school, college, university, or homeschool.':'enrollment_required',
    '* Provide documents that prove your current student status. See [Academic email requirements](#academic-email-requirements) below.':'student_status_evidence_required',
    '* Own a [{% data variables.product.prodname_dotcom %} personal account](/account-and-profile/how-tos/account-management/creating-an-account-on-github).':'personal_account_required',
}

def analyze_source(source):
    """Return candidate claims with exact end-exclusive Unicode code-point spans."""
    evidence=source.get('evidence')
    freshness=evidence.get('freshness') if evidence else None
    result={'source_id':source['id'],'extractor_version':EXTRACTOR_VERSION,
            'method':'deterministic_pattern_matching','status':'unknown',
            'reason':'no_cached_evidence','freshness':freshness,
            'last_error':source.get('last_error'),'source_url':source['source_url'],
            'content_hash':evidence.get('content_hash') if evidence else None,
            'retrieved_at':evidence.get('retrieved_at') if evidence else None,
            'offset_unit':'unicode_code_points','eligibility':'unknown',
            'deadline':'unknown','automation_status':'unknown',
            'claims':{key:{'state':'unknown','value':None,'reason':'not_observed','citation':None} for key in FIELDS}}
    def abstain(reason,status='unknown'):
        result['reason']=reason; result['status']=status
        for claim in result['claims'].values(): claim['reason']=reason
        return result
    if not evidence: return result
    retrieved=evidence.get('retrieved_at')
    if type(retrieved) not in (int,float) or not math.isfinite(retrieved) or not isinstance(evidence.get('content_hash'),str) or not re.fullmatch(r'[0-9a-f]{64}',evidence['content_hash']):
        return abstain('invalid_evidence')
    age=time.time()-retrieved
    result['freshness']='fresh' if 0<=age<FRESH_SECONDS else 'stale'
    if source.get('last_error') or age<0 or age>=FRESH_SECONDS or freshness=='stale':
        return abstain('evidence_requires_refresh','needs_refresh')
    if evidence.get('truncated'): return abstain('excerpt_truncated')
    text=evidence.get('excerpt')
    if not isinstance(text,str): return abstain('invalid_evidence')
    if source['id']!='github-education': return abstain('unsupported_source')
    # This curated version does not interpret HTML/raw-block contexts. Refuse
    # them conservatively instead of treating hidden/commented text as facts.
    if re.search(r'<[!/?A-Za-z]',text): return abstain('unsupported_markup_context')
    # Only literal GitHub data tokens are supported. Conditional/comment/raw
    # Liquid blocks can hide or change the meaning of the apparent section.
    if any(match.group(1)!='data' for match in re.finditer(r'{%-?\s*([A-Za-z_][A-Za-z0-9_]*)\b',text)):
        return abstain('unsupported_template_context')

    # Track raw offsets without transforming Markdown or evaluating Liquid.
    # Fenced examples never establish qualification context or candidate facts.
    lines=[]; offset=0; fence=None
    for raw in text.splitlines(keepends=True):
        line=raw.rstrip('\r\n')
        marker=re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$',line)
        inside=fence is not None
        if marker:
            run,tail=marker.groups()
            kind=run[0]
            if fence is None:
                # Backtick info strings cannot contain backticks.
                if kind!='`' or '`' not in tail:
                    fence=(kind,len(run)); inside=True
            elif fence[0]==kind and len(run)>=fence[1] and not tail.strip():
                fence=None; inside=True
        lines.append((line,offset,inside))
        offset+=len(raw)
    starts=[i for i,(line,_,inside) in enumerate(lines) if not inside and line==HEADING]
    if len(starts)!=1: return abstain('qualification_section_missing_or_ambiguous')
    start=starts[0]+1
    section=[]
    for line,offset,inside in lines[start:]:
        if not inside and re.match(r'^#{1,2} ',line): break
        if inside: return abstain('unsupported_qualification_content')
        section.append((line,offset))
    matched={key:[] for key in FIELDS}
    for line,offset in section:
        if not line.strip(): continue
        if line=='You qualify for {% data variables.product.prodname_global_campus %} if you:': continue
        if line in EXACT_BULLETS:
            matched[EXACT_BULLETS[line]].append((True,line,offset))
            continue
        age_match=re.fullmatch(r'\* Are at least ([0-9]{1,3}) years old\.',line)
        if age_match:
            matched['minimum_age'].append((int(age_match.group(1)),line,offset))
            continue
        # Unexpected wording (including injected prose, nested/alternate bullets
        # and negations) invalidates the recognized qualification context.
        return abstain('unsupported_qualification_content')
    if any(len(observations)!=1 for observations in matched.values()):
        if any(len(observations)>1 for observations in matched.values()):
            return abstain('ambiguous_or_duplicate_candidate_claims')
        return abstain('incomplete_supported_requirements')
    for key,observations in matched.items():
        value,quote,start=observations[0]
        citation={'quote':quote,'start':start,'end':start+len(quote),
                  'source_url':source['source_url'],'content_hash':evidence['content_hash'],
                  'retrieved_at':retrieved,'extractor_version':EXTRACTOR_VERSION}
        result['claims'][key]={'state':'candidate','value':value,'reason':'recognized_provider_wording','citation':citation}
    if any(claim['state']=='candidate' for claim in result['claims'].values()):
        result['status']='candidate_claims'; result['reason']='candidate_claims_require_manual_review'
    else: result['reason']='no_recognized_claims'
    return result
