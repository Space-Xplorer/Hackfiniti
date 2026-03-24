"""
Transparency Agent with Groq integration.

This module implements explanation generation using Groq LLM and
deterministic fallbacks based on feature contributions.
Includes async support for improved performance.
"""

import asyncio
from typing import Dict, Any, List, Tuple
import logging

from langchain_groq import ChatGroq

from src.schemas.state import ApplicationState

logger = logging.getLogger(__name__)


class TransparencyAgent:
	"""
	Generates user-friendly explanations for loan and insurance decisions.
	"""

	# Advisor = Friendly LLM explanation
	LOAN_ADVISOR_PROMPT = (
		"You are Daksha, a friendly AI financial advisor. Provide helpful, actionable guidance.\n\n"
		"Decision: {decision}\n"
		"Approval Probability: {probability}\n"
		"Top Contributing Factor: {insight}\n\n"
		"Write 3-5 conversational sentences that:\n"
		"- If probability < 70%: Give 2-3 specific improvement tips (e.g., 'Boost your credit score to 750+', 'Lower debt-to-income below 40%')\n"
		"- If probability >= 70%: Congratulate and explain what made the application strong\n"
		"Be warm, empathetic, and actionable. Avoid jargon."
	)

	# Description = Simple factual model output (deterministic)
	# This is generated deterministically, not via LLM

	# Advisor = Friendly LLM explanation
	INSURANCE_ADVISOR_PROMPT = (
		"You are Daksha, a friendly AI health advisor. Provide helpful, actionable guidance.\n\n"
		"Premium: Rs {premium}\n"
		"Top Contributing Factor: {insight}\n\n"
		"Write 3-5 conversational sentences that:\n"
		"- Start with a friendly tone like 'Great news!' or 'Your premium has been calculated'\n"
		"- Explain the key factor affecting the premium in simple terms\n"
		"- Give 1-2 actionable tips to reduce future premiums (e.g., 'Regular checkups', 'Exercise 3x/week', 'Quit smoking')\n"
		"Be warm, empathetic, and encouraging. Avoid medical jargon."
	)

	# Description = Simple factual model output (deterministic)
	# This is generated deterministically, not via LLM

	def __init__(self) -> None:
		# Use lighter model for faster processing and higher rate limits
		self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

	def explain_loan_decision(self, state: ApplicationState) -> ApplicationState:
		"""Generate explanation and description for loan decision."""
		prediction = state.get("loan_prediction") or {}
		model_output = (state.get("model_output") or {}).get("loan", {})
		reasoning = model_output.get("feature_contributions") or prediction.get("reasoning") or {}

		approved = bool(prediction.get("approved"))
		probability = float(prediction.get("probability", 0.0))
		decision_text = "APPROVED" if approved else "REJECTED"
		
		top_factors = self._format_top_factors(reasoning, top_k=3)
		top_factor_names = self._top_contributors(reasoning, top_k=1)
		insight = top_factor_names[0][0] if top_factor_names else "overall financial profile"

		# DESCRIPTION = Simple factual model output (deterministic)
		description = self._generate_loan_description(decision_text, probability, top_factors)
		state["loan_description"] = description

		# EXPLANATION = Friendly LLM advisory (for Daksha Advisor)
		advisor_prompt = self.LOAN_ADVISOR_PROMPT.format(
			decision=decision_text,
			probability=f"{probability:.1%}",
			insight=insight
		)
		explanation = self._run_llm_or_fallback(
			advisor_prompt,
			fallback=self._fallback_loan_advisor(approved, probability, insight)
		)
		validated = self._sanitize_advisor_text(self._validate_explanation(explanation))
		state["loan_explanation"] = validated
		
		return state
	
	def _generate_loan_description(self, decision: str, probability: float, factors: str) -> str:
		"""Generate deterministic factual description of model decision."""
		return (
			"--- OFFICIAL MODEL AUDIT ---\n"
			f"DECISION: {decision}\n"
			f"CONFIDENCE: {probability:.2%}\n\n"
			f"RAW FEATURE CONTRIBUTIONS:\n{factors}\n"
			"----------------------------"
		)

	def _sanitize_advisor_text(self, text: str) -> str:
		"""Remove question-style sentences and keep the tone declarative."""
		if not text:
			return text
		sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
		filtered = []
		for sentence in sentences:
			lowered = sentence.lower()
			if sentence.endswith("?"):
				continue
			if "i'd like to know" in lowered or "i would like to know" in lowered:
				continue
			if "could you" in lowered or "please share" in lowered:
				continue
			filtered.append(sentence)
		if not filtered:
			return text
		return ". ".join(filtered).strip() + "."

	def explain_insurance_premium(self, state: ApplicationState) -> ApplicationState:
		"""Generate explanation and description for insurance premium."""
		prediction = state.get("insurance_prediction") or {}
		model_output = (state.get("model_output") or {}).get("insurance", {})
		reasoning = model_output.get("feature_contributions") or prediction.get("reasoning") or {}

		premium = float(prediction.get("premium", 0.0))
		
		top_factors = self._format_top_factors(reasoning, top_k=3)
		top_factor_names = self._top_contributors(reasoning, top_k=1)
		insight = top_factor_names[0][0] if top_factor_names else "overall health profile"

		# DESCRIPTION = Simple factual model output (deterministic)
		description = self._generate_insurance_description(premium, top_factors)
		state["insurance_description"] = description

		# EXPLANATION = Friendly LLM advisory (for Daksha Advisor)
		advisor_prompt = self.INSURANCE_ADVISOR_PROMPT.format(
			premium=f"{premium:,.0f}",
			insight=insight
		)
		explanation = self._run_llm_or_fallback(
			advisor_prompt,
			fallback=self._fallback_insurance_advisor(premium, insight)
		)
		validated = self._sanitize_advisor_text(self._validate_explanation(explanation))
		state["insurance_explanation"] = validated
		
		return state
	
	def _generate_insurance_description(self, premium: float, factors: str) -> str:
		"""Generate deterministic factual description of premium calculation."""
		return (
			f"Estimated Premium: Rs {premium:,.0f}\\n\\n"
			f"Top Contributing Factors:\\n{factors}"
		)

	def _run_llm_or_fallback(self, prompt: str, fallback: str) -> str:
		"""Invoke LLM, fallback to deterministic explanation on failure."""
		try:
			response = self.llm.invoke(prompt)
			content = getattr(response, "content", "") if response is not None else ""
			return content.strip() or fallback
		except Exception as exc:
			logger.warning(f"Transparency LLM failed, using fallback: {exc}")
			return fallback
	
	async def _run_llm_or_fallback_async(self, prompt: str, fallback: str) -> str:
		"""Async version: Invoke LLM, fallback to deterministic explanation on failure."""
		try:
			response = await self.llm.ainvoke(prompt)
			content = getattr(response, "content", "") if response is not None else ""
			return content.strip() or fallback
		except Exception as exc:
			logger.warning(f"Transparency LLM failed (async), using fallback: {exc}")
			return fallback
	
	async def explain_loan_decision_async(self, state: ApplicationState) -> ApplicationState:
		"""Async version: Generate explanation and description for loan decision."""
		prediction = state.get("loan_prediction") or {}
		model_output = (state.get("model_output") or {}).get("loan", {})
		reasoning = model_output.get("feature_contributions") or prediction.get("reasoning") or {}

		approved = bool(prediction.get("approved"))
		probability = float(prediction.get("probability", 0.0))
		decision_text = "APPROVED" if approved else "REJECTED"
		
		top_factors = self._format_top_factors(reasoning, top_k=3)
		top_factor_names = self._top_contributors(reasoning, top_k=1)
		insight = top_factor_names[0][0] if top_factor_names else "overall financial profile"

		# DESCRIPTION = Simple factual model output (deterministic)
		description = self._generate_loan_description(decision_text, probability, top_factors)
		state["loan_description"] = description

		# EXPLANATION = Friendly LLM advisory (for Daksha Advisor)
		advisor_prompt = self.LOAN_ADVISOR_PROMPT.format(
			decision=decision_text,
			probability=f"{probability:.1%}",
			insight=insight
		)
		explanation = await self._run_llm_or_fallback_async(
			advisor_prompt,
			fallback=self._fallback_loan_advisor(approved, probability, insight)
		)
		validated = self._sanitize_advisor_text(self._validate_explanation(explanation))
		state["loan_explanation"] = validated
		
		return state
	
	async def explain_insurance_premium_async(self, state: ApplicationState) -> ApplicationState:
		"""Async version: Generate explanation and description for insurance premium."""
		prediction = state.get("insurance_prediction") or {}
		model_output = (state.get("model_output") or {}).get("insurance", {})
		reasoning = model_output.get("feature_contributions") or prediction.get("reasoning") or {}

		premium = float(prediction.get("premium", 0.0))
		
		top_factors = self._format_top_factors(reasoning, top_k=3)
		top_factor_names = self._top_contributors(reasoning, top_k=1)
		insight = top_factor_names[0][0] if top_factor_names else "overall health profile"

		# DESCRIPTION = Simple factual model output (deterministic)
		description = self._generate_insurance_description(premium, top_factors)
		state["insurance_description"] = description

		# EXPLANATION = Friendly LLM advisory (for Daksha Advisor)
		advisor_prompt = self.INSURANCE_ADVISOR_PROMPT.format(
			premium=f"{premium:,.0f}",
			insight=insight
		)
		explanation = await self._run_llm_or_fallback_async(
			advisor_prompt,
			fallback=self._fallback_insurance_advisor(premium, insight)
		)
		validated = self._sanitize_advisor_text(self._validate_explanation(explanation))
		state["insurance_explanation"] = validated
		
		return state

	def _format_top_factors(self, reasoning: Dict[str, float], top_k: int = 5) -> str:
		"""Directly converts EBM scores into a readable factual list."""
		items = [(name, float(score)) for name, score in reasoning.items()]
		items.sort(key=lambda x: abs(x[1]), reverse=True)
		top_items = items[:top_k]

		if not top_items:
			return "- No significant factors identified."

		lines = []
		for name, score in top_items:
			direction = "Positive" if score > 0 else "Negative"
			label = name.replace("_", " ").title()
			lines.append(f"• {label}: {score:+.4f} ({direction} Impact)")
		return "\n".join(lines)

	def _top_contributors(self, reasoning: Dict[str, float], top_k: int = 5) -> List[Tuple[str, float]]:
		"""Return top contributors by absolute value."""
		items = [(name, float(score)) for name, score in reasoning.items()]
		items.sort(key=lambda x: abs(x[1]), reverse=True)
		return items[:top_k]

	def _fallback_loan_advisor(self, approved: bool, probability: float, insight: str) -> str:
		"""Friendly fallback for loan advisory when LLM fails."""
		if approved and probability >= 0.7:
			return (
				f"Congratulations! Your application looks strong with {probability:.0%} approval probability. "
				f"The main positive factor is your {insight}. Keep up the good financial habits!"
			)
		elif probability < 0.5:
			return (
				f"Your application needs improvement for better chances. The key area to focus on is {insight}. "
				f"Consider building this up over the next few months and reapplying."
			)
		else:
			return (
				f"Your application is borderline with {probability:.0%} approval probability. "
				f"Strengthening your {insight} could tip the decision in your favor."
			)

	def _fallback_insurance_advisor(self, premium: float, insight: str) -> str:
		"""Friendly fallback for insurance advisory when LLM fails."""
		return (
			f"Your premium is Rs {premium:,.0f}. The main factor influencing this is your {insight}. "
			f"To potentially reduce future premiums, consider regular health checkups and maintaining a healthy lifestyle."
		)

	def _validate_explanation(self, text: str) -> str:
		"""Ensure explanations are non-empty and a reasonable length."""
		cleaned = (text or "").strip()
		if len(cleaned) < 20:
			return cleaned if cleaned else "We could not generate a detailed explanation at this time."
		if len(cleaned) > 800:
			return cleaned[:797].rstrip() + "..."
		return cleaned


