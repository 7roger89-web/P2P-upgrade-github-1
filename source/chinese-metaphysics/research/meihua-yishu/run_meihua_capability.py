#!/usr/bin/env python3
import argparse, importlib.util, json, subprocess, sys
from pathlib import Path
PIN='8a9a5e0f482dd225bfe4a1c52c2ae5546228607a'
SCRIPT_DIR=Path(__file__).resolve().parent
UPSTREAM=(SCRIPT_DIR/'../../upstreams/meihua-yishu').resolve()
def fail(msg,code=2): print(msg,file=sys.stderr); raise SystemExit(code)
if not UPSTREAM.exists(): fail(f'Pinned upstream missing: {UPSTREAM}')
try: head=subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip()
except Exception: fail(f'Cannot verify pinned upstream: {UPSTREAM}')
if head!=PIN: fail(f'Pinned upstream SHA mismatch: expected {PIN}, got {head}')
module_path=UPSTREAM/'scripts/meihua_calc.py'
spec=importlib.util.spec_from_file_location('pinned_meihua_calc', module_path); mc=importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)
def simp(s): return str(s).replace('澤','泽').replace('變','变').replace('體','体')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--fixture',default='guanmei'); a=p.parse_args()
    if a.fixture!='guanmei': fail(f'Unknown fixture: {a.fixture}')
    year_num,month,day,shichen=5,12,17,9
    upper_sum=year_num+month+day; lower_sum=upper_sum+shichen; moving_sum=lower_sum
    upper=mc.num_to_gua(upper_sum); lower=mc.num_to_gua(lower_sum); moving=mc.num_to_yao(moving_sum)
    result=mc._analyze_hexagram(upper,lower,moving,None)
    main_name=simp(result['本卦']['名稱']); changed_name=simp(result['變卦']['名稱'])
    if (main_name, moving, changed_name) != ('泽火革',1,'泽山咸'): fail(f'Classical fixture drift: {(main_name,moving,changed_name)}',1)
    relation=result['體用']['生克關係']
    if not relation.startswith('用克體'): fail(f'Unexpected initial 体用 relation: {relation}',1)
    changed_lower = result['變卦']['二進位'][3:]
    if changed_lower != '100': fail(f'Unexpected changed lower trigram bits: {changed_lower}',1)
    out={'DOMAIN':'MEIHUA_YISHU','ENGINE_PIN':PIN,'CASTING_MODE':'TRADITIONAL_TIME_CASTING',
         'INPUT':{'year_branch_number':5,'month':12,'day':17,'shichen_number':9},
         'ARITHMETIC':{'upper_total':upper_sum,'lower_total':lower_sum,'moving_total':moving_sum},
         'UPPER_TRIGRAM':result['本卦']['上卦'],'LOWER_TRIGRAM':result['本卦']['下卦'],'MOVING_LINE':moving,
         'MAIN_HEXAGRAM':main_name,'MUTUAL_HEXAGRAM':simp(result['互卦']['名稱']),'CHANGED_HEXAGRAM':changed_name,
         'BODY_USE':result['體用'],'RULE_TRACE':['MEIHUA_YEAR_MONTH_DAY_TIME_CAST','MEIHUA_TI_YONG_MOVING_TRIGRAM_AS_USE','MEIHUA_WUXING_SHENG_KE'],
         'STRUCTURAL_OUTPUT':'INITIAL_PRESSURE_WITH_LATER_SUPPORT','EXTERNAL_SIGN_STATUS':'MISSING_DO_NOT_FABRICATE',
         'PROVENANCE_STATUS':'CLASSICAL_TEXT_GROUNDED_SELECTED_SLICE','PREDICTIVE_STATUS':'NOT_ESTABLISHED_NEGATIVE_EVIDENCE_PRESERVED',
         'NONCLAIMS':['NO_PERSONAL_FUTURE_PREDICTION','NO_EXTERNAL_SIGN_INVENTION']}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
