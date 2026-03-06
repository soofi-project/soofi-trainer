# Task

- user story: [US-02](US-02-knowledge-base.md)
- depends on: [T-02-4](T-02-4-minio-knowledge-urls.md)

/label ~UserStory_US-02
/label ~Task
/label ~ToDo

# Description

**Knowledge Document Proxy via nginx**

Source links in Advisor responses currently point to the MinIO admin UI, which shows a
file-manager interface instead of the document itself. Replace with a clean nginx proxy that
serves the raw documents directly, so source links open the actual document in the browser.

## Current State

Advisor responses include source links like:

```markdown
**Quellen**
- [rag-best-practices](http://minio:9000/knowledge/rag-best-practices.md)
```

Clicking opens the MinIO Console — not the document itself.

## Solution: nginx Location Block

Add a location block to the existing nginx config that proxies to MinIO's S3 API:

```nginx
location /docs/ {
    proxy_pass http://minio:9000/knowledge/;
    proxy_set_header Host minio:9000;

    # Serve inline instead of download
    proxy_hide_header Content-Disposition;

    # Correct content types
    types {
        text/markdown md;
        text/plain txt;
        application/pdf pdf;
    }
}
```

## Source URL Update

Update the Advisor's `metadata.source` URLs (set during knowledge ingestion) to point to the
nginx proxy instead of MinIO directly:

```
Before: http://minio:9000/knowledge/rag-best-practices.md
After:  /docs/rag-best-practices.md
```

Relative URLs work because the frontend and nginx share the same origin.

## Markdown Rendering & Section Navigation

A `<soofi-doc-viewer>` Lit component that renders knowledge documents inline with section
anchors, so source links can scroll directly to the relevant section.

### Implementation

- Intercept source link clicks in the chat UI (don't open a new tab)
- Fetch the Markdown via `/docs/...`
- Render as HTML using a lightweight library (e.g. `marked`)
- Generate `id` anchors from headings (e.g. `## LoRA Hyperparameter` → `#lora-hyperparameter`)
- Scroll to the anchor if present in the URL fragment

### Source URLs with Section Anchors

Source links include the section anchor when the chunk metadata contains a heading:

```
/docs/rag-best-practices.md#chunk-strategie
```

This requires storing the section heading during knowledge ingestion as chunk metadata
(e.g. `metadata.section`). The Advisor prompt already instructs the LLM to use `metadata.source`
for links — the anchor can be appended there.

### Layout

The viewer opens as a **side panel** on the right. The chat remains visible on the left so the
presenter can reference both the source document and the agent's answer simultaneously.

- Panel slides in from the right (e.g. 40% width)
- Close button returns to full-width chat
- If multiple sections of the same document are referenced, a small jump list at the top of
  the panel shows all referenced sections as clickable anchors
- Referenced sections are visually highlighted (e.g. subtle background color) so the user can
  see at a glance which parts the agent used

## Acceptance Criteria

- [ ] nginx location `/docs/` proxies to MinIO knowledge bucket
- [ ] Source links in Advisor responses use `/docs/` URLs with section anchors
- [ ] `<soofi-doc-viewer>` Lit component renders Markdown as formatted HTML
- [ ] Clicking a source link opens the viewer and scrolls to the referenced section
- [ ] Documents accessible without authentication (internal demo system)
- [ ] Knowledge ingestion sets `metadata.source` to `/docs/` URLs
- [ ] Knowledge ingestion stores section heading in chunk metadata
- [ ] Existing documents re-ingested with updated URLs and section metadata
- [ ] PDFs open inline in the browser (no Markdown rendering needed)
- [ ] Viewer is closeable, user returns to full-width chat
- [ ] Multiple referenced sections in the same document shown as jump list
- [ ] Referenced sections visually highlighted in the rendered document

# Branches

- feature/T-02-5-docs-proxy
