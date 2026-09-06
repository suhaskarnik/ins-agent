# Submitted Documents are structured metadata, never fake file content

A claim's supporting documents could be modeled as fabricated file bodies (mock scanned images, OCR'd text) for the Sufficiency Assessment to read. We chose structured metadata only — each Submitted Document is a `{doc_type, filename, present}` entry from a fixed enum.

Fabricating realistic document content is unbounded scope for a POC and would make the Sufficiency Assessment about text comprehension rather than the actual domain judgment (does the *set* of what's present satisfy the Guideline's required set for this claim type). This is also an honest boundary: a real form-intake step captures what was uploaded, not its contents, so structured metadata is what this stage of a real pipeline would actually have to work with.
