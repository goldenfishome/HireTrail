import os
import streamlit as st
import requests
from datetime import date

# In production (Streamlit Cloud), set this in the app's Secrets as:
#   API_BASE = "https://your-api.onrender.com"
API_BASE = st.secrets.get("API_BASE", os.getenv("API_BASE", "http://localhost:8000"))

STATUS_OPTIONS = ["wishlist", "applied", "interviewing", "offer", "rejected", "withdrawn"]
STATUS_EMOJI = {
    "wishlist": "💭",
    "applied": "📤",
    "interviewing": "🎤",
    "offer": "🎉",
    "rejected": "❌",
    "withdrawn": "🚪",
}
RESULT_OPTIONS = ["pending", "passed", "failed"]
RESULT_EMOJI = {"pending": "⏳", "passed": "✅", "failed": "❌"}

st.set_page_config(page_title="HireTrail", page_icon="🎯", layout="wide")

# --- API helpers ---

def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        return r.json() if r.ok else []
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot reach the API. Make sure HireTrail API is running on port 8000.")
        return []


def api_post(path, data):
    return requests.post(f"{API_BASE}{path}", json=data, timeout=5)


def api_put(path, data):
    return requests.put(f"{API_BASE}{path}", json=data, timeout=5)


def api_delete(path):
    return requests.delete(f"{API_BASE}{path}", timeout=5)


# --- Sidebar ---

with st.sidebar:
    st.markdown("## 🎯 HireTrail")
    st.caption("Your job search command center")
    st.divider()
    page = st.radio(
        "Navigate",
        ["📋 Applications", "🎤 Interviews", "🏢 Companies"],
        label_visibility="collapsed",
    )
    st.divider()
    # Quick stats in sidebar
    all_apps = api_get("/applications/", params={"limit": 10000})
    if all_apps:
        st.markdown("**Quick Stats**")
        st.metric("Total Applications", len(all_apps))
        offers = sum(1 for a in all_apps if a["status"] == "offer")
        if offers:
            st.metric("🎉 Offers", offers)


# ==============================================================
# COMPANIES
# ==============================================================

