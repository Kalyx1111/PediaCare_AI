# PediaCare AI v1.0
## Paediatrics & Child Health Intelligence Platform
### Complete Setup, Usage & Troubleshooting Guide

---

## ⚠️ CRITICAL MEDICAL DISCLAIMER

**THIS IS AN AI-POWERED RESEARCH AND INFORMATION TOOL ONLY.**

- All information is generated from published medical literature and guidelines.
- Accuracy, completeness, and clinical applicability may be incomplete, outdated, or incorrect.
- This is **NOT** a medical diagnosis, prescription, or clinical recommendation.
- **ALWAYS** consult a qualified paediatrician or healthcare professional before:
  - Giving medications
  - Undergoing tests or investigations
  - Delaying medical attention
  - Making healthcare decisions for a child

### 🚑 FOR EMERGENCIES

| Country | Number |
|----------|---------|
| India | 108 |
| UK | 999 |
| USA | 911 |

**Breathing difficulty, choking, seizures, severe dehydration, allergic reactions, unconsciousness, or rapidly worsening illness require immediate emergency care.**

**FOR RESEARCH AND EDUCATIONAL PURPOSES ONLY.**

---

## 🚀 Quick Start

### Windows (Recommended)

1. Extract the ZIP anywhere.

2. Double-click:

```text
START_PediaCare_AI.bat
```

3. Everything installs automatically.

4. Browser opens automatically:

```text
http://localhost:5090
```

5. Accept the disclaimer and begin.

---

## 📁 File Structure

```text
PediaCareAI/
├── START_PediaCare_AI.bat
├── DIAGNOSTIC.bat
├── REPAIR_AND_RECOVER.bat
├── DOWNLOAD_OFFLINE_PACKAGES.bat
├── UPDATE.bat
├── STOP_SERVER.bat
├── server.py
├── README.md
├── static/
│   └── index.html
├── uploads/
├── offline_packages/
├── venv/
├── logs/
├── data/
└── reports_db/
```

---

## 🔧 BAT Files Explained

| File | Purpose | When To Use |
|------|----------|-------------|
| START_PediaCare_AI.bat | Main launcher | Daily use |
| DIAGNOSTIC.bat | System health check | Troubleshooting |
| REPAIR_AND_RECOVER.bat | Repair installation | Startup failures |
| DOWNLOAD_OFFLINE_PACKAGES.bat | Cache packages offline | Run once |
| UPDATE.bat | Update dependencies | Monthly |
| STOP_SERVER.bat | Stop server | Exit application |

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|----------|--------------|
| OS | Windows 10 | Windows 11 |
| RAM | 4 GB | 8 GB |
| Storage | 3 GB | 10 GB |
| Internet | First setup only | Broadband |
| Python | Auto-installed | 3.10–3.12 |

---

## 👶 Platform Features

### 🩺 Paediatric Conditions

Research support for 40+ conditions across:

#### Fever & Infections

- Viral fever
- Tonsillitis
- Ear infections
- Urinary tract infections
- Dengue
- Hand, Foot and Mouth Disease
- Chickenpox

#### Respiratory Conditions

- Asthma
- Bronchiolitis
- Croup
- Pneumonia
- Allergic rhinitis
- Wheezing disorders

#### Gastrointestinal Conditions

- Gastroenteritis
- Constipation
- Reflux
- Abdominal pain
- Food intolerance
- Coeliac disease

#### Skin & Rashes

- Eczema
- Impetigo
- Urticaria
- Heat rash
- Viral exanthems
- Fungal infections

#### Development & Behaviour

- Autism Spectrum Disorder
- ADHD
- Speech delay
- Learning difficulties
- Sleep problems
- Behavioural concerns

---

### 📈 Growth Tracker

Interactive growth assessment tool.

Enter:

- Age
- Sex
- Weight
- Height
- Head circumference

Receive:

- Growth interpretation
- Typical growth expectations
- Weight gain references
- Height gain references
- AI-generated growth context

---

### 💉 Vaccination Schedule

#### India National Immunization Schedule

Includes:

- Birth vaccines
- Infant schedule
- Childhood boosters
- Adolescent vaccines

#### United Kingdom Schedule

Complete NHS childhood immunisation schedule.

#### Vaccine Safety & Myths

Dedicated section covering:

- MMR vaccine
- Autism myth clarification
- Vaccine safety evidence
- Common parental concerns

---

### 💊 Medicines

#### Pain & Fever

- Paracetamol
- Ibuprofen
- Weight-based dosing
- Reye syndrome warning

#### Antibiotics

- Common paediatric antibiotics
- Indications
- Safety guidance

