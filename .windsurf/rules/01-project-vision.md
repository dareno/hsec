---
trigger: glob
globs: docs/*.md
---

- There is a hierarchy of documents
- Use the YAML metadata `upstream` key if it exists in a document to identify higher level documents
- A document must stay consistent with the intent of the higher level document
- if a document is not consistent with a higher level document, let the user know why
