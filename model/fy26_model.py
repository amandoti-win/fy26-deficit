#!/usr/bin/env python3
"""FY2026 US federal deficit: how much traces to the 2025 reconciliation act (OBBBA, P.L. 119-21).

Run:  python3 fy26_model.py          (needs matplotlib for the charts)
Writes: ../results.json, ../charts/*.png, ../inputs_sourced.csv

All dollar figures are $ billions unless stated. Every input carries a source
(publication, table/line). Anything not verified is flagged UNVERIFIED and is either
excluded or exposed as an explicit assumption.

Version 2: tariffs are not an analytical question here. Tariffs, refunds and the economy are
held at actuals; net customs duties are one revenue line inside the residual.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
os.makedirs(os.path.join(OUT, "charts"), exist_ok=True)

# --------------------------------------------------------------------------
# SOURCES (short keys used in INPUTS)
# --------------------------------------------------------------------------
SRC = {
    "MTS": "Treasury, Monthly Treasury Statement Sept 2026 (final FY2026), "
           "https://fiscaldata.treasury.gov/static-data/published-reports/mts/MonthlyTreasuryStatement_202609.pdf",
    "MBR": "CBO, Monthly Budget Review: September 2026 (Oct 8, 2026), https://www.cbo.gov/publication/61985",
    "BASE": "CBO, Budget and Economic Outlook 2026-2036 (Feb 2026) data, Table 1-1, "
            "https://www.cbo.gov/system/files/2026-02/51118-2026-02-Budget-Projections.xlsx",
    "SCORE": "CBO/JCT, Estimated Budgetary Effects of P.L. 119-21 vs Jan 2025 baseline (Jul 21, 2025), "
             "Summary Table + Title VII sheet, https://www.cbo.gov/system/files/2025-07/61570-pl119-21-2025Recon-CLB.xlsx",
    "DEBTSVC": "CBO letter to Sen. Merkley (Aug 4, 2025), Table 1 data, "
               "https://www.cbo.gov/system/files/2025-08/61466-data.xlsx",
    "JCX34": "JCT JCX-34-25 (Jul 1, 2025), revenue effects vs current-policy baseline, total line, "
             "https://www.jct.gov/publications/2025/jcx-34-25/",
    "OUTLOOK26": "CBO, The Budget and Economic Outlook: 2026 to 2036 (Feb 2026), https://www.cbo.gov/system/files/2026-02/61882-Outlook-2026.pdf",
    "JAN25": "CBO, Budget Projections Jan 2025, Table B-1, https://www.cbo.gov/system/files/2025-01/51118-2025-01-Budget-Projections.xlsx",
    "CBO62442": "CBO blog, Revenue Collections Through the Individual Income Tax Filing Season (May 21, 2026), https://www.cbo.gov/publication/62442",
    "JCX35": "JCT JCX-35-25 (Jul 1, 2025), estimated revenue effects relative to the present-law baseline, NET TOTAL line and footnote [1], "
             "https://www.jct.gov/publications/2025/jcx-35-25/",
    "FRED": "BEA NIPA Table 1.12 via FRED (A053RC1Q027SBEA, A446RC1Q027SBEA), GDP (BEA via FRED 'GDP'), "
            "retrieved 2026-10-16, https://fred.stlouisfed.org/",
}

# --------------------------------------------------------------------------
# INPUTS  (name -> value, source key, note)
# --------------------------------------------------------------------------
I = {}


def inp(name, value, src, note=""):
    I[name] = {"value": value, "source": src, "note": note}
    return value


# --- Treasury MTS (Table 3, Table 4, Table 9), $B ---
d26 = inp("deficit_fy26", 1992.473, "MTS", "Table 3 'Surplus or Deficit', FYTD")
d25 = inp("deficit_fy25", 1775.369, "MTS", "Table 3 prior-period FYTD")
rev26 = inp("receipts_fy26", 5403.327, "MTS", "Table 3 Total Receipts")
rev25 = inp("receipts_fy25", 5234.616, "MTS", "Table 3")
out26 = inp("outlays_fy26", 7395.800, "MTS", "Table 3 Total Outlays")
out25 = inp("outlays_fy25", 7009.986, "MTS", "Table 3")
ind26, ind25 = inp("individual_fy26", 2845.527, "MTS", "Table 3"), inp("individual_fy25", 2656.044, "MTS", "Table 3")
corp26, corp25 = inp("corp_net_fy26", 381.415, "MTS", "Table 3/9"), inp("corp_net_fy25", 452.089, "MTS", "Table 3/9")
corp_gross26 = inp("corp_gross_fy26", 442.900, "MTS", "Table 4 Corporation Income Taxes, gross")
corp_gross25 = inp("corp_gross_fy25", 486.363, "MTS", "Table 4")
corp_ref26 = inp("corp_refunds_fy26", 61.485, "MTS", "Table 4 refunds")
corp_ref25 = inp("corp_refunds_fy25", 34.273, "MTS", "Table 4 refunds")
pay26 = inp("social_ins_fy26", 1754.273 + 49.090 + 8.431, "MTS", "Table 3: employment + UI + other retirement")
pay25 = inp("social_ins_fy25", 1685.632 + 54.049 + 8.614, "MTS", "Table 3")
exc26, exc25 = inp("excise_fy26", 105.995, "MTS", "Table 3"), inp("excise_fy25", 105.936, "MTS", "Table 3")
est26, est25 = inp("estate_gift_fy26", 38.720, "MTS", "Table 3"), inp("estate_gift_fy25", 29.462, "MTS", "Table 3")
misc26, misc25 = inp("misc_fy26", 46.657, "MTS", "Table 3"), inp("misc_fy25", 47.925, "MTS", "Table 3")
cust26, cust25 = inp("customs_net_fy26", 173.219, "MTS", "Table 3 net customs duties; revenue line inside the residual"), \
    inp("customs_net_fy25", 194.866, "MTS", "Table 3")

# Outlays by function (Table 9), (FY26, FY25)
FUNC = {
    "National Defense": (965.160, 916.649),
    "International Affairs": (48.015, 45.170),
    "Science/Space/Technology": (39.877, 42.084),
    "Energy": (20.971, 20.892),
    "Natural Resources & Environment": (57.098, 88.312),
    "Agriculture": (52.566, 49.358),
    "Commerce & Housing Credit": (-15.465, -28.626),
    "Transportation": (142.864, 145.804),
    "Community & Regional Development": (62.430, 84.530),
    "Education/Training/Social Services": (107.551, 71.014),
    "Health (incl. Medicaid)": (1025.587, 978.878),
    "Medicare": (1072.626, 996.719),
    "Income Security": (694.224, 701.584),
    "Social Security": (1667.097, 1580.686),
    "Veterans Benefits": (416.204, 377.162),
    "Administration of Justice": (109.915, 85.182),
    "General Government": (32.343, 34.454),
    "Net Interest (Treasury function)": (1051.754, 970.359),
    "Undistributed Offsetting Receipts": (-155.019, -150.225),
}
inp("outlays_by_function", FUNC, "MTS", "Table 9 Net Outlays, (FY26, FY25)")

# CBO-definition net interest = gross interest on Treasury debt less undistributed interest receipts (MTS Table 3)
ni26 = inp("net_interest_cbo_def_fy26", 1359.953 - 217.671, "MTS", "Table 3: gross interest 1,359.953 less undistributed interest 217.671; "
                                                                    "matches CBO MBR Table 3 ($1,143B)")
ni25 = inp("net_interest_cbo_def_fy25", 1215.614 - 187.547, "MTS", "Table 3; matches CBO MBR Table 3 ($1,028B)")

# --- CBO Monthly Budget Review figures ---
inp("cbo_mbr_deficit_change", 218, "MBR", "Summary; Table 1 (rounded)")
inp("cbo_corp_change", -70, "MBR", "Table 2: -$70B (-16%); text attributes to 2025 reconciliation act's larger investment deductions")
inp("cbo_sept_timing", "Sept 1 2025 holiday shifted payments into Aug 2025 (within FY2025); Sept 2025 surplus $198B -> $110B adjusted", "MBR", "p.5, Table 4 note a")
STUDENT_LOAN_ONE_TIME = inp("cbo_education_sept25_student_loan", -131.0, "MBR",
                            "p.5: Sept 2025 recorded a $131B reduction in Education outlays from OBBBA student-loan program modifications")

# --- CBO Feb 2026 baseline, FY2026 corporate (used only in the corporate counterfactuals) ---
b_corp = inp("base_corp_fy26", 404.0, "BASE", "Table 1-1")

# --- OBBBA score, $B. Sign: + = deficit increase; revenue change as reported (negative = revenue loss) ---
sc = {
    "outlays": {2025: -152.014, 2026: 26.338},
    "revenues": {2025: -130.904, 2026: -460.501},   # JCT revenue change, vs Jan-2025 current-law baseline
    "deficit": {2025: -21.110, 2026: 486.839},
}
inp("obbba_score", sc, "SCORE", "Summary Table 'Total Changes'; deficit = outlays - revenues")
debt_svc = {2025: 0.398, 2026: 14.143}
inp("obbba_debt_service", debt_svc, "DEBTSVC", "Table 1 'Changes From Debt Service'")
jct_cp_rev = {2025: -124.612, 2026: -255.056}
inp("jct_current_policy_title7_revenue", jct_cp_rev, "JCX34", "Total line; Title VII revenue provisions only")
nonVII_rev = {2025: -130.904 - (-130.903), 2026: -460.501 - (-461.569)}
inp("nonTitleVII_revenue", nonVII_rev, "SCORE", "Summary Table: total revenues minus Title VII revenues")

# business-tax provisions (CBO/JCT present-law baseline), (FY25, FY26) $B revenue change, negative = revenue loss
BUS = {
    "70301 Full expensing, business property": (-33.5, -65.1),
    "70302 Domestic R&E expensing": (-53.8, -33.6),
    "70303 Business interest limit (EBITDA)": (-8.3, -6.5),
    "70306 Sec. 179 limits": (-2.3, -4.3),
    "70307 Qualified production property": (-2.2, -30.3),
    "70308 Adv. manufacturing credit": (0.0, -1.7),
    "70304 Paid leave credit": (0.0, -0.1),
    "International provisions (70311-70313, 70321-23, 70331, 70341-42, 70351-54), net": (0.0, -10.1),
}
inp("business_provisions", BUS, "SCORE", "Title VII sheet, JCT revenue rows by section (rounded to $0.1B). "
                                         "Covers ALL taxpayers (corporate + pass-through); JCT does not publish a corporate-only split here.")
# CBO Feb 2026 Outlook (ch.5 text on Table 5-1): the act reduced projected CORPORATE receipts by $98B in FY2026
# ($352B over 2026-2035) and INDIVIDUAL by $361B in FY2026.
OBBBA_CORP_FY26 = inp("cbo_obbba_corp_effect_fy26", 98.0, "OUTLOOK26",
                      "Outlook 2026-2036 (Feb 2026), 'Corporate Income Taxes' paragraph under legislative changes; p.106 of PDF. Level effect vs Jan-2025 law")
inp("cbo_obbba_individual_effect_fy26", 361.0, "OUTLOOK26", "same page; includes pass-through business income")
JAN25_CORP = {2025: inp("jan25_baseline_corp_fy25", 523.7, "JAN25", "Table B-1"), 2026: inp("jan25_baseline_corp_fy26", 495.1, "JAN25", "Table B-1")}

# --- BEA profits and GDP via FRED ($B, SAAR) ---
PROF_ECON = {  # profits WITH IVA and CCAdj (economic basis): A053RC1Q027SBEA
    "2023Q4": 3885.951, "2024Q1": 3970.797, "2024Q2": 4071.805, "2024Q3": 4035.126, "2024Q4": 4296.969,
    "2025Q1": 3966.993, "2025Q2": 3997.597, "2025Q3": 4240.461, "2025Q4": 4464.427, "2026Q1": 4673.220, "2026Q2": 5111.956}
PROF_TAX = {  # profits WITHOUT IVA/CCAdj (tax-return depreciation basis): A446RC1Q027SBEA
    "2023Q4": 3471.403, "2024Q1": 3543.767, "2024Q2": 3632.837, "2024Q3": 3642.877, "2024Q4": 3808.821,
    "2025Q1": 3478.754, "2025Q2": 3523.971, "2025Q3": 3736.828, "2025Q4": 3880.594, "2026Q1": 4154.402, "2026Q2": 4565.549}
GDP_Q = {"2025Q4": 31462.523, "2026Q1": 31906.274, "2026Q2": 32563.030}
inp("bea_profits_econ_basis", PROF_ECON, "FRED", "Corporate profits with IVA & CCAdj, $B SAAR")
inp("bea_profits_tax_basis", PROF_TAX, "FRED", "Corporate profits before tax without IVA/CCAdj, $B SAAR")
inp("gdp_quarterly", GDP_Q, "FRED", "Nominal GDP, $B SAAR")
GDP_Q3_26_ASSUMED_QOQ = inp("gdp_2026q3_assumed_qoq_growth", 0.016, "ASSUMPTION",
                            "UNVERIFIED. BEA advance Q3 GDP is scheduled Oct 29, 2026 (not yet published). +1.6% q/q nominal = Atlanta Fed "
                            "GDPNow real 3.7% SAAR (Oct 6, via Trading Economics) plus an ASSUMED ~3% deflator. Sensitivity in results.")

# --------------------------------------------------------------------------
# CALCULATIONS
# --------------------------------------------------------------------------
R = {}
dd = d26 - d25                       # Treasury YoY deficit change
R["deficit_change_treasury"] = dd
R["deficit_change_pct"] = dd / d25
R["receipts_change"] = rev26 - rev25
R["outlays_change"] = out26 - out25

gdp_q3 = GDP_Q["2026Q2"] * (1 + GDP_Q3_26_ASSUMED_QOQ)
gdp26 = (GDP_Q["2025Q4"] + GDP_Q["2026Q1"] + GDP_Q["2026Q2"] + gdp_q3) / 4
R["gdp_fy26_est"] = gdp26
R["deficit_pct_gdp"] = d26 / gdp26
R["cbo_implied_gdp"] = d26 / 0.062   # CBO/AAF report 6.2% of GDP; cross-check only
R["gdp_sensitivity"] = {}
for g in (0.011, 0.016, 0.021):
    fy = (GDP_Q["2025Q4"] + GDP_Q["2026Q1"] + GDP_Q["2026Q2"] + GDP_Q["2026Q2"] * (1 + g)) / 4
    R["gdp_sensitivity"]["Q3 q/q %.1f%%" % (100 * g)] = {"fy26_gdp": fy, "deficit_pct_gdp": d26 / fy}

# CBO 61570 Table 7 section rows (moved up: used for the count-once current-policy adjustment)
T7 = [["70101", "Extension and Enhancement of Reduced Rates", 0, -147.679, 0, 0], ["70102", "Extension and Enhancement of Increased Standard Deduction", -7.544, -90.405, 0, 1.719], ["70103", "Termination of Deduction for Personal Exemptions Other Than Temporary Senior Deduction", -9.264, 111.036, 0, 0.411], ["70104", "Extension and Enhancement of Increased Child Tax Credit", 0, -48.769, 0, 0], ["70108", "Extension and Modification of Limitation on Deduction for Qualified Residence Interest", 0, 1.639, 0, 0], ["70109", "Extension and Modification of Limitation on Casualty Loss Deduction", 0, 0.086, 0, 0], ["70115", "Extension and Enhancement of Increased Limitation on Contributions to ABLE Accounts", 0, 0, 0, 0], ["70116", "Extension and Enhancement of Savers Credit Allowed for ABLE Contributions", 0, 0, 0, 0], ["70117", "Extension of Rollovers from Qualified Tuition Programs to ABLE Accounts Permitted", 0, 0, 0, 0], ["70120", "Limitation on Individual Deductions for Certain State and Local Taxes", -5.07, 31.805, 0, 0.188], ["70204", "Trump Accounts and Contribution Pilot Program", 0, 0.132, 0.731, 6.628], ["70402", "Enhancement of Adoption Credit", -0.004, -0.009, 0.185, 0.41], ["70403", "Recognizing Indian Tribal Governments (adoption credit)", 0, 0, 0, 0], ["70404", "Enhancement of the Dependent Care Assistance Program", 0, -0.365, 0, 0], ["70405", "Enhancement of Child and Dependent Care Tax Credit", 0, -0.409, 0, 0], ["70421", "Permanent Renewal and Enhancement of Opportunity Zones", 0, 0, 0, 0.01], ["70427", "Permanent Increase in Limitation on Cover Over of Tax on Distilled Spirits", 0, 0, 0, 0.251], ["70439", "Restoration of Taxable REIT Subsidiary Asset Test", 0, -0.08, 0, 0], ["70501", "Termination of Previously-Owned Clean Vehicle Credit", 0, 0.15, 0, 0.043], ["70502", "Termination of Clean Vehicle Credit", 0, 0.107, 0, -0.966], ["70511", "Termination of Clean Hydrogen Production Credit", 0, 0, 0, 0], ["70512", "Termination and Restrictions on Clean Electricity Production Credit", 0, 0, 0, 0], ["70513", "Termination and Restrictions on Clean Electricity Investment Credit", 0, 0.281, 0, 0], ["70514", "Phase-Out and Restrictions on Advanced Manufacturing Production Credit", -0.027, 1.731, -0.027, -0.095], ["70531", "Modifications to De Minimis Entry Privilege for Commercial Shipments", 0, 0, 0, 0], ["70605", "Enforcement Provisions With Respect to COVID-Related Employee Retention Credits", 0.185, 0.752, -0.061, -0.251], ["70606", "Social Security Number Requirement for American Opportunity and Lifetime Learning Credits", 0, 0.015, 0, 0], ["70607", "Task Force on the Replacement of Direct File", 0, 0, 0, 0.008], ["71101", "Moratorium: Medicare Savings Programs eligibility rule", 0, 0, 0, -1.668], ["71102", "Moratorium: eligibility and enrollment rule (Medicaid, CHIP, BHP)", 0, -0.162, 0, -4.02], ["71103", "Reducing Duplicate Enrollment (Medicaid, CHIP)", 0, 0, 0, 0.001], ["71104", "Ensuring Deceased Individuals Do Not Remain Enrolled", 0, 0, 0, 0], ["71105", "Ensuring Deceased Providers Do Not Remain Enrolled", 0, 0, 0, 0], ["71106", "Payment Reduction for Erroneous Excess Payments", 0, 0, 0, 0], ["71107", "Eligibility Redeterminations", 0, 0, 0, 0.004], ["71108", "Home Equity Limit for Long-Term Care Eligibility", 0, 0, -0.001, -0.005], ["71109", "Alien Medicaid Eligibility", 0, 0, 0, -0.372], ["71110", "Expansion FMAP for Emergency Medicaid", 0, 0, 0, 0], ["71111", "Moratorium: Long-Term Care Staffing Standards Rule", 0, 0, 0, -0.287], ["71112", "Reducing State Medicaid Costs", 0, 0, 0, 0], ["71113", "Federal Payments to Prohibited Entities", 0, 0, -0.044, -0.031], ["71114", "Sunsetting Increased FMAP Incentive", 0, -0.059, 0, -0.953], ["71115", "Provider Taxes", 0, -0.188, 0, -2.786], ["71116", "State Directed Payments", 0, 0, 0, -5.457], ["71117", "Waiver of Uniform Tax Requirement for Medicaid Provider Taxes", 0, -0.061, 0, -3.158], ["71118", "Budget Neutrality for Medicaid Demonstration Projects", 0, 0, 0, 0.002], ["71119", "Medicaid Community Engagement Requirements", 0, 0, 0, 0.18], ["71120", "Cost Sharing for Expansion Individuals", 0, 0, 0, 0.001], ["71121", "Adjustments to Home or Community-Based Services Coverage", 0, 0, 0, 0.002], ["71201", "Limiting Medicare Coverage of Certain Individuals", 0, 0, 0, 0], ["71202", "Temporary Payment Increase Under the Medicare Physician Fee Schedule", 0, 0, 0, 1.221], ["71203", "Orphan Drugs Exclusion Under Drug Price Negotiation", 0, 0, 0, 0], ["71301", "Permitting Premium Tax Credit Only for Certain Individuals", 0, 0, 0, 0], ["71302", "Disallowing Premium Tax Credit During Periods of Medicaid Ineligibility (alien status)", 0, 0.011, 0, -3.307], ["71303", "Requiring Verification of Eligibility for Premium Tax Credit", 0, 0, 0, 0], ["71304", "Disallowing Premium Tax Credit for Certain Special Enrollment Period Coverage", 0, 0.052, 0, -1.587], ["71305", "Eliminating Limitation on Recapture of Advance Premium Tax Credit (incl. interactions row)", 0, -0.001, 0, 1.682], ["71401", "Rural Health Transformation Program", 0, 0, 0, 0.472], ["73001", "Ending Unemployment Payments to Jobless Millionaires", 0, 0, 0, 0], ["70105", "Extension and Enhancement of Deduction for Qualified Business Income", -6.97, -44.331, 0, 0], ["70106", "Extension and Enhancement of Increased Estate and Gift Tax Exemption Amounts", -0.05, -3.672, 0, 0], ["70107", "Extension of Increased Alternative Minimum Tax Exemption Amounts", 0, -76.835, 0, 0], ["70110", "Termination of Miscellaneous Itemized Deductions Other Than Educator Expenses", 0, 13.419, 0, 0], ["70111", "Limitation on Tax Benefit of Itemized Deductions", 0, -16.04, 0, 0], ["70112", "Qualified Transportation Fringe Benefits", 0, -0.071, 0, 0], ["70113", "Moving Expenses Deduction and Exclusion Limitation", 0, 0.673, 0, 0], ["70114", "Limitation on Wagering Losses", 0, 0.001, 0, 0], ["70118", "Treatment of Individuals Performing Services in the Sinai Peninsula", 0, -0.001, 0, 0], ["70119", "Exclusion of Student Loans Discharged on Death or Disability", 0, 0, 0, 0], ["70201", "No Tax on Tips", 0, -10.121, 0, 0], ["70202", "No Tax on Overtime", 0, -32.806, 0, 0], ["70203", "No Tax on Car Loan Interest", -1.932, -5.4, 0, 0], ["70301", "Full Expensing for Certain Business Property", -33.505, -65.123, 0, 0], ["70302", "Full Expensing of Domestic Research and Experimental Expenditures", -53.793, -33.585, 0, 0], ["70303", "Modification of Limitation on Business Interest", -8.268, -6.519, 0, 0], ["70304", "Paid Family and Medical Leave Credit", 0, -0.102, 0, 0], ["70305", "Exceptions From Limitations on Deduction for Business Meals", 0, -0.042, 0, 0], ["70306", "Increased Dollar Limitations for Expensing of Depreciable Business Assets", -2.301, -4.292, 0, 0], ["70307", "Special Depreciation Allowance for Qualified Production Property", -2.167, -30.28, 0, 0], ["70308", "Enhancement of Advanced Manufacturing Investment Credit", 0, -1.728, 0, 0], ["70309", "Spaceports Treated Like Airports Under Exempt Facility Bond Rules", 0, -0.011, 0, 0], ["70311", "Foreign Tax Credit Limitation", 0, -1.347, 0, 0], ["70312", "Deemed Paid Credit for Tested Income Taxes", 0, -1.476, 0, 0], ["70313", "Sourcing Income From Sale of US-Produced Inventory", 0, -0.462, 0, 0], ["70321", "Foreign-Derived Deduction Eligible Income and Net CFC Tested Income", 0, -4.131, 0, 0], ["70322", "Determination of Deduction Eligible Income", 0, -2.08, 0, 0], ["70323", "Rules Related to Deemed Intangible Income", 0, -0.394, 0, 0], ["70331", "Base Erosion Minimum Tax Amount", 0, -1.861, 0, 0], ["70341", "Coordination of Business Interest Limitation With Interest Capitalization", 0, 0.36, 0, 0], ["70342", "Adjusted Taxable Income for Business Interest Limitation", 0, 0.66, 0, 0], ["70351", "Look-Thru Rule for Related CFCs", 0, -0.534, 0, 0], ["70352", "Repeal of 1-Month Deferral Election", 0, 0.393, 0, 0], ["70353", "Limitation on Downward Attribution of Stock Ownership", 0, -0.316, 0, 0], ["70354", "Pro Rata Share Rules", 0, 0.867, 0, 0], ["70401", "Employer-Provided Child Care Credit", 0, -0.045, 0, 0], ["70411", "Credit for Contributions to Scholarship Granting Organizations", 0, 0, 0, 0], ["70412", "Exclusion for Employer Payments of Student Loans", 0, -0.706, 0, 0], ["70413", "Qualified Higher Education Expenses for 529 Accounts", 0, -0.022, 0, 0], ["70414", "Postsecondary Credentialing Expenses and 529 Accounts", 0, 0, 0, 0], ["70415", "Excise Tax on Investment Income of Private Colleges", 0, 0, 0, 0], ["70416", "Tax on Excess Compensation in Tax-Exempt Organizations", 0, 0.236, 0, 0], ["70422", "Low-Income Housing Tax Credit Enhancement", 0, -0.039, 0, 0], ["70423", "New Markets Tax Credit Extension", 0, 0, 0, 0], ["70424", "Partial Charitable Deduction for Non-Itemizers", 0, -1.543, 0, 0], ["70425", "0.5-Percent Floor on Individual Charitable Deductions", 0, 1.346, 0, 0], ["70426", "1-Percent Floor on Corporate Charitable Deductions", 0, 1.276, 0, 0], ["70428", "Nonprofit Community Development in Remote Native Villages", 0, 0, 0, 0], ["70429", "Charitable Deduction for Alaskan Subsistence Whaling", 0, 0, 0, 0], ["70430", "Percentage of Completion Method Exception", 0, -0.638, 0, 0], ["70431", "Expansion of Qualified Small Business Stock Gain Exclusion", 0.027, 0.056, 0, 0], ["70432", "De Minimis Rules for Third Party Network Transactions", -0.038, -1.108, 0, 0], ["70433", "Information Reporting Threshold for Payees", 0, -0.196, 0, 0], ["70434", "Qualified Sound Recording Productions", -0.085, -0.369, 0, 0], ["70435", "Exclusion of Interest on Rural or Agricultural Real Property Loans", -0.009, -0.06, 0, 0], ["70436", "Transfer and Manufacturing Taxes on Certain Devices", -0.015, -0.102, 0, 0], ["70437", "Capital Gains From Sale of Farmland", -0.055, -0.765, 0, 0], ["70438", "Disaster-Related Personal Casualty Losses", -0.006, -0.052, 0, 0], ["70503", "Termination of Qualified Commercial Clean Vehicles Credit", 0, 8.303, 0, 0], ["70504", "Termination of Alternative Fuel Vehicle Refueling Property Credit", 0, 0.02, 0, 0], ["70505", "Termination of Energy Efficient Home Improvement Credit", 0, 0.258, 0, 0], ["70506", "Termination of Residential Clean Energy Credit", -0.142, -0.753, 0, 0], ["70507", "Termination of Energy Efficient Commercial Buildings Deduction", 0, 0, 0, 0], ["70508", "Termination of New Energy Efficient Home Credit", 0, 0.104, 0, 0], ["70509", "Termination of Cost Recovery for Energy Property", 0.004, 0.057, 0, 0], ["70521", "Clean Fuel Production Credit Extension and Modification", -0.026, -1.11, 0, 0], ["70522", "Restrictions on Carbon Oxide Sequestration Credit", -0.179, -0.364, 0, 0], ["70523", "Intangible Drilling and Development Costs", 0, -0.025, 0, 0], ["70524", "Qualifying Income of Certain Publicly Traded Partnerships", 0, -0.157, 0, 0], ["70525", "Payments to Certain Individuals Who Dye Fuel", 0, 0, 0, 0], ["70601", "Limitation on Excess Business Losses", 0, 0.107, 0, 0], ["70602", "Payments From Partnerships to Partners", 0.338, 1.612, 0, 0], ["70603", "Excessive Employee Remuneration From Controlled Groups", 0, 0.643, 0, 0], ["70604", "Excise Tax on Remittance Transfers", 0, 0.362, 0, 0], ["71306", "Safe Harbor for Absence of Deductible for Telehealth", -0.007, -0.121, 0, 0], ["71307", "Bronze and Catastrophic Plans With HSAs", 0, -0.127, 0, 0], ["71308", "Direct Primary Care Service Arrangements", 0, 0.024, 0, 0]]
T7 = {r[0]: dict(label=r[1], rev25=r[2], rev26=r[3], out25=r[4], out26=r[5]) for r in T7}
for sec, r in T7.items():
    inp("prov_cbo_sec" + sec, [r["rev25"], r["rev26"], r["out25"], r["out26"]], "SCORE",
        "Table 7 (sheet 'Title VII'), Sec. " + sec + " " + r["label"] + ": [FY25 revenue, FY26 revenue, FY25 outlays, FY26 outlays] $B")


# ---- Q1: OBBBA ----------------------------------------------------------
q1 = {}
q1["level_present_law"] = {"outlays": sc["outlays"][2026], "revenue_loss": -sc["revenues"][2026], "deficit": sc["deficit"][2026]}
cp_rev26 = jct_cp_rev[2026] + nonVII_rev[2026]
cp_rev25 = jct_cp_rev[2025] + nonVII_rev[2025]
# Count-once adjustment. CBO's outlay total includes outlay effects of tax provisions that JCT also scores in its net
# revenue effect (JCX-34-25), so adding the two counts those outlays twice. Remove them from the outlay side. Medicaid
# revenue effects (Secs. 71101 to 71121) sit in the section rows but outside the JCT-based revenue total; add them.
def _tax_out(y):
    return sum(T7[x]["out" + y] for x in T7 if 70101 <= int(x) <= 70607 or 71301 <= int(x) <= 71308)
def _med_rev(y):
    return -sum(T7[x]["rev" + y] for x in T7 if 71101 <= int(x) <= 71121)
ADJ = {2025: (_tax_out("25"), _med_rev("25")), 2026: (_tax_out("26"), _med_rev("26"))}
cp_out = {y: sc["outlays"][y] - ADJ[y][0] for y in (2025, 2026)}
cp_revloss = {2025: -cp_rev25 + ADJ[2025][1], 2026: -cp_rev26 + ADJ[2026][1]}
R["cp_count_once_adjustment"] = {"tax_outlays_removed": {y: ADJ[y][0] for y in ADJ}, "medicaid_revenue_added": {y: ADJ[y][1] for y in ADJ},
                                 "uncorrected_level_fy26": sc["outlays"][2026] - cp_rev26,
                                 "uncorrected_yoy": (sc["outlays"][2026] - sc["outlays"][2025]) - (cp_rev26 - cp_rev25)}
q1["level_current_policy"] = {"outlays": cp_out[2026], "revenue_loss": cp_revloss[2026],
                              "deficit": cp_out[2026] + cp_revloss[2026]}
q1["yoy_present_law"] = {
    "outlays": sc["outlays"][2026] - sc["outlays"][2025],
    "revenue_loss": -(sc["revenues"][2026] - sc["revenues"][2025]),
    "deficit": sc["deficit"][2026] - sc["deficit"][2025]}
q1["yoy_current_policy"] = {
    "outlays": cp_out[2026] - cp_out[2025],
    "revenue_loss": cp_revloss[2026] - cp_revloss[2025],
    "deficit": (cp_out[2026] + cp_revloss[2026]) - (cp_out[2025] + cp_revloss[2025])}
for k, v in q1.items():
    v["pct_of_increase_treasury"] = v["deficit"] / dd
    v["pct_of_increase_cbo218"] = v["deficit"] / 218.0
    v["pct_of_fy26_deficit"] = v["deficit"] / d26
q1["debt_service_fy26"] = debt_svc[2026]
q1["debt_service_yoy"] = debt_svc[2026] - debt_svc[2025]
# One-time FY2025 student-loan entry: its non-recurrence is counted as a deficit increase in the YoY outlay swing
q1["one_time_student_loan_entry"] = STUDENT_LOAN_ONE_TIME
q1["student_loan_share_of_outlay_swing"] = -STUDENT_LOAN_ONE_TIME / q1["yoy_current_policy"]["outlays"]
q1["yoy_current_policy_ex_one_time"] = q1["yoy_current_policy"]["deficit"] + STUDENT_LOAN_ONE_TIME
q1["yoy_current_policy_ex_one_time_pct"] = q1["yoy_current_policy_ex_one_time"] / dd
q1["yoy_outlays_ex_one_time"] = q1["yoy_current_policy"]["outlays"] + STUDENT_LOAN_ONE_TIME
q1["level_pct_of_fy26_deficit"] = sc["deficit"][2026] / d26
R["q1"] = q1

# ---- Q3: corporate counterfactuals (unchanged from v1) --------------------


def avg(d, keys):
    return sum(d[k] for k in keys) / len(keys)


cy24 = ["2024Q1", "2024Q2", "2024Q3", "2024Q4"]
cy25 = ["2025Q1", "2025Q2", "2025Q3", "2025Q4"]
t4_26 = ["2025Q3", "2025Q4", "2026Q1", "2026Q2"]
t4_25 = ["2024Q3", "2024Q4", "2025Q1", "2025Q2"]
f3_26 = ["2025Q4", "2026Q1", "2026Q2"]     # FY2026 Q1-Q3 (Oct-Jun)
f3_25 = ["2024Q4", "2025Q1", "2025Q2"]
growth = {
    "low (CY2025 vs CY2024, econ basis)": avg(PROF_ECON, cy25) / avg(PROF_ECON, cy24) - 1,
}
growth_tax_basis = {
    "CY2025 vs CY2024": avg(PROF_TAX, cy25) / avg(PROF_TAX, cy24) - 1,
}
q3 = {"actual_decline_pct": corp26 / corp25 - 1, "actual_decline": corp26 - corp25}
cfs = {}
cfs["A: add back full 16% loss"] = corp25
for (name, g) in growth.items():
    cfs["B " + name] = corp25 * (1 + g)
bus_delta = sum(v[1] - v[0] for v in BUS.values())           # change in business-provision revenue effect, all taxpayers (negative = loss)
q3["business_provisions_delta_all_taxpayers"] = bus_delta
q3["business_provisions_fy25"] = sum(v[0] for v in BUS.values())
q3["business_provisions_fy26"] = sum(v[1] for v in BUS.values())
CORP_SHARE_IMPLIED = OBBBA_CORP_FY26 / -q3["business_provisions_fy26"]
q3["corp_share_implied"] = CORP_SHARE_IMPLIED
cfs["C1 score delta x CBO-implied corp share (%.0f%%)" % (100 * CORP_SHARE_IMPLIED)] = corp26 + (-bus_delta) * CORP_SHARE_IMPLIED
cfs["C2 CBO Feb-2026 baseline-implied"] = corp26 + (corp25 - b_corp)
jan25_path = corp25 * JAN25_CORP[2026] / JAN25_CORP[2025]
cfs["C3 CBO Jan-2025 (pre-OBBBA) path on FY25 actual"] = jan25_path
cfs["C4 CBO-reported FY26 OBBBA corporate effect (level)"] = corp26 + OBBBA_CORP_FY26
q3["jan25_expected_change"] = JAN25_CORP[2026] - JAN25_CORP[2025]
q3["jan25_path_receipts"] = jan25_path
q3["baseline_implied_decline"] = corp25 - b_corp
q3["actual_vs_baseline"] = corp26 - b_corp
q3["cf"] = {}
for name, v in cfs.items():
    q3["cf"][name] = {"receipts": v, "revenue_diff": v - corp26, "deficit_effect": -(v - corp26),
                      "deficit_cf": d26 - (v - corp26), "pct_of_actual_decline": (v - corp26) / (corp25 - corp26)}
q3["profit_growth"] = growth
q3["profit_growth_tax_basis"] = growth_tax_basis
q3["gross_receipts_change"] = corp_gross26 - corp_gross25
q3["refunds_change"] = corp_ref26 - corp_ref25
R["q3"] = q3

# ---- Q4: OBBBA-only bridge -------------------------------------------------
obbba_out = q1["yoy_current_policy"]["outlays"]
obbba_rev = q1["yoy_current_policy"]["revenue_loss"]
obbba_tot = q1["yoy_current_policy"]["deficit"]
ni_chg = ni26 - ni25
other_out = (out26 - out25) - obbba_out - ni_chg                  # plug: all other outlay growth
other_rev = -((rev26 - rev25) + obbba_rev)                        # plug: all other revenue growth incl. net customs; deficit effect
resid = dd - obbba_tot
q4 = {
    "denominator": dd,
    "obbba_total": obbba_tot, "obbba_pct": obbba_tot / dd,
    "obbba_outlays": obbba_out, "obbba_revenue_loss": obbba_rev,
    "observed_corp_drop": -q3["actual_decline"], "observed_corp_pct": -q3["actual_decline"] / dd,
    "residual_total": resid, "residual_pct": resid / dd,
    "net_interest": ni_chg, "other_outlays_plug": other_out, "other_revenue_incl_customs_plug": other_rev,
    "residual_check": ni_chg + other_out + other_rev - resid,
    "bridge_sum": d25 + obbba_out + obbba_rev + ni_chg + other_out + other_rev,
    "bridge_target": d26,
    "bridge_check": d25 + obbba_out + obbba_rev + ni_chg + other_out + other_rev - d26,
    "obbba_debt_service_in_interest": q1["debt_service_yoy"],
    "obbba_present_law": q1["yoy_present_law"]["deficit"],
}
q4["outlay_lines_change"] = {k: a - b for k, (a, b) in FUNC.items()}
q4["revenue_lines_deficit_effect"] = {
    "Individual income taxes": -(ind26 - ind25), "Social insurance (payroll)": -(pay26 - pay25),
    "Corporate income taxes": -(corp26 - corp25), "Net customs duties": -(cust26 - cust25),
    "Excise": -(exc26 - exc25), "Estate & gift": -(est26 - est25), "Miscellaneous": -(misc26 - misc25)}
R["q4"] = q4

# ---- Q5: deficit without OBBBA --------------------------------------------
cases = {
    "Low removal (current-policy baseline; TCJA-type provisions treated as continuing)": q1["level_current_policy"]["deficit"],
    "Base (CBO/JCT score vs Jan-2025 current-law baseline)": sc["deficit"][2026],
    "High removal (base + debt service)": sc["deficit"][2026] + debt_svc[2026],
}
q5 = {"gdp": gdp26, "actual": d26, "actual_pct": d26 / gdp26, "cases": {}}
for k, eff in cases.items():
    v = d26 - eff
    q5["cases"][k] = {"effect_removed": eff, "deficit": v, "pct_gdp": v / gdp26,
                      "pct_gdp_at_cbo_implied_gdp": v / R["cbo_implied_gdp"]}
q5["fy25_deficit_ex_obbba_current_law"] = d25 - sc["deficit"][2025]
R["q5"] = q5

# ---- Provision-level breakdown of the act's FY2026 effect (Section 6.1) -----------------------------
# Sign convention in this block: deficit effect, + raises the deficit. Source rows follow JCT/CBO signs
# (revenue change: negative = revenue loss; outlay change: positive = more outlays), so
#   deficit effect = outlays - revenues.
# CBO 61570 workbook, Table 7 (sheet "Title VII"): one revenue row (JCT estimate) and one outlay row per section.
# Row values below are (section, label, FY2025 revenue, FY2026 revenue, FY2025 outlays, FY2026 outlays) in $B,
# copied from the workbook. Section 71305 outlays combine the section row (-0.039) and the unlabelled
# interactions row that follows it (+1.721) so that Subtitle B outlays sum to the workbook subtotal (-20.066).
# JCT JCX-34-25 (current-policy baseline): (FY2025, FY2026) in $M, PDF page, chapter and item. These are NET budget
# effects: JCT footnote [1] states that the estimates include outlay effects of refundable credits and similar items.
JCX34 = {
    "c1_1_rates": (0, -4948, 1, "Ch.1 item 1"), "c1_2_stdded": (-7544, -18959, 1, "Ch.1 item 2"),
    "c1_3_persex": (-9264, -23050, 1, "Ch.1 item 3 (includes temporary senior deduction)"), "c1_4_ctc": (0, -10014, 1, "Ch.1 item 4"),
    "c1_5_qbi": (0, -388, 1, "Ch.1 item 5"), "c1_7_amt": (0, 742, 1, "Ch.1 item 7"), "c1_10_miscitem": (0, -9, 1, "Ch.1 item 10"),
    "c1_11_itemlim": (0, 1402, 1, "Ch.1 item 11"), "c1_20_salt": (-5070, -34177, 2, "Ch.1 item 20"),
    "c1_total": (-21878, -89657, 2, "Total of Chapter 1"),
    "c2_1_tips": (0, -10121, 2, "Ch.2 item 1"), "c2_2_ot": (0, -32806, 2, "Ch.2 item 2"), "c2_3_car": (-1932, -5400, 2, "Ch.2 item 3"),
    "c2_4_trump": (-731, -6446, 2, "Ch.2 item 4"), "c2_total": (-2663, -54773, 2, "Total of Chapter 2"),
    "c3A_1_bonus": (-33505, -54214, 2, "Ch.3 Subch.A item 1"), "c3A_2_rnd": (-53793, -33585, 2, "Ch.3 Subch.A item 2"),
    "c3A_3_163j": (-8268, -6519, 2, "Ch.3 Subch.A item 3"), "c3A_4_leave": (0, -102, 2, "Ch.3 Subch.A item 4"),
    "c3A_5_meals": (0, 2424, 2, "Ch.3 Subch.A item 5"), "c3A_6_179": (-2301, -4292, 2, "Ch.3 Subch.A item 6"),
    "c3A_7_qpp": (-2167, -30280, 3, "Ch.3 Subch.A item 7"), "c3A_8_advmfg": (0, -1728, 3, "Ch.3 Subch.A item 8"),
    "c3A_9_space": (0, -11, 3, "Ch.3 Subch.A item 9"), "c3_total": (-100034, -129384, 3, "Total of Chapter 3"),
    "c4D_1_qsbs": (27, 56, 5, "Ch.4 Subch.D item 1"), "c4_total": (-271, 893, 5, "Total of Chapter 4"),
    "c5A_3_commcv": (0, 8303, 5, "Ch.5 Subch.A item 3"), "c5_total": (-343, 9619, 6, "Total of Chapter 5"),
    "c6_total": (584, 3742, 7, "Total of Chapter 6"), "healthtax_total": (-7, 4504, 7, "Subtitle B, Chapter 3 (Health Tax) total"),
    "net_total": (-124612, -255056, 8, "NET TOTAL"),
}
for k, (a, b, pg, ref) in JCX34.items():
    inp("prov_jcx34_" + k, [a / 1000.0, b / 1000.0], "JCX34",
        "PDF p." + str(pg) + ", " + ref + ": [FY2025, FY2026] $B, net budget effect (revenue less outlay effects)")
J = {k: (v[0] / 1000.0, v[1] / 1000.0) for k, v in JCX34.items()}
jpage = {k: v[2] for k, v in JCX34.items()}

# Other CBO titles (Tables 1 to 6 and 8 to 10; Summary Table): (FY2025, FY2026) deficit effect, $B.
OTH = {
    "t1_nutrition": (0.000, -7.961, "Table 1 (Title I), Subtotal, Subtitle A. Nutrition"),
    "t1_other": (0.300, -7.901 - (-7.961), "Table 1 (Title I), total changes (FY25 0.300, FY26 -7.901) less Subtitle A"),
    "t2_defense": (2.020, 41.864, "Table 2 (Title II), Total Changes in Direct Spending"),
    "t3_banking": (-0.015, 0.070, "Summary Table, Title III net effect on the deficit"),
    "t4_commerce": (-0.064, 2.845, "Summary Table, Title IV net effect on the deficit"),
    "t5_energy": (-0.156, -0.178, "Table 5 (Title V), Total Changes in Direct Spending"),
    "t6_epw": (-0.857, -0.936, "Table 6 (Title VI), Total Changes in Direct Spending"),
    "t8_loanlimits": (0.000, -0.960, "Table 8 (Title VIII), Subtotal, Subtitle B. Loan Limits"),
    "t8_loanrepay": (-149.990, -12.090, "Table 8 (Title VIII), Subtotal, Subtitle C. Loan Repayment"),
    "t8_pell": (0.000, 2.730, "Table 8 (Title VIII), Subtotal, Subtitle D. Pell Grants"),
    "t8_other": (-154.029 - (0.000 - 149.990 + 0.000), -10.584 - (-0.960 - 12.090 + 2.730),
                 "Table 8 (Title VIII), Total Changes in Direct Spending less Subtitles B, C and D (Subtitles A, E, F, G, H and Total Interactions)"),
    "t9_dhs": (0.005, 9.511, "Table 9 (Title IX), Total Changes in Direct Spending"),
    "t10_judiciary": (0.000, 3.579 - 1.290, "Table 10 (Title X), outlays $3.579B less Subtitle A revenues $1.290B"),
    "interactions": (0.000, 0.000, "Summary Table, Interactions Among Titles (outlays and revenues both 0.0 in FY2026)"),
}
for k, (a, b, ref) in OTH.items():
    inp("prov_cbo_" + k, [round(a, 3), round(b, 3)], "SCORE", ref + ": [FY2025, FY2026] deficit effect $B")
# Title VII net deficit effect = outlays minus revenues, Table 7 totals: outlays (FY25 0.783, FY26 -11.710), revenues (FY25 -130.903, FY26 -461.569)
TITLE7_NET = {2025: 0.783 + 130.903, 2026: -11.710 + 461.569}
inp("prov_cbo_title7_net", [TITLE7_NET[2025], TITLE7_NET[2026]], "SCORE",
    "Table 7 (Title VII): Total Changes in Direct Spending (FY25 0.783, FY26 -11.710) minus Total Changes in Revenues (FY25 -130.903, FY26 -461.569): [FY2025, FY2026] $B")


def sect(a, b):
    return [T7[s] for s in sorted(T7) if a <= int(s) <= b]


def eff(rows, yr=26):          # deficit effect of a set of Table 7 sections, current-law baseline
    return sum(r["out" + str(yr)] - r["rev" + str(yr)] for r in rows)


def cl(a, b, yr=26):
    return eff(sect(a, b), yr)


def one(sec, yr=26):
    return eff([T7[str(sec)]], yr)


def cpd(k):
    return -J[k][1]               # JCX-34 net effect (FY2026) to deficit effect (sign flip)


prov = []          # rows: dict(label, cl, cp, src, kind)


def add(label, clv, cpv, src, kind="item"):
    prov.append(dict(label=label, cl=clv, cp=cpv, src=src, kind=kind))


# -- Tax provisions: individual (Chapter 1)
ch1_listed = {"70101": "c1_1_rates", "70102": "c1_2_stdded", "70103": "c1_3_persex", "70104": "c1_4_ctc", "70105": "c1_5_qbi",
              "70107": "c1_7_amt", "70110": "c1_10_miscitem", "70111": "c1_11_itemlim", "70120": "c1_20_salt"}
names1 = {"70101": "TCJA individual rate and bracket extension (Sec. 70101)",
          "70102": "Standard deduction increase (Sec. 70102)",
          "70103": "Personal exemption termination, including the temporary senior deduction (Sec. 70103)",
          "70104": "Child tax credit increase (Sec. 70104)",
          "70105": "Qualified business income deduction (Sec. 70105)",
          "70107": "Alternative minimum tax relief (Sec. 70107)",
          "70110": "Termination of miscellaneous itemized deductions (Sec. 70110)",
          "70111": "Limit on tax benefit of itemized deductions (Sec. 70111)",
          "70120": "SALT deduction cap increase (Sec. 70120)"}
for sec, jk in ch1_listed.items():
    add(names1[sec], one(sec), cpd(jk), "[3] Table 7, Sec. " + sec + "; [5] p. " + str(jpage[jk]) + ", " + JCX34[jk][3], "tax")
rem_cl = cl(70101, 70120) - sum(one(s) for s in ch1_listed)
rem_cp = -J["c1_total"][1] - sum(cpd(k) for k in ch1_listed.values())
add("Other Chapter 1 items (estate and gift tax, mortgage interest, casualty losses, ABLE, other)", rem_cl, rem_cp,
    "[3] Table 7, Secs. 70106, 70108, 70109, 70112 to 70119; [5] p. 2, Total of Chapter 1 less listed items", "tax")
# -- Chapter 2
for sec, jk, nm in [("70201", "c2_1_tips", "No tax on tips (Sec. 70201)"), ("70202", "c2_2_ot", "No tax on overtime (Sec. 70202)"),
                    ("70203", "c2_3_car", "Auto loan interest deduction (Sec. 70203)"),
                    ("70204", "c2_4_trump", "Trump accounts and contribution pilot program (Sec. 70204)")]:
    add(nm, one(sec), cpd(jk), "[3] Table 7, Sec. " + sec + "; [5] p. " + str(jpage[jk]) + ", " + JCX34[jk][3], "tax")
# -- Chapter 3 Subchapter A (domestic business)
c3a_listed = [("70301", "c3A_1_bonus", "100% bonus depreciation, full expensing of business property (Sec. 70301)"),
              ("70302", "c3A_2_rnd", "Immediate domestic research and experimental expensing (Sec. 70302)"),
              ("70303", "c3A_3_163j", "Business interest limit, section 163(j) (Sec. 70303)"),
              ("70307", "c3A_7_qpp", "Special depreciation for qualified production property (Sec. 70307)")]
for sec, jk, nm in c3a_listed:
    add(nm, one(sec), cpd(jk), "[3] Table 7, Sec. " + sec + "; [5] p. " + str(jpage[jk]) + ", " + JCX34[jk][3], "tax")
a_keys = ["c3A_1_bonus", "c3A_2_rnd", "c3A_3_163j", "c3A_4_leave", "c3A_5_meals", "c3A_6_179", "c3A_7_qpp", "c3A_8_advmfg", "c3A_9_space"]
a_total_cp = -sum(J[k][1] for k in a_keys)
add("Other domestic business items (section 179 limits, advanced manufacturing credit, leave credit, meals, spaceports)",
    cl(70301, 70309) - sum(one(s) for s, _, _ in c3a_listed), a_total_cp - sum(cpd(k) for _, k, _ in c3a_listed),
    "[3] Table 7, Secs. 70304 to 70306, 70308, 70309; [5] pp. 2-3, Ch.3 Subch.A items 4 to 6, 8, 9", "tax")
add("International tax provisions (Chapter 3 Subchapter B; includes the Part IV interest-limit coordination items)",
    cl(70311, 70354), -J["c3_total"][1] - a_total_cp,
    "[3] Table 7, Secs. 70311 to 70354; [5] p. 3, Total of Chapter 3 less Subchapter A items", "tax")
# -- Chapter 4
add("Qualified small business stock gain exclusion expansion (Sec. 70431)", one("70431"), cpd("c4D_1_qsbs"),
    "[3] Table 7, Sec. 70431; [5] p. 5, Ch.4 Subch.D item 1", "tax")
add("Other Chapter 4 items (families, education, community development, small business, rural)",
    cl(70401, 70439) - one("70431"), -J["c4_total"][1] - cpd("c4D_1_qsbs"),
    "[3] Table 7, Secs. 70401 to 70439 less 70431; [5] p. 5, Total of Chapter 4 less QSBS", "tax")
# -- Chapter 5
add("Termination of qualified commercial clean vehicles credit (Sec. 70503)", one("70503"), cpd("c5A_3_commcv"),
    "[3] Table 7, Sec. 70503; [5] p. 5, Ch.5 Subch.A item 3", "tax")
add("Other energy provisions (Chapter 5)", cl(70501, 70531) - one("70503"), -J["c5_total"][1] - cpd("c5A_3_commcv"),
    "[3] Table 7, Secs. 70501 to 70531 less 70503; [5] p. 6, Total of Chapter 5 less item 3", "tax")
add("Deduction and credit guardrails and other reforms (Chapter 6)", cl(70601, 70607), -J["c6_total"][1],
    "[3] Table 7, Secs. 70601 to 70607; [5] p. 7, Total of Chapter 6", "tax")
add("Health tax provisions (premium tax credit rules, HSA changes; Subtitle B, Chapter 3)", cl(71301, 71308), -J["healthtax_total"][1],
    "[3] Table 7, Secs. 71301 to 71308 (revenue and outlay rows); [5] p. 7, Subtitle B Chapter 3 total", "tax")
# -- Outlay provisions (same under both baselines: CBO scores)
medicaid = cl(71101, 71121)
add("Medicaid (Subtitle B, Chapter 1)", medicaid, medicaid,
    "[3] Table 7, Secs. 71101 to 71121 (sum of section rows; the sheet has no chapter subtotal)", "outlay")
medicare = cl(71201, 71203) + one("71401")
add("Medicare and rural health (Subtitle B, Chapters 2 and 4)", medicare, medicare, "[3] Table 7, Secs. 71201 to 71203 and 71401", "outlay")
add("SNAP and other nutrition (Title I, Subtitle A)", OTH["t1_nutrition"][1], OTH["t1_nutrition"][1], "[3] Table 1, Subtotal, Subtitle A", "outlay")
sl = OTH["t8_loanlimits"][1] + OTH["t8_loanrepay"][1]
add("Student loans: loan limits and loan repayment (Title VIII, Subtitles B and C)", sl, sl, "[3] Table 8, Subtotals for Subtitles B and C", "outlay")
add("Pell Grants (Title VIII, Subtitle D)", OTH["t8_pell"][1], OTH["t8_pell"][1], "[3] Table 8, Subtotal, Subtitle D", "outlay")
add("Other Title VIII (asset exemption, regulatory relief, other, interactions)", OTH["t8_other"][1], OTH["t8_other"][1],
    "[3] Table 8, Subtitles A, E, F, G, H and Total Interactions", "outlay")
add("Defense (Title II)", OTH["t2_defense"][1], OTH["t2_defense"][1], "[3] Table 2, Total Changes in Direct Spending", "outlay")
add("Homeland security (Title IX)", OTH["t9_dhs"][1], OTH["t9_dhs"][1], "[3] Table 9, Total Changes in Direct Spending", "outlay")
add("Immigration and judiciary, net of fee revenue (Title X)", OTH["t10_judiciary"][1], OTH["t10_judiciary"][1],
    "[3] Table 10, outlays less Subtitle A revenues", "outlay")
oth_titles = OTH["t1_other"][1] + OTH["t3_banking"][1] + OTH["t4_commerce"][1] + OTH["t5_energy"][1] + OTH["t6_epw"][1]
add("Other titles (Title I Subtitles B to F; Titles III to VI)", oth_titles, oth_titles,
    "[3] Table 1 less Subtitle A; Summary Table (Titles III, IV); Tables 5, 6", "outlay")

# -- Reconciliation to the paper's totals
CL_TOTAL = sc["deficit"][2026]                       # 486.839
CP_TOTAL = q1["level_current_policy"]["deficit"]     # count-once, 275.652
rows_cl = sum(p["cl"] for p in prov)
rows_cp = sum(p["cp"] for p in prov)
t7_rows_cl = eff(list(T7.values()))
t7_resid = TITLE7_NET[2026] - t7_rows_cl             # Title VII total less the sum of its section rows
inter = OTH["interactions"][1]
add("Unallocated: Title VII total less the sum of its section rows (rounding in the source; current law only)", t7_resid, 0.0,
    "[3] Table 7 totals less section rows", "recon")
add("Interactions among titles", inter, inter, "[3] Summary Table", "recon")
tax_out_cbo = sum(T7[s]["out26"] for s in T7 if 70101 <= int(s) <= 70607 or 71301 <= int(s) <= 71308)
medicaid_rev_in_rows = -sum(T7[s]["rev26"] for s in T7 if 71101 <= int(s) <= 71121)
cp_gap = CP_TOTAL - (rows_cp + inter)
tot_cl = sum(p["cl"] for p in prov)
tot_cp = sum(p["cp"] for p in prov)
add("Total: the act's FY2026 deficit effect", tot_cl, tot_cp, "Section 3.1, Table 2", "total")
prov_by = {
    "rows_cl": rows_cl, "rows_cp": rows_cp, "t7_resid": t7_resid, "t7_rows_cl": t7_rows_cl,
    "cl_total_paper": CL_TOTAL, "cl_total_rows": tot_cl, "cl_gap": CL_TOTAL - tot_cl,
    "cp_total_paper": CP_TOTAL, "cp_total_rows": tot_cp, "cp_gap_before_reconciling_items": cp_gap,
    "cp_gap_tax_outlays_in_both": tax_out_cbo, "cp_gap_medicaid_revenue_in_rows_only": -medicaid_rev_in_rows,
    "cp_gap_check": cp_gap,
}
assert abs(tot_cl - CL_TOTAL) < 0.0015, ("current-law provision rows do not reconcile", tot_cl, CL_TOTAL)
assert abs(tot_cp - CP_TOTAL) < 0.0015, ("current-policy provision rows do not reconcile", tot_cp, CP_TOTAL)
def short_label(lab):
    fixed = {
        "Personal exemption termination, including the temporary senior deduction (Sec. 70103)": "Personal exemption end, incl. senior deduction",
        "Student loans: loan limits and loan repayment (Title VIII, Subtitles B and C)": "Student loans (Title VIII, Subtitles B, C)",
        "International tax provisions (Chapter 3 Subchapter B; includes the Part IV interest-limit coordination items)": "International tax provisions (Ch. 3, Subch. B)",
        "Other domestic business items (section 179 limits, advanced manufacturing credit, leave credit, meals, spaceports)": "Other domestic business items (Ch. 3, Subch. A)",
        "Other Chapter 1 items (estate and gift tax, mortgage interest, casualty losses, ABLE, other)": "Other Chapter 1 items",
        "Other Chapter 4 items (families, education, community development, small business, rural)": "Other Chapter 4 items",
        "Health tax provisions (premium tax credit rules, HSA changes; Subtitle B, Chapter 3)": "Health tax provisions (Subtitle B, Ch. 3)",
        "Other Title VIII (asset exemption, regulatory relief, other, interactions)": "Other Title VIII items",
        "Termination of miscellaneous itemized deductions (Sec. 70110)": "End of misc. itemized deductions",
        "Medicare and rural health (Subtitle B, Chapters 2 and 4)": "Medicare and rural health (Subtitle B)",
        "Other titles (Title I Subtitles B to F; Titles III to VI)": "Other titles (I excl. Subtitle A; III to VI)",
        "Immigration and judiciary, net of fee revenue (Title X)": "Immigration and judiciary, net (Title X)",
        "100% bonus depreciation, full expensing of business property (Sec. 70301)": "100% bonus depreciation (full expensing)",
        "Termination of qualified commercial clean vehicles credit (Sec. 70503)": "Termination of commercial clean vehicles credit",
        "Trump accounts and contribution pilot program (Sec. 70204)": "Trump accounts and pilot program",
        "Special depreciation for qualified production property (Sec. 70307)": "Qualified production property depreciation",
        "Immediate domestic research and experimental expensing (Sec. 70302)": "Immediate domestic R&E expensing",
        "Qualified small business stock gain exclusion expansion (Sec. 70431)": "QSBS gain exclusion expansion",
        "Deduction and credit guardrails and other reforms (Chapter 6)": "Guardrails and other reforms (Chapter 6)",
        "Business interest limit, section 163(j) (Sec. 70303)": "Business interest limit, section 163(j)",
    }
    if lab in fixed:
        return fixed[lab]
    lab = lab.split(" (Sec.")[0] if " (Sec." in lab and lab.endswith(")") else lab
    return lab if len(lab) <= 56 else lab[:54] + "..."

for p_ in prov:
    p_["short"] = short_label(p_["label"]) if p_["kind"] in ("tax", "outlay") else p_["label"]

R["provisions"] = {
    "rows": prov, "reconciliation": prov_by,
    "tax_subtotal_cl": sum(p["cl"] for p in prov if p["kind"] == "tax"), "tax_subtotal_cp": sum(p["cp"] for p in prov if p["kind"] == "tax"),
    "outlay_subtotal_cl": sum(p["cl"] for p in prov if p["kind"] == "outlay"), "outlay_subtotal_cp": sum(p["cp"] for p in prov if p["kind"] == "outlay"),
    "jcx35_net_total_fy26": -464.627, "cbo_title7_revenue_fy26": -461.569,
    "jct_outlay_effects_implied_by_jcx35_less_cbo_revenue": 464.627 - 461.569,
}
# Student-loan tie-out to the headline change: scored FY2025 and FY2026 (Title VIII Subtitles B and C) and CBO's recorded Sept-2025 entry
sl25 = OTH["t8_loanlimits"][0] + OTH["t8_loanrepay"][0]
R["student_loans"] = {
    "fy2025_scored": sl25, "fy2026_scored": sl, "change": sl - sl25,
    "recorded_one_time_entry_sept2025": STUDENT_LOAN_ONE_TIME,
    "headline_change": q1["yoy_current_policy"]["deficit"],
    "scored_change_share_of_headline": (sl - sl25) / q1["yoy_current_policy"]["deficit"],
    "recorded_entry_share_of_headline": -STUDENT_LOAN_ONE_TIME / q1["yoy_current_policy"]["deficit"],
    "memo_excluding_recorded_entry": q1["yoy_current_policy"]["deficit"] + STUDENT_LOAN_ONE_TIME,
    "memo_excluding_recorded_entry_pct_of_increase": (q1["yoy_current_policy"]["deficit"] + STUDENT_LOAN_ONE_TIME) / dd,
}

R["inputs_check"] = {
    "mts_function_sum_matches_outlays": sum(a for a, b in FUNC.values()) - out26,
    "mts_function_sum_fy25_matches": sum(b for a, b in FUNC.values()) - out25,
    "revenue_lines_sum_matches": (ind26 + pay26 + corp26 + exc26 + est26 + cust26 + misc26) - rev26,
    "revenue_lines_sum_fy25": (ind25 + pay25 + corp25 + exc25 + est25 + cust25 + misc25) - rev25,
}

with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump({"inputs": I, "results": R}, f, indent=1, default=str)
with open(os.path.join(OUT, "inputs_sourced.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["input", "value", "source_key", "source", "note"])
    for k, v in I.items():
        w.writerow([k, json.dumps(v["value"]), v["source"], SRC.get(v["source"], v["source"]), v["note"]])

# --------------------------------------------------------------------------
# CHARTS (every bar chart's y-axis starts at zero)
# --------------------------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    WATERMARK = "amandoti.win"
    CHART_SOURCES = {
        "waterfall_fy25_to_fy26": "Sources: Treasury Monthly Treasury Statement Sept 2026 (Tables 3, 9); CBO Monthly Budget Review Sept 2026; "
                                  "CBO/JCT score of P.L. 119-21 (61570); JCT JCX-34-25.",
        "corporate_counterfactuals": "Sources: Treasury MTS Sept 2026 (Tables 3, 4); CBO Budget and Economic Outlook Feb 2026 (Table 1-1, ch.5 legislative changes); "
                                     "CBO Jan 2025 baseline (Table B-1); BEA NIPA Table 1.12 via FRED; CBO/JCT score (61570).",
        "provisions_fy2026": "Sources: CBO/JCT score of P.L. 119-21 (publication 61570), Tables 1 to 10 and Summary Table; sections listed in the paper's Table 10. "
                             "Rows with absolute value under $0.05B omitted.",
        "deficit_without_obbba": "Sources: Treasury MTS Sept 2026; CBO/JCT score of P.L. 119-21 (61570); JCT JCX-34-25; "
                                 "CBO letter to Sen. Merkley (61466); BEA via FRED (GDP).",
    }

    def save_chart(fig, name):
        """Reserve a footer strip, add the source line and the watermark, save PNG."""
        fig.tight_layout(rect=[0, 0.07, 1, 1])
        fig.text(0.01, 0.045, CHART_SOURCES[name], fontsize=7.5, color="#555555", ha="left", va="center", wrap=True)
        fig.text(0.99, 0.012, WATERMARK, fontsize=11, color="#333333", ha="right", va="bottom", alpha=0.65, fontweight="bold")
        fig.savefig(os.path.join(OUT, "charts", name + ".png"), dpi=150)
        plt.close(fig)

    RED, GRN, BLU, GRY, HATCH = "#b23a3a", "#2f7d5b", "#2b5d8a", "#7a7a7a", "//"

    # Waterfall, OBBBA only. Plug bars are hatched and labelled as residuals.
    steps = [
        ("FY2025\ndeficit", d25, "total", None),
        ("OBBBA:\noutlays", obbba_out, "delta", "obbba"),
        ("OBBBA:\nrevenue loss\n(incl. corporate,\ncounted once)", obbba_rev, "delta", "obbba"),
        ("Net interest\n(residual;\nincl. $14B OBBBA\ndebt service)", ni_chg, "delta", "resid"),
        ("Other outlays\n(residual plug)", other_out, "delta", "resid"),
        ("Other revenue\nincl. customs\n(residual plug)", other_rev, "delta", "resid"),
        ("FY2026\ndeficit", d26, "total", None),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.4))
    run = 0.0
    for i, (lab, v, kind, grp) in enumerate(steps):
        if kind == "total":
            ax.bar(i, v, color=BLU)
            ax.text(i, v + 30, f"{v:,.0f}", ha="center", fontsize=9, fontweight="bold")
            run = v
        else:
            bottom = run if v >= 0 else run + v
            colour = RED if v >= 0 else GRN
            ax.bar(i, abs(v), bottom=bottom, color=colour, hatch=HATCH if grp == "resid" else None,
                   edgecolor="white" if grp == "resid" else colour, linewidth=0)
            ax.text(i, max(run, run + v) + 30, f"{v:+,.0f}", ha="center", fontsize=9)
            ax.plot([i - 0.4, i + 1.4], [run + v, run + v], color=GRY, lw=0.6)
            run += v
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], fontsize=8.5)
    ax.set_ylabel("$ billions")
    ax.set_ylim(0, 2500)
    ax.set_title(f"Bridge: FY2025 to FY2026 deficit (+${dd:,.0f}B, Treasury MTS). Red raises the deficit, green lowers it. Hatched bars are residuals.\n"
                 f"OBBBA bars = change in CBO/JCT scored effect vs a current-policy baseline (+${obbba_tot:,.0f}B,\n"
                 f"including the one-time \\$131B Sept-2025 student-loan entry). Residuals sum to {resid:+,.1f}B.", fontsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    save_chart(fig, "waterfall_fy25_to_fy26")

    # Corporate counterfactuals (v1 content, y-axis from zero)
    order = ["A: add back full 16% loss",
             "B " + list(growth)[0],
             [k for k in cfs if k.startswith("C1")][0], [k for k in cfs if k.startswith("C2")][0],
             [k for k in cfs if k.startswith("C3")][0], [k for k in cfs if k.startswith("C4")][0]]
    labels = ["A\nfull loss\nadded back", "B\nprofits +%.1f%%\n(CY25 vs CY24,\ntax-year match)" % (100 * list(growth.values())[0]),
              "C1\nscore delta x\nCBO-implied\ncorp. share", "C2\nCBO Feb-2026\nbaseline-\nimplied", "C3\nCBO Jan-2025\npre-OBBBA path", "C4\nCBO OBBBA\nFY26 corp.\neffect (level)"]
    vals = [q3["cf"][k]["receipts"] for k in order]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(-1, corp26, color=BLU)
    ax.text(-1, corp26 + 8, f"{corp26:,.0f}", ha="center", fontsize=9, fontweight="bold")
    ax.axhline(corp25, color=GRY, ls="--", lw=1, label=f"FY2025 actual {corp25:,.0f}")
    ax.axhline(b_corp, color=GRN, ls=":", lw=1, label=f"CBO Feb-2026 baseline for FY2026 {b_corp:,.0f}")
    ax.legend(loc="upper left", fontsize=8.5, frameon=False)
    for i, v in enumerate(vals):
        ax.bar(i, v, color="#c98a3b" if order[i].startswith("B") else "#8a6bb0" if order[i].startswith("C") else RED)
        ax.text(i, v + 8, f"{v:,.0f}\n(deficit {-(v - corp26):+,.0f})", ha="center", fontsize=8)
    ax.set_xticks(range(-1, len(vals)))
    ax.set_xticklabels(["FY2026\nactual"] + labels, fontsize=8.5)
    ax.set_ylim(0, 640)
    ax.set_ylabel("Corporate income tax receipts, $ billions")
    ax.set_title("Corporate tax counterfactuals for FY2026 (implied receipts; deficit change in brackets)\n"
                 "A = add back decline; B = FY2025 grown by tax-year-matched BEA profits; C = OBBBA-attributed portion (CBO-based proxies)", fontsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    save_chart(fig, "corporate_counterfactuals")

    # Deficit without OBBBA
    vals5 = [d25, d26] + [c["deficit"] for c in q5["cases"].values()]
    pcts = [None, q5["actual_pct"]] + [c["pct_gdp"] for c in q5["cases"].values()]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(range(len(vals5)), vals5, color=[GRY, BLU, "#c98a3b", "#8a6bb0", "#2f7d5b"])
    ax.axhline(d25, color=GRY, ls="--", lw=1)
    for i, (v, p_) in enumerate(zip(vals5, pcts)):
        ax.text(i, v + 20, f"${v:,.0f}B" + ("" if p_ is None else f"\n{p_*100:.1f}% of GDP"), ha="center", fontsize=9, bbox=dict(fc="white", ec="none", pad=1), zorder=5)
    base_v = list(q5["cases"].values())[1]["deficit"]
    ax.annotate("", xy=(3.35, base_v + 15), xytext=(3.35, d25), arrowprops=dict(arrowstyle="<->", color="#222", lw=1))
    ax.text(3.0, d25 + 130, f"Base case is ${d25 - base_v:,.0f}B below FY2025", fontsize=9, ha="center", fontweight="bold")
    ax.set_xticks(range(len(vals5)))
    ax.set_xticklabels(["Actual\nFY2025", "Actual\nFY2026", "No OBBBA:\nlow removal", "No OBBBA:\nbase", "No OBBBA:\nhigh removal"], fontsize=9)
    ax.set_ylim(0, 2300)
    ax.set_ylabel("$ billions")
    ax.set_title("FY2026 deficit with OBBBA's FY2026 effect removed (static: tariffs, refunds and the economy held at actuals)", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    save_chart(fig, "deficit_without_obbba")

    # Provision-level bar chart, FY2026, current-law baseline (Section 6.1)
    rows = sorted([p for p in prov if p["kind"] in ("tax", "outlay") and abs(p["cl"]) >= 0.05], key=lambda p: p["cl"])
    short = short_label
    fig, ax = plt.subplots(figsize=(11.5, 0.34 * len(rows) + 2.4))
    ys = list(range(len(rows)))
    ax.barh(ys, [p["cl"] for p in rows], color=[RED if p["cl"] >= 0 else GRN for p in rows], height=0.72)
    ax.axvline(0, color="#222", lw=0.8)
    for y, p in zip(ys, rows):
        v = p["cl"]
        ax.text(v + (3 if v >= 0 else -3), y, f"{v:+,.1f}", va="center", ha="left" if v >= 0 else "right", fontsize=7.5)
    ax.set_yticks(ys)
    ax.set_yticklabels([short(p["label"]) for p in rows], fontsize=7.5)
    lo = min(p["cl"] for p in rows); hi = max(p["cl"] for p in rows)
    ax.set_xlim(lo - 25, hi + 28)
    ax.set_xlabel("FY2026 deficit effect, $ billions (positive raises the deficit); bars start at zero")
    ax.set_title("FY2026 deficit effect of the act by provision, current-law baseline\n(CBO/JCT score; rows plus a \\$0.1B unallocated row sum to \\$" + f"{CL_TOTAL:,.1f}" + "B)", fontsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    save_chart(fig, "provisions_fy2026")
except ImportError:
    print("matplotlib missing: charts skipped")

if __name__ == "__main__":
    print(json.dumps({k: R[k] for k in ("deficit_change_treasury", "deficit_pct_gdp", "gdp_fy26_est")}, indent=1))
    print(json.dumps(R["q1"], indent=1))
    print(json.dumps({k: v for k, v in R["q4"].items() if not isinstance(v, dict)}, indent=1))
    print(json.dumps(R["q5"], indent=1))
    print(json.dumps(R["inputs_check"], indent=1))
    for k, v in R["q3"]["cf"].items():
        print(f"{k:55s} receipts {v['receipts']:8.1f}  diff {v['revenue_diff']:7.1f}  deficit_cf {v['deficit_cf']:8.1f}")
    print(json.dumps(R["provisions"]["reconciliation"], indent=1))
    print("PROVISION TOTALS: current law %.3f (paper %.3f); current policy %.3f (paper %.3f)" % (sum(p["cl"] for p in R["provisions"]["rows"] if p["kind"] != "total"), CL_TOTAL, sum(p["cp"] for p in R["provisions"]["rows"] if p["kind"] != "total"), CP_TOTAL))
    assert abs(R["q4"]["bridge_check"]) < 0.01, "bridge does not sum to the FY2026 deficit"
    assert abs(R["q4"]["residual_check"]) < 0.01
    print("BRIDGE OK: FY2025 + components = %.3f ; FY2026 deficit = %.3f ; increase = %.3f" % (
        R["q4"]["bridge_sum"], d26, dd))
