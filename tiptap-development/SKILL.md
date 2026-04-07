---
name: tiptap-development
description: 'Develops TipTap v3 rich text editors with Vue 3. Activates when creating or modifying TipTap editor components, extensions, node views, or mark views; working with ProseMirror JSON, generateHTML, or generateJSON; building toolbars, bubble menus, or floating menus; implementing custom commands, input rules, or paste rules; or when the user mentions TipTap, ProseMirror, rich text editor, or content editor.'
---

# TipTap v3 Development

## When to Apply

Activate this skill when:

- Creating or modifying TipTap editor components
- Working with ProseMirror JSON content (reading, writing, manipulating)
- Building custom extensions (nodes, marks, functionality)
- Implementing toolbars, bubble menus, or floating menus
- Using `generateHTML()` or `generateJSON()` for content rendering
- Working with editor commands, input rules, or paste rules
- Building custom node views or mark views with Vue components

## Reference Documentation

Full internal reference: `docs/references/tiptap-v3-reference.md` — read this for detailed coverage of all APIs, extension methods, and migration notes.

### Official Docs (deep dive when the skill doesn't cover enough)

- **Editor API:** https://tiptap.dev/docs/editor/api/editor
- **Commands:** https://tiptap.dev/docs/editor/api/commands
- **Extensions overview:** https://tiptap.dev/docs/editor/extensions/overview
- **Custom extensions:** https://tiptap.dev/docs/editor/extensions/custom-extensions/create-new
- **Node views (Vue):** https://tiptap.dev/docs/editor/extensions/custom-extensions/node-views/vue
- **BubbleMenu:** https://tiptap.dev/docs/editor/extensions/functionality/bubble-menu
- **FloatingMenu:** https://tiptap.dev/docs/editor/extensions/functionality/floatingmenu
- **HTML utility:** https://tiptap.dev/docs/editor/api/utilities/html
- **v2 → v3 migration:** https://tiptap.dev/docs/guides/upgrade-tiptap-v2
- **Performance:** https://tiptap.dev/docs/guides/performance
- **ProseMirror concepts:** https://tiptap.dev/docs/editor/core-concepts/prosemirror

## Installed Packages (v3.20.x)

```
@tiptap/starter-kit
@tiptap/vue-3
@tiptap/extension-link
@tiptap/extension-placeholder
@tiptap/extension-table (+ table-cell, table-header, table-row)
@tiptap/extension-text-align
@tiptap/html
```

## Critical Rules

### SSR Safety

This app uses Inertia.js SSR. TipTap requires browser APIs.

```ts
// REQUIRED: Prevent server-side rendering attempts
const editor = useEditor({
  immediatelyRender: false, // ALWAYS set this
  extensions: [StarterKit],
  content: props.modelValue ?? undefined,
});

// Guard editor access - it's undefined on the server
const isBold = computed(() => editor.value?.isActive('bold') ?? false);
```

### Import Paths (v3 Breaking Change)

```ts
// Main exports
import { EditorContent, useEditor, VueNodeViewRenderer, VueMarkViewRenderer } from '@tiptap/vue-3';

// Menus are a SEPARATE subpath in v3
import { BubbleMenu, FloatingMenu } from '@tiptap/vue-3/menus';

// HTML utilities
import { generateHTML, generateJSON } from '@tiptap/html';
// For Node.js/SSR contexts:
import { generateHTML, generateJSON } from '@tiptap/html/server'; // requires happy-dom
```

### StarterKit v3 Includes

StarterKit now bundles more than v2. These are included by default:

- **Nodes:** Document, Paragraph, Text, Heading, Blockquote, CodeBlock, BulletList, OrderedList, ListItem, HardBreak, HorizontalRule
- **Marks:** Bold, Italic, Strike, Code, **Link** (new), **Underline** (new)
- **Functionality:** Dropcursor, Gapcursor, **UndoRedo** (renamed from `history`), ListKeymap, **TrailingNode** (new)

```ts
// Disable or configure any StarterKit extension
StarterKit.configure({
  heading: { levels: [2, 3] },
  codeBlock: false,
  undoRedo: false, // NOT 'history' (v2 name)
  link: false, // if using custom Link config
});
```

### Content Format

Store content as **ProseMirror JSON** (not HTML). JSON is the canonical format.

```ts
// Reading content
const json = editor.getJSON();
const html = editor.getHTML();
const text = editor.getText({ blockSeparator: '\n\n' });

// Setting content
editor.commands.setContent(json); // or HTML string
// v3 signature (options object, not positional args):
editor.commands.setContent(content, { emitUpdate: false, parseOptions: {} });
```

### Extension Matching

`generateHTML()` and `generateJSON()` must receive the **same extensions** used by the editor. Missing extensions cause nodes/marks to be **silently dropped**.

