# AGENTS.md

## Source Ingestion Rules

This project treats content sources as two explicit categories only:

1. Known RSS/Atom feed URL
2. Sites that truly do not provide RSS/Atom

Do not add an `auto`, `discover`, `feed-discovery`, or similar source type.

For sites that have a feed but do not expose it prominently in the UI, manually confirm the RSS/Atom URL and add that direct URL to `config/sources.json` with `"type": "rss"`. Quarkslab Blog is in this category:

```json
{
  "name": "Quarkslab Blog",
  "icon": "⚗️",
  "url": "https://blog.quarkslab.com/feeds/all.atom.xml",
  "type": "rss"
}
```

Sites that truly do not provide RSS/Atom must not be added to the RSS source list. They require a separate, explicit site adapter design with clear selectors, field mapping, rate limiting, and failure handling.
