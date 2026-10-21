# ADR 002: Choice of Tailwind CSS and Configuration

**Status:** Accepted
**Date:** 2024-05-29

## Context

The project requires a styling solution for the Vue.js frontend that is modern, maintainable, and allows for rapid development of a professional-looking UI.

## Decision

We will use **Tailwind CSS** as our primary styling framework. The integration will be configured as follows:
1.  **`main.css`:** Use the `@import "tailwindcss";` directive for CSS injection.
2.  **`postcss.config.js`:** Standard configuration with `tailwindcss` and `autoprefixer` plugins.
3.  **`@tailwindcss/postcss`:** This compatibility package will be installed as a dev dependency to resolve potential build tool conflicts.
4.  **`tailwind.config.js`:** The `content` path will be configured to scan all `.vue` and `.ts` files within the `/src` directory.

## Consequences

*   **Pros:**
    *   Utility-first approach prevents "CSS soup" and keeps HTML as the single source of truth for styling.
    *   Rapid prototyping and consistent design.
    *   Highly optimized final CSS bundle size.
*   **Cons:**
    *   Initial setup can be complex and sensitive to the build environment, as discovered during Phase 1.
    *   Can lead to long class lists in the HTML if not managed with components.
    *   Requires developers to learn the Tailwind utility class system.