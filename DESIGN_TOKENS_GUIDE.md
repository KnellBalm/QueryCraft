# Design Tokens Usage Guide

## What Are Design Tokens?

Design tokens are named entities that store visual design attributes. They're the single source of truth for design decisions, making it easy to maintain consistency and update styles across the entire application.

## Available Tokens

### Colors (`frontend/src/styles/tokens/colors.css`)

#### Background Colors
```css
--bg-primary: #0d0d1a;        /* Main background */
--bg-secondary: #0a0a12;      /* Secondary background */
--bg-tertiary: #1a1a2e;       /* Tertiary background */
--bg-dark: #0a0a12;           /* Dark background */
```

#### Text Colors
```css
--text-primary: #ffffff;      /* Primary text */
--text-secondary: #b4b4cc;    /* Secondary text */
--text-muted: #7a7a9a;        /* Muted/disabled text */
```

#### Semantic Colors
```css
--accent-color: #6366f1;      /* Primary accent (indigo) */
--success-color: #10b981;     /* Success state (green) */
--error-color: #ef4444;       /* Error state (red) */
--warning-color: #f59e0b;     /* Warning state (orange) */
```

#### Neon Colors (Arcade Theme)
```css
--neon-purple: #a855f7;
--neon-blue: #3b82f6;
--neon-green: #10b981;
```

#### Border & Effects
```css
--border-color: rgba(99, 102, 241, 0.2);
--accent-light: rgba(99, 102, 241, 0.15);
--accent-glow: rgba(99, 102, 241, 0.4);
```

---

### Spacing (`frontend/src/styles/tokens/spacing.css`)

All spacing uses a **4px base unit** for perfect alignment:

```css
--space-0: 0;           /* 0px */
--space-1: 0.25rem;     /* 4px */
--space-2: 0.5rem;      /* 8px */
--space-3: 0.75rem;     /* 12px */
--space-4: 1rem;        /* 16px */
--space-5: 1.25rem;     /* 20px */
--space-6: 1.5rem;      /* 24px */
--space-8: 2rem;        /* 32px */
--space-10: 2.5rem;     /* 40px */
--space-12: 3rem;       /* 48px */
--space-16: 4rem;       /* 64px */
--space-20: 5rem;       /* 80px */
--space-24: 6rem;       /* 96px */
```

#### Border Radius
```css
--radius-sm: 4px;
--radius-md: 6px;
--radius-lg: 8px;
--radius-xl: 10px;
--radius-2xl: 12px;
--radius-3xl: 16px;
--radius-4xl: 24px;
--radius-full: 100px;   /* Pills */
```

#### Gap Utilities
```css
--gap-xs: var(--space-1);   /* 4px */
--gap-sm: var(--space-2);   /* 8px */
--gap-md: var(--space-3);   /* 12px */
--gap-lg: var(--space-4);   /* 16px */
--gap-xl: var(--space-6);   /* 24px */
```

---

### Typography (`frontend/src/styles/tokens/typography.css`)

#### Font Sizes
```css
--font-xs: 0.65rem;     /* 10.4px - Very small labels */
--font-sm: 0.75rem;     /* 12px - Small text */
--font-base: 0.85rem;   /* 13.6px - Base text */
--font-md: 0.9rem;      /* 14.4px - Medium text */
--font-lg: 0.95rem;     /* 15.2px - Large text */
--font-xl: 1rem;        /* 16px - Extra large */
--font-2xl: 1.1rem;     /* 17.6px - Headings */
--font-3xl: 1.2rem;     /* 19.2px - Larger headings */
--font-4xl: 1.3rem;     /* 20.8px - Hero subtext */
--font-5xl: 2.5rem;     /* 40px - Hero text */
--font-6xl: 4rem;       /* 64px - Arcade title */
```

#### Font Weights
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
--font-black: 900;
```

#### Line Heights
```css
--leading-none: 1;
--leading-tight: 1.4;
--leading-normal: 1.6;
--leading-relaxed: 1.7;
```

#### Letter Spacing
```css
--tracking-tighter: -0.02em;
--tracking-tight: -0.01em;
--tracking-normal: 0;
--tracking-wide: 0.05em;
--tracking-wider: 0.08em;
--tracking-widest: 0.1em;
--tracking-ultra: 0.2em;    /* Arcade badges */
```

---

### Breakpoints (`frontend/src/styles/tokens/breakpoints.css`)

```css
--breakpoint-sm: 600px;     /* Mobile */
--breakpoint-md: 768px;     /* Tablet */
--breakpoint-lg: 1024px;    /* Small desktop */
--breakpoint-xl: 1200px;    /* Desktop */
--breakpoint-2xl: 1400px;   /* Large desktop */
```

**Usage in CSS:**
```css
@media (max-width: 600px) {
    .container {
        padding: var(--space-4);
    }
}
```

---

## Usage Examples

### Before & After Migration

#### Example 1: Card Component
```css
/* ❌ Before - Hardcoded values */
.card {
    padding: 1.25rem 1.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    font-weight: 700;
}

