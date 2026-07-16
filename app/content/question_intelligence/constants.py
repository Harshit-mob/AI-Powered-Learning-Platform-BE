import re

# Centralized constants and compiled regexes for performance
PUNCTUATION_REGEX = re.compile(r'[^\w\s]')

# Commonly used words that might indicate specific cognitive levels
RECALL_VERBS = {"define", "list", "name", "state", "identify"}
UNDERSTAND_VERBS = {"explain", "describe", "summarize", "paraphrase"}
APPLY_VERBS = {"apply", "use", "solve", "demonstrate"}
ANALYZE_VERBS = {"analyze", "compare", "contrast", "differentiate"}