```ts
// Define shared extension list once
const editorExtensions = [
  StarterKit.configure({ heading: { levels: [2, 3] } }),
  Table.configure({ resizable: false }),
  TableRow,
  TableCell,
  TableHeader,
  TextAlign.configure({ types: ['heading', 'paragraph'] }),
];

// Use in both editor and HTML generation
const editor = useEditor({ extensions: editorExtensions });
const html = generateHTML(json, editorExtensions);
```

## Commands

### Chain API (Preferred)

Always use the chain API for user-initiated actions. `focus()` ensures the editor regains focus after toolbar clicks.

```ts
// GOOD: Single transaction, maintains focus
editor.chain().focus().toggleBold().run();
editor.chain().focus().deleteRange({ from, to }).insertContentAt(from, html).run();

// BAD: Multiple transactions (each triggers re-render)
editor.commands.deleteRange({ from, to });
editor.commands.insertContentAt(from, html);
```

### Checking Command Availability

Use `can()` for toolbar button disabled states:

```ts
const canUndo = editor.can().undo();
const canBold = editor.can().chain().toggleBold().run();
```

### Content Insertion

`insertContent` and `insertContentAt` accept HTML strings, JSON, or plain text:

```ts
// HTML string (parsed by TipTap into ProseMirror nodes)
editor.chain().focus().insertContent('<p>Hello <strong>world</strong></p>').run();

// JSON content
editor
  .chain()
  .focus()
  .insertContent({
    type: 'paragraph',
    content: [{ type: 'text', text: 'Hello' }],
  })
  .run();

// At specific position without moving cursor
editor.chain().insertContentAt(pos, html, { updateSelection: false }).run();
```

### Key Content Commands

| Command                                   | Description             |
| ----------------------------------------- | ----------------------- |
| `setContent(content, options?)`           | Replace entire document |
| `insertContent(content, options?)`        | Insert at cursor        |
| `insertContentAt(pos, content, options?)` | Insert at position      |
| `deleteRange({ from, to })`               | Delete content range    |
| `clearContent(emitUpdate?)`               | Clear document          |

## Working with the Document

### Walking Nodes

```ts
// Walk all nodes
editor.state.doc.descendants((node, pos) => {
  if (node.type.name === 'heading' && node.attrs.level === 2) {
    console.log(node.textContent, 'at', pos);
  }
});

// Utility functions from @tiptap/core
import { findChildren, findParentNode } from '@tiptap/core';

const headings = findChildren(editor.state.doc, node => node.type.name === 'heading');
const parentList = findParentNode(node => node.type.name === 'bulletList')(editor.state.selection);
```

### Selection and Positions

```ts
const { from, to } = editor.state.selection;
const selectedText = editor.state.doc.textBetween(from, to);

// Resolved positions know their context
const $from = editor.state.selection.$from;
$from.parent; // parent node
$from.depth; // nesting depth
$from.node(depth); // ancestor at depth
```

### Active State Checking

```ts
editor.isActive('bold');
editor.isActive('heading', { level: 2 });
editor.isActive({ textAlign: 'center' });
```

## BubbleMenu and FloatingMenu

```ts
import { BubbleMenu, FloatingMenu } from '@tiptap/vue-3/menus';
```

**BubbleMenu** appears when text is selected. **FloatingMenu** appears on empty lines.

```vue
<BubbleMenu
  v-if="editor"
  :editor="editor"
  :should-show="({ from, to }) => from !== to"
  :options="{ placement: 'top', offset: { mainAxis: 8 } }"
>
  <button @click="editor.chain().focus().toggleBold().run()">Bold</button>
</BubbleMenu>
```

Key props: `editor` (required), `shouldShow` (filter function), `updateDelay` (default 250ms), `options` (Floating UI config), `pluginKey` (for multiple menus).

Both use `@floating-ui/dom` for positioning. Do NOT register BubbleMenu/FloatingMenu extensions separately when using these components.

## Custom Extensions

### Three Types

1. `Extension.create()` -- Functionality only (no schema). Keyboard shortcuts, plugins, commands.
2. `Node.create()` -- Adds a node type (paragraphs, callouts, embeds).
3. `Mark.create()` -- Adds a mark type (highlights, spoilers, custom formatting).

### Extension Method Reference

| Method                         | Purpose                                 |
| ------------------------------ | --------------------------------------- |
| `addOptions()`                 | Default configuration                   |
| `addStorage()`                 | Mutable extension state                 |
| `addAttributes()`              | Schema attributes                       |
| `addCommands()`                | Editor commands                         |
| `addKeyboardShortcuts()`       | Keyboard bindings                       |
| `addInputRules()`              | Type-triggered transforms               |
| `addPasteRules()`              | Paste-triggered transforms              |
| `addNodeView()`                | Custom Vue rendering for nodes          |
| `addMarkView()`                | Custom Vue rendering for marks (v3 new) |
| `addProseMirrorPlugins()`      | Raw PM plugins                          |
| `addGlobalAttributes()`        | Attributes on other extensions          |
| `parseHTML()` / `renderHTML()` | HTML parsing and serialization          |

