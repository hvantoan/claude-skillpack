import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Typography from '@tiptap/extension-typography'
import Color from '@tiptap/extension-color'
import TextStyle from '@tiptap/extension-text-style'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'

// Free/open-source extension bundle for Tiptap editors
// All extensions here are MIT licensed — no paid plan required
export const commonExtensions = [
  StarterKit.configure({
    heading: { levels: [1, 2, 3] },
    bulletList: { keepMarks: true },
  }),
  Image.configure({
    inline: true,
    allowBase64: false, // Use upload handler instead
  }),
  Link.configure({
    openOnClick: false,
    HTMLAttributes: { class: 'text-primary underline' },
  }),
  TextStyle,
  Color,
  Typography,
  Placeholder.configure({
    placeholder: 'Start writing...',
  }),
  CharacterCount.configure({
    limit: null, // No limit by default
  }),
]