/* ✅ After - Using tokens */
.card {
    padding: var(--space-5) var(--space-6);
    border-radius: var(--radius-3xl);
    margin-bottom: var(--space-6);
    font-size: var(--font-base);
    font-weight: var(--font-bold);
}
```

#### Example 2: Button Spacing
```css
/* ❌ Before */
.button {
    padding: 0.5rem 1.25rem;
    gap: 0.5rem;
    font-size: 0.85rem;
}

/* ✅ After */
.button {
    padding: var(--space-2) var(--space-5);
    gap: var(--space-2);
    font-size: var(--font-base);
}
```

#### Example 3: Responsive Layout
```css
/* ❌ Before */
.arcade-container {
    gap: 1.5rem;
    padding: 2rem;
}

@media (max-width: 1200px) {
    .arcade-container {
        gap: 1rem;
    }
}

@media (max-width: 600px) {
    .arcade-container {
        padding: 1rem;
    }
}

/* ✅ After */
.arcade-container {
    gap: var(--space-6);
    padding: var(--space-8);
}

@media (max-width: 1200px) {
    .arcade-container {
        gap: var(--space-4);
    }
}

@media (max-width: 600px) {
    .arcade-container {
        padding: var(--space-4);
    }
}
```

---

## Best Practices

### 1. Always Use Tokens for Common Values

✅ **DO:**
```css
.element {
    padding: var(--space-4);
    font-size: var(--font-base);
    color: var(--text-primary);
}
```

❌ **DON'T:**
```css
.element {
    padding: 1rem;
    font-size: 0.85rem;
    color: #ffffff;
}
```

### 2. Use Semantic Color Names

✅ **DO:**
```css
.success-message {
    color: var(--success-color);
}
```

❌ **DON'T:**
```css
.success-message {
    color: var(--neon-green);  /* Use semantic name instead */
}
```

### 3. Stick to the Spacing Scale

✅ **DO:**
```css
.element {
    margin: var(--space-4) var(--space-6);  /* 16px 24px */
}
```

❌ **DON'T:**
```css
.element {
    margin: 1.3rem 1.8rem;  /* Off scale */
}
```

### 4. Use Border Radius Tokens

✅ **DO:**
```css
.card {
    border-radius: var(--radius-3xl);  /* 16px */
}
```

❌ **DON'T:**
```css
.card {
    border-radius: 16px;
}
```

---

## Common Patterns

### Card Pattern
```css
.card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-3xl);
    padding: var(--space-5);
}
```

### Button Pattern
```css
.button {
    padding: var(--space-2) var(--space-5);
    border-radius: var(--radius-md);
    font-size: var(--font-base);
    font-weight: var(--font-semibold);
}
```

### Badge Pattern
```css
.badge {
    font-size: var(--font-xs);
    font-weight: var(--font-bold);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
}
```

### Panel Pattern
```css
.panel {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-3xl);
    padding: var(--space-5);
}

.panel-title {
    font-size: var(--font-md);
    font-weight: var(--font-bold);
    margin-bottom: var(--space-4);
    padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--border-color);
}
```

---

## Dark/Light Mode Support

All color tokens automatically adapt to theme changes via the `[data-theme="light"]` selector.

**How it works:**
```css
:root {
    --bg-primary: #0d0d1a;  /* Dark mode */
}

[data-theme="light"] {
    --bg-primary: #ffffff;  /* Light mode */
}
```

**No changes needed in components:**
```css
.element {
    background: var(--bg-primary);
    /* Automatically switches between dark/light */
}
```

---

## Future Enhancements

Potential additions to the token system:

1. **Animation Tokens**
   - `--duration-fast: 150ms`
   - `--duration-normal: 300ms`
   - `--easing-default: ease-in-out`

2. **Shadow Tokens**
   - `--shadow-sm`, `--shadow-md`, `--shadow-lg`

3. **Z-index Tokens**
   - `--z-dropdown: 1000`
   - `--z-modal: 2000`

4. **Container Tokens**
   - `--container-sm: 640px`
   - `--container-md: 768px`

---

## Migration Checklist

When migrating existing CSS to tokens:

- [ ] Replace hardcoded spacing with `--space-*`
- [ ] Replace font-sizes with `--font-*`
- [ ] Replace font-weights with `--font-*`
- [ ] Replace colors with semantic color tokens
- [ ] Replace border-radius with `--radius-*`
- [ ] Replace letter-spacing with `--tracking-*`
- [ ] Test in both light and dark modes
- [ ] Test at all breakpoints
- [ ] Verify no visual regressions

---

## Questions?

If you need a token that doesn't exist:
1. Check if an existing token can work
2. Propose a new token in the appropriate file
3. Follow the naming convention
4. Document the use case
