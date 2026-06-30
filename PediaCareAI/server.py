"""
PediaCare AI - Production Backend Server v1.0
Paediatric Health Intelligence Platform
=========================================
DISCLAIMER: All AI output is for research/education only.
Not medical advice. Always consult a qualified paediatrician.
PAEDIATRIC EMERGENCY: Difficulty breathing, blue lips, seizure,
unresponsive child, high fever in infant under 3 months -
Call 112 (India) / 999 (UK) / 911 (US).
"""

import os
import sys
import json
import uuid
import time
import hashlib
import logging
import datetime
import argparse
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_OK = True
except ImportError:
    print("[FATAL] Flask not installed. Run REPAIR_AND_RECOVER.bat")
    sys.exit(1)

try:
    import requests as req_lib
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

sys.path.insert(0, str(Path(__file__).parent / "modules"))
try:
    import ai_providers
    AI_PROVIDERS_OK = True
except ImportError:
    AI_PROVIDERS_OK = False

BASE_DIR    = Path(__file__).parent.resolve()
UPLOAD_DIR  = BASE_DIR / "uploads"
LOGS_DIR    = BASE_DIR / "logs"
DATA_DIR    = BASE_DIR / "data"
STATIC_DIR  = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports_db"

for d in [UPLOAD_DIR, LOGS_DIR, DATA_DIR, STATIC_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PORT    = int(os.environ.get("PEDIACARE_PORT", 5080))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_PROVIDER_KEYS = ai_providers.get_env_keys() if AI_PROVIDERS_OK else {}
VERSION = "1.0.0"

DISCLAIMER = (
    "WARNING - AI RESEARCH DISCLAIMER: All output is AI-generated from published "
    "paediatric literature (AAP, RCPCH, WHO, NICE, IAP, PubMed). This is for "
    "educational research only. NOT a medical diagnosis or prescription. ALWAYS consult "
    "a qualified paediatrician before any health decision for your child. PAEDIATRIC "
    "EMERGENCY (difficulty breathing, blue lips/face, seizure, unresponsive child, high "
    "fever in infant under 3 months, severe dehydration): Call 112 (India) / 999 (UK) / "
    "911 (US) immediately."
)

log_file = LOGS_DIR / f"server_{datetime.date.today()}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("PediaCareAI")

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
CORS(app, origins="*")

# Security: rate limiting & input sanitisation
_RATE_STORE = {}
_RATE_LIMIT  = 30
_RATE_WINDOW = 60

def _get_client_id():
    ip = request.remote_addr or '127.0.0.1'
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

def rate_limit_check():
    cid = _get_client_id()
    now = time.time()
    if cid not in _RATE_STORE:
        _RATE_STORE[cid] = []
    _RATE_STORE[cid] = [t for t in _RATE_STORE[cid] if now - t < _RATE_WINDOW]
    if len(_RATE_STORE[cid]) >= _RATE_LIMIT:
        return False
    _RATE_STORE[cid].append(now)
    return True

def sanitise_api_key(key):
    if not key or not isinstance(key, str):
        return ''
    key = key.strip()
    if len(key) > 512:
        return ''
    sanitised = ''.join(c for c in key if 0x21 <= ord(c) <= 0x7E)
    return sanitised if len(sanitised) >= 10 else ''

def validate_provider(provider):
    allowed = {'anthropic', 'openai', 'gemini', 'grok', 'deepseek'}
    if not provider or provider.lower() not in allowed:
        return 'anthropic'
    return provider.lower()

# =====================================================================
# OFFLINE PAEDIATRICS KNOWLEDGE BASE
# =====================================================================
KNOWLEDGE = {
    "growth_development": {
        "name": "Growth and Development Milestones",
        "growth_charts": "WHO growth standards (0-2 years) and UK-WHO/CDC growth charts (2-18 years) plot weight, height/length, head circumference, and BMI against age. Centiles (2nd, 9th, 25th, 50th, 75th, 91st, 98th) indicate relative position. Crossing 2+ centile lines (up or down) warrants review. Plotted at every health visit.",
        "developmental_milestones": "Gross motor: head control 3-4mo, sits unsupported 6-8mo, crawls 8-10mo, walks independently 12-15mo, runs 18mo, jumps 2yr. Fine motor: palmar grasp 4mo, pincer grasp 9-12mo, scribbles 15-18mo, builds tower of 6 cubes 2yr, draws circle 3yr. Language: coos 6-8wk, babbles 6mo, first words 12mo, 2-word phrases 18-24mo, 3-word sentences 3yr. Social: social smile 6wk, stranger anxiety 7-9mo, pretend play 18mo-2yr, shares toys 3-4yr.",
        "red_flags": "Red flags requiring assessment: no eye contact by 3 months, no smiling by 8 weeks, head circumference crossing centiles, not sitting by 12 months, not walking by 18 months, no words by 18 months, regression in any skill at any age, persistent toe-walking, asymmetric movements.",
        "failure_to_thrive": "Weight crossing down 2+ centiles, or weight persistently below 2nd centile, or weight-for-height below -2 SD. Causes: inadequate intake (feeding difficulties, neglect, psychosocial), malabsorption (coeliac, CF, cow's milk protein allergy), increased requirement (chronic illness, congenital heart disease), excessive losses. Assessment: detailed feeding history, growth chart review, examination, targeted investigations based on history.",
    },
    "fever_infections": {
        "name": "Fever and Common Childhood Infections",
        "fever_assessment": "NICE Traffic Light System for febrile children under 5: GREEN (low risk) - normal colour, responds normally, content, normal skin/eyes, moist mucous membranes. AMBER (intermediate risk) - pallor, decreased activity, nasal flaring, tachypnoea, SpO2 under 95%, crackles, tachycardia, CRT 3+ seconds, dry mucous membranes, reduced urine output, rigors, fever over 5 days, swelling of limb/joint. RED (high risk) - pale/mottled/ashen/blue, no response to social cues, appears unwell, weak/high-pitched/continuous cry, grunting, RR over 60, moderate/severe chest indrawing, reduced skin turgor, age under 3 months with temp 38C+, non-blanching rash, bulging fontanelle, neck stiffness, status epilepticus, focal neurological signs.",
        "under_3_months": "ANY fever (38C+) in an infant under 3 months requires URGENT paediatric assessment - full septic screen often required (blood culture, FBC, CRP, urine, +/- LP, CXR). Higher risk of serious bacterial infection at this age due to immature immune system.",
        "common_viral": "Most childhood fevers are viral and self-limiting: common cold, viral URTI, viral gastroenteritis, hand-foot-mouth disease (Coxsackievirus), roseola (HHV-6, fever then rash as fever resolves), chickenpox (varicella), fifth disease (parvovirus B19, slapped cheek).",
        "bacterial_concerns": "Bacterial infections requiring antibiotics: otitis media (ear pain, bulging tympanic membrane), bacterial tonsillitis (Centor criteria), UTI (always investigate fever without focus in young children), pneumonia (tachypnoea, crackles, reduced air entry), bacterial meningitis/sepsis (RED FLAG - non-blanching rash, neck stiffness, photophobia, bulging fontanelle).",
        "fever_management": "Antipyretics (paracetamol 15mg/kg every 4-6h, ibuprofen 5-10mg/kg every 6-8h) for distress/discomfort, not solely to reduce temperature. Do not use antipyretics solely to prevent febrile seizures (no evidence). Encourage fluids. Do not over-wrap. Seek medical advice if amber/red features, fever over 5 days, or parental concern.",
        "febrile_seizures": "Occur in 2-5% of children aged 6 months to 6 years, triggered by rapid temperature rise. Simple febrile seizure: under 15 minutes, generalised, no recurrence within 24h - benign, no long-term epilepsy risk increase beyond baseline population. Complex febrile seizure: over 15 minutes, focal features, or recurs within 24h - requires further assessment. First febrile seizure: medical assessment to identify fever source and exclude meningitis/encephalitis.",
    },
    "vaccination": {
        "name": "Childhood Vaccination Schedule",
        "definition": "Vaccination is one of the most effective public health interventions, preventing serious infectious diseases. Schedules vary slightly by country but follow similar principles based on WHO recommendations.",
        "india_schedule": "India National Immunization Schedule: Birth - BCG, OPV-0, Hep B-1. 6/10/14 weeks - DPT, OPV, Hep B (Pentavalent), Rotavirus, PCV, IPV. 9 months - Measles/MR, JE (in endemic areas), Vitamin A. 16-24 months - DPT booster, OPV booster, MR 2nd dose, JE 2nd dose, Vitamin A. 5-6 years - DPT booster 2, 10 years - TT/Tdap.",
        "uk_schedule": "UK Routine schedule: 8 weeks - 6-in-1 (DTaP/IPV/Hib/HepB), Rotavirus, MenB. 12 weeks - 6-in-1, PCV, Rotavirus. 16 weeks - 6-in-1, MenB. 1 year - Hib/MenC, MMR, PCV booster, MenB booster. 3yr 4mo - MMR 2nd dose, 4-in-1 preschool booster. 12-13yr - HPV. 14yr - 3-in-1 teenage booster, MenACWY.",
        "common_concerns": "Vaccine safety: extensive global surveillance confirms vaccines are safe and effective. Common mild side effects: soreness at injection site, mild fever, fussiness - resolve within 1-2 days. Serious adverse events are extremely rare and far outweighed by disease prevention benefit. MMR and autism: no causal link - this has been extensively studied and definitively disproven (the original 1998 study was retracted and found fraudulent).",
        "contraindications": "True contraindications are rare: anaphylaxis to previous dose or vaccine component, severe immunodeficiency (for live vaccines like MMR, BCG, rotavirus, varicella). Minor illness without fever is NOT a contraindication to vaccination - delay only for moderate/severe acute illness.",
        "catch_up": "Children who have missed vaccines can catch up at any age - it is never too late. Paediatrician or GP can advise on a catch-up schedule. No need to restart a vaccine series from the beginning even after delay.",
    },
    "neonatal_care": {
        "name": "Neonatal Care and Newborn Health",
        "newborn_exam": "Newborn and Infant Physical Examination (NIPE/routine baby check) within 72 hours of birth and repeated at 6-8 weeks. Checks: eyes (red reflex - excludes cataract/retinoblastoma), heart (murmurs, femoral pulses - coarctation screening), hips (Barlow/Ortolani tests for DDH), testes (descended in males).",
        "jaundice": "Neonatal jaundice affects up to 60% of term and 80% of preterm infants. Physiological jaundice: appears day 2-3, peaks day 3-5, resolves by 2 weeks (term) or 3 weeks (preterm) - due to immature liver conjugation + increased red cell breakdown. Pathological jaundice (requires urgent assessment): onset within 24 hours of birth, prolonged beyond 2-3 weeks, very high bilirubin levels, or with other symptoms (poor feeding, lethargy, pale stools, dark urine). Treatment: phototherapy for significant hyperbilirubinaemia per NICE threshold charts (by age in hours and risk factors). Exchange transfusion for severe cases approaching kernicterus risk.",
        "feeding": "Exclusive breastfeeding recommended for first 6 months (WHO/UNICEF), continuing alongside complementary foods to 2 years or beyond. Formula feeding: appropriate alternative when breastfeeding is not possible/chosen - prepare according to instructions, paced feeding to avoid overfeeding. Feeding cues: rooting, hand-to-mouth, lip-smacking (early); crying is a LATE hunger cue.",
        "weight_loss": "Normal newborn weight loss: up to 10% of birth weight in first 3-5 days is normal (fluid shifts + establishing feeding), should regain birth weight by 2-3 weeks. Weight loss over 10%, or failure to regain birth weight by 3 weeks, requires feeding assessment.",
        "umbilical_cord": "Cord stump dries and separates naturally within 5-15 days. Keep clean and dry, fold nappy below cord. Signs of infection requiring review: redness spreading from cord base, pus, foul smell, fever - omphalitis can progress rapidly in neonates.",
        "screening": "Newborn blood spot screening (heel prick, day 5): screens for congenital hypothyroidism, phenylketonuria (PKU), cystic fibrosis, sickle cell disease, MCADD, and other inherited metabolic conditions depending on national programme. Newborn hearing screening (OAE test): before discharge or by 4-5 weeks.",
    },
    "respiratory": {
        "name": "Paediatric Respiratory Conditions",
        "bronchiolitis": "Viral lower respiratory tract infection, predominantly RSV, affecting infants under 12 months (peak 3-6 months). Symptoms: coryza progressing to persistent cough, tachypnoea, chest wall recession, wheeze/crackles, feeding difficulty. Usually self-limiting over 1-2 weeks (cough may persist longer). RED FLAGS for hospital assessment: apnoea episodes, marked respiratory distress (grunting, severe recession, RR over 70), central cyanosis, SpO2 persistently under 92%, poor feeding (under 50% normal intake), clinical dehydration, exhaustion. Management: supportive (oxygen if SpO2 low, feeding support/NG if needed). No role for bronchodilators, steroids, or antibiotics in straightforward bronchiolitis (NICE guidance).",
        "croup": "Laryngotracheobronchitis, usually viral (parainfluenza most common). Barking cough, hoarse voice, inspiratory stridor, worse at night. Most cases mild and managed at home. Single dose oral dexamethasone (0.15mg/kg) reduces severity and duration even in mild cases. Severe croup (stridor at rest, marked recession, agitation/lethargy): hospital assessment, nebulised adrenaline, may need ICU. Cool/humidified air has limited evidence but is generally harmless and often used.",
        "asthma": "Most common chronic disease of childhood. Diagnosis in young children (under 5) is largely clinical - difficult to perform spirometry. Recurrent wheeze, cough (especially nocturnal/exercise-induced), atopy history. Stepwise management (BTS/SIGN, NICE): SABA (salbutamol) reliever first-line. Inhaler technique and spacer device use is critical - check at every review. ICS (inhaled corticosteroid) preventer if frequent symptoms. Personalised asthma action plan for all. Acute severe asthma: RED FLAGS - unable to complete sentences, accessory muscle use, SpO2 under 92%, silent chest, exhaustion, cyanosis - EMERGENCY.",
        "pneumonia": "Community-acquired pneumonia: fever, tachypnoea (key sign in children), cough, reduced air entry/crackles, may have chest pain (older children). WHO criteria for fast breathing by age: under 2 months RR 60+, 2-12 months RR 50+, 1-5 years RR 40+. Most paediatric pneumonia is viral under 5 years; bacterial more likely with high fever, focal signs, very unwell child. Amoxicillin first-line if bacterial cause suspected and treatment needed.",
        "cystic_fibrosis": "Autosomal recessive condition affecting chloride channel function (CFTR gene), causing thick mucus affecting lungs and pancreas. Detected on newborn screening (immunoreactive trypsinogen). Confirmed with sweat test (elevated chloride) and genetic testing. Management: airway clearance physiotherapy, mucolytics, prophylactic antibiotics, pancreatic enzyme replacement, high-calorie diet, fat-soluble vitamin supplementation. CFTR modulator therapies (ivacaftor, lumacaftor/ivacaftor, elexacaftor/tezacaftor/ivacaftor - Kaftrio) have transformed prognosis for eligible genotypes.",
    },
    "gastro_pediatric": {
        "name": "Paediatric Gastrointestinal Conditions",
        "gastroenteritis": "Most commonly viral (rotavirus, norovirus). Acute diarrhoea +/- vomiting. Main risk: dehydration. Assessment of dehydration: no signs (alert, normal urine, moist mucous membranes), some dehydration (restless/irritable, decreased urine, dry mucous membranes, sunken eyes, reduced skin turgor), severe dehydration (lethargic/unconscious, very dry mucous membranes, sunken eyes, skin pinch very slow to recoil) - SEVERE DEHYDRATION IS A MEDICAL EMERGENCY. Management: oral rehydration solution (ORS) for mild-moderate dehydration, continue breastfeeding, avoid fruit juices/carbonated drinks, IV fluids if severe dehydration or unable to tolerate oral intake.",
        "constipation": "Very common in childhood. Functional constipation (no organic cause) accounts for over 90%. ROME IV criteria for children: 2+ of - 2 or fewer stools/week, painful/hard stools, large diameter stools, faecal incontinence, stool withholding, palpable abdominal/rectal mass. Red flags for organic cause: delayed passage of meconium (over 48h), ribbon stools, abdominal distension, failure to thrive, neurological signs. Management: dietary advice (fluid, fibre), disimpaction if faecal loading (high-dose macrogol), maintenance laxative therapy (macrogol/Movicol Paediatric Plain first-line), behavioural approach (regular toileting, reward charts) - may take months for full resolution, do not stop laxatives too early.",
        "cows_milk_allergy": "IgE-mediated (immediate reaction - urticaria, vomiting, angioedema, anaphylaxis within minutes-2 hours) or non-IgE-mediated (delayed reaction - eczema, reflux, colic, blood/mucus in stool, faltering growth, over hours-days). Diagnosis: clinical history +/- skin prick test/specific IgE (IgE-mediated) or exclusion diet with reintroduction (non-IgE). Management: extensively hydrolysed formula or amino acid formula if formula-fed; maternal dairy exclusion if breastfed (non-IgE). Most children outgrow CMPA by age 3-5.",
        "reflux_infant": "Infant reflux (regurgitation) is extremely common and usually physiological - resolves by 12 months in most infants as the gut matures. Distinguish from GORD (gastro-oesophageal reflux disease) which causes troublesome symptoms: feeding refusal, faltering growth, distressed behaviour, chronic cough, recurrent pneumonia. Management of simple reflux: reassurance, smaller more frequent feeds, upright positioning after feeds. GORD: trial of alginate therapy, then PPI/H2 blocker if persisting, specialist referral if red flags or treatment failure.",
        "intussusception": "Telescoping of bowel into adjacent segment, typically ileocolic. Peak age 5-12 months. Classic triad (only present in minority): colicky abdominal pain (drawing legs up), vomiting, redcurrant jelly stool (blood and mucus - late sign). Sausage-shaped abdominal mass may be palpable. EMERGENCY - can cause bowel ischaemia/perforation. USS diagnostic (target sign). Treatment: air/contrast enema reduction (radiological), surgery if reduction fails or perforation.",
    },
    "rashes_skin": {
        "name": "Childhood Rashes and Skin Conditions",
        "non_blanching_rash": "RED FLAG: Non-blanching rash (does not fade when pressed with a glass - 'glass test') in an unwell, febrile child is a medical emergency until proven otherwise - suggests meningococcal sepsis. Call emergency services immediately. Other features of meningococcal disease: fever, neck stiffness, photophobia, drowsiness, cold hands/feet, rapid breathing.",
        "eczema": "Atopic dermatitis affects up to 20% of children, usually starting in infancy. Dry, itchy, inflamed skin - flexural distribution in older children (elbow/knee creases), face/scalp in infants. Management stepwise: emollients (liberal, frequent use - mainstay of treatment), topical corticosteroids for flares (potency appropriate to severity/site - milder on face), avoid trigger factors (soaps, certain fabrics), antihistamines for itch/sleep disturbance during flares. Infected eczema (weeping, crusting, fever): may need antibiotics. Eczema herpeticum (rapid widespread vesicles, punched-out erosions, unwell child) - EMERGENCY, needs urgent antiviral treatment.",
        "viral_exanthems": "Chickenpox (varicella): fever + itchy vesicular rash in crops, starts on trunk/face. Infectious until all lesions crusted. Calamine/antihistamines for itch, avoid aspirin (Reye syndrome risk), antivirals if immunocompromised or severe. Hand-foot-mouth disease (Coxsackievirus): vesicles on hands, feet, mouth, fever - self-limiting 7-10 days. Roseola (HHV-6): high fever 3-5 days then fever resolves as pink macular rash appears. Fifth disease/slapped cheek (Parvovirus B19): bright red cheeks, lacy rash on body - caution in pregnancy contacts (fetal hydrops risk).",
        "kawasaki_disease": "Medium vessel vasculitis, peak age 6 months-5 years. CRASH and Burn mnemonic: Conjunctivitis (bilateral, non-purulent), Rash (polymorphous), Adenopathy (cervical lymphadenopathy), Strawberry tongue/mucositis, Hands/feet (oedema, erythema, later peeling), and Fever 5+ days. Diagnosis: fever 5+ days plus 4 of 5 features. URGENT diagnosis important - risk of coronary artery aneurysms if untreated. Treatment: IVIG + high-dose aspirin within 10 days of fever onset significantly reduces coronary complications. Echocardiogram to assess coronary arteries.",
        "nappy_rash": "Irritant contact dermatitis from prolonged contact with urine/faeces. Erythema in contact areas, sparing skin folds (unlike candida which involves folds with satellite lesions). Management: frequent nappy changes, barrier cream, nappy-free time, avoid excessive wipes/soap. Candidal nappy rash: beefy red rash with satellite lesions, treat with topical antifungal (clotrimazole).",
    },
    "behavioral_development": {
        "name": "Behavioural and Developmental Concerns",
        "autism_spectrum": "Autism Spectrum Disorder (ASD): neurodevelopmental condition affecting social communication and behaviour, presenting in early childhood. Core features: differences in social communication/interaction, restricted/repetitive behaviours and interests, sensory sensitivities. Early signs may include: reduced eye contact, delayed language, reduced response to name, repetitive movements, intense focus on specific interests, difficulty with changes in routine. Diagnosis: comprehensive multidisciplinary assessment (paediatrician, psychologist, SLT). No single test - based on developmental history and observation against diagnostic criteria (DSM-5/ICD-11). Early intervention (speech therapy, occupational therapy, behavioural approaches) improves outcomes - earlier identification allows earlier support.",
        "adhd": "Attention Deficit Hyperactivity Disorder: persistent pattern of inattention and/or hyperactivity-impulsivity affecting function across settings (home, school), present before age 12. Assessment: detailed history from multiple settings (parents, teachers), rule out other causes of symptoms, formal questionnaires (Conners, SNAP-IV). Management: psychoeducation and parent training first-line for under 5s. School-age: behavioural interventions, and medication (methylphenidate first-line, also atomoxetine, lisdexamfetamine) if significant impairment persists despite environmental adaptations - specialist initiation and monitoring required (growth, cardiovascular, sleep).",
        "speech_delay": "Language delay is common and has many causes: hearing impairment (always check first), bilingual exposure (normal, not a cause for delay alone), autism spectrum, global developmental delay, specific language impairment, environmental factors (limited interaction/screen time overuse). Red flags: no babbling by 12 months, no words by 18 months, no 2-word phrases by 2 years, regression of language at any age, unintelligible speech beyond expected age. Assessment: hearing test essential, SLT assessment, paediatric review for broader developmental concerns.",
        "sleep_problems": "Common across childhood - settling difficulties, night waking, nightmares/night terrors. Sleep hygiene principles: consistent bedtime routine, appropriate sleep environment (dark, quiet, comfortable temperature), avoid screens before bed, consistent wake times. Night terrors (non-REM, child not fully awake, no memory) vs nightmares (REM, child wakes distressed, remembers) - reassurance for both, safety measures for night terrors (very rarely concerning unless very frequent/prolonged - consider epilepsy if atypical).",
        "tantrums_behaviour": "Tantrums are a normal part of development (peak 18 months-3 years) as children develop emotional regulation. Management: consistent boundaries, praise for positive behaviour, ignore (safely) attention-seeking behaviour where appropriate, time-out/time-in strategies, model calm behaviour. Concerning patterns requiring assessment: severe aggression causing injury, persistent beyond age 5-6 with no improvement, significant impact on family/school functioning, regression in other developmental areas.",
    },
    "nutrition_pediatric": {
        "name": "Paediatric Nutrition",
        "infant_feeding": "WHO recommends exclusive breastfeeding for first 6 months, then introduction of complementary foods alongside continued breastfeeding to 2 years or beyond. Weaning/complementary feeding starts around 6 months (not before 4 months) - signs of readiness: can sit supported, good head control, can bring objects to mouth, shows interest in food. Start with single-ingredient purees or baby-led weaning (soft finger foods), introduce allergenic foods early and one at a time (egg, peanut, dairy) - early introduction reduces allergy risk per current evidence (LEAP study).",
        "vitamin_supplementation": "Vitamin D supplementation recommended for all breastfed infants (formula contains adequate D) and often for all children in countries with limited sunlight/darker skin populations - 400 IU/day from birth. Iron: term infants have sufficient iron stores until 6 months; preterm/low birth weight infants need earlier supplementation. Multivitamin drops (A, C, D) often recommended for young children with limited dietary variety per national guidance (e.g., UK Healthy Start vitamins).",
        "picky_eating": "Extremely common in toddlers (food fussiness/selective eating) - usually a normal developmental phase. Strategies: offer variety without pressure, model eating behaviour, involve child in food preparation, repeated exposure without force-feeding (may take 10-15 exposures to accept new food), avoid using food as reward/punishment, regular meal/snack routine. Concerning if: very limited food range affecting growth, extreme distress around food/mealtimes, significant nutritional deficiency - consider feeding therapy referral.",
        "obesity_pediatric": "Childhood obesity: BMI above 95th centile for age/sex (UK-WHO charts) or above 97th centile depending on classification used. Multifactorial: dietary patterns, physical activity levels, sleep, family/environmental factors, occasionally endocrine/genetic causes. Management: whole-family lifestyle approach (not singling out child), increase physical activity, reduce screen time, improve dietary quality (reduce sugary drinks/processed food, increase fruit/vegetables), address psychological factors. Avoid restrictive dieting language with children - focus on healthy habits.",
        "food_allergy": "True food allergy affects 6-8% of children, most commonly: cow's milk, egg, peanut, tree nuts, soy, wheat, fish, shellfish. IgE-mediated reactions occur rapidly (minutes to 2 hours): urticaria, angioedema, vomiting, anaphylaxis (always have emergency action plan and adrenaline auto-injector if prescribed). Management: strict avoidance of confirmed allergen, allergy action plan, regular allergy specialist review (many outgrow milk/egg allergy, peanut/tree nut allergy more often persists). Avoid unnecessary exclusion diets without confirmed diagnosis - risk of nutritional deficiency and delayed resolution of tolerance.",
    },
    "pediatric_emergency": {
        "name": "Paediatric Emergencies",
        "breathing_difficulty": "EMERGENCY signs in a child with breathing difficulty: grunting, severe chest wall recession, nasal flaring, RR over 60 (any age), inability to feed/talk due to breathlessness, central cyanosis (blue lips/tongue), exhaustion, silent chest (in known asthma - means almost no air movement, very serious), SpO2 under 92%. Call 112/999/911 immediately. Position child upright/comfortable, do not force lying flat.",
        "choking": "Conscious choking infant (under 1 year): 5 back blows (infant face-down on forearm, head lower than chest) then 5 chest thrusts (infant face-up) if back blows fail, repeat cycle. Conscious choking child (over 1 year): 5 back blows then 5 abdominal thrusts (Heimlich) if back blows fail, repeat cycle. Unconscious choking child/infant: start CPR immediately, check mouth for visible object before each set of breaths. Call 112/999/911 if choking does not resolve quickly or child becomes unconscious.",
        "seizures": "First aid for any seizure: time it, protect from injury (move hazardous objects, cushion head), do NOT restrain or put anything in mouth, once jerking stops place in recovery position. Call 112/999/911 if: first-ever seizure, lasts over 5 minutes, difficulty breathing after, child does not regain consciousness, injury occurs, child is known epileptic but this seizure differs from usual pattern, or another seizure starts before recovery from first.",
        "allergic_reaction_anaphylaxis": "Anaphylaxis signs: difficulty breathing/wheeze, swelling of lips/face/throat, widespread hives, dizziness/collapse, vomiting (in context of allergen exposure). EMERGENCY: call 112/999/911, use adrenaline auto-injector (EpiPen/Jext) immediately if prescribed and available - inject into outer thigh, lay child flat with legs raised (or sitting if breathing difficulty predominates) unless vomiting (recovery position), second dose after 5-15 minutes if no improvement before ambulance arrives.",
        "head_injury": "Most childhood head injuries are minor. RED FLAGS requiring urgent assessment: loss of consciousness, persistent vomiting (3+ episodes), abnormal drowsiness, clear fluid from nose/ears, seizure, focal neurological signs, suspicion of non-accidental injury, high-energy mechanism (fall from height, RTC), age under 1 year with any swelling/bruise to head. CT head per NICE/PECARN criteria for higher-risk presentations.",
        "burns_scalds": "First aid: cool the burn under cool (not ice-cold) running water for 20 minutes, remove clothing/jewellery near burn (unless stuck to skin), cover with clean non-fluffy material/cling film, do not apply creams/butter/ice. Seek emergency care for: burns to face/hands/feet/genitals, burns larger than child's palm, full-thickness (white/charred) burns, electrical/chemical burns, any burn in infant under 1 year, suspicion of non-accidental injury.",
        "dehydration_severe": "Severe dehydration signs: lethargic or unconscious, sunken eyes, very dry mucous membranes, skin pinch recoils very slowly, reduced/absent urine output, sunken fontanelle (infants), rapid weak pulse. MEDICAL EMERGENCY requiring IV fluid resuscitation - call 112/999/911 or proceed immediately to emergency department.",
        "non_accidental_injury": "Signs that may raise concern for child abuse/neglect: injury inconsistent with developmental stage or explanation given, delayed presentation, multiple injuries of different ages, bruising in unusual sites (ears, neck, buttocks, soft tissue away from bony prominences), patterned injuries, fractures in non-mobile infants, retinal haemorrhages, repeated attendances. Any suspicion should be discussed with senior paediatric colleague/safeguarding lead - duty to act in the child's best interest and report concerns through appropriate safeguarding channels.",
    },
}

def save_knowledge():
    with open(DATA_DIR / "pedia_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(KNOWLEDGE, f, indent=2, ensure_ascii=False)

def load_sessions():
    sf = DATA_DIR / "sessions.json"
    if sf.exists():
        with open(sf, "r") as f:
            return json.load(f)
    return {}

def save_session(sid, data):
    sessions = load_sessions()
    sessions[sid] = {**data, "updated": datetime.datetime.now().isoformat()}
    with open(DATA_DIR / "sessions.json", "w") as f:
        json.dump(sessions, f, indent=2)

def is_online():
    if not REQUESTS_OK:
        return False
    try:
        req_lib.get("https://8.8.8.8", timeout=3)
        return True
    except Exception:
        return False

def extract_pdf_text(filepath):
    if not FITZ_OK:
        return "[PDF extraction unavailable]"
    try:
        doc = fitz.open(str(filepath))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text[:8000]
    except Exception as e:
        return f"[PDF extraction error: {e}]"

DEFAULT_SYSTEM_PROMPT = (
    "You are PediaCare AI, a paediatric health research assistant. You help parents and "
    "carers understand child health conditions, growth and development, vaccination, "
    "medications, and when to seek care, from published paediatric literature. "
    "ALWAYS begin with a brief disclaimer that this is AI research. "
    "Provide thorough, evidence-based information referencing AAP, RCPCH, WHO, NICE, IAP guidelines. "
    "ALWAYS end with a reminder to consult a qualified paediatrician. "
    "For paediatric emergencies (breathing difficulty, seizure, unresponsive child, non-blanching "
    "rash, severe dehydration), advise calling 112 India / 999 UK / 911 US immediately. "
    "Be specific with weight-based dosing where relevant but always caveat that dosing must be "
    "confirmed by the treating clinician. Never refuse educational information."
)

def call_ai(prompt, system_prompt=None, max_tokens=2500, provider=None, api_key=None):
    if not AI_PROVIDERS_OK:
        return None, "ai_providers_module_missing"
    provider = validate_provider(provider or "anthropic")
    effective_key = sanitise_api_key(api_key) or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider == "anthropic" else "")
    if not effective_key or not REQUESTS_OK or not is_online():
        return None, "offline_or_no_key"
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    text, mode = ai_providers.call_ai(provider, effective_key, prompt, system_prompt, max_tokens)
    if text is None:
        log.error(f"{provider} API error: {mode}")
        return None, mode
    return text, "live_ai"

def build_offline_response(topic, details="", patient_info=None):
    topic_l = topic.lower()
    kb_key = None
    for key in KNOWLEDGE:
        kb_name = KNOWLEDGE[key].get("name", "").lower()
        if key.replace("_"," ") in topic_l or topic_l in key.replace("_"," ") or topic_l in kb_name:
            kb_key = key
            break

    lines = [
        "# PediaCare AI Research Report",
        f"**Topic:** {topic}",
        "**Mode:** Offline Research (Embedded Paediatrics Knowledge Base)",
        "",
        "> WARNING - DISCLAIMER: AI-generated educational information from published paediatric "
        "literature (AAP, RCPCH, WHO, NICE, IAP). NOT a medical diagnosis or prescription. "
        "ALWAYS consult a qualified paediatrician. "
        "PAEDIATRIC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US) immediately.",
        "",
        "---",
        ""
    ]

    if kb_key:
        kb = KNOWLEDGE[kb_key]
        lines.append(f"## {kb.get('name', topic)}")
        lines.append("")
        for field, value in kb.items():
            if field == "name":
                continue
            if isinstance(value, str):
                lines.append(f"**{field.replace('_',' ').title()}:** {value}")
                lines.append("")
            elif isinstance(value, list):
                lines.append(f"### {field.replace('_',' ').title()}")
                for item in value:
                    lines.append(f"- {item}")
                lines.append("")
    else:
        lines += [
            f"## Research Overview: {topic}",
            "",
            f"Paediatric research from AAP, RCPCH, WHO, NICE, IAP guidelines for {topic}.",
            "",
            "Enable live AI in Settings for detailed research, or consult your paediatrician.",
            ""
        ]

    lines += [
        "---",
        "## India Paediatric Resources",
        "- **IAP:** Indian Academy of Pediatrics (iapindia.org)",
        "- **AIIMS Paediatrics, New Delhi:** aiims.edu",
        "- **Apollo Cradle / Rainbow Children's Hospital**",
        "- **National Immunization Schedule:** mohfw.gov.in",
        "- **Emergency:** 112",
        "",
        f"WARNING - {DISCLAIMER}"
    ]
    return "\n".join(lines)

# Routes
@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": VERSION, "online": is_online(),
                    "pdf_extract": FITZ_OK, "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        return jsonify({"error": "No files"}), 400
    session_id = request.form.get("session_id") or str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for f in request.files.getlist("files"):
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        safe = f"{uuid.uuid4().hex}{ext}"
        dest = session_dir / safe
        f.save(str(dest))
        ftype = "pdf" if ext == ".pdf" else ("image" if ext in [".jpg",".jpeg",".png"] else "text")
        extracted = extract_pdf_text(dest) if ext == ".pdf" else ""
        results.append({"original": f.filename, "saved": safe, "type": ftype,
                        "size_kb": round(dest.stat().st_size/1024, 1), "has_content": bool(extracted)})
    existing = load_sessions().get(session_id, {})
    save_session(session_id, {"session_id": session_id, "files": existing.get("files",[]) + results})
    return jsonify({"success": True, "session_id": session_id, "uploaded": len(results), "files": results, "disclaimer": DISCLAIMER})

@app.route("/api/analyse", methods=["POST"])
def analyse():
    data = request.json or {}
    if not rate_limit_check():
        return jsonify({"error": "Rate limit exceeded. Please wait before making another request.", "mode": "rate_limited"}), 429
    topic        = data.get("topic", "General Paediatrics")
    condition    = data.get("condition", "")
    patient_info = data.get("patient_info", {})
    section      = data.get("section", "general")
    session_id   = data.get("session_id", "")
    provider     = validate_provider(data.get("provider", "anthropic"))
    api_key_from_client = sanitise_api_key(data.get("api_key", ""))
    effective_key = api_key_from_client or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")

    log.info(f"Analysis: topic={topic} section={section} provider={provider}")

    file_context = ""
    if session_id:
        sessions = load_sessions()
        if session_id in sessions:
            files = sessions[session_id].get("files", [])
            if files:
                file_context = f"\n\nUploaded Reports ({len(files)} files):\n"
                for fi in files[:10]:
                    file_context += f"- {fi['original']} ({fi['type']}, {fi['size_kb']} KB)\n"

    prompt = f"""
Paediatric Health Research Request:
Topic/Condition: {topic}
Specific Condition: {condition}
Child's Age: {patient_info.get('age','Not specified')}
Symptoms: {patient_info.get('symptoms','Not specified')}
Current Medications: {patient_info.get('medications','None specified')}
Other Conditions: {patient_info.get('conditions','None specified')}
Section Requested: {section}
{file_context}

Please provide comprehensive paediatric research covering:
1. Overview and clinical context appropriate for the child's age
2. Diagnosis criteria and investigations typically used
3. Evidence-based treatment options
4. Relevant medications with weight-based dosing principles from AAP/RCPCH/WHO/NICE guidelines
5. Home care and when to seek medical attention (red flags)
6. India-specific resources and hospitals
7. Questions to ask their paediatrician
8. Growth/development considerations if relevant

Reference AAP, RCPCH, WHO, NICE, IAP guidelines. Be specific about emergency warning signs for children.
"""
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key) if (effective_key and is_online()) else (None, "offline")
    if not result:
        result = build_offline_response(topic, condition, patient_info)
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "analysis": result, "topic": topic, "disclaimer": DISCLAIMER, "timestamp": datetime.datetime.now().isoformat()})

