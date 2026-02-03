# def build_medical_prompt(extracted_text):
#     return(
#         "You are a medical report analysis assistant.\n\n"

#         "TASK:\n"
#         "Explain the following patient laboratory report in very simple, "
#         "patient-friendly language.\n\n"

#         "IMPORTANT INSTRUCTIONS:\n"
#         "1. Identify normal and abnormal values.\n"
#         "2. Clearly mention if a value is high or low.\n"
#         "3. Explain findings in non-technical language.\n"
#         "4. Do NOT diagnose diseases.\n"
#         "5. Do NOT prescribe medicines.\n"
#         "6. Keep the tone calm, supportive, and non-alarming.\n"
#         "7. If reference ranges are missing, mention that interpretation is limited.\n"
#         "8. End the response with a clear disclaimer.\n\n"

#         "OUTPUT STRUCTURE:\n"
#         "• Short overall summary\n"
#         "• Explanation of abnormal values\n"
#         "• General lifestyle-level suggestions only\n"
#         "• Final disclaimer\n\n"

#         "PATIENT REPORT TEXT:\n"
#         "--------------------\n"
#         f"{extracted_text}\n"
#         "--------------------\n\n"

#         "DISCLAIMER (MANDATORY AT END):\n"
#         "\"This explanation is for educational purposes only and is not a medical "
#         "diagnosis. Please consult a qualified healthcare professional for medical advice.\""
#     )

def build_medical_prompt(extracted_text):
    return (
        "Role: You are 'MedAI,' a medical analyst. Your job is to filter noise and highlight ONLY what matters.\n\n"

        "INPUT DATA:\n"
        f"'''{extracted_text}'''\n\n"

        "STRICT INSTRUCTIONS:\n"
        "1. IGNORE normal values unless they are vital for context.\n"
        "2. FOCUS on 'Abnormal', 'High', 'Low', or 'Critical' values.\n"
        "3. FORMATTING: Use a Blockquote (start line with >) for any critical/abnormal finding. This will create a red alert card in the UI.\n\n"

        "GENERATE THIS EXACT OUTPUT:\n\n"

        "### 🏥 Quick Status\n"
        "(1 sentence summary: Is the report mostly normal or does it require attention?)\n\n"

        "### 🚨 Critical Findings (Abnormal Values)\n"
        "> **(Test Name): (Value)**\n"
        "> 🔴 **Status:** High/Low\n"
        "> 💡 **Meaning:** (Explain simply why this is bad. e.g. 'Low hemoglobin causes fatigue.')\n"
        "(If there are no abnormal values, write: '✅ No critical abnormalities found.')\n\n"

        "### 📋 Key Vitals (For Reference)\n"
        "| Test | Result | Reference Range |\n"
        "|------|--------|-----------------|\n"
        "(List only the top 3-5 most important markers here, even if normal)\n\n"

        "### 💡 Next Steps\n"
        "(2-3 simple lifestyle or follow-up suggestions)\n\n"

        "--- \n"
        "*Disclaimer: AI generated for educational purposes. Consult a doctor for diagnosis.*"
    )