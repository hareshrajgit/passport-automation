import streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
from PIL import Image
import io
import base64
import re
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Passport Automation System",
    page_icon="🛂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-header {
        font-size: 2.6rem;
        font-weight: 700;
        color: #1a56db;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
        font-size: 1rem;
    }
    .status-approved  { color: #059669; font-weight: 600; }
    .status-pending   { color: #d97706; font-weight: 600; }
    .status-rejected  { color: #dc2626; font-weight: 600; }
    .status-processing{ color: #7c3aed; font-weight: 600; }

    div[data-testid="stForm"] {
        background: #f9fafb;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #374151;
        margin: 1rem 0 0.5rem 0;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.3rem;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
MONGO_URI      = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME        = "passport_db"
COLLECTION     = "passports"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@2024")

INDIAN_STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Delhi","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand",
    "Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur",
    "Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan",
    "Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh",
    "Uttarakhand","West Bengal"
]

# ─────────────────────────────────────────────
# MONGODB CONNECTION
# ─────────────────────────────────────────────
@st.cache_resource
def get_db():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[DB_NAME]
        db[COLLECTION].create_index("application_id", unique=True)
        return db
    except ConnectionFailure as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        st.stop()

db = get_db()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def generate_app_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PAS{ts}"

def validate_mobile(m: str) -> bool:
    return m.isdigit() and len(m) == 10

def validate_pincode(p: str) -> bool:
    return p.isdigit() and len(p) == 6

def validate_email(e: str) -> bool:
    return bool(re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$", e, re.IGNORECASE))

def photo_to_b64(photo) -> str | None:
    if photo is None:
        return None
    photo.seek(0)
    return base64.b64encode(photo.read()).decode("utf-8")

def b64_to_image(b64: str):
    return Image.open(io.BytesIO(base64.b64decode(b64)))

def status_badge(status: str) -> str:
    css  = {"Approved":"status-approved","Pending":"status-pending",
            "Rejected":"status-rejected","Processing":"status-processing"}
    icons = {"Approved":"✅","Pending":"⏳","Rejected":"❌","Processing":"🔄"}
    cls  = css.get(status, "")
    icon = icons.get(status, "")
    return f'<span class="{cls}">{icon} {status}</span>'

# ─────────────────────────────────────────────
# DB OPERATIONS
# ─────────────────────────────────────────────
def save_application(doc: dict) -> str:
    app_id = generate_app_id()
    doc["application_id"]  = app_id
    doc["status"]          = "Pending"
    doc["submitted_date"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db[COLLECTION].insert_one(doc)
    return app_id

def get_app_by_id(app_id: str) -> dict | None:
    return db[COLLECTION].find_one({"application_id": app_id}, {"_id": 0})

def search_apps(query: str = "", status_filter: list = None) -> list:
    q = {}
    if query:
        q["$or"] = [
            {"application_id": {"$regex": query, "$options": "i"}},
            {"full_name":       {"$regex": query, "$options": "i"}},
            {"mobile":          {"$regex": query, "$options": "i"}},
        ]
    if status_filter:
        q["status"] = {"$in": status_filter}
    return list(db[COLLECTION].find(q, {"_id": 0}).sort("submitted_date", -1))

def update_status(app_id: str, status: str):
    db[COLLECTION].update_one({"application_id": app_id}, {"$set": {"status": status}})

def get_stats() -> dict:
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    counts = {d["_id"]: d["count"] for d in db[COLLECTION].aggregate(pipeline)}
    total  = sum(counts.values())
    return {
        "Total":      total,
        "Pending":    counts.get("Pending", 0),
        "Approved":   counts.get("Approved", 0),
        "Rejected":   counts.get("Rejected", 0),
        "Processing": counts.get("Processing", 0),
    }

def export_csv() -> bytes:
    apps = list(db[COLLECTION].find({}, {"_id": 0, "photo_b64": 0}))
    if not apps:
        return b""
    df = pd.DataFrame(apps)
    return df.to_csv(index=False).encode("utf-8")

# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────
def page_new_application():
    st.header("📝 New Passport Application")

    with st.form("passport_form", clear_on_submit=True):
        st.markdown('<p class="section-title">👤 Personal Details</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            full_name     = st.text_input("Full Name *")
            father_name   = st.text_input("Father's Name *")
            mother_name   = st.text_input("Mother's Name *")
            nationality   = st.selectbox("Nationality *", ["Indian", "Other"])
            passport_type = st.selectbox("Application Type *", ["Fresh", "Renewal", "Tatkal"])
        with col2:
            dob            = st.date_input("Date of Birth *", min_value=date(1900, 1, 1), max_value=date.today())
            gender         = st.radio("Gender *", ["Male", "Female", "Other"])
            marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])
            mobile         = st.text_input("Mobile Number *", help="10-digit mobile number")
            email          = st.text_input("Email Address *")

        st.markdown('<p class="section-title">📍 Address Details</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            house_no = st.text_input("House No / Street *")
            city     = st.text_input("City *")
        with col2:
            state   = st.selectbox("State *", INDIAN_STATES)
            pincode = st.text_input("Pincode *", max_chars=6)

        st.markdown('<p class="section-title">📸 Passport Photo</p>', unsafe_allow_html=True)
        photo = st.file_uploader(
            "Upload Passport Size Photo (JPG/PNG, max 2MB)",
            type=["jpg", "jpeg", "png"],
            help="3.5x4.5 cm, white background, recent photo"
        )

        submitted = st.form_submit_button("🚀 Submit Application", use_container_width=True)

        if submitted:
            errors = []
            if not full_name.strip() or len(full_name.strip()) < 3:
                errors.append("Full name must be at least 3 characters.")
            if not father_name.strip():
                errors.append("Father's name is required.")
            if not mother_name.strip():
                errors.append("Mother's name is required.")
            if not validate_mobile(mobile):
                errors.append("Enter a valid 10-digit mobile number.")
            if not validate_email(email):
                errors.append("Enter a valid email address.")
            if not house_no.strip() or not city.strip():
                errors.append("Address fields are required.")
            if not validate_pincode(pincode):
                errors.append("Enter a valid 6-digit pincode.")
            if photo is None:
                errors.append("Passport photo is required.")
            elif photo.size > 2 * 1024 * 1024:
                errors.append("Photo must be under 2MB.")

            if errors:
                for e in errors:
                    st.error(f"⚠️ {e}")
            else:
                doc = {
                    "full_name":      full_name.strip(),
                    "father_name":    father_name.strip(),
                    "mother_name":    mother_name.strip(),
                    "nationality":    nationality,
                    "passport_type":  passport_type,
                    "dob":            str(dob),
                    "gender":         gender,
                    "marital_status": marital_status,
                    "mobile":         mobile.strip(),
                    "email":          email.strip().lower(),
                    "address": {
                        "house_no": house_no.strip(),
                        "city":     city.strip(),
                        "state":    state,
                        "pincode":  pincode.strip(),
                    },
                    "photo_b64": photo_to_b64(photo),
                }
                try:
                    app_id = save_application(doc)
                    st.success(f"✅ Application submitted! **App ID: `{app_id}`**")
                    st.info("💡 Save this ID to track your application.")
                    st.balloons()

                    st.markdown("---")
                    st.subheader("📄 Application Summary")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Application ID", app_id)
                        st.metric("Applicant",       full_name)
                        st.metric("Type",            passport_type)
                        st.metric("Submitted On",    datetime.now().strftime("%Y-%m-%d %H:%M"))
                    with c2:
                        photo.seek(0)
                        st.image(photo, caption="Submitted Photo", width=180)
                except Exception as e:
                    st.error(f"❌ Submission failed: {e}")


def page_track():
    st.header("🔍 Track Application")
    app_id = st.text_input("Enter Application ID (e.g. PAS20250610153045)")

    if st.button("🔍 Search") and app_id:
        app = get_app_by_id(app_id.strip())
        if app:
            st.success(f"✅ Found: **{app['application_id']}**")
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**Name:** {app['full_name']}")
                st.markdown(f"**DOB:** {app['dob']}")
                st.markdown(f"**Type:** {app['passport_type']}")
                st.markdown(f"**Nationality:** {app['nationality']}")
                st.markdown(f"**Mobile:** {app['mobile']}")
                addr = app.get("address", {})
                st.markdown(f"**Address:** {addr.get('house_no','')}, {addr.get('city','')}, {addr.get('state','')}, {addr.get('pincode','')}")
                st.markdown(f"**Submitted:** {app['submitted_date']}")
                st.markdown(f"**Status:** {status_badge(app['status'])}", unsafe_allow_html=True)
            with c2:
                if app.get("photo_b64"):
                    st.image(b64_to_image(app["photo_b64"]), caption="Photo", width=160)
        else:
            st.error("❌ No application found with that ID.")


def page_dashboard():
    st.header("📊 Dashboard")
    stats = get_stats()

    if stats["Total"] == 0:
        st.info("📭 No applications yet.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📊 Total",      stats["Total"])
    c2.metric("⏳ Pending",    stats["Pending"])
    c3.metric("✅ Approved",   stats["Approved"])
    c4.metric("❌ Rejected",   stats["Rejected"])
    c5.metric("🔄 Processing", stats["Processing"])

    st.markdown("---")
    st.subheader("📈 Status Distribution")
    chart_data = pd.DataFrame({
        "Status": ["Pending","Approved","Rejected","Processing"],
        "Count":  [stats["Pending"], stats["Approved"], stats["Rejected"], stats["Processing"]]
    }).set_index("Status")
    st.bar_chart(chart_data)

    st.markdown("---")
    st.subheader("🕐 Recent Applications")
    recent = search_apps()[:10]
    if recent:
        rows = [{
            "App ID":    a["application_id"],
            "Name":      a["full_name"],
            "Type":      a.get("passport_type",""),
            "Status":    a["status"],
            "Submitted": a["submitted_date"],
        } for a in recent]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def page_admin():
    st.header("👨‍💼 Admin Panel")

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("🔑 Admin Password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
        return

    if st.button("🚪 Logout"):
        st.session_state.admin_auth = False
        st.rerun()

    stats = get_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total",      stats["Total"])
    c2.metric("Pending",    stats["Pending"])
    c3.metric("Approved",   stats["Approved"])
    c4.metric("Rejected",   stats["Rejected"])
    c5.metric("Processing", stats["Processing"])

    st.divider()

    col_s, col_f = st.columns([3, 1])
    with col_s:
        search = st.text_input("🔎 Search by Name / App ID / Mobile")
    with col_f:
        status_filter = st.multiselect("Filter Status", ["Pending","Approved","Rejected","Processing"])

    csv_bytes = export_csv()
    if csv_bytes:
        st.download_button("⬇️ Export to CSV", csv_bytes, "passport_applications.csv", "text/csv")

    st.divider()

    apps = search_apps(query=search, status_filter=status_filter if status_filter else None)

    if not apps:
        st.info("No applications found.")
    else:
        st.caption(f"Showing {len(apps)} application(s)")
        for app in apps:
            label = f"**{app['application_id']}** — {app['full_name']} | {app.get('passport_type','')} | {app['status']}"
            with st.expander(label):
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.markdown(f"📧 {app.get('email','—')}")
                    st.markdown(f"📱 {app.get('mobile','—')}")
                    addr = app.get("address", {})
                    st.markdown(f"📍 {addr.get('city','')}, {addr.get('state','')}")
                    st.markdown(f"🎂 DOB: {app.get('dob','—')}")
                    st.caption(f"Submitted: {app['submitted_date']}")
                with col2:
                    if app.get("photo_b64"):
                        st.image(b64_to_image(app["photo_b64"]), width=90)
                with col3:
                    aid = app["application_id"]
                    if st.button("✅ Approve",    key=f"ap_{aid}"):
                        update_status(aid, "Approved");   st.rerun()
                    if st.button("🔄 Processing", key=f"pr_{aid}"):
                        update_status(aid, "Processing"); st.rerun()
                    if st.button("❌ Reject",     key=f"rj_{aid}"):
                        update_status(aid, "Rejected");   st.rerun()
                    if st.button("↩️ Reset",      key=f"rs_{aid}"):
                        update_status(aid, "Pending");    st.rerun()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    st.markdown('<h1 class="main-header">🛂 Passport Automation System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Powered by MongoDB • Streamlit</p>', unsafe_allow_html=True)

    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox("Go to:", [
        "📝 New Application",
        "🔍 Track Application",
        "📊 Dashboard",
        "👨‍💼 Admin Panel",
    ])

    st.sidebar.markdown("---")
    st.sidebar.caption("🗄️ MongoDB: localhost:27017")
    st.sidebar.caption("Set MONGO_URI & ADMIN_PASSWORD env vars for production.")

    if page == "📝 New Application":
        page_new_application()
    elif page == "🔍 Track Application":
        page_track()
    elif page == "📊 Dashboard":
        page_dashboard()
    elif page == "👨‍💼 Admin Panel":
        page_admin()

    st.markdown("---")
    st.caption("🛂 Passport Automation System | MongoDB + Streamlit")


if __name__ == "__main__":
    main()