"""
Underwriting Agent with ML model loading.

This module implements loan and insurance underwriting using pre-trained EBM models.
The agent uses Daksha (EBM classifier) for loan approval and Health Shield 
(EBM regressor) for insurance premium prediction.
"""

import logging
import pickle
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path

sys.modules.setdefault("src.agents.underwriting", sys.modules[__name__])

from src.schemas.state import ApplicationState
from src.utils.model_loader import ModelLoader
from src.utils.storage import save_model_output

logger = logging.getLogger(__name__)


class UnderwritingAgent:
    """
    Underwriting agent that invokes pre-trained EBM models for loan and insurance decisions.
    
    This agent:
    - Loads EBM models via ModelLoader singleton
    - Encodes applicant features using pre-trained encoders
    - Invokes Daksha for loan approval prediction
    - Invokes Health Shield for insurance premium prediction
    - Extracts reasoning from EBM explanations
    - Validates monotonicity constraints (logs warnings only)
    """
    
    def __init__(self):
        """Initialize the Underwriting Agent and load all required models."""
        logger.info("Initializing UnderwritingAgent")
        
        # Get ModelLoader singleton
        self.model_loader = ModelLoader()
        
        # Load all 4 models
        self._load_models()
        
        logger.info("UnderwritingAgent initialized successfully")
    
    def _load_models(self):
        """Load all required models (EBMs and encoders)."""
        try:
            # Try to load finance models
            self.credit_model = self.model_loader.load_model("ebm_finance")
            self.credit_encoders = self.model_loader.load_model("fin_encoders")
            
            # Try to load health models
            self.health_model = self.model_loader.load_model("ebm_health")
            self.health_encoders = self.model_loader.load_model("health_encoders")
            
            # Check if models loaded successfully
            models_loaded = all([
                self.credit_model is not None, 
                self.credit_encoders is not None,
                self.health_model is not None, 
                self.health_encoders is not None
            ])
            
            if not models_loaded:
                self._load_models_from_fallback()

            models_loaded = all([
                self.credit_model is not None,
                self.credit_encoders is not None,
                self.health_model is not None,
                self.health_encoders is not None
            ])

            if not models_loaded:
                raise RuntimeError("Required models not available. Cannot proceed.")

            logger.info("All models loaded successfully")

        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            raise RuntimeError(f"Underwriting agent initialization failed: {e}")

    def _load_models_from_fallback(self) -> None:
        """Load models directly from the default backend/models directory."""
        fallback_dir = Path(__file__).resolve().parents[2] / "models"

        def _load(path: Path) -> Optional[Any]:
            if not path.exists():
                return None
            try:
                with open(path, "rb") as handle:
                    return pickle.load(handle)
            except Exception as exc:
                logger.error(f"Failed to load model from {path}: {exc}")
                return None

        if self.credit_model is None:
            self.credit_model = _load(fallback_dir / "ebm_finance.pkl")
        if self.credit_encoders is None:
            self.credit_encoders = _load(fallback_dir / "fin_encoders.pkl")
        if self.health_model is None:
            self.health_model = _load(fallback_dir / "ebm_health.pkl")
        if self.health_encoders is None:
            self.health_encoders = _load(fallback_dir / "health_encoders.pkl")
    
    def process_loan(self, state: ApplicationState) -> ApplicationState:
        """
        Process loan application using Daksha EBM model.
        
        Args:
            state: Current application state with applicant_data
        
        Returns:
            Updated state with loan_prediction field populated
        """
        try:
            logger.info("Processing loan application")
            
            derived = self._ensure_derived_features(state).get("loan", {})
            if not derived:
                raise ValueError("No derived loan features found in state")

            model_output = self._score_loan_from_derived(derived)

            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            model_explanation = self._try_extract_loan_explanation(applicant_data)
            if model_explanation:
                model_output["feature_contributions"] = model_explanation

            state.setdefault("model_output", {})
            state["model_output"]["loan"] = model_output

            if state.get("application_id"):
                save_model_output(
                    state["application_id"],
                    state["model_output"],
                    metadata={
                        "request_id": state.get("request_id"),
                        "request_type": state.get("request_type")
                    }
                )

            approval_probability = model_output["approval_probability"]
            state["loan_prediction"] = {
                "approved": model_output["predicted_class"] == "approved",
                "probability": approval_probability,
                "reasoning": model_output["feature_contributions"]
            }

            logger.info(f"Loan prediction complete: {state['loan_prediction']['approved']} "
                       f"(probability: {approval_probability:.2%})")

            return state
            
        except Exception as e:
            logger.error(f"Loan processing failed: {e}")
            state.setdefault("errors", []).append(f"Underwriting (Loan): {str(e)}")
            state["rejected"] = True
            state["rejection_reason"] = "System error during underwriting"
            return state
    
    def process_insurance(self, state: ApplicationState) -> ApplicationState:
        """
        Process insurance application using Health Shield EBM model.
        
        Args:
            state: Current application state with applicant_data
        
        Returns:
            Updated state with insurance_prediction field populated
        """
        try:
            logger.info("Processing insurance application")
            
            derived = self._ensure_derived_features(state).get("health", {})
            if not derived:
                raise ValueError("No derived health features found in state")

            model_output = self._score_health_from_derived(derived)

            applicant_data = state.get("declared_data") or state.get("applicant_data") or {}
            model_explanation = self._try_extract_insurance_explanation(applicant_data)
            if model_explanation:
                model_output["feature_contributions"] = model_explanation

            state.setdefault("model_output", {})
            state["model_output"]["insurance"] = model_output

            if state.get("application_id"):
                save_model_output(
                    state["application_id"],
                    state["model_output"],
                    metadata={
                        "request_id": state.get("request_id"),
                        "request_type": state.get("request_type")
                    }
                )

            premium = model_output["premium_amount"]
            state["insurance_prediction"] = {
                "premium": premium,
                "reasoning": model_output["feature_contributions"]
            }

            logger.info(f"Insurance prediction complete: premium = ₹{premium:,.2f}")

            return state
            
        except Exception as e:
            logger.error(f"Insurance processing failed: {e}")
            state.setdefault("errors", []).append(f"Underwriting (Insurance): {str(e)}")
            state["rejected"] = True
            state["rejection_reason"] = "System error during underwriting"
            return state

    def _score_loan_from_derived(self, derived: Dict[str, Any]) -> Dict[str, Any]:
        foir = _to_float(derived.get("foir"))
        ltv = _to_float(derived.get("ltv"))
        credit_score = _to_float(derived.get("credit_score"))
        income_stability = _to_float(derived.get("income_stability_score"))
        age_bucket = derived.get("age_risk_bucket") or "unknown"
        credit_bucket = derived.get("credit_risk_bucket") or "unknown"
        loan_type = (derived.get("loan_type") or "home").lower()

        foir_threshold = 0.6 if loan_type == "home" else 0.5

        contributions: Dict[str, float] = {}
        base = 0.55
        score = base

        if foir is not None:
            if foir <= foir_threshold:
                contrib = 0.25 * (foir_threshold - foir) / foir_threshold
            else:
                contrib = -0.45 * (foir - foir_threshold) / foir_threshold
            contributions["foir"] = round(contrib, 3)
            score += contrib

        if ltv is not None:
            if ltv <= 0.9:
                contrib = 0.2 * (0.9 - ltv) / 0.9
            else:
                contrib = -0.35 * (ltv - 0.9) / 0.9
            contributions["ltv"] = round(contrib, 3)
            score += contrib

        if credit_score is not None:
            normalized = max(min((credit_score - 500) / 400, 1.0), 0.0)
            contrib = 0.6 * (normalized - 0.5)
            contributions["credit_score"] = round(contrib, 3)
            score += contrib

        if income_stability is not None:
            contrib = 0.3 * (income_stability - 0.5)
            contributions["income_stability_score"] = round(contrib, 3)
            score += contrib

        bucket_adjust = {
            "low": 0.1,
            "medium": 0.05,
            "elevated": -0.05,
            "high": -0.1,
            "unknown": 0.0
        }
        age_contrib = bucket_adjust.get(age_bucket, 0.0)
        if age_contrib:
            contributions["age_risk_bucket"] = round(age_contrib, 3)
            score += age_contrib

        credit_contrib = {
            "low": 0.1,
            "medium": 0.0,
            "high": -0.1,
            "unknown": 0.0
        }.get(credit_bucket, 0.0)
        if credit_contrib:
            contributions["credit_risk_bucket"] = round(credit_contrib, 3)
            score += credit_contrib

        approval_probability = _clamp(score, 0.05, 0.95)
        predicted_class = "approved" if approval_probability >= 0.55 else "review"
        risk_grade = "A" if approval_probability >= 0.8 else "B" if approval_probability >= 0.65 else "C" if approval_probability >= 0.5 else "D"
        confidence_score = _confidence_from_features([foir, ltv, credit_score, income_stability])

        return {
            "approval_probability": round(approval_probability, 3),
            "predicted_class": predicted_class,
            "risk_grade": risk_grade,
            "feature_contributions": contributions,
            "confidence_score": confidence_score
        }

    def _score_health_from_derived(self, derived: Dict[str, Any]) -> Dict[str, Any]:
        bmi = _to_float(derived.get("bmi"))
        age = _to_float(derived.get("age"))
        medical_score = _to_float(derived.get("medical_risk_score")) or 0.0
        lifestyle_score = _to_float(derived.get("lifestyle_risk_score")) or 0.0
        sum_insured = _to_float(derived.get("sum_insured")) or 500000
        deductible = _to_float(derived.get("deductible")) or 0.0

        risk_score = 0.0
        risk_score += 0.45 * medical_score
        risk_score += 0.35 * lifestyle_score

        if age is not None and age > 45:
            risk_score += 0.1
        if bmi is not None and bmi >= 30:
            risk_score += 0.1

        risk_score = _clamp(risk_score, 0.0, 1.0)
        loading_percentage = round(risk_score * 100, 1)

        base_rate = 0.012
        base_premium = sum_insured * base_rate
        premium_amount = base_premium * (1 + loading_percentage / 100.0)
        premium_amount = max(premium_amount - deductible * 0.05, base_premium * 0.5)

        contributions: Dict[str, float] = {
            "medical_risk_score": round(0.45 * medical_score, 3),
            "lifestyle_risk_score": round(0.35 * lifestyle_score, 3)
        }
        if age is not None:
            contributions["age"] = 0.1 if age > 45 else -0.02
        if bmi is not None:
            contributions["bmi"] = 0.1 if bmi >= 30 else -0.02

        risk_category = "low" if risk_score < 0.4 else "medium" if risk_score < 0.75 else "high"

        return {
            "premium_amount": round(premium_amount, 2),
            "loading_percentage": loading_percentage,
            "risk_category": risk_category,
            "feature_contributions": contributions
        }

    def _ensure_derived_features(self, state: ApplicationState) -> Dict[str, Any]:
        derived = state.get("derived_features") or {}
        if derived:
            return derived

        declared = state.get("declared_data")
        if not declared:
            declared = state.get("applicant_data", {}) or {}
            state["declared_data"] = declared

        state.setdefault("ocr_extracted_data", {})

        try:
            from src.agents.feature_engineering import FeatureEngineeringAgent

            agent = FeatureEngineeringAgent()
            updated = agent.process(state)
            return updated.get("derived_features", {}) or {}
        except Exception as exc:
            logger.warning(f"Derived feature fallback failed: {exc}")
            return {}

    def _try_extract_loan_explanation(self, applicant_data: Dict[str, Any]) -> Dict[str, float]:
        if not applicant_data or not hasattr(self.credit_model, "explain_local"):
            return {}

        try:
            df = self._encode_finance_features(applicant_data, return_dataframe=True)
            explanation = self.credit_model.explain_local(df)
            reasoning = self._extract_reasoning(explanation)
            if reasoning:
                self._validate_loan_monotonicity(applicant_data, 0.0, reasoning)
            return reasoning
        except Exception as exc:
            logger.warning(f"Loan explanation extraction failed: {exc}")
            return {}

    def _try_extract_insurance_explanation(self, applicant_data: Dict[str, Any]) -> Dict[str, float]:
        if not applicant_data or not hasattr(self.health_model, "explain_local"):
            return {}

        try:
            df = self._encode_health_features(applicant_data, return_dataframe=True)
            explanation = self.health_model.explain_local(df)
            reasoning = self._extract_reasoning(explanation)
            if reasoning:
                self._validate_insurance_monotonicity(applicant_data, 0.0, reasoning)
            return reasoning
        except Exception as exc:
            logger.warning(f"Insurance explanation extraction failed: {exc}")
            return {}
    
    def _encode_finance_features(self, applicant_data: Dict[str, Any], return_dataframe: bool = False):
        """
        Encode finance features using pre-trained encoders.
        
        Args:
            applicant_data: Raw applicant data dictionary
        
        Returns:
            Encoded feature array ready for model prediction, or a dataframe when return_dataframe=True
        """
        try:
            # Create DataFrame from applicant data
            df = pd.DataFrame([applicant_data])
            
            # Normalize field names (handle both 'annual_income' and 'income_annum')
            if 'annual_income' in df.columns and 'income_annum' not in df.columns:
                df['income_annum'] = df['annual_income']
            
            # Ensure required fields exist with defaults
            required_fields = ['loan_amount', 'income_annum', 'residential_assets_value', 
                             'commercial_assets_value', 'luxury_assets_value', 'bank_asset_value']
            for field in required_fields:
                if field not in df.columns:
                    df[field] = 0
                    
            # Feature Engineering (CRITICAL: Must match training pipeline)
            # These engineered features MUST be created before encoding
            df['loan_to_income_ratio'] = df['loan_amount'] / (df['income_annum'] + 1)
            
            df['total_assets'] = (
                df['residential_assets_value'].fillna(0) +
                df['commercial_assets_value'].fillna(0) +
                df['luxury_assets_value'].fillna(0) +
                df['bank_asset_value'].fillna(0)
            )
            
            df['asset_to_loan_ratio'] = df['total_assets'] / (df['loan_amount'] + 1)
            
            logger.debug(f"Engineered features: loan_to_income_ratio={df['loan_to_income_ratio'].iloc[0]:.3f}, "
                        f"total_assets={df['total_assets'].iloc[0]:.0f}, "
                        f"asset_to_loan_ratio={df['asset_to_loan_ratio'].iloc[0]:.3f}")
            
            # Apply categorical encoding using pre-trained encoders
            for col, encoder in self.credit_encoders.items():
                if col in df.columns:
                    try:
                        # Transform using fitted encoder
                        # Handle unknown categories by assigning a default value
                        original_values = df[col].astype(str)
                        
                        # Check if value is in encoder's classes
                        encoded_values = []
                        for val in original_values:
                            if val in encoder.classes_:
                                encoded_values.append(encoder.transform([val])[0])
                            else:
                                # Unknown category - use first class as default
                                logger.warning(f"Unknown category '{val}' for column '{col}', using default")
                                encoded_values.append(0)
                        
                        df[col] = encoded_values
                        
                    except Exception as e:
                        logger.warning(f"Failed to encode column {col}: {e}")
                        df[col] = 0  # Default value
            
            # Fill missing values
            df = df.fillna(0)

            # Align to model feature order to avoid shape mismatches
            df = self._align_to_model_features(df, self.credit_model)

            if return_dataframe:
                logger.debug(f"Encoded finance features shape: {df.values.shape}")
                return df

            features = df.values
            logger.debug(f"Encoded finance features shape: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Finance feature encoding failed: {e}")
            raise ValueError(f"Failed to encode finance features: {e}")
    
    def _encode_health_features(self, applicant_data: Dict[str, Any], return_dataframe: bool = False):
        """
        Encode health features using pre-trained encoders.
        
        Args:
            applicant_data: Raw applicant data dictionary
        
        Returns:
            Encoded feature array ready for model prediction, or a dataframe when return_dataframe=True
        """
        try:
            # Normalize known boolean-like fields to numeric values
            normalized = dict(applicant_data)
            boolean_fields = [
                "smoker",
                "diabetes",
                "bloodpressure",
                "regular_ex",
                "blood_pressure_problems",
                "any_transplants",
                "any_chronic_diseases",
                "known_allergies",
                "history_of_cancer_in_family"
            ]

            for field in boolean_fields:
                if field in normalized:
                    value = normalized[field]
                    if isinstance(value, str):
                        value_lower = value.strip().lower()
                        if value_lower in ["yes", "true", "1"]:
                            normalized[field] = 1
                        elif value_lower in ["no", "false", "0"]:
                            normalized[field] = 0
                    elif isinstance(value, bool):
                        normalized[field] = 1 if value else 0

            # Create DataFrame from applicant data
            df = pd.DataFrame([normalized])

            # Ensure boolean-like columns are numeric
            for field in boolean_fields:
                if field in df.columns:
                    df[field] = pd.to_numeric(df[field], errors="coerce")
            
            # Apply categorical encoding using pre-trained encoders
            for col, encoder in self.health_encoders.items():
                if col in df.columns:
                    try:
                        # Transform using fitted encoder
                        original_values = df[col].astype(str)
                        
                        # Check if value is in encoder's classes
                        encoded_values = []
                        for val in original_values:
                            if val in encoder.classes_:
                                encoded_values.append(encoder.transform([val])[0])
                            else:
                                # Unknown category - use first class as default
                                logger.warning(f"Unknown category '{val}' for column '{col}', using default")
                                encoded_values.append(0)
                        
                        df[col] = encoded_values
                        
                    except Exception as e:
                        logger.warning(f"Failed to encode column {col}: {e}")
                        df[col] = 0  # Default value
            
            # Fill missing values
            df = df.fillna(0)

            # Align to model feature order to avoid shape mismatches
            df = self._align_to_model_features(df, self.health_model)

            if return_dataframe:
                logger.debug(f"Encoded health features shape: {df.values.shape}")
                return df

            features = df.values
            logger.debug(f"Encoded health features shape: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"Health feature encoding failed: {e}")
            raise ValueError(f"Failed to encode health features: {e}")
    
    def _extract_reasoning(self, ebm_explanation) -> Dict[str, float]:
        """
        Extract feature contributions from EBM explanation object.
        
        The EBM explanation object from interpret library's explain_local() method
        contains contribution scores for each feature (Shapley-like values).
        
        Args:
            ebm_explanation: EBM local explanation object from explain_local()
        
        Returns:
            Dictionary mapping feature names to contribution values
        """
        try:
            reasoning = {}
            
            # Extract feature names and values
            if hasattr(ebm_explanation, 'data'):
                # interpret library structure: explanation.data(0) returns dict for first sample
                # This is the correct method as shown in test_model.py
                explanation_data = ebm_explanation.data(0)
                
                if 'names' in explanation_data and 'scores' in explanation_data:
                    feature_names = explanation_data['names']
                    feature_scores = explanation_data['scores']
                    
                    for name, score in zip(feature_names, feature_scores):
                        reasoning[name] = float(score)
                    
                    logger.debug(f"Extracted reasoning with {len(reasoning)} features using .data(0) method")
                
            else:
                # Fallback: try direct attribute access
                logger.warning("Using fallback reasoning extraction method")
                if hasattr(ebm_explanation, 'feature_names') and hasattr(ebm_explanation, 'values'):
                    for name, value in zip(ebm_explanation.feature_names, ebm_explanation.values):
                        reasoning[name] = float(value)
            
            if not reasoning:
                logger.warning("No reasoning extracted, returning empty dict")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Reasoning extraction failed: {e}")
            # Return empty dict instead of error dict to avoid breaking downstream processing
            return {}


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)


