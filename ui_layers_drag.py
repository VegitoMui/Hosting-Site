# ui_layers_drag.py
from typing import Dict, List
import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items
from config import COMPLEXITY_CRITERIA  # embedded complexity details from config.py


# ---------- Select source (ONE only; lock UI after selection) ----------
def render_layer1_drag(spec: dict, working_days_per_week: int):
    """
    User can drag exactly ONE source into Low / Medium / High.
    After selection, other sources are not shown (non-draggable).
    A 'Change source' button unlocks to re-select.
    Table shows complexity details (no price).
    """
    st.subheader("Select source")

    itsm_options: List[Dict] = spec.get("layer1_itsm_sources", [])
    all_sources = [o["name"] for o in itsm_options]

    ss = st.session_state
    if "l1_selected_source" not in ss:
        ss.l1_selected_source = None
    if "l1_selected_tier" not in ss:
        ss.l1_selected_tier = None

    # ----- LOCKED VIEW (source chosen): show only the chosen source; others hidden (non-draggable)
    if ss.l1_selected_source and ss.l1_selected_tier in ("low", "medium", "high"):
        chosen_source = ss.l1_selected_source
        chosen_tier = ss.l1_selected_tier

        # Tiny control to change source (unlocks UI)
        cols = st.columns([1, 2])
        with cols[0]:
            st.button("Change source", key="l1_change_source_btn", on_click=_l1_reset_selection)
        with cols[1]:
            st.info(f"Selected source: **{chosen_source}**  •  Priority: **{chosen_tier.title()}**")

        # Allow changing priority by dragging the ONE item between Low/Medium/High
        low_items  = [chosen_source] if chosen_tier == "low" else []
        med_items  = [chosen_source] if chosen_tier == "medium" else []
        high_items = [chosen_source] if chosen_tier == "high" else []

        original_items = [
            {"header": "Low",    "items": low_items},
            {"header": "Medium", "items": med_items},
            {"header": "High",   "items": high_items},
        ]
        st.caption("Adjust priority by dragging the selected source between Low / Medium / High.")
        result = sort_items(original_items, multi_containers=True, key="layer1_locked_sortables")

        # Read back tier if the user moved it
        new_tier = chosen_tier
        for container in result:
            header = container.get("header")
            items = container.get("items", [])
            if chosen_source in items:
                new_tier = header.lower()
                break

        if new_tier != chosen_tier:
            ss.l1_selected_tier = new_tier
            st.rerun()

        # Compute details
        return _l1_compute_table_and_totals(itsm_options, chosen_source, ss.l1_selected_tier, working_days_per_week)

    # ----- UNLOCKED VIEW (no source yet): show full drag with all sources
    st.caption("Drag exactly one source into Low / Medium / High.")
    original_items = [
        {"header": "Unassigned", "items": all_sources},
        {"header": "Low",       "items": []},
        {"header": "Medium",    "items": []},
        {"header": "High",      "items": []},
    ]
    result = sort_items(original_items, multi_containers=True, key="layer1_unlock_sortables")

    # Find first placed source (ignore extras)
    chosen_source, chosen_tier = None, None
    for container in result:
        header = container.get("header")
        if header in ("Low", "Medium", "High"):
            items = container.get("items", [])
            if items and chosen_source is None:
                chosen_source = items[0]
                chosen_tier = header.lower()

    if not chosen_source:
        st.info("Please drag exactly one source into Low, Medium, or High to continue.")
        return [], 0.0, 0

    # Persist selection and lock UI
    ss.l1_selected_source = chosen_source
    ss.l1_selected_tier = chosen_tier
    st.rerun()


def _l1_reset_selection():
    """Clear Layer-1 selection to re-enable choosing a different source."""
    ss = st.session_state
    ss.l1_selected_source = None
    ss.l1_selected_tier = None


