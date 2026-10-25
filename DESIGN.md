---
name: Football Intelligence Platform
description: Under the floodlights — a supporter’s working matchday hub.
colors:
  bg: "#0b1511"
  nav: "#080f0c"
  panel: "#14231b"
  raised: "#1a2c21"
  line: "#314438"
  text: "#f3f6ed"
  muted: "#b4c4b7"
  accent: "#c3ea7b"
  away: "#83a6d0"
  draw: "#b6bda7"
  danger: "#ffb3a9"
  button-ink: "#17260f"
  accent-hover: "#d3f3a2"
  nameplate: "#f2f5e9"
  nameplate-ink: "#102116"
typography:
  display:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(2.6rem, 4.2vw, 4rem)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(1.65rem, 2.5vw, 2rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "1.45rem"
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  body:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "15px"
    lineHeight: 1.55
  label:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "13px"
    fontWeight: 600
rounded:
  control: "7px"
  filter: "6px"
  menu: "10px"
  panel: "14px"
  panel-mobile: "12px"
spacing:
  compact: "8px"
  control: "12px"
  content: "18px"
  section: "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.button-ink}"
    rounded: "{rounded.control}"
    padding: "12px 19px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.button-ink}"
  button-subtle:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "12px 19px"
  input:
    backgroundColor: "{colors.nav}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  filter:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.filter}"
    padding: "9px 14px"
  forecast-panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
    padding: "26px"
  navigation:
    textColor: "{colors.muted}"
  nameplate:
    backgroundColor: "{colors.nameplate}"
    textColor: "{colors.nameplate-ink}"
    padding: "7px 10px"
---

# Design System: Football Intelligence Platform

## Overview

**Creative North Star: "Under the floodlights"**

A supporter’s working matchday hub: near-black forest surfaces, chalk text and lime actions bring fixtures and club identities into focus. Condensed football headings carry the broadcast character while readable UI text supports searches, tables and forecast explanations.

Large matchups pair real club crests and white team-name plates around a factual central information column. Stadium photography supplies atmosphere: dashboard and shared hero photography remains generic decoration, while Matches cards use mapped home-ground photographs. Neither treatment confirms a fixture’s actual venue. The same palette and type pairing extend across the public, authentication and signed-in football pages.

**Key Characteristics:**
- Dark forest surfaces with restrained lime emphasis.
- Condensed football headings and readable UI text.
- Recognisable real crests, with paired matchups retained on mobile.
- Three-way probabilities with explicit uncertainty and unavailable states.

## Colors

### Day and Night appearance

The Day/Night control extends the established matchday identity. Night retains the forest canvas, chalk copy, lime actions and floodlit stadium atmosphere. Day uses a warm chalk canvas (`#f2f4ea`), white content surfaces, deep pitch-green actions (`#315b25`), forest copy (`#17291d`) and muted green supporting text (`#4e6250`). The shared semantic roles are remapped in `stadium-appearance.css`; action ink and hover/track/inverse roles keep controls readable in both themes.

The first visit follows the system appearance. An explicit Day or Night selection persists across reloads and routes, is applied before first paint and synchronizes across tabs. Public, authentication and app navigation expose the same keyboard-accessible control. Mobile app navigation uses two rows to leave account and menu controls unobstructed. Reduced-motion preferences suppress appearance transitions.

Generic atmospheric panels use the existing floodlit photograph at night and the credited daylight Emirates photograph by day. These are decorative, not claims about the featured fixture's venue. Club-specific match cards retain their reviewed ground photo and change only the presentation overlay. White monochrome crest assets sit on a forest backing in Day mode so their original detail remains visible.

The palette resembles a floodlit pitch: forest neutrals, chalk lettering and a sharp lime accent. The frontmatter records the reused palette from the shared stylesheet; secondary values below describe roles, not extra primitives. Sidecar tonal ramps are synthesized OKLCH preview strips, not additional shipped colour tokens.

### Primary
- **Floodlight lime** (`accent`): primary actions, links, keyboard focus, leading probabilities and the home-outcome bar segment. `accent-hover` is the brighter primary-button hover.

### Secondary
- **Away blue** (`away`): away-outcome bar segment.
- **Draw grey-green** (`draw`): draw-outcome bar segment.
- **Soft danger** (`danger`): failure and error emphasis.

### Neutral
- **Pitch night** (`bg`) and **deep concourse** (`nav`): page canvas, navigation and field backgrounds.
- **Forest panel** (`panel`) and **raised forest** (`raised`): content grouping and menus/filters.
- **Boundary green** (`line`): separators and control outlines.
- **Chalk** (`text`) and **muted sage** (`muted`): main and supporting copy.
- **Nameplate chalk** (`nameplate`) and **nameplate ink** (`nameplate-ink`): club-name plates; `button-ink` keeps lime actions legible.

**The Outcome Identity Rule.** Preserve home/draw/away order and their bar colours; use lime on the leading numeric estimate without implying measured accuracy.

## Typography

**Display Font:** self-hosted Barlow Condensed, sans-serif fallback.
**Body Font:** self-hosted DM Sans, sans-serif fallback.

The condensed face gives match names, scores and headings their broadcast character. DM Sans carries navigation, labels and explanations. Font files use swap loading; Barlow Condensed ships weights 600/700/800 and DM Sans 400/500/600/700.

### Hierarchy
- **Display:** the frontmatter display role is the shared desktop h1; mobile dashboard headings use 36px.
- **Headline:** the shared h2 role; compact forecast headings override it to 30px, then 28px below the navigation breakpoint.
- **Title:** shared h3 size; weight remains component-specific rather than an invented universal token.
- **Body:** shared body role; paragraphs use 1.65 line-height and mobile body text uses 14px.
- **Label:** navigation’s observed 13px/600 role. Supporting source and outcome labels use 12px.
- **Probability figures:** Barlow Condensed 700, clamp(2.3rem, 4vw, 3.6rem), tabular numerals; compact forecasts use 40px. Match-page overrides remain local.

**The Football Voice Rule.** Use the condensed face for football headings and figures; keep controls and explanatory copy in DM Sans.

## Layout

The shared desktop container is capped at 1360px with 32px side gutters. The dashboard feature grid uses minmax(0, 2.05fr) beside minmax(310px, 1fr), separated by 24px. Reused gaps include 8px, 12px, 18px and 24px; these are observed spacing steps rather than a universal mathematical scale.

At 950px the featured workspace stacks and navigation becomes a toggle-controlled menu. At 650px dashboard gutters become 18px, the feature gap becomes 16px and the matchup retains three columns: two clubs around a 73px information column. Long names wrap rather than truncate. The club strip scrolls horizontally. Larger layout adjustments also exist at 1200px and 1600px; incumbent feature grids retain their own structural breakpoints in feature-layout.css.

## Elevation & Depth

Depth comes mainly from tonal surfaces and separators. Content panels are flat; menus alone use diffuse black shadows. The matchup combines a green darkening overlay with the stadium photograph to protect foreground legibility. There is no universal decorative card shadow.

### Shadow Vocabulary
- **Dropdown:** `0 16px 35px #0005` for search/account/notification overlays.
- **More menu:** `0 14px 30px #0005` for overflow navigation and picker menus.
- **Mobile navigation:** `0 16px 30px #0006` for the expanded menu.

**The Flat Content Rule.** Group ordinary content through forest tones and boundaries; reserve the observed shadows for floating controls.

## Shapes

Panels use softly rounded corners; controls are tighter and menus sit between them. The matchup reduces its panel radius on mobile. White team-name plates and the central lime information column retain square corners, making their broadcast geometry distinct from the surrounding panel. Crests use object-fit contain without colour-flattening filters.

## Components

### Buttons

Compact and confident: primary buttons use lime with dark ink, 44px minimum height, 13px/700 DM Sans and the frontmatter padding/radius. Hover brightens the background over 0.18s ease. Subtle buttons use transparent backgrounds with a boundary-green stroke and chalk text. Disabled buttons reduce opacity to 0.6 and use a waiting cursor. Global keyboard focus uses a 2px lime outline offset by 4px.

### Chips

Quick filters are raised-forest controls with a boundary stroke, 44px minimum height and 12px UI text. Active filters become lime with dark ink. Preserve visible labels; status indicators accompany factual fixture state.

### Cards / Containers

Forecast panels use the forest panel tone, shared panel radius and 26px padding, reduced to 24px below 950px. Ordinary feature panels use boundary strokes and no shadow. Use explicit loading, unavailable, empty and error content instead of fabricated figures.

### Inputs / Fields

Fields use deep-concourse backgrounds, chalk text, a boundary stroke and a 44px minimum height. Placeholder text is muted; caret and keyboard focus use lime. Compact navbar search has its own 42px height. Preserve those local exceptions without turning them into a second global control scale.

### Navigation

The sticky desktop header is 84px high; links use muted text, chalk hover/active text and a lime active underline. It becomes 76px high below 950px, with a two-column expanded menu. The implemented menu supports Escape and keyboard focus. Lower-priority routes remain accessible through More.

### Broadcast Matchup and Forecast

Real crests flank a factual kickoff/score, date and venue column; club names sit on chalk plates. Reviewed monochrome vectors are selected explicitly for eight mapped clubs. Others retain colour assets, then fall back to two-letter missing-image text. Compact lists keep colour crests. Never flatten detailed colour crests into white silhouettes.

Matches cards select locally hosted, freely licensed photographs through exact home-club aliases: 26 stadiums cover 27 clubs, with AC Milan and Inter sharing San Siro. A dark contrast overlay protects the foreground, and a visible stadium name links to photo credits with author, licence, source and photo date. Photos can be archival and provide home-ground context, never confirmation of a fixture’s actual venue. Unknown clubs and failed images use a neutral forest surface with an unavailable label; never substitute the away club’s ground or an unrelated stadium. Dashboard and shared hero backgrounds retain their generic decorative photography.

Outcome estimates always show home, draw and away together, a segmented bar and explanatory copy. Invalid or absent probabilities show an unavailable message. The largest individual estimate can remain below 50%; probabilities are estimates, not historical accuracy. Dedicated match pages hold the full breakdown.

## Do's and Don'ts

### Do:
- **Do** preserve real crest detail and wrap long club names.
- **Do** show all three outcome probabilities with uncertainty and source context.
- **Do** retain visible keyboard focus and reduced-motion behaviour.
- **Do** use tonal surfaces to group ordinary content.

### Don't:
- **Don't** flatten coloured crests into unreadable white silhouettes.
- **Don't** invent fixture facts, data coverage or performance claims.
- **Don't** present the decorative stadium as the fixture venue.
- **Don't** turn local layout overrides into universal design tokens.
