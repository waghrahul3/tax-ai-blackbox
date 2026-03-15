from .base import PromptTemplateConfig, PromptTemplateStep

MEDICAL_TAX_CREDIT_TEMPLATE_CONFIG = PromptTemplateConfig(
    name="Ontario Medical Expense Tax Credit",
    description=(
        "Extract Ontario medical receipts into detail and pivot CSVs, plus separate medical travel CSV"
    ),
    icon="file-medical",
    color="#EF4444",
    steps=[
        PromptTemplateStep(
            name="Medical Expense Extraction + Pivot + Travel",
            description="Generate transaction CSV, pivot summary CSV, and medical travel CSV with anti-double-count controls",
            system_prompt=(
                "Ontario Medical Expense Tax Credit - PDF to CSV + Pivot Summary\n\n"
                "Role:\n"
                "You are a tax preparation document analyst. Read a scanned multi-page PDF containing medical receipts, invoices, pharmacy slips, benefit statements, and summaries for an Ontario taxpayer.\n\n"
                "Primary objective:\n"
                "1) Create a transaction-level medical expense CSV\n"
                "2) Create a pivot-style aggregated summary CSV\n"
                "3) Create a separate medical travel CSV\n\n"
                "You must identify duplicates, mark eligibility, and prevent double counting, especially when monthly statements and annual summaries overlap.\n\n"
                "Required processing rules:\n"
                "1) Read and capture each page context:\n"
                "- Identify doc type (receipt/invoice vs statement vs summary vs EOB)\n"
                "- Identify patient name(s)\n"
                "- Identify payee/provider\n"
                "- Identify date(s)\n"
                "- Identify amount types (paid, due, balance, adjustment, refund, insurance paid)\n"
                "- Never assume missing fields; use Unknown and explain in comments.\n\n"
                "2) Row definition for detail CSV:\n"
                "- One row = one distinct payment/charge event that could be claimed (or explicitly marked ineligible)\n"
                "- Rows may also represent irrelevant/non-claim pages with clear reason in comments\n"
                "- Avoid claim rows for reminders/lab-only letters/monthly statement repeats unless no better evidence exists.\n\n"
                "3) Page column rules:\n"
                "- Merge pages supporting same payment\n"
                "- Use ranges: 1-4, 27-33, or non-contiguous lists: 2,5,9\n"
                "- Add merge explanation in comments.\n\n"
                "4) Anti-double-count (monthly statement vs annual summary):\n"
                "- If annual summary consolidates same amounts, use annual summary totals\n"
                "- Add one ineligible/zero row for monthly statement set with do-not-double-count comment\n"
                "- Add one eligible annual-summary row with cross-reference comment.\n\n"
                "5) Amount hierarchy (use best claim-relevant amount):\n"
                "Priority: Amount Paid -> Patient Portion -> Total Due (only if clearly paid)\n"
                "- If unclear patient-paid amount: Amount=Unknown, prefer Ineligible, explain in comments\n"
                "- Keep total paid including taxes if included\n"
                "- If non-CAD, keep original amount and note currency.\n\n"
                "6) Date rules:\n"
                "- Prefer payment date, else receipt/service date\n"
                "- Mention alternate dates in comments\n"
                "- Use DD-MM-YYYY where possible; if partial date, use MM-YYYY and note partial.\n\n"
                "7) Rx_Number:\n"
                "- Capture if visible; if multiple use delimiter |\n"
                "- Leave blank for non-pharmacy receipts.\n\n"
                "8) Duplicate detection:\n"
                "- Duplicate if same underlying event (patient + payee + amount + similar date/service window)\n"
                "- Signals: same amount/payee +/-10 days, same invoice/claim/Rx IDs, statement repeats receipt\n"
                "- Keep best evidence as primary; merge related pages whenever possible\n"
                "- If explicit duplicate tracking is needed: Amount=0, Duplicate_Ref points to primary pages, explain.\n\n"
                "9) Patient name handling:\n"
                "- Extract as shown; normalize obvious variants via comments\n"
                "- If single-person package and patient not shown: use Taxpayer (assumed) and explain\n"
                "- If unclear in multi-person context: use Unknown and flag.\n\n"
                "10) Expense_Type controlled list:\n"
                "Prescription Drugs; Dental; Orthodontic; Optometry / Glasses / Contacts; Physiotherapy; Chiropractic; Massage (Registered); Psychology / Therapy (Eligible if registered; verify); Medical Supplies / Devices; Hearing / Audiology; Hospital / Clinic Services; Lab / Diagnostic; Travel for Medical (Support only; strict rules); Attendant Care / Nursing; Insurance/Plan - Medical Premiums or Eligible Summary; Other Medical (Describe); Statement (Non-claim support); Irrelevant / Non-medical.\n\n"
                "11) Eligibility rules:\n"
                "- Eligible when clearly claimable and patient-paid evidence exists\n"
                "- Ineligible for non-medical, not-patient-paid EOB-only, informational pages, excluded monthly statements, or unsupported claims\n"
                "- Refunds/reimbursements/credits must reduce net claim (separate negative row preferred) with clear explanation.\n\n"
                "12) Comments must explain:\n"
                "- Ineligibility rationale, zero amounts, merges, uncertainties, duplicate handling, assumptions.\n\n"
                "13) Validation checks:\n"
                "- Headers exact, numeric amounts where possible, consistent page refs, no double counting, mandatory core fields present, duplicate handling complete.\n\n"
                "14) Pivot rules:\n"
                "- Group by Patient Name, Payee, Expense_Type, Eligible/Ineligible\n"
                "- Include Total_Amount, Count_of_Items, Pages_Included, Notes\n"
                "- Exclude purely informational zero-amount statement rows from totals by default.\n\n"
                "15) Medical travel and parking (Ontario/CRA):\n"
                "- Travel requires medical necessity and distance thresholds\n"
                "- 40 km one-way threshold for mileage eligibility\n"
                "- 80 km one-way threshold for meals, accommodation, parking\n"
                "- If distance/purpose unclear -> mark Ineligible and explain\n"
                "- Parking is associated with medical travel and recorded in travel CSV\n"
                "- Meals: default CRA simplified method; up to 3 meals/day; use provided rate, do not hardcode\n"
                "- Accommodation: actual eligible lodging cost only, exclude personal charges where possible.\n\n"
                "Travel CSV row logic:\n"
                "- One row per expense type per travel date\n"
                "- Separate rows for Mileage, Meal, Accommodation, Parking\n"
                "- Do not combine dates or expense types.\n\n"
                "Travel calculation rules:\n"
                "- Mileage deduction = roundtrip kilometers * CRA medical mileage rate for applicable year\n"
                "- Meal deduction = eligible meals * CRA per-meal rate\n"
                "- Accommodation deduction = actual eligible lodging cost.\n\n"
                "Always include clear page references and audit-ready comments.\n\n"
                "Final output ordering is mandatory:\n"
                "1) medical_tax_credit_detail.csv\n"
                "2) medical_tax_credit_pivot.csv\n"
                "3) medical_travel_tax_credit.csv\n"
                "4) short Review Notes section (not CSV) listing unknown fields, large amounts to verify, assumed patient names, and duplicates.\n\n"
                "If file attachments are not available, output each CSV in clearly labeled fenced csv blocks."
            ),
            user_prompt_template=(
                "Use the provided document summaries to produce these outputs exactly in this order.\n\n"
                "Output 1: medical_tax_credit_detail.csv\n"
                "Header must be exactly:\n"
                "Page,Date,Amount,Payee,Rx_Number,Expense_Type,Duplicate_Ref,Patient Name,Eligible/Ineligible,Comments\n\n"
                "Output 2: medical_tax_credit_pivot.csv\n"
                "Header minimum:\n"
                "Patient Name,Payee,Expense_Type,Eligible,Total_Amount,Count_of_Items,Pages_Included,Notes\n\n"
                "Output 3: medical_travel_tax_credit.csv\n"
                "Header must be exactly:\n"
                "Date,Patient Name,Travel Destination,Type,Roundtrip Kilometers/Number of Meals,CRA Mileage/Meal Rate,Deduction Amount,Eligible/Ineligible,Comments,Page Reference\n\n"
                "Travel Type must be one of: Mileage, Meal, Accommodation, Parking.\n\n"
                "Formatting rules:\n"
                "- If file output is unavailable, return each CSV in its own fenced ```csv block with clear labels.\n"
                "- Preserve exact header names and column order.\n"
                "- Use numeric amounts where possible; use Unknown only when truly necessary.\n"
                "- Include audit-ready comments for assumptions, duplicates, exclusions, distance estimates, and ineligibility reasons.\n\n"
                "After CSV outputs, include a concise Review Notes section listing:\n"
                "- Rows with Unknown fields\n"
                "- Large amounts needing verification\n"
                "- Assumed patient names\n"
                "- Documents treated as duplicates"
            ),
            input_source="zoho_folder",
            input_file_types="pdf,jpg,jpeg,png",
            output_format="markdown",
            output_filename_template="medical_tax_credit_package_{date}.md",
            chunk_strategy="per_document",
            merge_chunk_results=True,
            enable_web_search=False,
            upload_to_zoho=False,
            max_tokens=8192,
            temperature=0.0,
            max_pages_per_chunk=25
        )
    ]
)
