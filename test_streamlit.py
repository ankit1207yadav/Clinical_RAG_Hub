import unittest
import os
import base64
from io import BytesIO

# Import target helper functions
from rag_utils import (
    retrieve_guidelines_context,
    encode_image_base64,
    parse_metrics_regex
)

class TestClinicalStreamlitUtils(unittest.TestCase):
    
    def test_01_parse_metrics_diabetic(self):
        """Verify regex correctly parses blood sugar parameters from clinical logs."""
        log = "Patient details: HbA1c: 7.2%, Hemoglobin: 12.8 g/dL"
        metrics = parse_metrics_regex(log)
        
        self.assertIn("hba1c", metrics)
        self.assertEqual(metrics["hba1c"], 7.2)
        self.assertIn("hb", metrics)
        self.assertEqual(metrics["hb"], 12.8)

    def test_02_parse_metrics_hypertension(self):
        """Verify regex parses blood pressure logs correctly."""
        log = "BP reading today is 142/92. Patient is high risk."
        metrics = parse_metrics_regex(log)
        
        self.assertIn("bp", metrics)
        self.assertEqual(metrics["bp"]["sys"], 142)
        self.assertEqual(metrics["bp"]["dia"], 92)

    def test_03_parse_metrics_cholesterol(self):
        """Verify regex parses LDL cholesterol markers."""
        log = "LDL: 165 mg/dL. HDL is 38."
        metrics = parse_metrics_regex(log)
        
        self.assertIn("ldl", metrics)
        self.assertEqual(metrics["ldl"], 165)

    def test_04_base64_encoder(self):
        """Verify base64 converter outputs expected standard format strings."""
        dummy_bytes = b"medical_image_data_block"
        expected_b64 = base64.b64encode(dummy_bytes).decode("utf-8")
        
        output = encode_image_base64(dummy_bytes)
        self.assertEqual(output, expected_b64)

    def test_05_guidelines_context_rag(self):
        """Verify keyword matching maps to relevant section standards in medical_guidelines.txt."""
        # Query that maps to Glycated Hemoglobin guidelines
        query = "What does a high HbA1c level of 7.2% mean?"
        context = retrieve_guidelines_context(query)
        
        self.assertGreater(len(context), 0)
        self.assertIn("CLINICAL REFERENCE GUIDELINE: GLYCATED HEMOGLOBIN", context)
        self.assertNotIn("CLINICAL REFERENCE GUIDELINE: HEMOGLOBIN (Hb) & ANEMIA", context)

        # Query that maps to Blood Pressure guidelines
        query = "Explain normal limits for high blood pressure"
        context = retrieve_guidelines_context(query)
        self.assertIn("CLINICAL REFERENCE GUIDELINE: BLOOD PRESSURE", context)

if __name__ == "__main__":
    unittest.main()
