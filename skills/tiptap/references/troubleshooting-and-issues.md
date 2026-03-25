# Troubleshooting & Known Issues

## Issue #1: SSR Hydration Mismatch
**Error:** "SSR has been detected, please set immediatelyRender explicitly to false"
**Source:** GitHub Issue #5856, #5602
**Cause:** Default `immediatelyRender: true` breaks Next.js hydration
**Fix:** Add `immediatelyRender: false` to `useEditor()` config

## Issue #2: Editor Re-renders on Every Keystroke
**Error:** Laggy typing, poor performance in large documents
**Cause:** `useEditor()` hook re-renders component on every change
**Fix:** Use `useEditorState()` hook for read-only rendering, or memoize editor config

## Issue #3: Tailwind Typography Not Working
**Error:** Headings/lists render unstyled, no formatting visible
**Cause:** Missing `@tailwindcss/typography` plugin
**Fix:** `npm install @tailwindcss/typography` + add `prose` classes to editor container

## Issue #4: Image Upload Base64 Bloat
**Error:** JSON payloads become megabytes, slow saves, database bloat
**Cause:** Default allows base64, no upload handler configured
**Fix:** Set `allowBase64: false` in Image extension + use upload handler (see templates)

## Issue #5: Build Errors in Create React App
**Error:** "jsx-runtime" module resolution errors after upgrading to v3
**Source:** GitHub Issue #6812
**Cause:** CRA incompatibility with v3 module structure
**Fix:** Switch to Vite — CRA incompatible with Tiptap v3

## Issue #6: ProseMirror Multiple Versions Conflict
**Error:** "Looks like multiple versions of prosemirror-model were loaded"
**Source:** GitHub Issue #577, #6171
**Cause:** Extensions pull different prosemirror versions
**Fix:** Add package resolutions:
```json
{
  "resolutions": {
    "prosemirror-model": "~1.21.0",
    "prosemirror-view": "~1.33.0",
    "prosemirror-state": "~1.4.3"
  }
}
```
Or: `rm -rf node_modules package-lock.json && npm install`

## Issue #7: EditorProvider vs useEditor Confusion
**Error:** SSR error when both used together
**Source:** GitHub Issue #5856 Comment
**Cause:** EditorProvider wraps useEditor — using both creates duplicate editors

**Wrong:**
```tsx
<EditorProvider>
  <MyComponent /> {/* MyComponent uses useEditor() — WRONG */}
</EditorProvider>
```

**Correct — Option 1 (EditorProvider only):**
```tsx
<EditorProvider immediatelyRender={false} extensions={[StarterKit]}>
  <EditorContent />
</EditorProvider>
```

**Correct — Option 2 (useEditor only):**
```tsx
function Editor() {
  const editor = useEditor({
    extensions: [StarterKit],
    immediatelyRender: false,
  })
  return <EditorContent editor={editor} />
}
```

## Issue #8: Accidentally Using Pro Extensions
**Error:** 404 or auth errors when installing `@tiptap/extension-collaboration`, `-comments`, `-ai`
**Cause:** Pro extensions require Tiptap Cloud subscription and private npm registry auth
**Fix:** Only use free/MIT extensions listed in `SKILL.md`. If you need collab, consider open-source alternatives like Y.js + y-prosemirror directly (without Tiptap's wrapper).

## React Version Compatibility
- Core Tiptap: React 19 supported since v2.10.0
- Free extensions: Full React 19 support
- Pro UI Components: May require React 18 — drag-handle depends on archived tippyjs-react

## Markdown Recent Fixes (v3.15.0-v3.16.0)
- Fixed incorrect output when underline mixed with bold/italic and ranges don't fully overlap
- Improved serialization for overlapping formatting marks
