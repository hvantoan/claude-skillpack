# Styling & Configuration

## Tailwind Prose Styling (tiptap-prose.css)

```css
.tiptap {
  @apply prose prose-sm sm:prose-base lg:prose-lg dark:prose-invert max-w-none;

  h1 { @apply text-3xl font-bold mt-8 mb-4; }
  h2 { @apply text-2xl font-semibold mt-6 mb-3; }
  p { @apply my-4 text-base leading-7; }
  ul, ol { @apply my-4 ml-6; }
  code { @apply bg-muted px-1.5 py-0.5 rounded text-sm font-mono; }
  pre { @apply bg-muted p-4 rounded-lg overflow-x-auto; }
  blockquote { @apply border-l-4 border-primary pl-4 italic my-4; }
}
```

- `prose` classes provide consistent formatting
- `dark:prose-invert` handles dark mode automatically
- Custom overrides use semantic Tailwind v4 colors

## Tailwind v4 Setup

```bash
npm install @tailwindcss/typography
```

```ts
// tailwind.config.ts
import typography from '@tailwindcss/typography'
export default { plugins: [typography] }
```

## Dependencies (Updated 2026-03-25)

### Required
```json
{
  "@tiptap/react": "^3.16.0",
  "@tiptap/starter-kit": "^3.16.0",
  "@tiptap/pm": "^3.16.0"
}
```

### Optional (All Free/MIT Licensed)
```json
{
  "@tiptap/extension-image": "^3.16.0",
  "@tiptap/extension-color": "^3.16.0",
  "@tiptap/extension-text-style": "^3.16.0",
  "@tiptap/extension-typography": "^3.16.0",
  "@tiptap/extension-link": "^3.16.0",
  "@tiptap/extension-placeholder": "^3.16.0",
  "@tiptap/extension-character-count": "^3.16.0",
  "@tiptap/extension-focus": "^3.16.0",
  "@tiptap/extension-highlight": "^3.16.0",
  "@tiptap/extension-text-align": "^3.16.0",
  "@tiptap/extension-subscript": "^3.16.0",
  "@tiptap/extension-superscript": "^3.16.0",
  "@tiptap/extension-underline": "^3.16.0",
  "@tiptap/extension-table": "^3.16.0",
  "@tiptap/extension-table-row": "^3.16.0",
  "@tiptap/extension-table-cell": "^3.16.0",
  "@tiptap/extension-table-header": "^3.16.0",
  "@tiptap/extension-task-list": "^3.16.0",
  "@tiptap/extension-task-item": "^3.16.0",
  "@tiptap/extension-markdown": "^3.16.0",
  "@tiptap/extension-code-block-lowlight": "^3.16.0"
}
```

### Dev
```json
{
  "@tailwindcss/typography": "^0.5.19",
  "react": "^19.2.3",
  "react-dom": "^19.2.3"
}
```

## Setup Checklist
- [ ] Installed @tiptap/react, @tiptap/starter-kit, @tiptap/pm
- [ ] Set `immediatelyRender: false` in useEditor()
- [ ] Installed @tailwindcss/typography
- [ ] Added prose classes to editor container
- [ ] Configured image upload handler (if using images)
- [ ] Set `allowBase64: false` in Image extension
- [ ] Editor renders without hydration errors

## Official Documentation
- Tiptap: https://tiptap.dev
- Installation: https://tiptap.dev/docs/editor/installation/react
- Extensions: https://tiptap.dev/docs/editor/extensions
- API Reference: https://tiptap.dev/docs/editor/api/editor
- shadcn minimal-tiptap: https://github.com/Aslam97/shadcn-minimal-tiptap
- Context7 Library ID: /ueberdosis/tiptap-docs
