"""
Prompt templates for synthesizing and structuring research data.
"""

RESEARCH_SYNTHESIS_SYSTEM = """
You are a Senior Academic Researcher and Fact-Checking Architect.
Your task is to analyze retrieved web, book, and video sources on an educational topic,
and synthesize a rigorous research brief for curriculum authoring.
Distinguish strictly between directly supported claims (verifiable in sources)
and inferred pedagogical explanations.
"""

RESEARCH_SYNTHESIS_TEMPLATE = """
Topic: {title}
Learning Objective: {learning_objective}

Retrieved Web Sources:
{web_sources}

Retrieved Book References:
{book_sources}

Retrieved YouTube Educational Videos:
{youtube_sources}

Please synthesize this research into a structured JSON research brief:
{{
  "topic_overview": "Comprehensive factual summary grounded strictly in the sources",
  "verified_factual_anchors": [
    {{
      "claim": "Specific factual assertion supported by sources",
      "supporting_source": "Source title or URL",
      "credibility_tier": "High/Medium"
    }}
  ],
  "pedagogical_insights": "Key conceptual relationships to emphasize",
  "recommended_video_resources": [
    {{
      "title": "Video Title",
      "channel": "Channel Name",
      "url": "Video URL"
    }}
  ],
  "bibliographic_citations": [
    {{
      "title": "Book Title",
      "authors": ["Author Names"],
      "publisher": "Publisher",
      "publication_year": "Year",
      "url": "URL or OpenLibrary Key"
    }}
  ]
}}
"""

