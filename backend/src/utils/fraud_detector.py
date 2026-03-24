from pathlib import Path


class FraudDetector:
    def analyze_document(self, file_path: str, extracted_text: str = "", document_type: str = "unknown") -> dict:
        path = Path(file_path)
        exists = path.exists()
        text_len = len(extracted_text or "")

        score = 0.0
        flags: list[str] = []

        if not exists:
            score += 40.0
            flags.append("file_missing")
        if text_len < 30:
            score += 25.0
            flags.append("low_text_content")

        return {
            "document_type": document_type,
            "fraud_score": round(min(score, 100.0), 2),
            "flags": flags,
            "heuristics": {
                "file_exists": exists,
                "text_length": text_len,
            },
        }