if page == "🏢 Companies":
    st.title("🏢 Companies")

    companies = api_get("/companies/", params={"limit": 10000})
    st.metric("Tracked Companies", len(companies))

    # Add company form
    with st.expander("➕ Add a Company"):
        with st.form("add_company_form", clear_on_submit=True):
            name = st.text_input("Company Name *")
            col1, col2 = st.columns(2)
            with col1:
                website = st.text_input("Website")
            with col2:
                location = st.text_input("Location")
            notes = st.text_area("Notes", height=80)
            submitted = st.form_submit_button("Add Company", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Company name is required.")
            else:
                r = api_post("/companies/", {
                    "name": name.strip(),
                    "website": website.strip() or None,
                    "location": location.strip() or None,
                    "notes": notes.strip() or None,
                })
                if r.ok:
                    st.success(f"✅ **{name}** added!")
                    st.rerun()
                else:
                    st.error(f"Error: {r.json().get('detail', 'Unknown error')}")

    st.divider()

    # Company list
    if not companies:
        st.info("No companies yet. Add one above to get started.")
    else:
        for c in companies:
            with st.expander(f"**{c['name']}**  ·  {c.get('location') or 'No location'}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"🌐 **Website:** {c.get('website') or '—'}")
                    st.markdown(f"📍 **Location:** {c.get('location') or '—'}")
                with col2:
                    st.markdown(f"📝 **Notes:** {c.get('notes') or '—'}")
                    st.caption(f"Added: {c['created_at'][:10]}")
                with col3:
                    if st.button("🗑️ Delete", key=f"del_co_{c['id']}", use_container_width=True):
                        r = api_delete(f"/companies/{c['id']}")
                        if r.ok:
                            st.success("Deleted.")
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Error"))


# ==============================================================
# APPLICATIONS
# ==============================================================

elif page == "📋 Applications":
    st.title("📋 Applications")

    companies = api_get("/companies/", params={"limit": 10000})
    company_map = {c["id"]: c["name"] for c in companies}
    all_apps = api_get("/applications/", params={"limit": 10000})

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", len(all_apps))
    col2.metric("📤 Applied", sum(1 for a in all_apps if a["status"] == "applied"))
    col3.metric("🎤 Interviewing", sum(1 for a in all_apps if a["status"] == "interviewing"))
    col4.metric("🎉 Offers", sum(1 for a in all_apps if a["status"] == "offer"))
    col5.metric("❌ Rejected", sum(1 for a in all_apps if a["status"] == "rejected"))

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All"] + STATUS_OPTIONS)
    with col2:
        company_names = [c["name"] for c in companies]
        filter_company = st.selectbox("Filter by Company", ["All"] + company_names)
    with col3:
        sort_by = st.selectbox("Sort by", ["date_applied", "role_title", "status"])

    params = {"sort_by": sort_by, "limit": 10000}
    if filter_status != "All":
        params["status"] = filter_status
    if filter_company != "All":
        cid = next((c["id"] for c in companies if c["name"] == filter_company), None)
        if cid:
            params["company_id"] = cid

    applications = api_get("/applications/", params=params)

    # Add application form
    with st.expander("➕ Add an Application"):
        with st.form("add_app_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                role_title = st.text_input("Role Title *")
                job_link = st.text_input("Job Posting URL")
                status = st.selectbox("Status", STATUS_OPTIONS, index=1)
                source = st.text_input("Source  (e.g. LinkedIn, Referral)")
            with col2:
                company_options = ["— None —"] + [c["name"] for c in companies]
                selected_company = st.selectbox("Company (optional)", company_options)
                applied_date = st.date_input("Date Applied", value=date.today())
                salary_min = st.number_input("Salary Min ($)", min_value=0, step=1000)
                salary_max = st.number_input("Salary Max ($)", min_value=0, step=1000)
            notes = st.text_area("Notes", height=80)
            submitted = st.form_submit_button("Add Application", use_container_width=True)

        if submitted:
            if not role_title.strip():
                st.error("Role title is required.")
            elif salary_min and salary_max and salary_min > salary_max:
                st.error("Salary min must be ≤ salary max.")
            else:
                comp_id = next(
                    (c["id"] for c in companies if c["name"] == selected_company), None
                )
                r = api_post("/applications/", {
                    "company_id": comp_id,
                    "role_title": role_title.strip(),
                    "status": status,
                    "job_link": job_link.strip() or None,
                    "date_applied": str(applied_date),
                    "source": source.strip() or None,
                    "salary_min": salary_min or None,
                    "salary_max": salary_max or None,
                    "notes": notes.strip() or None,
                })
                if r.ok:
                    st.success("✅ Application added!")
                    st.rerun()
                else:
                    st.error(f"Error: {r.json().get('detail', 'Unknown error')}")

    # CSV Import
    with st.expander("📂 Import from CSV"):
        st.markdown(
            "Upload a CSV file exported from a spreadsheet. "
            "Column names are detected automatically — supported names include:"
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("**Title:** title, job_title, role, position")
            st.caption("**Company:** company, employer")
            st.caption("**Status:** status, stage")
        with col2:
            st.caption("**Date:** date, date_applied, applied_date")
            st.caption("**Link:** link, url, job_link, posting_url")
            st.caption("**Source:** source, platform, via")
        with col3:
            st.caption("**Notes:** notes, comments")
            st.caption("**Salary Min:** salary_min, min_salary")
            st.caption("**Salary Max:** salary_max, max_salary")

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file and st.button("⬆️ Import", use_container_width=True):
            with st.spinner("Importing..."):
                r = requests.post(
                    f"{API_BASE}/import/applications",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                    timeout=30,
                )
            if r.ok:
                result = r.json()
                st.success(f"✅ Imported **{result['created']}** applications, skipped **{result['skipped']}**.")
                if result.get("errors"):
                    st.warning("Some rows had errors:")
                    for e in result["errors"]:
                        st.caption(f"Row {e['row']}: {e['error']}")
                st.caption(f"Columns detected: {', '.join(f'{k} → {v}' for k, v in result['columns_detected'].items())}")
                st.rerun()
            else:
                st.error(f"Import failed: {r.json().get('detail', 'Unknown error')}")

    st.divider()

    # Application list
    if not applications:
        st.info("No applications found. Try adjusting the filters or add one above.")
    else:
        for a in applications:
            company_name = company_map.get(a["company_id"], "Unknown Company")
            emoji = STATUS_EMOJI.get(a["status"], "")
            label = f"{emoji} **{a['role_title']}** at {company_name} — `{a['status'].upper()}`"

            with st.expander(label):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if a.get("job_link"):
                        st.markdown(f"🔗 **Job Posting:** [{a['job_link']}]({a['job_link']})")
                    st.markdown(f"📅 **Applied:** {a.get('date_applied') or '—'}")
                    st.markdown(f"📣 **Source:** {a.get('source') or '—'}")
                    if a.get("salary_min") or a.get("salary_max"):
                        lo = f"${a['salary_min']:,}" if a.get("salary_min") else "?"
                        hi = f"${a['salary_max']:,}" if a.get("salary_max") else "?"
                        st.markdown(f"💰 **Salary:** {lo} – {hi}")
                    st.markdown(f"📝 **Notes:** {a.get('notes') or '—'}")
                with col2:
                    new_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(a["status"]),
                        key=f"sel_status_{a['id']}",
                    )
                    if st.button("💾 Update", key=f"upd_app_{a['id']}", use_container_width=True):
                        r = api_put(f"/applications/{a['id']}", {"status": new_status})
                        if r.ok:
                            st.success("Updated!")
                            st.rerun()
                    if st.button("🗑️ Delete", key=f"del_app_{a['id']}", use_container_width=True):
                        r = api_delete(f"/applications/{a['id']}")
                        if r.ok:
                            st.success("Deleted.")
                            st.rerun()


# ==============================================================
# INTERVIEWS
# ==============================================================

elif page == "🎤 Interviews":
    st.title("🎤 Interviews")

    applications = api_get("/applications/", params={"limit": 10000})
    companies = api_get("/companies/", params={"limit": 10000})
    company_map = {c["id"]: c["name"] for c in companies}
    app_map = {a["id"]: a["role_title"] for a in applications}

    def app_label(a):
        company = company_map.get(a["company_id"], "") if a.get("company_id") else ""
        if company:
            return f"{company} — {a['role_title']}"
        return a["role_title"]

    # Filter
    app_labels = ["All"] + [app_label(a) for a in applications]
    app_ids = [None] + [a["id"] for a in applications]
    filter_app = st.selectbox("Filter by Application", app_labels)

    params = {}
    if filter_app != "All":
        selected_index = app_labels.index(filter_app)
        params["application_id"] = app_ids[selected_index]

    params["limit"] = 10000
    interviews = api_get("/interviews/", params=params)

    # Stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rounds", len(interviews))
    col2.metric("✅ Passed", sum(1 for i in interviews if i["result"] == "passed"))
    col3.metric("❌ Failed", sum(1 for i in interviews if i["result"] == "failed"))

    st.divider()

    # Add interview form
    with st.expander("➕ Add an Interview"):
        if not applications:
            st.warning("You need to add an application first.")
        else:
            with st.form("add_interview_form", clear_on_submit=True):
                selected_app = st.selectbox(
                    "Application *",
                    [f"#{a['id']} — {a['role_title']}" for a in applications],
                )
                col1, col2 = st.columns(2)
                with col1:
                    round_name = st.text_input("Round Name *  (e.g. Phone Screen, Technical, Final)")
                    interview_date = st.date_input("Interview Date", value=date.today())
                with col2:
                    interviewer_name = st.text_input("Interviewer Name")
                    result = st.selectbox("Result", RESULT_OPTIONS)
                notes = st.text_area("Notes", height=80)
                submitted = st.form_submit_button("Add Interview", use_container_width=True)

            if submitted:
                if not round_name.strip():
                    st.error("Round name is required.")
                else:
                    app_id = int(selected_app.split("—")[0].strip().lstrip("#"))
                    r = api_post("/interviews/", {
                        "application_id": app_id,
                        "round_name": round_name.strip(),
                        "interview_date": str(interview_date),
                        "interviewer_name": interviewer_name.strip() or None,
                        "result": result,
                        "notes": notes.strip() or None,
                    })
                    if r.ok:
                        st.success("✅ Interview added!")
                        st.rerun()
                    else:
                        st.error(f"Error: {r.json().get('detail', 'Unknown error')}")

    st.divider()

    # Interview list
    if not interviews:
        st.info("No interviews found.")
    else:
        for i in interviews:
            app_title = app_map.get(i["application_id"], "Unknown Application")
            emoji = RESULT_EMOJI.get(i["result"], "")
            label = f"{emoji} **{i['round_name']}** — {app_title} — `{i['result'].upper()}`"

            with st.expander(label):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📅 **Date:** {i.get('interview_date') or '—'}")
                    st.markdown(f"👤 **Interviewer:** {i.get('interviewer_name') or '—'}")
                    st.markdown(f"📝 **Notes:** {i.get('notes') or '—'}")
                    st.caption(f"Added: {i['created_at'][:10]}")
                with col2:
                    new_result = st.selectbox(
                        "Result",
                        RESULT_OPTIONS,
                        index=RESULT_OPTIONS.index(i["result"]),
                        key=f"sel_result_{i['id']}",
                    )
                    if st.button("💾 Update", key=f"upd_int_{i['id']}", use_container_width=True):
                        r = api_put(f"/interviews/{i['id']}", {"result": new_result})
                        if r.ok:
                            st.success("Updated!")
                            st.rerun()
                    if st.button("🗑️ Delete", key=f"del_int_{i['id']}", use_container_width=True):
                        r = api_delete(f"/interviews/{i['id']}")
                        if r.ok:
                            st.success("Deleted.")
                            st.rerun()
