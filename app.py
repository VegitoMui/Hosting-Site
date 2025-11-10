# app.py
from datetime import date
import json
import pandas as pd
import streamlit as st

from config import DEFAULT_SPEC  # your existing spec
from pricing import (
    load_spec, currency, working_days_per_week,
    buffer_days, to_calendar_days, add_business_days
)
from ui_layers_drag import (
    render_layer1_drag, render_layer2_drag, render_layer3_drag
)

# ---------- Page setup (no visible title/caption) ----------
st.set_page_config(page_title="Quote Builder", page_icon="🧭", layout="centered")

# Minimal, clean styling
st.markdown("""
<style>
/* hide default Streamlit header/footer */
header {visibility: hidden;}
footer {visibility: hidden;}
/* tighter content width + spacing */
.block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1024px;}
/* nicer subheaders */
h2, h3 { margin-top: 0.25rem; }
/* subtle caption color */
.st-emotion-cache-5rimss, .stCaption { color: #5f6368 !important; }
/* metric emphasis */
div[data-testid="stMetricValue"] { font-weight: 700; }
/* dataframe header weight */
[data-testid="stTable"] thead th { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar: JSON spec editor ----------
st.sidebar.header("⚙️ Pricing & Timeline Spec")
default_text = json.dumps(DEFAULT_SPEC, indent=2)
spec_text = st.sidebar.text_area("Paste/modify JSON spec then click **Apply**.", value=default_text, height=380)
if st.sidebar.button("Apply"):
    st.session_state["_spec_text"] = spec_text

spec_raw = st.session_state.get("_spec_text", spec_text)
SPEC, err = load_spec(spec_raw, DEFAULT_SPEC)
if err:
    st.sidebar.error(err)
else:
    st.sidebar.success("Spec applied.")

# ---------- Main flow ----------
# Select source (drag priorities; shows details-only table; uses weeks upper-bound)
wd = working_days_per_week(SPEC)
l1_rows, l1_cost, l1_impl_days_sum = render_layer1_drag(SPEC, wd)

# Select middleware (Azure option by drag)
azure_choice, l2_cost, l2_days = render_layer2_drag(SPEC, num_sources=len(l1_rows))

# Select destination + Add-ons
target_name, l3_fixed, l3_base_days, addon_rows, l3_addons_cost, l3_addons_days = render_layer3_drag(SPEC)

# ---------- Summary (prices only) ----------
st.divider()
st.subheader("Summary (Prices)")
grand_total = (l1_cost or 0.0) + (l2_cost or 0.0) + (l3_fixed or 0.0) + (l3_addons_cost or 0.0)
summary_df = pd.DataFrame(
    [
        {"Section": "Select source",            "Amount (USD)": l1_cost},
        {"Section": "Select middleware",        "Amount (USD)": l2_cost},
        {"Section": "Select destination (fixed)","Amount (USD)": l3_fixed},
        {"Section": "Add-ons",                  "Amount (USD)": l3_addons_cost},
        {"Section": "TOTAL",                    "Amount (USD)": grand_total},
    ]
)
st.dataframe(summary_df, hide_index=True, use_container_width=True)
st.metric("Total Price", f"${grand_total:,.2f}")

# ---------- Total time only (weeks→business days via working_days_per_week) ----------
buffer = buffer_days(SPEC)
total_business_days = int(l1_impl_days_sum) + int(l2_days) + int(l3_base_days + l3_addons_days) + int(buffer)
approx_calendar = to_calendar_days(total_business_days, wd)

st.subheader("Total Implementation Time")
st.success(f"**Total:** {total_business_days} business days (~{approx_calendar} calendar days, assuming {wd} working days/week).")

today = date.today()
finish = add_business_days(today, total_business_days, wd)
st.write(f"**Start:** {today.isoformat()} → **Finish:** {finish.isoformat()}")

# ---------- Export JSON ----------
export_payload = {
    "currency": currency(SPEC),
    "billing_cycle": SPEC.get("billing_cycle", "monthly"),
    "selections": {
        "source": l1_rows,  # contains Timeline (weeks)_max + price (for record)
        "middleware": azure_choice,
        "destination": {"target": target_name, "addons": [r['Add-on'] for r in addon_rows]}
    },
    "totals": {
        "source": l1_cost,
        "middleware": l2_cost,
        "destination_fixed": l3_fixed,
        "addons": l3_addons_cost,
        "grand_total": grand_total
    },
    "timeline": {
        "source_weeks_upper_bound_used": True,
        "total_business_days": total_business_days,
        "approx_calendar_days": approx_calendar,
        "start_date": today.isoformat(),
        "finish_date": finish.isoformat()
    }
}
export_json = json.dumps(export_payload, indent=2)

st.download_button(
    "📥 Download Quote + Timeline (JSON)",
    data=export_json.encode("utf-8"),
    file_name="quote_timeline.json",
    mime="application/json"
)

with st.expander("Preview JSON export"):
    st.code(export_json, language="json")
