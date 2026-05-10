"""TRA VFD Configuration"""
VFD_TAX_CODES = {
    "1": "Standard VAT (18%)",
    "2": "Zero Rated",
    "3": "Exempt",
}

VFD_CUSTOMER_ID_TYPES = {
    1: "TIN",
    2: "NID (NIN)",
    3: "Passport",
    4: "Driving License",
    5: "Voter ID",
    6: "Other",
}

VFD_RECEIPT_TYPES = {
    "RCTNUM": "Receipt Number (matches GC)",
    "DC": "Daily Counter (resets at midnight)",
    "GC": "Global Counter (never resets)",
    "ZNUM": "Z-Report Number (YYYYMMDD)",
}
