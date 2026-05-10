"""NHIF API Configuration"""
NHIF_ENDPOINTS = {
    "auth": "/stsidentity",
    "verify": "/verification",
    "price_package": "/GetPricePackage",
    "claim_submit": "/ClaimSubmit",
    "verify_services": "/VerifyServices",
}

NHIF_SCHEMES = {
    "nhif_tanzania": "NHIF Tanzania",
    "nhif_zanzibar": "NHIF Zanzibar",
    "private": "Private Insurance",
}

# Item categories for NHIF claims
NHIF_ITEM_CATEGORIES = [
    ("CONS", "Consultation"),
    ("PROC", "Procedure"),
    ("LAB", "Laboratory"),
    ("RAD", "Radiology"),
    ("MED", "Medication"),
    ("WARD", "Ward Charges"),
]
