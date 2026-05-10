"""SMS Provider Configuration"""
SMS_PROVIDERS = {
    "notify_africa": {
        "name": "Notify Africa",
        "base_url": "https://api.notifyafrica.com/v1",
        "latency_ms": 24,
        "features": ["swahili_support", "bulk_sms", "delivery_reports"],
    },
    "beem_africa": {
        "name": "Beem Africa",
        "base_url": "https://apisms.beem.africa/v1",
        "features": ["sms", "ussd", "whatsapp", "omnichannel"],
    },
    "fasthub": {
        "name": "FastHub",
        "base_url": "https://api.fasthub.co.tz/v1",
        "features": ["tcra_compliant", "detailed_tracking", "webhooks"],
    },
}

# Default Swahili templates
SWAHILI_TEMPLATES = {
    "appointment_reminder": "Habari {name}, unakumbushwa kuhusu tembeleo lako la hospitali kesho {time}. Tafadhali fika kwa wakati. Asante.",
    "lab_ready": "Habari {name}, matokeo ya vipimo vyako vimekamilika. Tafadhali tembelea kituo cha afya kwa maelezo zaidi.",
    "otp": "HospFlow OTP yako ni: {code}. Usiambie mtu. Muda wake ni dakika 5.",
    "receipt": "HospFlow Receipt: {receipt_num} TZS {amount} Date: {date} Asante kwa kutumia huduma zetu.",
}
