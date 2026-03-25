# Extensions & Patterns (Free/Open-Source Only)

## StarterKit — What's Included
**Nodes:** Blockquote, BulletList, CodeBlock, Document, HardBreak, Heading, HorizontalRule, ListItem, OrderedList, Paragraph, Text
**Marks:** Bold, Code, Italic, Link, Strike, Underline
**Extensions:** Dropcursor, Gapcursor, History (Undo/Redo), ListKeymap, TrailingNode

## Extension Configuration

```tsx
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Typography from '@tiptap/extension-typography'

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
      bulletList: { keepMarks: true },
    }),
    Image.configure({
      inline: true,
      allowBase64: false, // Prevent base64 bloat
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: { class: 'text-primary underline' },
    }),
    Typography, // Smart quotes, dashes
  ],
  immediatelyRender: false,
})
```

Extension order matters — dependencies must load first.

## Additional Free Extensions

```bash
# Table support
npm install @tiptap/extension-table @tiptap/extension-table-row @tiptap/extension-table-cell @tiptap/extension-table-header

# Task lists (checkboxes)
npm install @tiptap/extension-task-list @tiptap/extension-task-item

# Text formatting
npm install @tiptap/extension-highlight @tiptap/extension-text-align @tiptap/extension-subscript @tiptap/extension-superscript @tiptap/extension-underline

# Utilities
npm install @tiptap/extension-placeholder @tiptap/extension-character-count @tiptap/extension-focus

# Code highlighting
npm install @tiptap/extension-code-block-lowlight lowlight
```

## Image Upload Pattern (Base64 Preview → Upload → URL)

```tsx
async function uploadImage(editor: Editor, file: File, uploadEndpoint = '/api/upload'): Promise<string> {
  // 1. Base64 preview for immediate display
  const reader = new FileReader()
  const base64 = await new Promise<string>((resolve) => {
    reader.onload = () => resolve(reader.result as string)
    reader.readAsDataURL(file)
  })

  // 2. Insert preview
  editor.chain().focus().setImage({ src: base64 }).run()

  // 3. Upload to server
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(uploadEndpoint, { method: 'POST', body: formData })
  const { url } = await response.json()

  // 4. Replace base64 with permanent URL
  editor.chain().focus().updateAttributes('image', { src: url }).run()
  return url
}
```

## Markdown Support

```tsx
import { Markdown } from '@tiptap/extension-markdown'

const editor = useEditor({
  extensions: [StarterKit, Markdown],
  content: '# Hello\n\nThis is **Markdown**!',
  contentType: 'markdown', // CRITICAL: must specify
  immediatelyRender: false,
})

// Get/set markdown
const md = editor.getMarkdown()
editor.commands.setContent('## New', { contentType: 'markdown' })
```

Install: `npm install @tiptap/extension-markdown@^3.16.0`

## Form Integration (react-hook-form)

```tsx
import { useForm, Controller } from 'react-hook-form'

function BlogForm() {
  const { control, handleSubmit } = useForm()
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        name="content"
        control={control}
        render={({ field }) => (
          <Editor
            content={field.value}
            onUpdate={({ editor }) => field.onChange(editor.getHTML())}
          />
        )}
      />
    </form>
  )
}
```

## Custom Extensions

```tsx
import { Node } from '@tiptap/core'

const CustomNode = Node.create({
  name: 'customNode',
  group: 'block',
  content: 'inline*',
  parseHTML() { return [{ tag: 'div[data-custom]' }] },
  renderHTML({ HTMLAttributes }) {
    return ['div', { 'data-custom': '', ...HTMLAttributes }, 0]
  },
  addCommands() {
    return {
      insertCustomNode: () => ({ commands }) =>
        commands.insertContent({ type: this.name }),
    }
  },
})
```

## Slash Commands (Notion-like)

```tsx
import { Extension } from '@tiptap/core'
import Suggestion from '@tiptap/suggestion'

const SlashCommands = Extension.create({
  name: 'slashCommands',
  addOptions() {
    return {
      suggestion: {
        char: '/',
        items: ({ query }) => [
          { title: 'Heading 1', command: ({ editor, range }) => {
            editor.chain().focus().deleteRange(range).setHeading({ level: 1 }).run()
          }},
          { title: 'Bullet List', command: ({ editor, range }) => {
            editor.chain().focus().deleteRange(range).toggleBulletList().run()
          }},
        ],
      },
    }
  },
  addProseMirrorPlugins() {
    return [Suggestion({ editor: this.editor, ...this.options.suggestion })]
  },
})
```

## Pro Extensions (NOT free — require paid Tiptap Cloud plan)
Do NOT use without subscription:
- `@tiptap/extension-collaboration` — Real-time collab (Y.js)
- `@tiptap/extension-comments` — Document comments
- `@tiptap/extension-ai` — Content AI
- Version History / Snapshots
- Pages, Emoji (with suggestions), Drag handle
