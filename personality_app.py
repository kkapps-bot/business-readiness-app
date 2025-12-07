import streamlit as st
import io
import json
import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Business Personality & Readiness", page_icon="🧭", layout="centered")
st.title("🧭 Business Personality & Readiness Assessment")

# ---------------- INITIALIZE ----------------
if "stage" not in st.session_state:
    st.session_state.stage = 1

if "data" not in st.session_state:
    st.session_state.data = {}

if "user_type" not in st.session_state:
    st.session_state.user_type = None  # 'owner', 'starter', 'future'

# Utility: Google Sheets saver (uses st.secrets for credentials)
def save_to_google_sheet(data_dict):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(
            json.loads(st.secrets["gcp"]["service_account"]),
            scopes=scopes
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(st.secrets["gcp"]["spreadsheet_key"]).sheet1

        # Prepare row with defined order
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        # include basic fields first
        keys_order = ["Registration Code", "Age Group", "Gender", "KK Number"]
        for k in keys_order:
            row.append(data_dict.get(k, ""))

        # Add rest of data in alphabetical order to keep stable
        for k in sorted([kk for kk in data_dict.keys() if kk not in keys_order]):
            row.append(data_dict.get(k, ""))

        sheet.append_row(row)
    except Exception as e:
        st.error(f"Failed to save to Google Sheets: {e}")

# Navigation helpers
def go_next():
    st.session_state.stage += 1
    st.rerun()

def go_back():
    st.session_state.stage = max(1, st.session_state.stage - 1)
    st.rerun()

# ----------------- STAGE 1 -----------------
if st.session_state.stage == 1:
    st.header("Stage 1 — Basic Details")

    reg_code = st.text_input("Registration Code")

    age_group = st.selectbox(
        "Age group",
        ["Select age group", "Below 18", "20–30", "31–40", "41–50", "51–60", "Above 60"]
    )

    gender = st.selectbox(
        "Gender",
        ["Select gender", "Male", "Female", "Other"]
    )

    kk_number = st.selectbox(
        "KK Number",
        ["Select KK number", "1", "2", "3", "4", "5", "6"]
    )

    if st.button("Next ➡️"):
        if (
            not reg_code
            or age_group.startswith("Select")
            or gender.startswith("Select")
            or kk_number.startswith("Select")
        ):
            st.error("⚠️ Please fill all fields before moving ahead.")
        else:
            st.session_state.data.update({
                "Registration Code": reg_code,
                "Age Group": age_group,
                "Gender": gender,
                "KK Number": kk_number
            })

            # Branching logic (Option A)
            if age_group == "Below 18":
                st.session_state.user_type = "future"
                st.session_state.stage = 2  # go to future entrepreneur form
                st.rerun()
            else:
                # For adults ask whether currently running a business
                st.session_state.stage = 1.5
                st.rerun()

# Small intermediate screen to ask business ownership for adults
elif st.session_state.stage == 1.5:
    st.header("Quick question — Business ownership")
    st.write("Are you currently running a business?")
    own = st.selectbox("", ["Select", "Yes", "No"]) 
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            go_back()
    with col2:
        if st.button("Continue"):
            if own == "Select":
                st.error("Please choose Yes or No to continue.")
            else:
                if own == "Yes":
                    st.session_state.user_type = "owner"
                    st.session_state.stage = 2  # existing Stage 2 for owners
                else:
                    st.session_state.user_type = "starter"
                    st.session_state.stage = 2  # will show starter form
                st.rerun()

# ----------------- STAGE 2: multiple variants -----------------
elif st.session_state.stage == 2:
    # FUTURE ENTREPRENEUR
    if st.session_state.user_type == "future":
        st.header("Future Entrepreneur — Assessment")
        st.write("This short form is for young future entrepreneurs (below 18).")

        fe1 = st.selectbox("1. Which subjects do you enjoy the most?",
                           ["Select an option", "Math/Science", "Commerce/Economics", "Arts/Humanities", "Computer/Technology", "Other"])
        fe2 = st.selectbox("2. What activities make you feel confident?",
                           ["Select an option", "Public speaking", "Coding/Building things", "Arts & Crafts", "Sports", "Other"])
        fe3 = st.selectbox("3. Do you enjoy solving problems or creating new ideas?",
                           ["Select an option", "Yes, very much", "Sometimes", "Not really"]) 
        fe4 = st.selectbox("4. Do you take initiative in school or at home?",
                           ["Select an option", "Often", "Sometimes", "Rarely"]) 
        fe5 = st.selectbox("5. Does your family support your interest in business?",
                           ["Select an option", "Strongly support", "Somewhat support", "Not supportive"]) 
        fe6 = st.selectbox("6. Do you have role models or entrepreneurs you look up to?",
                           ["Select an option", "Yes", "No"]) 
        fe7 = st.selectbox("7. Would you like to become an entrepreneur someday?",
                           ["Select an option", "Yes", "Maybe", "No"]) 
        fe8 = st.selectbox("8. How comfortable are you making decisions?",
                           ["Select an option", "Very comfortable", "Somewhat comfortable", "Not comfortable"]) 
        fe9 = st.selectbox("9. What type of business attracts you?",
                           ["Select an option", "Technology", "Shop/Store", "Online services", "Food", "Other"]) 
        fe10 = st.selectbox("10. Do you want to study further before starting a business?",
                            ["Select an option", "Yes", "No", "Maybe"]) 

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                go_back()
        with col2:
            if st.button("Finish & Generate Report"):
                missing = any([v.startswith("Select") for v in [fe1, fe2, fe3, fe4, fe5, fe6, fe7, fe8, fe9, fe10]])
                if missing:
                    st.error("Please answer all questions before continuing.")
                else:
                    st.session_state.data.update({
                        "fe1": fe1, "fe2": fe2, "fe3": fe3, "fe4": fe4, "fe5": fe5,
                        "fe6": fe6, "fe7": fe7, "fe8": fe8, "fe9": fe9, "fe10": fe10
                    })
                    # save and generate combined PDF (Option B: smart PDF)
                    save_to_google_sheet(st.session_state.data)

                    # build PDF
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                                            rightMargin=40, leftMargin=40,
                                            topMargin=60, bottomMargin=40)
                    styles = getSampleStyleSheet()
                    elements = []

                    title_style = ParagraphStyle(name='TitleStyle', fontSize=18, alignment=1, textColor=colors.HexColor("#023e8a"))
                    elements.append(Paragraph("<b>Business Personality & Readiness Report</b>", title_style))
                    elements.append(Spacer(1, 0.2 * inch))
                    date_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
                    elements.append(Paragraph(f"Generated on {date_str}", styles["Normal"]))
                    elements.append(Spacer(1, 0.2 * inch))

                    heading = ParagraphStyle(name='Heading', fontSize=14, textColor="#0077b6")
                    elements.append(Paragraph("<b>Stage 1 – Personal Information</b>", heading))
                    for key in ["Registration Code", "Age Group", "Gender", "KK Number"]:
                        elements.append(Paragraph(f"<b>{key}:</b> {st.session_state.data.get(key)}", styles["Normal"]))
                    elements.append(Spacer(1, 0.2 * inch))

                    elements.append(Paragraph("<b>Future Entrepreneur Assessment</b>", heading))
                    for i in range(1, 11):
                        elements.append(Paragraph(f"<b>Q{i}:</b> {st.session_state.data.get(f'fe{i}')}", styles["Normal"]))
                        elements.append(Spacer(1, 0.05 * inch))

                    note_text = ("<b>Note:</b> This assessment is an introductory guidance for young entrepreneurs. "
                                 "Parents/guardians should supervise and support execution of plans.")
                    note = Table([[Paragraph(note_text, styles["Normal"]) ]], colWidths=[6.3 * inch], style=[
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF8C4")),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#B8860B"))
                    ])
                    elements.append(Spacer(1, 0.2 * inch))
                    elements.append(note)

                    doc.build(elements)
                    pdf_buffer.seek(0)
                    st.download_button("⬇️ Download Report (Future Entrepreneur)", pdf_buffer.getvalue(), file_name=f"Future_Entrepreneur_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
                    st.success("Report generated successfully!")
                    st.session_state.stage = 4
                    

    # STARTER (Adult not running business)
    elif st.session_state.user_type == "starter":
        st.header("New Business Starter — Readiness")
        st.write("This short form helps you evaluate readiness to start a business.")

        s1 = st.selectbox("1. Do you have a business idea?",
                          ["Select an option", "Yes, clear idea", "Have a few ideas", "No idea yet"]) 
        s2 = st.selectbox("2. What problem will your business solve?",
                          ["Select an option", "Local customer need", "Online convenience", "Skill/service gap", "Other"]) 
        s3 = st.selectbox("3. Do you have savings to invest?",
                          ["Select an option", "Enough savings", "Small savings", "No savings"]) 
        s4 = st.selectbox("4. Will family support financially?",
                          ["Select an option", "Yes", "Maybe", "No"]) 
        s5 = st.selectbox("5. Do you have skills related to idea?",
                          ["Select an option", "Yes", "Somewhat", "No"]) 
        s6 = st.selectbox("6. Are you willing to take training?",
                          ["Select an option", "Yes", "Maybe", "No"]) 
        s7 = st.selectbox("7. Have you researched competitors?",
                          ["Select an option", "Yes", "Partially", "Not yet"]) 
        s8 = st.selectbox("8. Do you know your target customer?",
                          ["Select an option", "Yes", "Somewhat", "No"]) 
        s9 = st.selectbox("9. Are you comfortable taking risks?",
                          ["Select an option", "Very", "Somewhat", "Not really"]) 
        s10 = st.selectbox("10. How disciplined are you?",
                           ["Select an option", "Very disciplined", "Moderately", "Not disciplined"]) 

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                go_back()
        with col2:
            if st.button("Finish & Generate Report"):
                missing = any([v.startswith("Select") for v in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10]])
                if missing:
                    st.error("Please answer all questions before continuing.")
                else:
                    st.session_state.data.update({
                        "s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5,
                        "s6": s6, "s7": s7, "s8": s8, "s9": s9, "s10": s10
                    })
                    save_to_google_sheet(st.session_state.data)

                    # Build PDF (Starter) — smart PDF includes only relevant sections
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                                            rightMargin=40, leftMargin=40,
                                            topMargin=60, bottomMargin=40)
                    styles = getSampleStyleSheet()
                    elements = []

                    title_style = ParagraphStyle(name='TitleStyle', fontSize=18, alignment=1, textColor=colors.HexColor("#023e8a"))
                    elements.append(Paragraph("<b>Business Personality & Readiness Report</b>", title_style))
                    elements.append(Spacer(1, 0.2 * inch))
                    date_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
                    elements.append(Paragraph(f"Generated on {date_str}", styles["Normal"]))
                    elements.append(Spacer(1, 0.2 * inch))

                    heading = ParagraphStyle(name='Heading', fontSize=14, textColor="#0077b6")
                    elements.append(Paragraph("<b>Stage 1 – Personal Information</b>", heading))
                    for key in ["Registration Code", "Age Group", "Gender", "KK Number"]:
                        elements.append(Paragraph(f"<b>{key}:</b> {st.session_state.data.get(key)}", styles["Normal"]))
                    elements.append(Spacer(1, 0.2 * inch))

                    elements.append(Paragraph("<b>New Business Starter Assessment</b>", heading))
                    for i in range(1, 11):
                        elements.append(Paragraph(f"<b>Q{i}:</b> {st.session_state.data.get(f's{i}')}", styles["Normal"]))
                        elements.append(Spacer(1, 0.05 * inch))

                    note_text = ("<b>Note:</b> This assessment helps you plan initial steps to start your business. "
                                 "Consider mentorship and training to improve your readiness.")
                    note = Table([[Paragraph(note_text, styles["Normal"]) ]], colWidths=[6.3 * inch], style=[
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF8C4")),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#B8860B"))
                    ])
                    elements.append(Spacer(1, 0.2 * inch))
                    elements.append(note)

                    doc.build(elements)
                    pdf_buffer.seek(0)
                    st.download_button("⬇️ Download Report (Starter)", pdf_buffer.getvalue(), file_name=f"Starter_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
                    st.success("Report generated successfully!")
                    st.session_state.stage = 4
                    

    # OWNER (we keep existing Stage 2 contents exactly — assume earlier code exists)
    elif st.session_state.user_type == "owner":
        # Here we will include the exact existing Stage 2 questions and flow
        # For brevity and safety we will import existing behavior by reading from a helper
        # But since you asked to keep things intact, we assume the owner flow continues as before.
        # To keep this file self-contained, we replicate the previous 'owner' Stage 2 questions.

        st.header("Stage 2 — Personality & Lifestyle")
        st.write("Please answer honestly. Use the dropdowns to select the best option.")

        # Family
        family1 = st.selectbox("1. How would you describe your relationship with your family members?",
                               ["Select an option", "Very close and understanding", "Supportive but sometimes distant",
                                "Occasionally conflicting", "Difficult or strained"])
        family2 = st.selectbox("2. How much support do you receive from your family in your personal growth?",
                               ["Select an option", "Always supportive", "Supportive when needed",
                                "Neutral or limited support", "Rarely supportive"])
        family3 = st.selectbox("3. How often do you spend quality time with your family?",
                               ["Select an option", "Every day", "Few times a week", "Occasionally", "Rarely"])

        # Physical
        physical1 = st.selectbox("1. How active are you physically in your daily routine?",
                                 ["Select an option", "Very active (daily exercise)", "Moderately active",
                                  "Occasionally active", "Mostly inactive"])
        physical2 = st.selectbox("2. Do you maintain a healthy diet and sleeping pattern?",
                                 ["Select an option", "Always maintain", "Most of the time", "Sometimes", "Rarely"])
        physical3 = st.selectbox("3. Do you feel your physical health affects your confidence and overall personality?",
                                 ["Select an option", "Yes, strongly", "Somewhat", "Not much", "No impact"])

        # Mental
        # For mental2 we keep link usage optional; showing plain question
        mental1 = st.selectbox("1. How well do you handle stress or unexpected challenges?",
                               ["Select an option", "Very well", "Manageable", "Sometimes struggle", "Find it difficult"])
        mental2 = st.selectbox("2. Do you often feel positive and confident about your goals?",
                               ["Select an option", "Always confident and focused", "Usually positive with minor doubts",
                                "Sometimes uncertain", "Often lack clarity or motivation"])
        mental3 = st.selectbox("3. How frequently do you take time to relax or clear your mind?",
                               ["Select an option", "Daily", "Few times a week", "Occasionally", "Rarely"])

        # Social
        social1 = st.selectbox("1. How frequently do you meet or interact with friends or social groups?",
                               ["Select an option", "Very frequently", "Occasionally", "Rarely", "Almost never"])
        social2 = st.selectbox("2. Are you comfortable expressing your thoughts in social situations?",
                               ["Select an option", "Very comfortable", "Somewhat comfortable", "Uncomfortable", "Avoid social interaction"])
        social3 = st.selectbox("3. How do you usually contribute to your community or social circles?",
                               ["Select an option", "Actively volunteer or participate", "Support occasionally", "Prefer to stay uninvolved"])

        # Financial
        financial1 = st.selectbox("1. Current Status of Income",
                                  ["Select an option", "I have a regular and stable source of income", "I am self-employed or doing freelance work",
                                   "I am currently unemployed but actively seeking opportunities", "I am a student or dependent on family",
                                   "Retired or not seeking employment"])
        financial2 = st.selectbox("2. Primary Source of Income",
                                  ["Select an option", "Salary or professional income", "Business or self-employment",
                                   "Parental/family support", "Savings or pension", "No fixed source of income"])
        financial3 = st.selectbox("3. Financial Goal",
                                  ["Select an option", "To find a stable source of income", "To grow my business or income level",
                                   "To save and invest wisely", "To clear debts or improve stability", "I am financially comfortable"]) 

        # Spiritual
        spiritual1 = st.selectbox("1. How connected do you feel with your inner self or spiritual side?",                                   ["Select an option", "Strongly connected", "Moderately connected", "Slightly connected", "Not connected"])
        spiritual2 = st.selectbox("2. Do you engage in activities like meditation, prayer, or self-reflection?",                                   ["Select an option", "Daily", "Few times a week", "Occasionally", "Rarely or never"]) 
        spiritual3 = st.selectbox("3. How important is spiritual growth in your life?",                                   ["Select an option", "Very important", "Somewhat important", "Not very important", "Not important at all"]) 

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                go_back()
        with col2:
            if st.button("Next ➡️"):
                missing = any([
                    family1.startswith("Select"), family2.startswith("Select"), family3.startswith("Select"),
                    physical1.startswith("Select"), physical2.startswith("Select"), physical3.startswith("Select"),
                    mental1.startswith("Select"), mental2.startswith("Select"), mental3.startswith("Select"),
                    social1.startswith("Select"), social2.startswith("Select"), social3.startswith("Select"),
                    financial1.startswith("Select"), financial2.startswith("Select"), financial3.startswith("Select"),
                    spiritual1.startswith("Select"), spiritual2.startswith("Select"), spiritual3.startswith("Select")
                ])

                if missing:
                    st.error("⚠️ Please answer all Stage 2 questions before continuing.")
                else:
                    st.session_state.data.update({
                        "family1": family1, "family2": family2, "family3": family3,
                        "physical1": physical1, "physical2": physical2, "physical3": physical3,
                        "mental1": mental1, "mental2": mental2, "mental3": mental3,
                        "social1": social1, "social2": social2, "social3": social3,
                        "financial1": financial1, "financial2": financial2, "financial3": financial3,
                        "spiritual1": spiritual1, "spiritual2": spiritual2, "spiritual3": spiritual3
                    })
                    go_next()

# ----------------- STAGE 3 for owners (kept intact) -----------------
elif st.session_state.stage == 3:
    st.header("Stage 3 — Mandatory Requirements")

    reqs = {}
    def q(txt):
        return st.radio(txt, ["Select", "Yes", "No"])

    reqs["Daily Account Review"] = q("1. Do you review business accounts daily (zero-zero balance)?")
    reqs["Minimize Financial Burden"] = q("2. Do you maintain minimum loans and debts?")
    reqs["Complete Technical Knowledge"] = q("3. Do you have complete technical knowledge of your business?")
    reqs["Complete Equipment Knowledge"] = q("4. Do you have complete knowledge of your equipment (if any)?")
    reqs["Fixed Duty Hours"] = q("5. Do you follow fixed duty hours?")
    reqs["Accounting Course"] = q("6. Have you completed a share/purchase or accounting course?")
    reqs["Tax & Compliance"] = q("7. Do you understand GST, tax, banking, and other government compliance?")
    reqs["Worker Insurance"] = q("8. Have you insured your workers?")
    reqs["Firm Insurance"] = q("9. Is your firm insured?")
    reqs["Fire Safety"] = q("10. Do you have fire safety arrangements at the firm?")
    reqs["Labour Rules"] = q("11. Do you understand basic labour rules?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            go_back()
    with col2:
        if st.button("Generate Report 🧾"):

            if any(v == "Select" for v in reqs.values()):
                st.error("⚠️ Please answer all mandatory requirement questions.")
            else:
                st.session_state.data.update(reqs)

                # generate PDF for owner (original behavior)
                pdf_buffer = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                                        rightMargin=40, leftMargin=40,
                                        topMargin=60, bottomMargin=40)
                styles = getSampleStyleSheet()
                elements = []

                title_style = ParagraphStyle(name='TitleStyle', fontSize=18, alignment=1, textColor=colors.HexColor("#023e8a"))
                elements.append(Paragraph("<b>Business Personality & Readiness Report</b>", title_style))
                elements.append(Spacer(1, 0.2 * inch))
                date_str = datetime.now().strftime("%d %B %Y, %I:%M %p")
                elements.append(Paragraph(f"Generated on {date_str}", styles["Normal"]))
                elements.append(Spacer(1, 0.2 * inch))

                heading = ParagraphStyle(name='Heading', fontSize=14, textColor="#0077b6")
                elements.append(Paragraph("<b>Stage 1 – Personal Information</b>", heading))
                for key in ["Registration Code", "Age Group", "Gender", "KK Number"]:
                    elements.append(Paragraph(f"<b>{key}:</b> {st.session_state.data.get(key)}", styles["Normal"]))
                elements.append(Spacer(1, 0.2 * inch))

                elements.append(Paragraph("<b>Stage 2 – Personality & Lifestyle</b>", heading))
                stage2_labels = {
                    "family1": "Relationship with family",
                    "family2": "Family support",
                    "family3": "Quality time",
                    "physical1": "Physical activity",
                    "physical2": "Diet & sleep",
                    "physical3": "Health effect on confidence",
                    "mental1": "Stress handling",
                    "mental2": "Goal confidence",
                    "mental3": "Relaxation frequency",
                    "social1": "Social interaction",
                    "social2": "Comfort expressing thoughts",
                    "social3": "Community contribution",
                    "financial1": "Income status",
                    "financial2": "Financial support",
                    "financial3": "Financial goal",
                    "spiritual1": "Spiritual connection",
                    "spiritual2": "Meditation/reflection",
                    "spiritual3": "Spiritual importance"
                }

                for key, label in stage2_labels.items():
                    ans = st.session_state.data.get(key)
                    elements.append(Paragraph(f"<b>{label}:</b> {ans}", styles["Normal"]))
                    elements.append(Spacer(1, 0.05 * inch))
                elements.append(Spacer(1, 0.2 * inch))

                elements.append(Paragraph("<b>Stage 3 – Mandatory Requirements</b>", heading))
                table_data = [["Requirement", "Status"]]

                for k, v in reqs.items():
                    table_data.append([k, v])

                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0077b6")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.2 * inch))

                note_text = ("<b>Note:</b> To proceed further, the firm must ensure that all the listed requirements are fully implemented. "
                             "Once all conditions are satisfied, a verification visit will be conducted by our team to validate completion and compliance.")
                note = Table([[Paragraph(note_text, styles["Normal"]) ]], colWidths=[6.3 * inch], style=[
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF8C4")),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#B8860B"))
                ])
                elements.append(note)

                doc.build(elements)
                pdf_buffer.seek(0)
                st.download_button("⬇️ Download Professional PDF Report", pdf_buffer.getvalue(), file_name=f"Business_Readiness_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
                st.success("Report generated successfully!")
                save_to_google_sheet(st.session_state.data)
                st.session_state.stage = 4
                

# ----------------- FINAL STAGE -----------------
elif st.session_state.stage == 4:
    st.header("🎉 Thank You!")
    st.write("Your personalized Business Personality & Readiness Report has been generated successfully.")

    if st.button("Start New Assessment"):
        st.session_state.stage = 1
        st.session_state.data = {}
        st.session_state.user_type = None
        st.rerun()
