# Accessibility Checklist

> WCAG 2.1 AA compliance quick reference. Concise and practical.

## Keyboard Navigation

- [ ] All interactive elements reachable via Tab
- [ ] Visible focus indicator on all focusable elements
- [ ] No keyboard traps — Esc or Tab exits any widget
- [ ] Custom components support standard key interactions (Enter, Space, Arrow keys)
- [ ] Tab order follows logical DOM order

## Screen Reader

- [ ] All images have meaningful `alt` text (or `role="presentation"` if decorative)
- [ ] Form inputs have associated `<label>` elements
- [ ] ARIA landmarks used: `<nav>`, `<main>`, `<aside>`, `role="banner"`, `role="contentinfo"`
- [ ] Dynamic content updates announced via `aria-live` regions
- [ ] Error messages associated with inputs via `aria-describedby`
- [ ] Custom widgets have correct `role`, `aria-*` states, and properties

## Visual

- [ ] Color contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] Information not conveyed by color alone (add icons, patterns, or text)
- [ ] Text can be resized up to 200% without loss of content
- [ ] Touch targets ≥ 44×44 CSS pixels

## Forms

- [ ] Required fields indicated programmatically (`aria-required="true"`)
- [ ] Validation errors are clear and actionable
- [ ] Success confirmation provided after form submission
- [ ] Autocomplete attributes on common fields (`autocomplete="email"` etc.)

## Content

- [ ] Page title is descriptive and unique
- [ ] Heading hierarchy is logical (h1 → h2 → h3, no skips)
- [ ] Link text is descriptive (not "click here")
- [ ] Language attribute set on `<html>` element
- [ ] Tables use `<th>`, `scope`, and `<caption>` where appropriate

## Common HTML Patterns

```html
<!-- Skip link -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Accessible icon button -->
<button aria-label="Close">
  <span aria-hidden="true">✕</span>
</button>

<!-- Live region for updates -->
<div aria-live="polite" aria-atomic="true">
  <!-- dynamic content -->
</div>
```

## Testing Tools

- Lighthouse Accessibility audit
- axe DevTools browser extension
- NVDA / JAWS screen reader (manual test)
- Tab key navigation test (no mouse)
- Color contrast analyzer

## Anti-Patterns

- ❌ `aria-label` on non-interactive elements
- ❌ Removing focus outlines without providing alternatives
- ❌ Using `role="alert"` on static content
- ❌ Empty buttons or links
- ❌ Auto-playing video/audio without pause control