@app.route("/api/condition/<condition_name>", methods=["GET"])
def condition_detail(condition_name):
    cn = condition_name.lower().replace("-","_").replace(" ","_")
    if cn in KNOWLEDGE:
        return jsonify({"success": True, "mode": "offline_kb", "condition": KNOWLEDGE[cn], "disclaimer": DISCLAIMER})
    provider = validate_provider(request.args.get("provider", "anthropic"))
    api_key  = sanitise_api_key(request.args.get("api_key", ""))
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    prompt = f"Provide comprehensive clinical research about {condition_name} in paediatrics. Include: definition, prevalence, causes, age-specific symptoms, diagnosis criteria, evidence-based treatment options, prognosis, and management guidelines from AAP, RCPCH, WHO, NICE."
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = build_offline_response(condition_name)
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/growth/assess", methods=["POST"])
def assess_growth():
    data = request.json or {}
    age = data.get("age", "")
    weight = data.get("weight", "")
    height = data.get("height", "")
    head_circ = data.get("head_circumference", "")
    sex = data.get("sex", "")
    provider = validate_provider(data.get("provider", "anthropic"))
    api_key  = sanitise_api_key(data.get("api_key", ""))
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    prompt = f"""
Paediatric Growth Assessment Research:
Age: {age}
Sex: {sex}
Weight: {weight}
Height/Length: {height}
Head Circumference: {head_circ}

Please research what these measurements may suggest in the context of WHO/UK-WHO growth standards:
1. General context about typical growth ranges at this age (NOT a specific centile calculation without proper charts)
2. What patterns of growth tracking are reassuring vs concerning
3. When growth concerns warrant paediatric assessment
4. Questions to ask at the next health visit

IMPORTANT: This is general research only. Plotting on actual WHO/UK-WHO growth charts by a healthcare professional is required for accurate centile assessment.
"""
    result, mode = call_ai(prompt, provider=provider, api_key=effective_key)
    if not result:
        result = "Growth assessment requires plotting on official WHO or UK-WHO growth charts by a healthcare professional. General guidance: regaining birth weight by 2-3 weeks is expected for newborns; steady tracking along a centile line is generally reassuring; crossing 2+ centile lines in either direction warrants review. Enable live AI in Settings for detailed research, or discuss with your paediatrician/health visitor."
        mode = "offline"
    return jsonify({"success": True, "mode": mode, "content": result, "disclaimer": DISCLAIMER})

