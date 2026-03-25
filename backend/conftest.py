# backend/conftest.py  (root-level, executed before any test module is imported)
# Setting TEST_MODE here ensures main.py's _rate_key() reads it correctly
# at request time, bypassing slowapi rate limits in the test suite.
import os
os.environ["TEST_MODE"] = "true"
