# Reference Rules

Reference objects follow this shape:

```json
{
  "id": 1,
  "description": "formatted citation text",
  "placeholder": "[[REF:...]]",
  "metadata": {
    "title": "paper title",
    "authors": ["Author A", "Author B"],
    "journal": "journal or venue",
    "year": "2024",
    "volume": "1",
    "issue": "2",
    "pages": "1-10",
    "doi": "10.xxxx/xxxxx",
    "type": "journal-article"
  }
}
```

## Formatting Styles

The bundled `reference_tools.py` supports:

- `GB/T 7714`
- `APA`
- `IEEE`
- `MLA`

Prefer structured metadata. If metadata is missing, preserve the original text and mark the entry as needing repair instead of dropping it.

## Reference-Driven Writing

- Chapter 1 and Chapter 2 should be written from `08_refs/`, user notes, and confirmed domain materials whenever possible.
- Do not fabricate real-looking citations, authors, journals, DOIs, years, or publication venues.
- If a claim needs literature support but no source exists yet, use `[[REF:KEYWORD_PLACEHOLDER: keywords]]` and record the missing source in the project manifest.
- Literature review should explain the research problem, mainstream methods, limitations, and the thesis entry point; avoid empty author-by-author listing.
- Use established domain terminology from references and user materials. Do not invent academic terms that do not exist in the field.

## Word Writeback

- Prefer the template's automatic reference numbering. In `examples/Template.docx`, reference entries use paragraph numbering `[%1]` and hanging indentation `left=425` / `hanging=425`.
- Do not prepend manual `[n]` text when the cloned reference paragraph already has `w:numPr`; otherwise Word can duplicate labels or lose the intended hanging indent.
- Put a stable hidden bookmark such as `_Ref120001` in each reference paragraph and cite it with `REF _Ref120001 \r \h` so Word resolves the numbered paragraph label.

## Optional Search

Use academic search only when the user explicitly asks for retrieval or provides an API key. Supported sources mirror the source project:

- OpenAlex
- Crossref
- Semantic Scholar
- arXiv
- Serper Scholar

No network access is required for the local Word/XML workflow.