def generate_transparency(state: ApplicationState) -> ApplicationState:
	"""
	Convenience function for workflow integration.
	"""
	agent = TransparencyAgent()
	request_type = state.get("request_type", "both")

	if request_type in ["loan", "both"] and state.get("loan_prediction"):
		state = agent.explain_loan_decision(state)

	if request_type in ["insurance", "both"] and state.get("insurance_prediction"):
		state = agent.explain_insurance_premium(state)

	return state


async def generate_transparency_async(state: ApplicationState) -> ApplicationState:
	"""
	Async convenience function for workflow integration with parallel LLM calls.
	"""
	agent = TransparencyAgent()
	request_type = state.get("request_type", "both")

	tasks = []
	
	if request_type in ["loan", "both"] and state.get("loan_prediction"):
		tasks.append(agent.explain_loan_decision_async(state.copy()))
	
	if request_type in ["insurance", "both"] and state.get("insurance_prediction"):
		tasks.append(agent.explain_insurance_premium_async(state.copy()))
	
	if tasks:
		# Run explanations in parallel
		results = await asyncio.gather(*tasks)
		# Merge results back into state
		for result in results:
			if "loan_explanation" in result:
				state["loan_explanation"] = result["loan_explanation"]
			if "insurance_explanation" in result:
				state["insurance_explanation"] = result["insurance_explanation"]
	
	return state