### Extending Existing Extensions

```ts
import Link from '@tiptap/extension-link';

const CustomLink = Link.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      rel: { default: 'noopener noreferrer nofollow' },
    };
  },
});
```

### Priority

Default is 100. Higher = processed first:

```ts
const MyExtension = Extension.create({
  name: 'myExtension',
  priority: 1000,
});
```

## Vue Node Views

Render Vue components inside the editor for custom block types:

```ts
// In the extension
addNodeView() {
  return VueNodeViewRenderer(MyComponent);
}
```

```vue
<script setup lang="ts">
import { NodeViewWrapper, NodeViewContent, nodeViewProps } from '@tiptap/vue-3';

const props = defineProps(nodeViewProps);
// props.editor, props.node, props.selected, props.getPos,
// props.updateAttributes, props.deleteNode
</script>

<template>
  <NodeViewWrapper as="div">
    <NodeViewContent as="p" />
  </NodeViewWrapper>
</template>
```

Rules:

- Must use `NodeViewWrapper` as root
- Use `NodeViewContent` where editable content renders
- For non-editable (atom) nodes, omit `NodeViewContent`
- Use `contenteditable="false"` on non-editable sections

## Vue Mark Views (v3 New)

```ts
addMarkView() {
  return VueMarkViewRenderer(MyMarkComponent);
}
```

```vue
<script setup lang="ts">
import { MarkViewContent, markViewProps } from '@tiptap/vue-3';

const props = defineProps(markViewProps);
</script>

<template>
  <span v-bind="props.HTMLAttributes">
    <MarkViewContent as="span" />
  </span>
</template>
```

## Events

### Editor-level Callbacks

```ts
const editor = useEditor({
  onUpdate: ({ editor, transaction }) => {
    if (transaction.docChanged) {
      // Content actually changed (not just selection)
      emit('update:modelValue', editor.getJSON());
    }
  },
  onSelectionUpdate: ({ editor }) => {
    /* ... */
  },
  onFocus: ({ editor, event }) => {
    /* ... */
  },
  onBlur: ({ editor, event }) => {
    /* ... */
  },
});
```

### Dynamic Event Subscription

```ts
editor.on('update', handler);
editor.once('create', handler);
editor.off('update', handler);
```

### v3 New Events

`onBeforeTransaction`, `onPaste`, `onDrop`, `onDelete`, `onMount`, `onUnmount`, `onContentError`

## Available First-Party Extensions (Not Installed)

Consider these when features are needed:

| Extension               | Package                                 | What It Does                |
| ----------------------- | --------------------------------------- | --------------------------- |
| Image                   | `@tiptap/extension-image`               | `<img>` blocks              |
| TaskList + TaskItem     | `@tiptap/extension-task-list`           | Checkbox lists              |
| Mention                 | `@tiptap/extension-mention`             | @-mentions with suggestions |
| Highlight               | `@tiptap/extension-highlight`           | Text highlighting           |
| CharacterCount          | `@tiptap/extension-character-count`     | Character/word counting     |
| Color + TextStyle       | `@tiptap/extension-color`               | Text color                  |
| FontFamily + TextStyle  | `@tiptap/extension-font-family`         | Font selection              |
| Typography              | `@tiptap/extension-typography`          | Smart quotes, em-dashes     |
| Subscript / Superscript | `@tiptap/extension-subscript`           | Sub/superscript text        |
| YouTube                 | `@tiptap/extension-youtube`             | YouTube embeds              |
| CodeBlockLowlight       | `@tiptap/extension-code-block-lowlight` | Syntax highlighting         |
| Collaboration           | `@tiptap/extension-collaboration`       | Real-time editing via Yjs   |

## Performance

- Chain commands into single transactions (avoid multiple `.run()` calls)
- Use `{ updateSelection: false }` when inserting content without moving cursor
- Use `onUpdate` with `transaction.docChanged` to avoid saving on selection-only changes
- Debounce auto-save -- don't save on every keystroke
- `useEditor()` auto-destroys on unmount; manual `new Editor()` requires `editor.destroy()`
- Documents with 1500+ nodes can degrade; consider pagination for very large content

## Built-in Markdown Shortcuts (via StarterKit)

| Input        | Result          |
| ------------ | --------------- |
| `# `         | Heading 1       |
| `## `        | Heading 2-6     |
| `> `         | Blockquote      |
| `- ` or `* ` | Bullet list     |
| `1. `        | Ordered list    |
| ` ``` `      | Code block      |
| `---`        | Horizontal rule |
| `**text**`   | Bold            |
| `*text*`     | Italic          |
| `` `text` `` | Inline code     |
| `~~text~~`   | Strikethrough   |
