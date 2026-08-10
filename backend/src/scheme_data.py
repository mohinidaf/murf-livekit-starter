"""
Local dataset of Indian government financial scheme document checklists.

Data source: Publicly available scheme guidelines from respective ministry
websites (PM-KISAN, PMJJBY, PMSBY, MUDRA, Sukanya Samriddhi, etc.).

This is a LOCAL snapshot. It is NOT live data.
Last updated: 2026-08-10

For the most current requirements, always refer to the official scheme
website or your nearest bank / government office.
"""

SCHEMES = {
    "pm kisan": {
        "full_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "objective": (
            "Provides income support of six thousand rupees per year "
            "to small and marginal farmer families."
        ),
        "documents": [
            "Aadhaar card",
            "Bank account details (account number and IFSC code)",
            "Land records (Khatauni or equivalent land ownership document)",
            "Passport-size photograph",
            "Mobile number linked to Aadhaar",
        ],
        "eligibility_notes": (
            "Farmer families with cultivable landholding. "
            "Institutional landholders, former or current constitutional "
            "post holders, and income-tax payers are excluded."
        ),
    },
    "pmjjby": {
        "full_name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "objective": (
            "Life insurance cover of two lakh rupees at a low annual "
            "premium for individuals aged 18 to 50."
        ),
        "documents": [
            "Aadhaar card",
            "Bank account details (auto-debit mandate)",
            "Passport-size photograph",
            "Nominee details (name and relationship)",
            "Age proof (Aadhaar or birth certificate)",
        ],
        "eligibility_notes": (
            "Individuals aged 18 to 50 years with a savings bank "
            "account. One-year cover from June 1 to May 31."
        ),
    },
    "pmsby": {
        "full_name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "objective": (
            "Accidental death and disability insurance cover of two "
            "lakh rupees at a very low annual premium."
        ),
        "documents": [
            "Aadhaar card",
            "Bank account details (auto-debit mandate)",
            "Passport-size photograph",
            "Nominee details (name and relationship)",
        ],
        "eligibility_notes": (
            "Individuals aged 18 to 70 years with a savings bank "
            "account. Annual premium is deducted via auto-debit."
        ),
    },
    "mudra": {
        "full_name": "MUDRA (Micro Units Development and Refinance Agency) Loan",
        "objective": (
            "Provides loans up to ten lakh rupees to non-corporate, "
            "non-farm small or micro enterprises."
        ),
        "documents": [
            "Identity proof (Aadhaar, PAN, or voter ID)",
            "Address proof (utility bill, Aadhaar, or rental agreement)",
            "Passport-size photograph",
            "Business plan or project report",
            "Proof of business existence (registration, licence, or shop act certificate)",
            "Bank account statements for the last six months",
            "Quotation for machinery or equipment (if applicable)",
            "Category certificate (SC/ST/OBC) if applicable",
        ],
        "eligibility_notes": (
            "Three categories: Shishu (up to fifty thousand), "
            "Kishore (fifty thousand to five lakh), "
            "Tarun (five lakh to ten lakh). "
            "Applicable to shops, workshops, service enterprises, "
            "food units, and other small businesses."
        ),
    },
    "sukanya samriddhi": {
        "full_name": "Sukanya Samriddhi Yojana (SSY)",
        "objective": (
            "Savings scheme for the benefit of a girl child, "
            "offering a high interest rate and tax benefits."
        ),
        "documents": [
            "Girl child's birth certificate",
            "Address proof of the parent or legal guardian",
            "Identity proof of the parent or legal guardian (Aadhaar, PAN, or voter ID)",
            "Passport-size photograph of the depositor",
        ],
        "eligibility_notes": (
            "Can be opened for a girl child below the age of ten "
            "years. Maximum two accounts per family. "
            "Minimum deposit two hundred fifty rupees per year, "
            "maximum one and a half lakh rupees per year."
        ),
    },
    "atal pension yojana": {
        "full_name": "Atal Pension Yojana (APY)",
        "objective": (
            "Guaranteed minimum pension for workers in the unorganised "
            "sector after the age of sixty."
        ),
        "documents": [
            "Aadhaar card",
            "Bank account details",
            "Mobile number",
            "Nominee details",
        ],
        "eligibility_notes": (
            "Indian citizens aged 18 to 40 with a bank or post "
            "office savings account. Subscriber chooses a pension "
            "amount between one thousand and five thousand rupees "
            "per month."
        ),
    },
    "jan dhan": {
        "full_name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "objective": (
            "Financial inclusion scheme providing universal access "
            "to banking facilities with a RuPay debit card."
        ),
        "documents": [
            "Aadhaar card (or any other valid identity document)",
            "Address proof",
            "Passport-size photograph",
            "Mobile number (optional but recommended)",
        ],
        "eligibility_notes": (
            "Any Indian citizen above the age of ten years can open "
            "a Jan Dhan account. No minimum balance required. "
            "Includes overdraft facility and RuPay card with "
            "accident insurance cover."
        ),
    },
    "pm swayam siksha prayog": {
        "full_name": "Pradhan Mantri Swayam Siksha Prayog",
        "objective": (
            "Skill development and training for youth under the Skill India Mission."
        ),
        "documents": [
            "Aadhaar card",
            "Age proof (birth certificate or Aadhaar)",
            "Educational certificates",
            "Passport-size photograph",
            "Bank account details",
            "Caste certificate (if applicable)",
        ],
        "eligibility_notes": (
            "Youth aged 15 to 45 years. Focus on school and "
            "college dropouts as well as unemployed youth."
        ),
    },
    "kcc": {
        "full_name": "Kisan Credit Card (KCC)",
        "objective": (
            "Provides affordable credit to farmers for their "
            "agricultural and allied needs."
        ),
        "documents": [
            "Aadhaar card",
            "Land records or land ownership documents",
            "Bank account details",
            "Passport-size photograph",
            "Identity and address proof",
            "Crop details and sowing season information",
            "Security documents (if loan exceeds the limit)",
        ],
        "eligibility_notes": (
            "Farmer, fisherman, or animal husbandry owner with "
            "cultivable land. Covers crop loans, post-harvest "
            "expenses, and working capital for agriculture."
        ),
    },
    "ayushman bharat": {
        "full_name": "Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)",
        "objective": (
            "Health insurance cover of five lakh rupees per family "
            "per year for secondary and tertiary hospitalisation."
        ),
        "documents": [
            "Aadhaar card or any government-issued photo ID",
            "Ration card (for family verification)",
            "Income certificate (if required for eligibility check)",
            "Mobile number",
        ],
        "eligibility_notes": (
            "Families identified based on the deprivation criteria "
            "of the Socio Economic Caste Census 2011. "
            "Covers over five lakh rupees per family per year "
            "at empanelled hospitals."
        ),
    },
}

DATA_SOURCE = (
    "Local dataset compiled from publicly available scheme guidelines. "
    "Sources include respective ministry websites and official notifications."
)

LAST_UPDATED = "2026-08-10"


def get_scheme_info(scheme_name: str) -> dict | None:
    """Return scheme info matching the given name, or None."""
    key = scheme_name.strip().lower()

    if key in SCHEMES:
        return SCHEMES[key]

    for scheme_key, info in SCHEMES.items():
        if key in scheme_key or scheme_key in key:
            return info

    return None


def list_available_schemes() -> list[str]:
    """Return sorted list of available scheme short names."""
    return sorted(SCHEMES.keys())
