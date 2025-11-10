# config.py
DEFAULT_SPEC = {
    "currency": "USD",
    "billing_cycle": "monthly",
    "timeline_policy": {
        "working_days_per_week": 5,
        "assumption_notes": "Sources are onboarded in parallel up to 'parallel_sources'. Azure provisioning is sequential before target setup.",
        "parallel_sources": 2,
        "buffer_days": 2
    },
    "layer1_itsm_sources": [
        {
            "name": "ServiceNow",
            "pricing_model": "flat_per_source",
            "tiers": {
                "low":    {"price": 120, "impl_days": 2},
                "medium": {"price": 200, "impl_days": 3},
                "high":   {"price": 320, "impl_days": 5}
            }
        },
        {
            "name": "Tanium",
            "pricing_model": "flat_per_source",
            "tiers": {
                "low":    {"price": 90,  "impl_days": 2},
                "medium": {"price": 160, "impl_days": 3},
                "high":   {"price": 260, "impl_days": 4}
            }
        },
        {
            "name": "BMC",
            "pricing_model": "flat_per_source",
            "tiers": {
                "low":    {"price": 110, "impl_days": 2},
                "medium": {"price": 180, "impl_days": 3},
                "high":   {"price": 300, "impl_days": 4}
            }
        }
    ],
    "layer2_azure": {
        "options": [
            {
                "name": "Customer’s Azure subscription",
                "cost": {"fixed": 0, "per_source": 0},
                "provision_days": 1,
                "notes": "Lightweight validation & role wiring only."
            },
            {
                "name": "Managed Azure (provided by us)",
                "cost": {"fixed": 250, "per_source": 40},
                "provision_days": 3,
                "notes": "We create & configure resources; includes governance."
            }
        ]
    },
    "layer3_target": {
        "required": {
            "name": "Agentic IT Service",
            "fixed_price": 400,
            "base_days": 3,
            "notes": "Core landing zone, pipelines, and basic QA."
        },
        "addons": [
            {"name": "Enhanced SLA (24x7)", "type": "flat", "price": 200, "extra_days": 1},
            {"name": "PII Redaction Pipeline", "type": "flat", "price": 180, "extra_days": 2},
            {"name": "Data Retention (12 months)", "type": "flat", "price": 120, "extra_days": 1},
            {"name": "Observability Pack (dashboards + alerts)", "type": "flat", "price": 150, "extra_days": 1}
        ]
    }
}

# ---- Complexity criteria (copied from Factory Model.xlsx → "Complexity criteria") ----
COMPLEXITY_CRITERIA = {
    "low": {
        "volumetrics": "<500K records total (Incident, Problem, CR, SR)",
        "customization": (
            "Standard ITSM Objects Only (Incident, Problem, Change, SR).\n"
            "Minimal custom fields (<10%).\n"
            "Simple 1:1 mapping.\n"
            "No CMDB or Knowledge migration."
        ),
        "timeline_text": "2-3 weeks post prerequisite validation",
        "weeks_min": 2,
        "weeks_max": 3,
    },
    "medium": {
        "volumetrics": "<2.5M records total (Incident, Problem, CR, SR)",
        "customization": (
            "Standard + Custom Objects (Knowledge Articles, limited CMDB).\n"
            "Moderate custom fields (10-20%).\n"
            "Basic lookups and conditional data cleansing required."
        ),
        "timeline_text": "3-5 weeks post prerequisite validation",
        "weeks_min": 3,
        "weeks_max": 5,
    },
    "high": {
        "volumetrics": "> 2.5M records (including deep archival data).",
        "customization": (
            "Deep Customization (>20% custom fields, full CMDB migration with complex relationship mapping).\n"
            "Advanced transformation with external enrichment or custom business logic."
        ),
        "timeline_text": "5-7 weeks post prerequisite validation",
        "weeks_min": 5,
        "weeks_max": 7,
    },
}
