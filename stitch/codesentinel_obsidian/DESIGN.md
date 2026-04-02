# Design System Specification: The Tactical Command Interface

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Ops-Room."** This is not a standard SaaS dashboard; it is a high-fidelity tactical instrument. The goal is to move beyond "user-friendly" into "expert-authoritative." 

We break the "template" look through **Tonal Brutalism**: a philosophy where structure is defined by weight and light rather than lines. By utilizing a 4px "Micro-Radius" and high-contrast data visualization against an obsidian void, we create an environment that feels mission-critical, precise, and uncompromising. The interface should feel like a custom-built physical console—dense with information but hyper-legible under pressure.

---

## 2. Colors: The Obsidian Spectrum
Our palette is rooted in the `surface` (#131313), a deep obsidian that serves as the "void" from which all data emerges.

### The Color Roles
*   **Primary (Cyber Blue - #98CBFF):** The pulse of the system. Used for Blue Team operations, active states, and general telemetry.
*   **Secondary (Stealth Red - #FFB4AA):** High-urgency Red Team indicators. This is a "hot" color—use it sparingly to ensure it maintains its psychological impact.
*   **Tertiary (Acid Green - #2AE500):** System health and success metrics. It should vibrate against the dark background.
*   **Error / Alert (Amber/Red):** Utilizes `error` (#FFB4AB) and `secondary_container` (#C5020B) for tiered threat levels.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to section the UI. 
Boundaries must be defined through background shifts. A `surface_container_low` section sitting on a `surface` background is the only way to denote structural change. If you feel the need to "draw a line," use a `4px` vertical padding increase from the Spacing Scale instead.

### The "Glass & Gradient" Rule
To elevate CTAs, use a subtle vertical gradient from `primary` (#98CBFF) to `primary_container` (#00A3FF). For floating overlays (modals/popovers), use **Glassmorphism**: `surface_container_highest` at 60% opacity with a `24px` backdrop-blur. This ensures the "Command Center" feels layered and multidimensional.

---

## 3. Typography: Precision Hierarchy
We utilize a dual-font strategy to balance human readability with machine-driven data.

*   **Display & Headlines (Space Grotesk):** Our "Editorial" voice. Used for high-level metrics and page titles. Its geometric nature reflects the technical precision of cybersecurity.
*   **UI & Body (Inter):** The "Workhorse." Used for all functional UI, labels, and descriptions. It is neutral and highly legible at small scales.
*   **Technical Data (JetBrains Mono):** **Mandatory** for all logs, IP addresses, terminal outputs, and diff viewers. It signals to the user that they are looking at "raw" system truth.

---

## 4. Elevation & Depth: Tonal Layering
In an ultra-dark environment, traditional shadows are invisible. We use **Luminance Stacking**.

*   **The Layering Principle:** 
    *   **Level 0 (Base):** `surface` (#131313)
    *   **Level 1 (Sections):** `surface_container_low` (#1C1B1B)
    *   **Level 2 (Cards):** `surface_container` (#201F1F)
    *   **Level 3 (Interactive/Hover):** `surface_container_high` (#2A2A2A)
*   **Ambient Shadows:** For floating elements (like Tooltips), use a shadow with a `32px` blur, 8% opacity, tinted with `primary` (#98CBFF) to create a subtle blue atmospheric "glow" rather than a dark shadow.
*   **The "Ghost Border":** If a container requires definition against a similar background, use `outline_variant` at **15% opacity**. It should be felt, not seen.

---

## 5. Components: Tactical Primitives

### Buttons & Selection
*   **Primary Button:** Solid `primary` background. Sharp 4px corners (`rounded-sm`). No border.
*   **Secondary/Ghost:** `outline` (#88919D) ghost border at 20% opacity. Text in `on_surface`.
*   **Severity Pills:** Small, high-contrast badges. `secondary_container` for Critical, `on_primary_fixed_variant` for Low. Use JetBrains Mono for the text within pills.

### Data Visualization & Logs
*   **Monospaced Logs:** Background `surface_container_lowest`. Use a 1px `primary` left-border accent for the currently active log line.
*   **Circular Score Gauges:** Use `tertiary` (#2AE500) with a "Glow" effect (drop-shadow with the same color) to indicate system health.
*   **Attack Graph Nodes:** Nodes are 4px radius squares. Connections use `outline_variant` with 0.5px thickness. Active paths should "pulse" using a `primary` gradient.

### Input Fields
*   **Text Inputs:** `surface_container_low` background. No border, only a bottom-accent line (2px) that illuminates to `primary` when focused.
*   **Cards:** Forbid divider lines. Separate content using `spacing-5` (1.1rem) or by shifting from `surface_container` to `surface_container_high`.

---

## 6. Do's and Don'ts

### Do:
*   **DO** use JetBrains Mono for any string of text that is not a sentence (hashes, IDs, timestamps).
*   **DO** use "Glow Borders" for high-severity alerts. Apply a 1px `secondary` border with a `4px` outer spread of the same color at 30% opacity.
*   **DO** embrace asymmetry. In a command center, the most important data (the "Attack Vector") should take up 70% of the screen, with logs occupying a narrow 30% sidebar.

### Don't:
*   **DON'T** use standard 1px grey borders. It makes the platform look like a generic template.
*   **DON'T** use rounded corners larger than `rounded-md` (0.375rem). Soft corners kill the "Tactical" aesthetic.
*   **DON'T** use pure white (#FFFFFF) for text. Use `on_surface` (#E5E2E1) to reduce eye strain in dark environments.