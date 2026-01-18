# UI Primitives Library

A bold, arcade-inspired UI component library for QueryCraft. All components are fully typed, theme-aware, and optimized with React.memo.

## Design Philosophy

**Arcade Gaming Aesthetic** - Drawing inspiration from retro gaming arcades with neon glows, bold borders, scanline effects, and high-impact animations. The components adapt seamlessly between Core Skills (Track A) and Future Lab (Track B) themes.

## Components

### Button

Interactive button with multiple variants, sizes, and states.

**Props:**
- `variant`: `'primary' | 'secondary' | 'danger' | 'ghost'` (default: `'primary'`)
- `size`: `'sm' | 'md' | 'lg'` (default: `'md'`)
- `loading`: `boolean` (default: `false`)
- `icon`: `React.ReactNode`
- `iconPosition`: `'left' | 'right'` (default: `'left'`)
- All standard button HTML attributes

**Examples:**

```tsx
import { Button } from '@/components/ui';

// Primary button
<Button variant="primary">Submit Query</Button>

// Loading state
<Button loading>Processing...</Button>

// With icon
<Button icon={<span>🚀</span>} iconPosition="left">
  Launch
</Button>

// Danger variant
<Button variant="danger" size="lg">
  Delete Problem
</Button>

// Ghost button
<Button variant="ghost" disabled>
  Unavailable
</Button>
```

**Features:**
- Neon glow effects on hover
- Smooth scale animations
- Spinner animation during loading
- Track-specific gradient styling for Future Lab

---

### Badge

Small status indicator with color-coded variants.

**Props:**
- `variant`: `'default' | 'success' | 'error' | 'warning' | 'info'` (default: `'default'`)
- `size`: `'sm' | 'md'` (default: `'md'`)
- `onRemove`: `() => void` (optional, shows remove button)

**Examples:**

```tsx
import { Badge } from '@/components/ui';

// Status badges
<Badge variant="success">Solved</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="warning">In Progress</Badge>
<Badge variant="info">New</Badge>

// Removable tag
<Badge
  variant="default"
  size="sm"
  onRemove={() => console.log('removed')}
>
  SQL
</Badge>

// Difficulty indicator
<Badge variant="warning">Medium</Badge>
```

**Features:**
- Glowing borders with variant-specific colors
- Smooth hover lift effect
- Optional remove button with scale animation
- ARIA-compliant

---

### Card

Container component with optional slots for structured content.

**Props:**
- `header`: `React.ReactNode`
- `body`: `React.ReactNode`
- `footer`: `React.ReactNode`
- `children`: `React.ReactNode` (use when not using slots)
- `border`: `boolean` (default: `true`)
- `hover`: `boolean` (default: `false`)
- `padding`: `'none' | 'sm' | 'md' | 'lg'` (default: `'md'`)

**Examples:**

```tsx
import { Card } from '@/components/ui';

// Simple card
<Card>
  <h3>Problem Statistics</h3>
  <p>You've solved 42 problems this week.</p>
</Card>

// Card with slots
<Card
  header={<h2>Daily Challenge</h2>}
  body={
    <>
      <p>Analyze user retention for Q4 2025</p>
      <p>Difficulty: Hard</p>
    </>
  }
  footer={
    <Button variant="primary">Start Problem</Button>
  }
  hover
/>

// Borderless card with custom padding
<Card border={false} padding="lg">
  Custom content
</Card>
```

**Features:**
- Scanline overlay for retro arcade feel
- Hover effect with glow and lift animation
- Flexible slot-based or children-based content
- Track-specific gradient backgrounds

---

### Input

Form input with label, error handling, and icon support.

**Props:**
- `label`: `string`
- `error`: `string`
- `type`: `'text' | 'email' | 'password' | 'number'` (default: `'text'`)
- `prefixIcon`: `React.ReactNode`
- `suffixIcon`: `React.ReactNode`
- `disabled`: `boolean`
- All standard input HTML attributes

**Examples:**

```tsx
import { Input } from '@/components/ui';

// Basic input with label
<Input
  label="Username"
  placeholder="Enter your username"
/>

// Input with error
<Input
  label="Email"
  type="email"
  error="Invalid email format"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>

// Input with icons
<Input
  label="Search Problems"
  prefixIcon={<span>🔍</span>}
  placeholder="Type to search..."
/>

<Input
  label="Password"
  type="password"
  suffixIcon={<span>👁</span>}
/>

// Disabled state
<Input
  label="Score"
  value="1250"
  disabled
/>
```

