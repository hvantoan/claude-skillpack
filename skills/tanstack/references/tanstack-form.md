# TanStack Form — Complete Reference

## Setup
```bash
npm i @tanstack/react-form
npm i zod  # optional, v1+ passes schemas directly — no adapter needed
```

## 1. useForm — Create a form
```tsx
import { useForm } from '@tanstack/react-form'

const form = useForm({
  defaultValues: { name: '', email: '', tags: [] as string[] },
  validators: {
    onChange: ({ value }) => (!value.name ? 'Name required' : undefined),
    onSubmit: zodSchema,  // pass Zod schema directly
  },
  onSubmit: async ({ value, formApi }) => {
    try { await api.save(value); formApi.reset() }
    catch (err) { return { email: 'Already exists' } } // server errors → fields
  },
  asyncDefaultValues: async () => await api.fetchData(id), // load data for edit mode
  listeners: { country: () => form.setFieldValue('province', '') }, // linked fields
})
```

## 2. form.Field — Render prop for each field
```tsx
<form.Field
  name="email"
  validators={{
    onChange: ({ value }) => (!value.includes('@') ? 'Invalid email' : undefined),
    onChangeAsync: async ({ value }) => (await checkEmail(value)) ? 'Already taken' : undefined,
  }}
  asyncDebounceMs={500}
>
  {(field) => (
    <div>
      <input
        value={field.state.value}
        onChange={(e) => field.handleChange(e.target.value)}
        onBlur={field.handleBlur}
      />
      {field.state.meta.isTouched && field.state.meta.errors[0] && (
        <span className="text-red-500">{field.state.meta.errors[0]}</span>
      )}
    </div>
  )}
</form.Field>
```

## 3. Validation — Types of validators
| Event | When | Async variant | Use case |
|-------|------|---------------|----------|
| `onChange` | Every change | `onChangeAsync` | Format, length |
| `onBlur` | Loses focus | `onBlurAsync` | Required, server checks |
| `onSubmit` | Form submit | `onSubmitAsync` | Final validation |

Debounce: `asyncDebounceMs={500}`. Accepts inline function OR Zod/Valibot schema.

**Zod schema validation:**
```tsx
const schema = z.object({ title: z.string().min(5), email: z.string().email() })
const form = useForm({
  defaultValues: { title: '', email: '' },
  validators: { onChange: schema, onSubmit: schema },
})
```

**Cross-field validation (e.g. password confirm):**
```tsx
<form.Field name="confirmPassword"
  onChangeListenTo={['password']}  // auto re-validate when password changes
  validators={{ onChange: ({ value, formApi }) =>
    value !== formApi.getFieldValue('password') ? 'Passwords do not match' : undefined
  }}
>{(field) => <input type="password" value={field.state.value} ... />}</form.Field>
```

## 4. form.Subscribe & useStore — Watching form state
```tsx
// Subscribe: only re-renders inside, does NOT re-render parent component
<form.Subscribe selector={(s) => [s.canSubmit, s.isSubmitting]}>
  {([canSubmit, isSubmitting]) => (
    <button disabled={!canSubmit} onClick={() => form.handleSubmit()}>
      {isSubmitting ? 'Saving...' : 'Save'}
    </button>
  )}
</form.Subscribe>

// useStore: use in JS logic (DOES re-render the component)
const isDirty = form.useStore((s) => s.isDirty)  // always use a selector
const allState = form.useStore()                   // never do this — re-renders on ANY change
```

**Selector properties:** `canSubmit`, `isSubmitting`, `isDirty`, `isFieldsValid`, `isValidating`, `isLoading`, `values`, `errorMap`

## 5. Nested & Array Fields
```tsx
// Nested object: use dot notation
<form.Field name="address.city">{(f) => <input value={f.state.value} ... />}</form.Field>

// Array: mode="array"
<form.Field name="tags" mode="array">
  {(field) => (<>
    {field.state.value.map((_, i) => (
      <form.Field key={i} name={`tags[${i}]`}>
        {(sub) => (<div>
          <input value={sub.state.value} onChange={(e) => sub.handleChange(e.target.value)} />
          <button onClick={() => field.removeValue(i)}>Remove</button>
        </div>)}
      </form.Field>
    ))}
    <button onClick={() => field.pushValue('')}>Add</button>
  </>)}
</form.Field>
```
Array methods: `pushValue`, `removeValue`, `insertValue`, `replaceValue`, `swapValues`, `moveValue`, `clearValues`

