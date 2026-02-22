# Design: Mobile-Optimized Config Panel

**Product Review Item:** #7 — Mobile-Optimized Config Panel
**Production Queue:** Phase 8
**Priority:** MEDIUM

---

## Problem

The pitch says "manage from your phone." The config panel is desktop-oriented with
small click targets, horizontal layouts, and no touch optimization. Room builders
stand in their build holding a phone, not sitting at a desk.

---

## Design

### Responsive breakpoints

```css
/* Desktop: current layout */
@media (min-width: 769px) { /* existing styles */ }

/* Tablet: 2-column grids, larger targets */
@media (min-width: 481px) and (max-width: 768px) {
    .screen-cards { grid-template-columns: 1fr 1fr; }
    .tab-btn { min-height: 48px; font-size: 14px; }
    .scene-btn { min-height: 48px; padding: 12px 20px; }
}

/* Phone: single column, full-width elements */
@media (max-width: 480px) {
    .screen-cards { grid-template-columns: 1fr; }
    .tab-bar { overflow-x: auto; flex-wrap: nowrap; }
    .scene-bar { overflow-x: auto; }
    .modal { width: 95vw; max-height: 90vh; overflow-y: auto; }
}
```

### Key changes

1. **Scene bar scrolls horizontally** on narrow screens (already in scene quicklaunch design)
2. **Tab navigation** becomes horizontally scrollable icons on phone
3. **Screen cards** stack single-column on phone
4. **Modals** go nearly full-screen on phone
5. **Touch targets** minimum 44×44px (Apple HIG guideline)
6. **Swipeable rooms** — swipe left/right to navigate between rooms in Rooms tab
7. **Quick-action FAB** — floating action button for scene switching on mobile
8. **Pull-to-refresh** on screen list

### No separate mobile app

This is a CSS-only responsive redesign of the existing config.html — not a
separate mobile app. The same URL works on desktop and phone.

---

## Estimated effort
1-2 sessions (CSS responsive + touch targets + swipe gestures)