@app.route("/api/chat/send", methods=["POST"])
def chat_send():
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    provider = validate_provider(data.get("provider", "anthropic"))
    api_key  = sanitise_api_key(data.get("api_key", ""))
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    if data.get("request_ai", False) and is_online() and effective_key:
        prompt = f"A paediatric health question from a parent/carer: '{message}'\n\nProvide a compassionate, research-based response (3-4 paragraphs). Always end with reminder to consult their paediatrician, and for emergencies (breathing difficulty, seizure, unresponsive child, non-blanching rash) to call 112/999/911."
        result, _ = call_ai(prompt, max_tokens=800, provider=provider, api_key=effective_key)
    else:
        result = None
    return jsonify({"success": True, "ai_response": result, "disclaimer": "Not medical advice. Consult your paediatrician."})

@app.route("/api/report/generate", methods=["POST"])
def generate_report():
    data = request.json or {}
    topic   = data.get("topic", "General Paediatrics")
    patient = data.get("patient_info", {})
    provider = validate_provider(data.get("provider", "anthropic"))
    api_key  = sanitise_api_key(data.get("api_key", ""))
    effective_key = api_key or DEFAULT_PROVIDER_KEYS.get(provider, "") or (API_KEY if provider=="anthropic" else "")
    content = build_offline_response(topic, patient_info=patient)
    if effective_key and is_online():
        ai_content, _ = call_ai(f"Generate a comprehensive paediatric research report for: {topic}. Child info: {patient}. Cover assessment, treatment options, medications with weight-based dosing principles, home care, and when to seek medical attention.", max_tokens=3500, provider=provider, api_key=effective_key)
        if ai_content:
            content = ai_content
    report_id = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    report = {"report_id": report_id, "generated": datetime.datetime.now().isoformat(), "topic": topic, "patient": patient, "content": content, "disclaimer": DISCLAIMER}
    with open(REPORTS_DIR / f"{report_id}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return jsonify(report)

@app.route("/api/providers", methods=["GET"])
def list_providers():
    if not AI_PROVIDERS_OK:
        return jsonify({"providers": [], "error": "ai_providers module not available"})
    providers = []
    for key, cfg in ai_providers.PROVIDERS.items():
        providers.append({"id": key, "label": cfg["label"], "default_model": cfg["default_model"],
                          "key_prefix": cfg["key_prefix"], "get_key_url": cfg["get_key_url"],
                          "server_default_configured": bool(DEFAULT_PROVIDER_KEYS.get(key))})
    return jsonify({"providers": providers, "online": is_online()})

@app.route("/api/status", methods=["GET"])
def status():
    any_key = bool(API_KEY) or any(DEFAULT_PROVIDER_KEYS.values())
    return jsonify({
        "server": "running", "version": VERSION, "online": is_online(),
        "mode": "live_ai" if (any_key and is_online()) else "offline_research",
        "capabilities": {"pdf": FITZ_OK, "images": PIL_OK, "live_ai": bool(any_key and is_online()),
                         "offline": True, "multi_provider": AI_PROVIDERS_OK, "rate_limiting": True, "aes256_frontend": True},
        "knowledge_base": list(KNOWLEDGE.keys()),
        "providers": list(ai_providers.PROVIDERS.keys()) if AI_PROVIDERS_OK else [],
        "disclaimer": DISCLAIMER
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PediaCare AI Server")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    save_knowledge()
    log.info("=" * 60)
    log.info(f"  PediaCare AI Server v{VERSION} - Port {args.port}")
    log.info(f"  Online: {is_online()}")
    log.info(f"  URL: http://localhost:{args.port}")
    log.info("=" * 60)
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True, use_reloader=False)