## 6. Form Composition — Splitting forms into child components

**DO NOT pass form as prop** (complex generics). Use the Context API instead:

```tsx
import { createFormHookContexts, createFormHook } from '@tanstack/react-form'

// Step 1: Create contexts + hook (typically in shared/form-hook.ts)
const { fieldContext, formContext } = createFormHookContexts()
export const { useAppForm } = createFormHook({
  fieldContext, formContext,
  fieldComponents: { TextField, SelectField },
  formComponents: { SubmitButton },
})

// Step 2: Custom field component — uses useFieldContext (no props needed)
function TextField({ label }: { label: string }) {
  const field = useFieldContext<string>()
  return (<div>
    <label>{label}</label>
    <input value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} />
    {field.state.meta.isTouched && field.state.meta.errors[0] && <span>{field.state.meta.errors[0]}</span>}
  </div>)
}

// Step 3: Use in forms
function UserForm() {
  const form = useAppForm({
    defaultValues: { name: '', email: '' },
    onSubmit: async ({ value }) => await api.saveUser(value),
  })
  return (<form.AppForm>
    <form.AppField name="name" children={() => <TextField label="Name" />} />
    <form.AppField name="email" children={() => <TextField label="Email" />} />
    <SubmitButton />
  </form.AppForm>)
}
```

### Fallback: Passing form as prop with `typeof` inference

If Context API is overkill (e.g. one-off child), use `ReturnType<typeof>` instead of importing `ReactFormExtendedApi` (requires too many generics):

```tsx
// ❌ Don't — ReactFormExtendedApi needs massive generic list
import { ReactFormExtendedApi } from '@tanstack/react-form'
function Child({ form }: { form: ReactFormExtendedApi<MyData, any, any...> }) { ... }

// ✅ Do — infer exact type from your hook
function useMyForm() {
  return useForm({ defaultValues: { username: '' }, onSubmit: async ({ value }) => {} })
}
type MyFormInstance = ReturnType<typeof useMyForm>

function Child({ form }: { form: MyFormInstance }) {
  return <form.Field name="username">{(f) => <input value={f.state.value} ... />}</form.Field>
}
```

## 7. TanStack Query Integration — Fetch → Form → Mutate
```tsx
function EditUserForm({ userId }) {
  const queryClient = useQueryClient()
  const { data: user, isLoading } = useQuery({ queryKey: ['user', userId], queryFn: () => fetchUser(userId) })
  const mutation = useMutation({
    mutationFn: (values) => updateUser(userId, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['user', userId] }),
  })
  const form = useAppForm({
    defaultValues: user ?? { name: '', email: '' },
    onSubmit: async ({ value }) => mutation.mutateAsync(value),
  })
  if (isLoading) return <Skeleton />
  return (<form.AppForm>
    <form.AppField name="name" children={() => <TextField label="Name" />} />
    <SubmitButton />
  </form.AppForm>)
}
```

## 8. MUI Integration
```tsx
<form.Field name="title" validators={{ onChange: ({ value }) => !value ? 'Required' : undefined }}>
  {(field) => (
    <MuiTextField label="Title" value={field.state.value}
      onChange={(e) => field.handleChange(e.target.value)} onBlur={field.handleBlur}
      error={field.state.meta.isTouched && !field.state.meta.isValid}
      helperText={field.state.meta.isTouched ? field.state.meta.errors[0] : ''} />
  )}
</form.Field>
```

## Quick Reference

**Field state:** `field.state.value`, `.meta.errors`, `.meta.isTouched`, `.meta.isValid`, `.meta.isDirty`, `.meta.isValidating`

**Form methods:** `handleSubmit()`, `reset()`, `validate()`, `getFieldValue(name)`, `setFieldValue(name, v)`, `getValues()`

| Need | API |
|------|-----|
| Create a basic form | `useForm()` |
| Render a field | `form.Field` render prop |
| Submit button / form state | `form.Subscribe` |
| Use state in component logic | `form.useStore((s) => s.field)` |
| Split form into child components | `createFormHook` + `useFieldContext` |
| Pass form as prop (fallback) | `ReturnType<typeof useMyForm>` |
| Cross-field validation | `onChangeListenTo` |
| Load data from API | TanStack Query → `defaultValues` |
| Submit + invalidate cache | `useMutation` + `queryClient.invalidateQueries` |