**Features:**
- Focus glow effect with neon border
- Error state with warning icon
- Auto-styled autofill
- Custom scrollbar for number inputs
- ARIA-compliant labels and error messages

---

### Modal

Full-featured modal dialog with backdrop blur and animations.

**Props:**
- `isOpen`: `boolean` (required)
- `onClose`: `() => void` (required)
- `header`: `React.ReactNode`
- `body`: `React.ReactNode`
- `footer`: `React.ReactNode`
- `children`: `React.ReactNode` (use when not using slots)
- `closeOnBackdropClick`: `boolean` (default: `true`)
- `showCloseButton`: `boolean` (default: `true`)
- `size`: `'sm' | 'md' | 'lg' | 'xl'` (default: `'md'`)

**Examples:**

```tsx
import { Modal, Button } from '@/components/ui';
import { useState } from 'react';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>
        Show Modal
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        header={<h2>Problem Submitted</h2>}
        body={
          <>
            <p>Your solution has been submitted successfully!</p>
            <p>Score: 100/100</p>
          </>
        }
        footer={
          <Button onClick={() => setIsOpen(false)}>
            Close
          </Button>
        }
      />
    </>
  );
}

// Simple modal without slots
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  size="sm"
>
  <h3>Are you sure?</h3>
  <p>This action cannot be undone.</p>
</Modal>

// Large modal without close button
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  size="xl"
  showCloseButton={false}
  closeOnBackdropClick={false}
>
  <div>Mandatory tutorial content</div>
</Modal>
```

**Features:**
- Backdrop blur effect
- Smooth fade and scale-in animation
- ESC key to close
- Click outside to close (optional)
- Body scroll lock when open
- Portal rendering to document.body
- Responsive sizing on mobile
- Custom scrollbar for long content

---

## Design Tokens

All components use design tokens from `/frontend/src/styles/tokens/`:

### Colors (`colors.css`)
- `--accent-color`: Primary brand color (indigo)
- `--success-color`: Success state (green)
- `--error-color`: Error state (red)
- `--warning-color`: Warning state (orange)
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary`: Background hierarchy
- `--text-primary`, `--text-secondary`, `--text-muted`: Text hierarchy
- `--border-color`: Border and divider color

### Spacing (`spacing.css`)
- 4px scale: `--space-1` (4px) through `--space-24` (96px)
- Border radius: `--radius-sm` through `--radius-full`

### Typography (`typography.css`)
- Font sizes: `--font-xs` through `--font-6xl`
- Font weights: `--font-normal` through `--font-black`
- Letter spacing: `--tracking-tighter` through `--tracking-ultra`

## Theme Support

All components automatically adapt to:
- **Light/Dark mode** via `[data-theme="light"]` attribute
- **Track context** via `[data-track="future"]` attribute (Future Lab gets purple/cyan gradients)

Example:
```html
<!-- Dark mode, Core Skills -->
<body data-theme="dark" data-track="core">

<!-- Light mode, Future Lab -->
<body data-theme="light" data-track="future">
```

## Performance

All components use `React.memo` for optimized re-rendering. They only re-render when props actually change.

## Accessibility

- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation support
- Focus management
- Screen reader friendly

## Import

```tsx
// Named imports
import { Button, Badge, Card, Input, Modal } from '@/components/ui';

// With types
import type { ButtonProps, BadgeVariant, ModalProps } from '@/components/ui';
```

## Examples in Production

Check these files to see the components in action:
- `/frontend/src/pages/MainPage.tsx` - Card and Badge usage
- `/frontend/src/components/LoginModal.tsx` - Modal implementation
- `/frontend/src/components/FloatingContact.tsx` - Button variants

## Contributing

When adding new components:
1. Create `ComponentName.tsx` and `ComponentName.module.css`
2. Use design tokens from `/styles/tokens/`
3. Add theme support with `[data-theme]` and `[data-track]`
4. Export from `index.ts`
5. Document in this README
6. Use `React.memo` for optimization
