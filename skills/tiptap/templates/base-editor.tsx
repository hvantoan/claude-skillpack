import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

export function Editor({
  content = '<p>Hello World!</p>',
  onUpdate,
}: {
  content?: string
  onUpdate?: (html: string) => void
}) {
  const editor = useEditor({
    extensions: [StarterKit],
    content,
    immediatelyRender: false, // CRITICAL for SSR/Next.js
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose-base focus:outline-none min-h-[200px] p-4',
      },
    },
    onUpdate: ({ editor }) => {
      onUpdate?.(editor.getHTML())
    },
  })

  return <EditorContent editor={editor} />
}
