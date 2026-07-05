# PediaCare AI v1.0
## Paediatric Health Intelligence Platform

---

## IMPORTANT MEDICAL DISCLAIMER

**THIS IS AN AI-POWERED RESEARCH AND INFORMATION TOOL ONLY.**

- All content is AI-generated from published paediatric literature (AAP, RCPCH, WHO, NICE, IAP, PubMed)
- This is **NOT** a medical diagnosis, prescription, or clinical recommendation
- **ALWAYS** consult a qualified paediatrician before any health decision for your child
- **PAEDIATRIC EMERGENCY** — Call **112 (India) / 999 (UK) / 911 (US)** IMMEDIATELY for:
  - Difficulty breathing, blue lips or face
  - Seizure, or an unresponsive/floppy child
  - Non-blanching rash with fever (does not fade when pressed with a glass)
  - High fever (38°C+) in an infant under 3 months
  - Severe dehydration, choking that does not resolve, or anaphylaxis
- The creators accept **no liability** for health decisions made without professional paediatric consultation

---

## Quick Start (Windows)

1. Extract the ZIP to any folder (e.g., `C:\PediaCareAI\`)
2. Double-click **`START_PediaCare_AI.bat`**
3. Everything installs automatically (2-5 minutes first time)
4. Browser opens at `http://localhost:5080`
5. Accept disclaimer and begin

---

## Security — AES-256-GCM Key Encryption

Your AI provider API keys are protected with:
- **AES-256-GCM encryption** before storage in your browser
- **PBKDF2 key derivation** (100,000 iterations) from a device fingerprint
- Keys **never leave your browser** except going directly to the chosen AI provider's API
- Keys are **never logged** by the backend server
- Backend includes rate limiting (30 requests/60s) and strict provider whitelisting

---

## Choose Your AI Provider (5 Options)

Without any API key, the platform works in **offline research mode** using the embedded paediatrics knowledge base.

| Provider | Model Used | Get a Free Key |
|----------|-----------|----------------|
| **Claude** (Anthropic) | claude-sonnet-4 | console.anthropic.com |
| **ChatGPT** (OpenAI) | gpt-4o | platform.openai.com/api-keys |
| **Gemini** (Google) | gemini-2.0-flash | aistudio.google.com/apikey |
| **Grok** (xAI) | grok-2-latest | console.x.ai |
| **DeepSeek** | deepseek-chat | platform.deepseek.com/api_keys |

---

## File Structure

```
PediaCareAI/
├── START_PediaCare_AI.bat         <- MAIN LAUNCHER
├── DIAGNOSTIC.bat                 <- System health checker
├── REPAIR_AND_RECOVER.bat         <- Fix problems
├── DOWNLOAD_OFFLINE_PACKAGES.bat  <- Save packages for offline use
├── UPDATE.bat                     <- Update packages
├── STOP_SERVER.bat                <- Stop the server
├── server.py                      <- Python Flask backend
├── README.md                      <- This file
├── modules/
│   └── ai_providers.py            <- Multi-provider AI module
├── static/
│   └── index.html                 <- Full web application
├── uploads/                       <- Your uploaded reports
├── offline_packages/              <- Cached Python packages
├── venv/                          <- Python environment (auto-created)
├── logs/                          <- Server and diagnostic logs
├── data/                          <- Knowledge base and sessions
└── reports_db/                    <- Generated AI reports
```

---

## What's Covered (10 Sections)

### Child Health Conditions (40+)
Fever and febrile seizures, otitis media, tonsillitis, UTI, chickenpox, hand-foot-mouth disease, roseola, bronchiolitis, croup, asthma, pneumonia, cystic fibrosis, gastroenteritis, constipation, cow's milk protein allergy, infant reflux/GORD, intussusception, coeliac disease, eczema, nappy rash, Kawasaki disease, non-blanching rash, autism spectrum disorder, ADHD, speech delay, sleep problems, tantrums, failure to thrive, childhood obesity, food allergy, and more via live AI.

### Growth Tracker
Interactive measurement entry (age, sex, weight, height, head circumference) with AI-researched growth context, plus a reference table of typical weight/height gain by age and guidance on when centile crossing warrants review.

### Vaccination Schedule
Full India National Immunization Schedule and UK Routine schedule tables, plus a dedicated safety and common concerns section addressing the MMR-autism myth, normal side effects, illness/vaccination timing, and catch-up guidance.

### Medicines (5 Categories)
Pain and fever (paracetamol/ibuprofen weight-based dosing, Reye syndrome warning), antibiotics (when needed vs not, resistance awareness), asthma inhalers (technique, spacers, action plans), allergy and skin (antihistamines, emollients, topical steroids, adrenaline auto-injectors), vitamins and supplements.

### Emergency Guide
Breathing difficulty, choking (infant and child techniques), seizures, anaphylaxis — all with step-by-step first aid. Plus non-blanching rash, severe dehydration, head injury red flags, burns/scalds, and safeguarding guidance.

### Newborn Care
Routine newborn checks (NIPE, blood spot screening, hearing screening), jaundice (physiological vs pathological), feeding (hunger cues, normal weight loss), umbilical cord care.

### Nutrition
Weaning/complementary feeding timing and allergenic food introduction, picky eating strategies, childhood obesity (whole-family approach), food allergy management.

### Development
Milestone table by age (gross motor, fine motor, language, social), red flags requiring assessment, autism spectrum disorder, ADHD, speech and language delay.

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 4 GB | 8 GB |
| Storage | 2 GB free | 5 GB free |
| Internet | For first setup | For live AI |
| Python | Auto-installed | 3.10-3.12 |

---

## India-Specific Resources

| Resource | Website |
|----------|---------|
| IAP — Indian Academy of Pediatrics | iapindia.org |
| AIIMS Paediatrics, New Delhi | aiims.edu |
| National Immunization Schedule | mohfw.gov.in |
| **Emergency** | **112** |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Double-click does nothing | Right-click → Run as Administrator |
| Python not found | Launcher downloads it automatically (needs internet) |
| Browser doesn't open | Go to http://localhost:5080 manually |
| Port in use | Run STOP_SERVER.bat, then START again |
| Package install fails | Run REPAIR_AND_RECOVER.bat → Option 6 |
| Works offline | Run DOWNLOAD_OFFLINE_PACKAGES.bat once while online |

---

## Clinical Sources

- **AAP** — American Academy of Pediatrics (aap.org)
- **RCPCH** — Royal College of Paediatrics and Child Health (rcpch.ac.uk)
- **WHO** — World Health Organization Child Health
- **NICE** — National Institute for Health and Care Excellence, UK
- **IAP** — Indian Academy of Pediatrics (iapindia.org)
- **PubMed** — National Library of Medicine Research Database

---

## Legal Notice

This software is provided for research and educational purposes only. The creators make no representations about medical accuracy, completeness, or fitness for clinical use. Use of this tool does not constitute a medical consultation. The creators are not liable for any health outcomes arising from use of this platform. By using this software you confirm you have read and accepted the full medical disclaimer.

**PAEDIATRIC EMERGENCY: Call 112 (India) / 999 (UK) / 911 (US) immediately. Do not rely on this software in an emergency.**

---

*PediaCare AI v1.0 — Paediatric Health Intelligence Platform*
*Research informs. Your paediatrician heals. Use both.*