def _l1_compute_table_and_totals(itsm_options: List[Dict], chosen_source: str, chosen_tier: str, working_days_per_week: int):
    """Build the details table and compute price + business days for the selected source."""
    # Excel details (embedded)
    c = COMPLEXITY_CRITERIA.get(chosen_tier, {})
    weeks_max = int(c.get("weeks_max", 0))
    impl_days_sum = weeks_max * working_days_per_week

    # Silent price (for totals)
    src_def = next((o for o in itsm_options if o["name"] == chosen_source), {})
    tiers = src_def.get("tiers", {})
    price = float(tiers.get(chosen_tier, {}).get("price", 0.0))

    detail_row = {
        "Source": chosen_source,
        "Priority": chosen_tier.title(),
        "Volumetrics": c.get("volumetrics", ""),
        "Customization & Logic": c.get("customization", ""),
        "Timeline (weeks)": c.get("timeline_text", ""),
        "_weeks_max": weeks_max,
        "_price": price,
    }

    df = pd.DataFrame([detail_row])[["Source", "Priority", "Volumetrics", "Customization & Logic", "Timeline (weeks)"]]
    st.dataframe(df, hide_index=True, use_container_width=True)

    rows_for_export = [{
        "Source": detail_row["Source"],
        "Priority": detail_row["Priority"],
        "Volumetrics": detail_row["Volumetrics"],
        "Customization & Logic": detail_row["Customization & Logic"],
        "Timeline (weeks)_max": detail_row["_weeks_max"],
        "Price (USD)": detail_row["_price"],
    }]

    return rows_for_export, price, impl_days_sum


# ---------- Select middleware ----------
def render_layer2_drag(spec: dict, num_sources: int):
    """
    Drag exactly one Azure option to 'Chosen'.
    Returns: choice_name, total_price, provision_days (business days)
    """
    st.subheader("Select middleware")

    azure_opts = spec.get("layer2_azure", {}).get("options", [])
    if not azure_opts:
        st.error("No Azure options defined in the spec.")
        return None, 0.0, 0

    names = [o["name"] for o in azure_opts]
    original_items = [
        {"header": "Available Azure Options", "items": names},
        {"header": "Chosen Azure Option",     "items": []},
    ]
    st.caption("Drag one option to 'Chosen'. If you drag more than one, the first will be used.")
    result = sort_items(original_items, multi_containers=True, key="layer2_drag_sortables")

    chosen_list = []
    for container in result:
        if container.get("header") == "Chosen Azure Option":
            chosen_list = container.get("items", [])
            break

    choice_name = chosen_list[0] if chosen_list else names[0]
    entry = next((o for o in azure_opts if o["name"] == choice_name), azure_opts[0])

    cost = entry.get("cost", {"fixed": 0, "per_source": 0})
    total = float(cost.get("fixed", 0)) + float(cost.get("per_source", 0)) * max(num_sources, 1)
    days = int(entry.get("provision_days", 0))  # business days

    st.write(f"**Azure Price:** ${total:,.2f}")
    return choice_name, total, days


# ---------- Select destination + Add-ons ----------
def render_layer3_drag(spec: dict):
    """
    Destination is fixed; add-ons are optional via drag.
    Returns: target_name, fixed_cost, base_days, addon_rows, addons_cost, addons_days
    """
    # Destination
    st.subheader("Select destination")
    target = spec.get("layer3_target", {})
    required = target.get("required", {"name": "Agentic IT Service", "fixed_price": 0, "base_days": 0})
    target_name = required.get("name", "Agentic IT Service")
    fixed_cost = float(required.get("fixed_price", 0))
    base_days = int(required.get("base_days", 0))

    st.success(f"Included: **{target_name}** — ${fixed_cost:,.2f}")

    # Add-ons
    st.subheader("Add-ons")
    addons_spec = target.get("addons", [])
    addon_names = [a["name"] for a in addons_spec]

    original_items = [
        {"header": "Available Add-ons", "items": addon_names},
        {"header": "Selected Add-ons",  "items": []},
    ]
    st.caption("Drag the add-ons you want into 'Selected Add-ons'.")
    result = sort_items(original_items, multi_containers=True, key="layer3_drag_sortables")

    selected_names = []
    for container in result:
        if container.get("header") == "Selected Add-ons":
            selected_names = container.get("items", [])
            break

    addon_rows, addons_cost, addons_days = [], 0.0, 0
    lookup = {a["name"]: a for a in addons_spec}
    for nm in selected_names:
        a = lookup.get(nm)
        if not a:
            continue
        price = float(a.get("price", 0))
        days = int(a.get("extra_days", 0))  # business days
        addon_rows.append({"Add-on": nm, "Price (USD)": price, "Extra days": days})
        addons_cost += price
        addons_days += days

    if addon_rows:
        st.dataframe(pd.DataFrame(addon_rows).drop(columns=["Extra days"]), hide_index=True, use_container_width=True)
        st.write(f"**Add-ons Price:** ${addons_cost:,.2f}")
    else:
        st.info("No add-ons selected.")

    return target_name, fixed_cost, base_days, addon_rows, addons_cost, addons_days
