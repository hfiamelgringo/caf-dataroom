# Design System Specification: Architectural Institutionalism

## 1. Overview & Creative North Star: "The Digital Curator"
This design system rejects the "SaaS-template" aesthetic in favor of a bespoke, editorial experience. It is designed for high-stakes environments—development banks and high-net-worth individuals—where clarity is a form of respect and precision is the ultimate luxury. 

**Creative North Star: The Digital Curator.** 
We treat the interface like a high-end physical gallery. The layout is driven by intentional white space, rhythmic asymmetry, and "tonal layering." Instead of boxing content in, we allow the eye to be guided by the architectural weight of **Plus Jakarta Sans** and the deep, immersive quality of the primary navy base. This is not just a tool; it is a trusted advisor in digital form.

---

## 2. Colors: Tonal Depth & The Emerald Pulse
The palette is anchored in institutional stability but punctuated by a "tech-forward" emerald. 

### Core Palette
*   **Primary Base (`primary_container` #001F3F):** Our "Institutional Navy." This is the foundation of trust. It should be used for major structural backgrounds or hero moments.
*   **The Emerald Pulse (`tertiary_fixed` #9EF3D6 / `on_tertiary_container` #40957B):** Replacing the previous orange, this green represents growth, sustainability, and technological precision. Use it sparingly for high-impact CTAs and success indicators.
*   **The Neutral Surface (`surface` #F9F9FF):** A crisp, cool-toned white that prevents the deep navy from feeling claustrophobic.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders for sectioning. Structural definition must be achieved through background color shifts. To separate a sidebar from a main feed, transition from `surface` to `surface_container_low`. 

### Surface Hierarchy & Nesting
Treat the UI as physical layers of fine paper.
*   **Level 0:** `surface_container_lowest` (#FFFFFF) – The base canvas.
*   **Level 1:** `surface_container` (#ECEDF6) – Content groupings.
*   **Level 2:** `surface_container_high` (#E6E8F0) – Modals or elevated cards.

### Signature Textures & Glassmorphism
To avoid a flat "Bootstrap" feel, use **Glassmorphism** for floating navigation and top-level headers. Apply `surface` with 70% opacity and a `backdrop-blur` of 20px. This creates a sense of depth where the institutional navy can "glow" through the frosted glass of the interface.

---

## 3. Typography: Modern Architectural Feel
Typography is our primary tool for conveying authority. We pair the geometric precision of **Plus Jakarta Sans** with the humanistic clarity of **Manrope**.

*   **Display & Headlines (Plus Jakarta Sans):** These are architectural. Use `display-lg` (3.5rem) with tightened letter-spacing (-0.02em) for hero statements. This font conveys a forward-looking, structural confidence.
*   **Body & Titles (Manrope):** We use Manrope for all functional reading. Its balanced proportions ensure high readability for complex financial data.
*   **The "Hierarchy of Scale":** In editorial layouts, don't be afraid of extreme contrast. A `display-sm` headline next to a `label-md` metadata tag creates a sophisticated, "curated" look that feels more like a premium report than a generic dashboard.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are too "noisy" for this demographic. We achieve hierarchy through **Tonal Layering**.

*   **The Layering Principle:** Instead of a shadow, place a `surface_container_lowest` card on top of a `surface_container_low` background. The subtle 2% shift in brightness provides a "natural" lift.
*   **Ambient Shadows:** If a floating element (like a dropdown) requires a shadow, use a large blur (32px+) at 4% opacity, using the `on_surface` color as the shadow tint. It should look like an ambient glow, not a dark stain.
*   **The Ghost Border Fallback:** If a border is required for accessibility, use `outline_variant` at 15% opacity. If you can see the border clearly, it is too heavy. It should be felt, not seen.

---

## 5. Components: Precision & Minimalist Ritual

### Buttons (The High-Impact CTA)
*   **Primary:** Solid `primary_container` (#001F3F) with `on_primary` text. Use the `md` (0.375rem) corner radius for a sharp, tailored look.
*   **Tertiary (The "Emerald" Action):** Use a subtle gradient transition from `tertiary_fixed_dim` to `tertiary_fixed`. This adds a "jewel-like" quality that signals high value.

### Cards & Lists
*   **Forbid Dividers:** Do not use horizontal lines between list items. Use vertical white space (16px or 24px) or a subtle hover state shift to `surface_container_high`.
*   **Data Cards:** Use `surface_container_lowest` with a "Ghost Border." Align text to a strict grid, but allow images or charts to "break" the container edges for an asymmetrical, editorial feel.

### Input Fields
*   **Stateful Design:** Avoid heavy boxes. Use a "Bottom-Line-Only" approach or a very faint `surface_variant` fill. On focus, transition the bottom border to the Emerald `tertiary` (#000704) to signal "Precision Mode."

---

## 6. Do’s and Don’ts

### Do:
*   **Embrace Asymmetry:** Place a large headline on the left and a small body paragraph on the far right. The "tension" between elements creates a premium feel.
*   **Use Generous Padding:** If you think there is enough white space, add 20% more. Institutional trust is built on the luxury of "breathing room."
*   **Color as Signal:** Reserve the Emerald green exclusively for "growth," "success," or "action." If it’s everywhere, it loses its tech-forward edge.

### Don’t:
*   **No 100% Black:** Never use #000000. Use `primary` (#000613) for text to maintain the navy-tinted sophistication.
*   **No Sharp Corners:** Avoid `none` (0px) or `full` (9999px) for primary containers. Stick to the `md` (0.375rem) or `lg` (0.5rem) scale to feel architectural but approachable.
*   **No Traditional Grids:** Avoid the "3-column card row" whenever possible. Try overlapping a card 10% over a background image to create visual depth.