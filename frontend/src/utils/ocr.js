/**
 * Browser-side OCR using Puter.js (puter.ai.img2txt)
 * User-Pays model — no API keys, no backend calls for OCR.
 */

const PROMPTS = {
  bank_statement: `You are a financial document parser. Extract the following from this bank statement image and return ONLY valid JSON, no markdown:
{
  "account_name": "string or null",
  "current_balance": number or null,
  "avg_monthly_balance": number or null,
  "recurring_salary_deposits": number or null,
  "statement_date": "YYYY-MM-DD or null",
  "bank_name": "string or null"
}`,

  salary_slip: `You are a payroll document parser. Extract the following from this salary slip image and return ONLY valid JSON, no markdown:
{
  "employee_name": "string or null",
  "employer_name": "string or null",
  "net_income": number or null,
  "slip_date": "YYYY-MM-DD or null"
}`,

  loan_statement: `You are a loan document parser. Extract the following from this loan statement image and return ONLY valid JSON, no markdown:
{
  "current_emi": number or null,
  "outstanding_balance": number or null,
  "lender_name": "string or null"
}`,

  property_document: `You are a property document parser. Extract the following from this property document image and return ONLY valid JSON, no markdown:
{
  "property_value": number or null,
  "owner_name": "string or null",
  "property_address": "string or null"
}`,

  aadhaar_card: `You are an ID document parser. Extract the following from this ID proof image and return ONLY valid JSON, no markdown:
{
  "full_name": "string or null",
  "dob": "YYYY-MM-DD or null",
  "id_number": "string or null"
}`,

  diagnostic_report: `You are a medical document parser. Extract the following from this medical report image and return ONLY valid JSON, no markdown:
{
  "patient_name": "string or null",
  "report_date": "YYYY-MM-DD or null",
  "diagnosis": "string or null"
}`,

  itr: `You are a tax document parser. Extract the following from this ITR document image and return ONLY valid JSON, no markdown:
{
  "taxpayer_name": "string or null",
  "annual_income": number or null,
  "assessment_year": "string or null"
}`,
}

function parseJsonFromText(text) {
  if (!text) return null
  // Strip markdown code fences if present
  const cleaned = text.replace(/```json\s*/gi, '').replace(/```\s*/g, '').trim()
  try {
    return JSON.parse(cleaned)
  } catch {
    // Try to extract first JSON object
    const match = cleaned.match(/\{[\s\S]*\}/)
    if (match) {
      try { return JSON.parse(match[0]) } catch { return null }
    }
    return null
  }
}

/**
 * Run OCR on a single File object for a given document type.
 * Returns { docType, extracted, rawText, error }
 */
export async function ocrDocument(file, docType) {
  const prompt = PROMPTS[docType] || PROMPTS.aadhaar_card
  try {
    // puter.ai.img2txt accepts a File/Blob or URL
    const rawText = await window.puter.ai.img2txt(file)
    // Now use puter.ai.chat to parse structured fields from the raw text
    const parsePrompt = `${prompt}\n\nDocument text:\n${rawText}`
    const chatResponse = await window.puter.ai.chat(parsePrompt)
    const responseText = typeof chatResponse === 'string' ? chatResponse : chatResponse?.message?.content || ''
    const extracted = parseJsonFromText(responseText)
    return { docType, extracted, rawText, error: null }
  } catch (err) {
    return { docType, extracted: null, rawText: null, error: err.message || 'OCR failed' }
  }
}

/**
 * Cross-document consistency checks.
 * Returns { extracted_data, document_freshness_passed, consistency_flags, confidence_score }
 */
export function validateOcrResults(ocrResults) {
  const byType = {}
  for (const r of ocrResults) {
    if (r.extracted) byType[r.docType] = r.extracted
  }

  const flags = []
  let freshnessOk = true
  const now = new Date()

  // --- Name consistency ---
  const salaryName = byType.salary_slip?.employee_name?.trim().toLowerCase()
  const bankName = byType.bank_statement?.account_name?.trim().toLowerCase()
  const idName = byType.aadhaar_card?.full_name?.trim().toLowerCase()

  if (salaryName && bankName && salaryName !== bankName) {
    flags.push(`Name mismatch: Salary slip ("${byType.salary_slip.employee_name}") ≠ Bank account ("${byType.bank_statement.account_name}")`)
  }
  if (salaryName && idName && salaryName !== idName) {
    flags.push(`Name mismatch: Salary slip ("${byType.salary_slip.employee_name}") ≠ ID proof ("${byType.aadhaar_card.full_name}")`)
  }
  if (bankName && idName && bankName !== idName) {
    flags.push(`Name mismatch: Bank account ("${byType.bank_statement.account_name}") ≠ ID proof ("${byType.aadhaar_card.full_name}")`)
  }

  // --- Income consistency ---
  const netIncome = byType.salary_slip?.net_income
  const salaryDeposits = byType.bank_statement?.recurring_salary_deposits
  if (netIncome && salaryDeposits) {
    const diff = Math.abs(netIncome - salaryDeposits) / netIncome
    if (diff > 0.2) {
      flags.push(`Income mismatch: Salary slip net income (₹${netIncome}) differs from bank deposits (₹${salaryDeposits}) by more than 20%`)
    }
  }

  // --- Document freshness ---
  const slipDate = byType.salary_slip?.slip_date
  if (slipDate) {
    const d = new Date(slipDate)
    const monthsOld = (now - d) / (1000 * 60 * 60 * 24 * 30)
    if (monthsOld > 3) {
      flags.push(`Salary slip is older than 3 months (dated ${slipDate})`)
      freshnessOk = false
    }
  }

  const stmtDate = byType.bank_statement?.statement_date
  if (stmtDate) {
    const d = new Date(stmtDate)
    const monthsOld = (now - d) / (1000 * 60 * 60 * 24 * 30)
    if (monthsOld > 6) {
      flags.push(`Bank statement is older than 6 months (dated ${stmtDate})`)
      freshnessOk = false
    }
  }

  // --- Build extracted_data ---
  const monthly_income = byType.salary_slip?.net_income
    || (byType.itr?.annual_income ? byType.itr.annual_income / 12 : null)
    || byType.bank_statement?.recurring_salary_deposits
    || null

  const existing_emi = byType.loan_statement?.current_emi || null
  const property_value = byType.property_document?.property_value || null
  const employer_name = byType.salary_slip?.employer_name || null

  // Confidence: starts at 1.0, deduct for flags and missing fields
  let confidence = 1.0
  confidence -= flags.length * 0.15
  if (!monthly_income) confidence -= 0.1
  if (!byType.aadhaar_card) confidence -= 0.1
  confidence = Math.max(0.1, Math.round(confidence * 100) / 100)

  return {
    extracted_data: { monthly_income, existing_emi, property_value, employer_name },
    document_freshness_passed: freshnessOk,
    consistency_flags: flags,
    confidence_score: confidence,
    raw_by_type: byType,
  }
}
