# Exa web search

Pi extension that registers `web_search` using the [Exa Search API](https://docs.exa.ai/reference/search).

## Configuration

Set the key in the environment that launches Pi:

```bash
export EXA_API_KEY='...'
```

The extension deliberately has no `auth.json` fallback. Do not commit credentials.

## Tool contract

```text
query         base search query
exactPhrases phrases added as quoted search terms
excludeTerms terms added with a leading minus
site          domain restriction sent as Exa includeDomains
count         number of results, 1–10 (default 5)
```

Results contain a title, URL, and the first Exa highlight as a bounded relevant snippet.

## Relationship to `web_fetch`

`web_search` discovers candidate pages. `web_fetch` remains a separate direct-URL reader with HTML readability conversion, PDF/plain-text handling, and Jina fallback. Search does not proxy URL fetching through Exa.

## Reload

After editing the extension or changing the environment, restart Pi or run:

```text
/reload
```

A missing key produces:

```text
Missing EXA_API_KEY in the Pi process environment.
```
