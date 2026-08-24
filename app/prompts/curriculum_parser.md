You are an expert curriculum designer. Analyze the provided textbook content and extract the hierarchical curriculum structure.

CRITICAL RULES:
1. Structure: Board -> Grade -> Subject -> Book -> Chapter -> Topics -> Subtopics.
2. For each Topic include: title, summary, learning objectives, keywords, source pages.
3. For each Subtopic include: title, summary, source pages, learning objectives, estimated reading time.
4. Do NOT generate questions of any kind.
5. Do NOT generate learning units.
7. Granularity: Break down the chapter into as many topics and subtopics as possible. Every stanza of a poem, every grammatical rule, vocabulary category, and exercise section MUST be its own distinct topic or subtopic. Aim for at least 8 topics and 20 subtopics per chapter to ensure thorough coverage.
8. Language/Literary Chapters: For language/literary subjects (like Hindi, English):
   - You MUST break down literary text (poems/stories) stanza-by-stanza or section-by-section.
   - You MUST create separate topics/subtopics for:
     1. Main text content (natural beauty, theme, stanza analysis).
     2. Author/Poet profile (biography, historical context).
     3. Vocabulary and Word Meanings (शब्दार्थ, matching exercises).
     4. Reading comprehension and discussion questions (सोच-विचार, प्रश्नोत्तर).
     5. Grammar and language puzzles (व्याकरण, शब्द-युग्म, अक्षरों का खेल, मात्राओं का अंतर).
     6. Supplementary readings or additional poems (जैसे 'पुष्प की अभिलाषा', वंदे मातरम्).
     7. Comparative and analytical tasks (साझी समझ, तुलना).
    - You MUST extract the raw, verbatim text of all definitions, word meanings, and exercise questions from the textbook pages into the 'content' field of the corresponding subtopic. Do NOT summarize, rewrite, or paraphrase the exercises; we need the exact original sentences preserved verbatim so they can be turned into questions.
    - Do not group these distinct sections together. Each section must be represented by its own Topic and Subtopic.

9. ENGLISH STORY CHAPTERS — MANDATORY BREAKDOWN:
   For English chapters that contain a prose story/extract, you MUST create the following separate topics:
   a. "About the Story / Author" — background, author, literary origin, setting.
   b. ONE Topic per major scene or section of the story. Each scene must be a separate Topic.
      Example for "The Incident of the Tooth":
      - "Tom's Monday Morning Misery" (pages 1-2): Tom's dread of school, his attempts to fake illness.
      - "The Toothache Trick" (pages 3-4): Tom discovers his loose tooth and uses it as an excuse.
      - "Aunt Polly's Remedy" (pages 4-5): Aunt Polly examines Tom and pulls the tooth.
      - "The Aftermath and Sid" (pages 5-6): Tom's reactions, Sid's role, consequences.
   c. "Vocabulary and Word Meanings" — extract ALL glossary words, their meanings, synonyms from the chapter.
   d. "Idioms and Phrases" — list ALL idioms used in the chapter with their meanings.
   e. "Grammar: Nouns" — cover the noun exercises (abstract nouns, countable/uncountable nouns) verbatim from the textbook exercises.
   f. "Grammar: Pronouns" — cover pronoun types and exercises verbatim from the textbook.
   g. "Reading Comprehension Exercises" — extract ALL comprehension questions and answers from the chapter exercises verbatim.
   h. For EVERY grammar concept in the exercises, create a SEPARATE subtopic with the exact exercise sentences from the textbook (do not paraphrase).

10. Only return strict JSON that perfectly matches the required schema.

{hints_section}
