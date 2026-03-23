# Design System Document

## 1. Overview & Creative North Star

This design system is engineered to bridge the gap between high-end editorial web design and the native intimacy of iOS 17. Our Creative North Star is **"The Translucent Editorial."** 

We are moving away from the rigid, grid-locked patterns of standard mobile apps toward a fluid, layered experience. By leveraging the generous whitespace and bold typography found in the source material, we create a UI that breathes. The signature look is achieved through intentional asymmetry—placing content off-center or overlapping containers—and a commitment to depth over borders. This isn't just an interface; it's a curated digital surface that feels as tactile as fine stationery and as modern as polished glass.

---

## 2. Colors & Surface Philosophy

The color palette is derived from a sophisticated interplay of deep forest greens and clinical, crisp navies, reimagined for a mobile-first environment.

### The "No-Line" Rule
To maintain a premium editorial feel, **1px solid borders are strictly prohibited for sectioning.** Boundaries must be established through tonal shifts. For instance, a `surface-container-low` card should sit on a `surface` background. If you feel the need for a line, use whitespace (`spacing-4` or higher) instead.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. We use a "stacking" logic to define importance:
- **Base Layer:** `surface` (#f9f9fe) - The canvas.
- **Secondary Level:** `surface-container-low` (#f3f3f8) - For inset content or grouped lists.
- **Interactive Level:** `surface-container-lowest` (#ffffff) - High-contrast cards that invite a touch.
- **Overlay Level:** Semi-transparent versions of `surface-bright` with a 20px-30px Backdrop Blur.

### The Glass & Gradient Rule
Floating elements (Navigation Bars, Action Sheets) must utilize **Glassmorphism**. Apply `surface-tint` with 10-15% opacity over a heavy backdrop blur. For primary Call-to-Actions (CTAs), use a subtle linear gradient from `primary` (#00523b) to `primary-container` (#1a6b51) at a 135-degree angle to provide "visual soul" and depth.

---

## 3. Typography: The Editorial Voice

We utilize **SF Pro** (or Inter as the web-fallback) to maintain the iOS 17 aesthetic while embracing high-contrast scaling.

*   **Display (Large Titles):** Use `display-lg` (3.5rem) for hero headers. This mimics the "Large Title" behavior in iOS but with tighter letter spacing (-0.02em) for a more custom, editorial look.
*   **Headlines:** `headline-lg` (2rem) serves as the primary entry point for sections. It should be bold and authoritative.
*   **Body Copy:** `body-lg` (1rem) is our workhorse. We prioritize legibility with a generous line height (1.5).
*   **Labels:** `label-md` (0.75rem) should be used in `on-surface-variant` (#3f4944) for auxiliary information, ensuring it doesn't compete with the primary narrative.

**The Typographic Hierarchy:** The brand identity is conveyed through the juxtaposition of massive `display` titles against delicate `label` text, creating a sense of luxury and space.

---

## 4. Elevation & Depth

In this system, depth is a functional tool, not just a visual flourish.

*   **The Layering Principle:** Avoid shadows where background color shifts can do the work. A `surface-container-highest` element placed on a `surface-dim` background creates natural separation without visual clutter.
*   **Ambient Shadows:** For elements that truly "float" (like a central action card), use extra-diffused shadows:
    *   *Offset:* 0px 10px
    *   *Blur:* 40px
    *   *Color:* `on-surface` (#1a1c1f) at 6% opacity.
*   **The "Ghost Border" Fallback:** If accessibility requires a container edge, use a Ghost Border: `outline-variant` (#bec9c2) at 15% opacity. Never use 100% opaque borders.
*   **Glassmorphism:** Navigation bars and tab bars must use `surface` at 80% opacity with a `blur(20px)` filter. This allows the primary green and navy accents of the content to bleed through as the user scrolls, keeping the experience integrated.

---

## 5. Components

### Cards & Lists
*   **Radii:** All cards must use `lg` (2rem / 32px) or `xl` (3rem / 48px) corner radii to mirror the organic feel of the source imagery.
*   **Separation:** Forbid divider lines. Use `spacing-3` (1rem) of vertical whitespace or a transition from `surface-container` to `surface-container-low`.

### Buttons
*   **Primary:** A gradient of `primary` to `primary-container`, rounded-full, with `on-primary` text. High-contrast and tactile.
*   **Secondary:** `surface-container-highest` background with `primary` colored text. No border.
*   **Tertiary:** Transparent background with `primary` text and a standard iOS system icon (SF Symbols style).

### Input Fields
*   **Style:** Soft, pill-shaped (`rounded-full`) or highly rounded (`rounded-lg`) containers using `surface-container-low`. 
*   **Focus State:** A 2px "Ghost Border" of `primary` at 40% opacity.

### Featured Content (Custom)
*   **Editorial Hero:** A combination of a `display-lg` title overlapping a `rounded-xl` image container. This creates the "signature" custom look that moves beyond standard app templates.

---

## 6. Do's and Don'ts

### Do
*   **Do** use the `primary-fixed-dim` (#8ad6b6) for subtle icon backgrounds to create a "tinted" native iOS look.
*   **Do** embrace asymmetry. If a headline is left-aligned, try placing the supporting body text with a slight inset.
*   **Do** use `spacing-20` (7rem) for section breaks to let the design breathe.

### Don't
*   **Don't** use pure black (#000000) for shadows. Use tinted shadows based on `on-surface`.
*   **Don't** use 1px dividers to separate list items; let the whitespace or subtle `surface` shifts define the rhythm.
*   **Don't** cram content. If it feels tight, increase the `surface-container` padding to at least `spacing-6` (2rem).
*   **Don't** use standard "Drop Shadows." If an element needs elevation, it needs "Ambient Light."