#### Asthma Inhalers

- Reliever inhalers
- Preventer inhalers
- Spacer use guidance

#### Allergy & Skin Medicines

- Antihistamines
- Topical treatments
- Eczema management

#### Vitamins & Supplements

- Vitamin D
- Iron
- Multivitamins
- Nutritional supplements

---

### 🚨 Emergency Guide

#### Breathing Difficulty

Immediate action steps.

#### Choking

Separate guidance for:

- Infants
- Children

#### Seizures

#### Anaphylaxis

Additional emergency guidance includes:

- Non-blanching rash
- Severe dehydration
- Head injury
- Burns
- Safeguarding concerns

Emergency numbers (108/999/911) are prominently displayed throughout the platform.

---

### 👶 Newborn Care

#### NIPE Checks

#### Newborn Screening

- Blood spot screening
- Hearing screening

#### Jaundice

- Physiological jaundice
- Pathological jaundice

#### Feeding Support

- Feeding cues
- Breastfeeding information
- Formula guidance

#### Umbilical Cord Care

---

### 🥗 Nutrition

#### Weaning

- Timing of solids
- Complementary feeding

#### Food Allergy Prevention

- Allergenic food introduction
- LEAP study evidence

#### Picky Eating

#### Childhood Obesity

#### Food Allergy Management

---

### 🧠 Development

Complete milestone guidance across:

#### Gross Motor Skills

#### Fine Motor Skills

#### Speech & Language

#### Social Development

Includes:

- Milestone tables by age
- Developmental red flags
- Autism recognition
- ADHD awareness
- Speech delay guidance

---

## 📚 Clinical Sources

Information references include:

- AAP — American Academy of Pediatrics
- RCPCH — Royal College of Paediatrics and Child Health
- IAP — Indian Academy of Pediatrics
- NICE — National Institute for Health and Care Excellence
- NHS — National Health Service
- WHO — World Health Organization
- CDC — Centers for Disease Control and Prevention
- PubMed — National Library of Medicine

---

## 🔑 AI Providers (5 Supported)

| Provider | Model |
|----------|--------|
| OpenAI | GPT-4o |
| Google | Gemini 2.0 Flash |
| xAI | Grok |
| Anthropic | Claude Sonnet |
| DeepSeek | DeepSeek Chat |

Without an API key, PediaCare AI operates using the embedded child health knowledge base.

---

## 🔒 Privacy & Security

### Built-In Security Architecture

- AES-256-GCM encryption
- PBKDF2 key derivation (100,000 iterations)
- Secure local storage (`pediacare_keys`)
- API key sanitisation
- Provider whitelist validation
- Rate limiting functionality
- Local-first architecture
- No telemetry or tracking
- Full offline mode supported

API keys remain stored locally and are never transmitted to third-party servers except selected AI providers.

---

## 🌐 Online vs Offline Mode

| Feature | Live AI | Offline |
|---------|---------|----------|
| Condition Research | Full | Core Conditions |
| Growth Assessment | Detailed | Embedded |
| Vaccination Guidance | Detailed | Embedded |
| Development Assessment | Detailed | Embedded |
| Upload Analysis | AI Assisted | Text Extraction |
| Chat | AI Responses | Basic Responses |

---

## 🇮🇳 Important Resources

| Resource | Website |
|----------|---------|
| AIIMS Paediatrics | aiims.edu |
| Indian Academy of Pediatrics | iapindia.org |
| Apollo Hospitals | apollohospitals.com |
| Fortis Healthcare | fortishealthcare.com |
| WHO | who.int |
| UNICEF India | unicef.org/india |
| Emergency | 108 |

---

## 🔧 Troubleshooting

### Browser Doesn't Open

Open manually:

```text
http://localhost:5090
```

### Package Installation Fails

Run:

```text
REPAIR_AND_RECOVER.bat
```

### Port Already In Use

Run:

```text
STOP_SERVER.bat
```

### Server Errors

Inspect:

```text
logs\server_*.log
```

or run:

```text
DIAGNOSTIC.bat
```

---

## ⚖️ Legal Notice

This software is provided **"as is"** for research and educational purposes only.

The creators make no representations regarding medical accuracy, completeness, or suitability for clinical use.

Use of this platform does **not** constitute a doctor-patient relationship.

The creators are **not liable** for health outcomes arising from use of this software.

By using this application, you acknowledge that you have read and accepted the medical disclaimer.

---

# ❤️ PediaCare AI v1.0
## Paediatrics & Child Health Intelligence Platform

*Knowledge supports healthy childhoods. Your paediatrician heals. Use both.*
