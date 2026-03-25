import type { Editor } from '@tiptap/core'

// Generic image upload: base64 preview → background upload → URL replace
// Works with any backend endpoint that accepts FormData and returns { url: string }
export async function uploadImage(
  editor: Editor,
  file: File,
  uploadEndpoint = '/api/upload'
): Promise<string> {
  // 1. Create base64 preview for immediate display
  const reader = new FileReader()
  const base64 = await new Promise<string>((resolve) => {
    reader.onload = () => resolve(reader.result as string)
    reader.readAsDataURL(file)
  })

  // 2. Insert preview into editor
  editor.chain().focus().setImage({ src: base64 }).run()

  // 3. Upload to server in background
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(uploadEndpoint, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`)
  }

  const { url } = await response.json()

  // 4. Replace base64 with permanent URL
  editor.chain().focus().updateAttributes('image', { src: url }).run()

  return url
}
