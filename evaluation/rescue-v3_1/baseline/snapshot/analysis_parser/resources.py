"""Frozen reusable interpretation choices; no case outputs or method templates."""
import hashlib,json
PROFILES={
 'ST_elapsed':{'count':'elapsed','input':'epoch_elapsed_years','basis':'C2017 §173; L2003 pp.23–24'},
 'SF_Liu_inclusive':{'count':'inclusive','input':'epoch_inclusive_year','normalization':'E=Y−1; U=localE+1','basis':'L2003 pp.64–67; project I03 boundary normalization'},
 'ST_intercalation_Cullen_Liu_GT':{'stop':'gt','basis':'C2017 p.93; L2003 eq2.9'},
 'ST_intercalation_GE_contrast':{'stop':'ge','basis':'diagnostic contrast to strict exceeds interpretation'},
 'SF_completed_four':{'threshold':'ge','basis':'C2017 §50; L2003 p.70'},
 'instant_lunation':{'boundary':'instant','basis':'C2017 pp.93–95'},
 'civil_whole_day':{'boundary':'whole_day','basis':'C2017 pp.94–96; L2003 p.70'},
}
WINTER_LIFT={'days_per_elapsed_year':360,'basis':'C2017 pp.47–48,167; annual residual constants omit 360 days per elapsed year','evidence_basis':'model_rule'}
SEXAGENARY={'sequence':[''.join((a,b)) for a,b in zip(('甲乙丙丁戊己庚辛壬癸'*6),('子丑寅卯辰巳午未申酉戌亥'*5))],'convention':'one_based_cyclic_labels; not a chronology','basis':'C2017 pp.8–10; full runtime sexagenary_sequence background, independently stem/branch generated'}
def resource_hashes():
    return {name:hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest() for name,value in [('profiles',PROFILES),('winter_lift',WINTER_LIFT),('sexagenary',SEXAGENARY),('contextual_rates',CONTEXTUAL_RATES)]}

# Contextual uses, not globally assigned physical units for historical integers.
CONTEXTUAL_RATES=[
 {'traditions':['San_tong_li','Han_Si_fen_li'],'tasks':['new_moon'],'numerator_term':'章月','denominator_terms':['章歲','章法'],'from_unit':'year','to_unit':'month','basis':'C2017 §§174,46; L2003 eq2.6,3.7'},
 {'traditions':['San_tong_li'],'tasks':['new_moon'],'numerator_term':'月法','denominator_terms':['日法'],'from_unit':'month','to_unit':'day','basis':'C2017 §175; L2003 eq2.7'},
 {'traditions':['Han_Si_fen_li'],'tasks':['new_moon'],'numerator_term':'蔀日','denominator_terms':['蔀月'],'from_unit':'month','to_unit':'day','basis':'C2017 §47; L2003 eq3.8'},
 {'traditions':['San_tong_li'],'tasks':['winter'],'numerator_term':'策餘','denominator_terms':['統法'],'from_unit':'year','to_unit':'day','residual':True,'basis':'C2017 §177; L2003 eq2.10'},
 {'traditions':['Han_Si_fen_li'],'tasks':['winter'],'numerator_term':'日餘','denominator_terms':['中法'],'from_unit':'year','to_unit':'day','residual':True,'basis':'C2017 §49; L2003 eq3.12'},
]