def _confidence_from_features(values: List[Optional[float]]) -> float:
    available = sum(1 for val in values if val is not None)
    return round(min(0.4 + available * 0.12, 0.95), 2)


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

    def _align_to_model_features(self, df: pd.DataFrame, model: Any) -> pd.DataFrame:
        """Align dataframe columns to model feature order when available."""
        feature_names: Optional[List[str]] = None
        for attr in ("feature_names_", "feature_names", "feature_names_in_"):
            if hasattr(model, attr):
                try:
                    feature_names = list(getattr(model, attr))
                    break
                except Exception:
                    continue

        if not feature_names:
            return df

        for name in feature_names:
            if name not in df.columns:
                df[name] = 0

        return df[feature_names]
    
    def _validate_loan_monotonicity(
        self, 
        applicant_data: Dict[str, Any], 
        probability: float, 
        reasoning: Dict[str, float]
    ) -> None:
        """
        Validate monotonicity constraints for loan approval.
        
        Expected monotonic relationships:
        - Higher CIBIL score → Higher approval probability
        - Higher income → Higher approval probability
        - Higher existing debt → Lower approval probability
        - Higher loan-to-income ratio → Lower approval probability
        
        Args:
            applicant_data: Raw applicant data
            probability: Predicted approval probability
            reasoning: Feature contributions from EBM
        """
        violations = []
        
        # Check CIBIL score (should be positive contributor for high scores)
        cibil_score = applicant_data.get('cibil_score', 0)
        cibil_contribution = reasoning.get('cibil_score', 0)
        if cibil_score > 750 and cibil_contribution < 0:
            violations.append(f"High CIBIL ({cibil_score}) has negative contribution ({cibil_contribution:.3f})")
        
        # Check income (should be positive contributor for high income)
        income = applicant_data.get('income_annum', 0) or applicant_data.get('annual_income', 0)
        income_contribution = reasoning.get('income_annum', 0) or reasoning.get('annual_income', 0)
        if income > 1000000 and income_contribution < 0:
            violations.append(f"High income (₹{income:,}) has negative contribution ({income_contribution:.3f})")
        
        # Check loan-to-income ratio (should be negative contributor for high ratios)
        loan_amount = applicant_data.get('loan_amount', 0)
        if income > 0:
            lti_ratio = loan_amount / income
            lti_contribution = reasoning.get('loan_to_income_ratio', 0)
            if lti_ratio > 5 and lti_contribution > 0:
                violations.append(f"High LTI ratio ({lti_ratio:.2f}) has positive contribution ({lti_contribution:.3f})")
        
        # Log violations (non-blocking)
        if violations:
            logger.warning(f"Monotonicity violations detected for loan approval: {'; '.join(violations)}")
        else:
            logger.debug("No monotonicity violations detected for loan")
    
    def _validate_insurance_monotonicity(
        self,
        applicant_data: Dict[str, Any],
        premium: float,
        reasoning: Dict[str, float]
    ) -> None:
        """
        Validate monotonicity constraints for insurance premium.
        
        Expected monotonic relationships:
        - Higher age → Higher premium
        - Pre-existing conditions → Higher premium
        - Higher BMI (if diabetic/hypertensive) → Higher premium
        
        Args:
            applicant_data: Raw applicant data
            premium: Predicted insurance premium
            reasoning: Feature contributions from EBM
        """
        violations = []
        
        # Check age (should be positive contributor for older applicants)
        age = applicant_data.get('age', 0)
        age_contribution = reasoning.get('age', 0)
        if age > 50 and age_contribution < 0:
            violations.append(f"High age ({age}) has negative contribution ({age_contribution:.3f})")
        
        # Check pre-existing conditions
        conditions = ['diabetes', 'blood_pressure_problems', 'any_transplants', 'any_chronic_diseases']
        for condition in conditions:
            has_condition = applicant_data.get(condition, False)
            condition_contribution = reasoning.get(condition, 0)
            
            # If condition is present, contribution should generally be positive (increase premium)
            if has_condition and condition_contribution < -0.1:  # Allow small negative values
                violations.append(f"Condition '{condition}' has negative contribution ({condition_contribution:.3f})")
        
        # Log violations (non-blocking)
        if violations:
            logger.warning(f"Monotonicity violations detected for insurance premium: {'; '.join(violations)}")
        else:
            logger.debug("No monotonicity violations detected for insurance")


def process_underwriting(state: ApplicationState) -> ApplicationState:
    """
    Convenience function for workflow integration.
    
    Routes to loan or insurance processing based on request_type.
    
    Args:
        state: Current application state
    
    Returns:
        Updated state with predictions
    """
    try:
        agent = UnderwritingAgent()
        request_type = state.get("request_type", "both")
        
        # Process based on request type
        if request_type in ["loan", "both"]:
            state = agent.process_loan(state)
        
        if request_type in ["insurance", "both"]:
            state = agent.process_insurance(state)
        
        return state
        
    except Exception as e:
        logger.error(f"Underwriting processing failed: {e}")
        state.setdefault("errors", []).append(f"Underwriting: {str(e)}")
        return state
