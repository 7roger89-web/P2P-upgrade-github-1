"""Small deterministic design-intelligence adapter derived from the pinned upstream taxonomy."""

from copy import deepcopy

UPSTREAM_REFERENCE = {
    "name": "ui-ux-pro-max",
    "commit": "abb7f2fd5a083fa1ff55c326a963ff0d95c33f99",
    "skill_metadata_version": "2.13.0",
    "observed_tag_at_commit": "v2.14.1",
    "license": "MIT",
    "mode": "PINNED REFERENCE ADAPTER",
}

ACCESSIBILITY_RULES = {
    "contrast": "Use measured contrast evidence; target 4.5:1 for normal text and do not claim conformance without a real audit.",
    "typography_readability": "Use a readable base size, adequate line height, and semantic hierarchy; avoid text embedded only in imagery.",
    "focus": "Provide a visible focus indicator for interactive controls.",
    "keyboard": "Support keyboard operation wherever the platform and interaction model make it applicable.",
    "target_size": "Use a comfortable target of at least 44px for primary touch controls unless the platform has a documented exception.",
    "motion": "Respect reduced-motion preferences and keep transitions purposeful.",
    "semantic_structure": "Use semantic headings, landmarks, labels, and status semantics.",
    "form_errors": "Expose field labels, errors, recovery guidance, and non-color feedback.",
    "color_only": "Never make color the only carrier of status or meaning.",
    "responsive_reading": "Preserve reading order, legibility, and task completion at narrow widths.",
}

PRODUCT_PATTERNS = {
    "logistics": {
        "label": "Logistics operations",
        "user_need": "Dispatchers need to scan operational state quickly and act on exceptions with low ambiguity.",
        "ux_principles": ["operational clarity", "scannability", "exception-first prioritization", "low decoration"],
        "information_architecture": ["overview", "active operations", "exceptions", "history", "settings"],
        "visual_direction": "Calm, high-signal, operational surface with restrained decoration and strong status semantics.",
        "typography": {"family": "system-ui", "scale": "compact semantic scale", "line_height": 1.45},
        "palette": {"background": "#F7F8FA", "surface": "#FFFFFF", "text": "#16202A", "primary": "#0B6E99", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "compact-but-readable"},
        "navigation": "Persistent operational navigation with clear active state and direct exception access.",
        "components": ["data table", "status badge", "filters", "bulk action bar", "timeline", "empty state"],
        "responsive": "Desktop-first scanning with a deliberate mobile exception/action path.",
        "motion": "Short, functional state transitions; no decorative motion in high-frequency workflows.",
        "do": ["make exceptions visible", "keep columns scannable", "show freshness and ownership"],
        "dont": ["hide state in color alone", "use oversized marketing hero patterns", "turn every status into a modal"],
        "assertion_tags": ["operational", "scannable", "low_decoration"],
    },
    "interactive_narrative_game": {
        "label": "Interactive narrative game",
        "user_need": "Players need to read, feel context, and make choices without a dashboard interrupting the narrative.",
        "ux_principles": ["reading first", "immersion", "choice clarity", "contextual feedback"],
        "information_architecture": ["story scene", "choice state", "inventory or codex", "settings", "save state"],
        "visual_direction": "Immersive editorial scene with atmosphere controlled by story context, not SaaS chrome.",
        "typography": {"family": "readable editorial serif + system UI fallback", "scale": "generous reading scale", "line_height": 1.6},
        "palette": {"background": "#17131A", "surface": "#241D2A", "text": "#F8F1E8", "primary": "#D9A441", "danger": "#E36B5D", "success": "#8BCB88"},
        "spacing": {"unit_px": 8, "density": "breathing reading rhythm"},
        "navigation": "Contextual, low-chrome navigation that keeps the current scene primary.",
        "components": ["story text", "choice group", "character cue", "progress indicator", "accessible dialogue control"],
        "responsive": "Protect reading measure and choice reachability across portrait and landscape play.",
        "motion": "Slow, interruptible atmosphere where useful; always provide reduced-motion behavior.",
        "do": ["protect reading order", "make choices explicit", "use sound and motion as optional enhancement"],
        "dont": ["frame the experience as a generic admin dashboard", "bury choices in icon-only controls", "make animation required to understand text"],
        "assertion_tags": ["reading_first", "immersive", "not_dashboard"],
    },
    "ecommerce": {
        "label": "Ecommerce",
        "user_need": "Shoppers need confidence, product understanding, and a low-friction path to a trustworthy purchase.",
        "ux_principles": ["conversion with trust", "product comprehension", "reassurance", "progressive commitment"],
        "information_architecture": ["discovery", "category", "product detail", "cart", "checkout", "account"],
        "visual_direction": "Clear commercial editorial system with product focus, proof, and visible purchase state.",
        "typography": {"family": "system-ui", "scale": "confident product hierarchy", "line_height": 1.5},
        "palette": {"background": "#FCFCFA", "surface": "#FFFFFF", "text": "#1E2428", "primary": "#0E6B5B", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "comfortable catalog rhythm"},
        "navigation": "Search-led navigation with category clarity and persistent cart visibility.",
        "components": ["product card", "gallery", "price and availability", "trust proof", "cart summary", "checkout stepper"],
        "responsive": "Mobile purchase flow is first-class; preserve product proof and checkout recovery.",
        "motion": "Subtle feedback for add-to-cart and loading; never delay the purchase path.",
        "do": ["show total cost clearly", "surface returns and delivery proof", "keep purchase actions consistent"],
        "dont": ["use deceptive urgency", "hide unavailable states", "make trust claims impossible to verify"],
        "assertion_tags": ["conversion", "trust", "catalog"],
    },
    "finance_admin": {
        "label": "Finance administration",
        "user_need": "Finance operators need clear, auditable state and predictable actions with little room for ambiguity.",
        "ux_principles": ["clarity", "low ambiguity", "auditability", "reversible action"],
        "information_architecture": ["portfolio", "review queue", "records", "approvals", "audit log", "settings"],
        "visual_direction": "Precise, calm, evidence-led interface with explicit states and restrained hierarchy.",
        "typography": {"family": "system-ui", "scale": "numeric and tabular clarity", "line_height": 1.45},
        "palette": {"background": "#F5F7FA", "surface": "#FFFFFF", "text": "#182230", "primary": "#304C89", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "dense with readable row height"},
        "navigation": "Stable task navigation with visible context, filters, and audit access.",
        "components": ["review table", "approval step", "status semantics", "audit trail", "confirmation", "error recovery"],
        "responsive": "Prioritize focused review on narrow screens; never collapse critical numeric context silently.",
        "motion": "Minimal motion; state changes need clear text and persistent status.",
        "do": ["explain irreversible actions", "show timestamps and ownership", "use redundant status cues"],
        "dont": ["rely on red/green alone", "hide audit history", "use playful ambiguity for financial state"],
        "assertion_tags": ["clarity", "low_ambiguity", "audit"],
    },
    "mobile_content": {
        "label": "Mobile content",
        "user_need": "Readers need a comfortable content hierarchy, reachable controls, and predictable navigation on a small screen.",
        "ux_principles": ["content hierarchy", "readability", "reachability", "predictability"],
        "information_architecture": ["feed", "reader", "saved", "profile", "settings"],
        "visual_direction": "Content-led mobile surface with clear hierarchy and a quiet navigation frame.",
        "typography": {"family": "system-ui", "scale": "comfortable reading scale", "line_height": 1.55},
        "palette": {"background": "#FAFAF8", "surface": "#FFFFFF", "text": "#202124", "primary": "#4A55A2", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "comfortable touch rhythm"},
        "navigation": "Predictable bottom navigation with a distinct active state and no hidden core route.",
        "components": ["content card", "reader", "bottom navigation", "progress", "save action", "inline error"],
        "responsive": "Mobile-first; preserve reading order and 44px targets at narrow widths.",
        "motion": "Small feedback transitions with reduced-motion alternatives.",
        "do": ["keep content primary", "respect thumb reach", "persist reading progress"],
        "dont": ["pack controls into tiny icon clusters", "make bottom navigation shift position", "truncate essential context"],
        "assertion_tags": ["mobile_hierarchy", "readability", "bottom_navigation"],
    },
    "saas": {
        "label": "SaaS workspace",
        "user_need": "Users need to complete recurring work with a stable mental model and visible progress.",
        "ux_principles": ["workflow clarity", "progressive disclosure", "stable navigation", "feedback"],
        "information_architecture": ["home", "workspaces", "tasks", "reports", "settings"],
        "visual_direction": "Purposeful product interface with strong hierarchy and restrained utility chrome.",
        "typography": {"family": "system-ui", "scale": "semantic product scale", "line_height": 1.5},
        "palette": {"background": "#F8FAFC", "surface": "#FFFFFF", "text": "#172033", "primary": "#4657C8", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "balanced"},
        "navigation": "Stable primary navigation with contextual secondary navigation.",
        "components": ["workspace shell", "command bar", "table", "form", "toast", "empty state"],
        "responsive": "Adapt dense workflows into focused panels without hiding primary state.",
        "motion": "150–300ms purposeful transitions with reduced-motion support.",
        "do": ["show state and next action", "use semantic tokens", "keep forms recoverable"],
        "dont": ["add decorative gradients by default", "hide core actions behind novelty", "break the mental model per screen"],
        "assertion_tags": ["workflow", "progressive_disclosure", "stable_navigation"],
    },
    "dashboard": {
        "label": "Analytics dashboard",
        "user_need": "Operators need to understand the current signal, trend, and next decision at a glance.",
        "ux_principles": ["signal over decoration", "comparison", "drill-down clarity", "freshness"],
        "information_architecture": ["overview", "trend", "segments", "alerts", "detail"],
        "visual_direction": "Evidence-led data surface with a clear signal hierarchy and explicit time context.",
        "typography": {"family": "system-ui", "scale": "numeric clarity", "line_height": 1.45},
        "palette": {"background": "#F7F9FC", "surface": "#FFFFFF", "text": "#172033", "primary": "#3A67B7", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "dense but legible"},
        "navigation": "Contextual dashboard navigation with visible time range and filters.",
        "components": ["metric card", "chart", "filter bar", "data table", "alert", "drill-down"],
        "responsive": "Prioritize one decision per viewport on narrow layouts.",
        "motion": "Use motion only to show data state changes, not as decoration.",
        "do": ["label units and freshness", "provide tabular alternatives", "preserve comparison context"],
        "dont": ["use chart color without labels", "animate every data point", "hide empty or stale states"],
        "assertion_tags": ["signal", "comparison", "freshness"],
    },
    "landing_page": {
        "label": "Landing page",
        "user_need": "Visitors need to understand value, trust the offer, and take one clear next step.",
        "ux_principles": ["message clarity", "proof", "focused conversion", "scannable hierarchy"],
        "information_architecture": ["value proposition", "proof", "how it works", "objections", "call to action"],
        "visual_direction": "Editorial conversion page with one narrative spine and purposeful visual emphasis.",
        "typography": {"family": "system-ui", "scale": "high-contrast editorial scale", "line_height": 1.5},
        "palette": {"background": "#FBFBF8", "surface": "#FFFFFF", "text": "#1F2529", "primary": "#A44A2A", "danger": "#B42318", "success": "#18794E"},
        "spacing": {"unit_px": 8, "density": "generous section rhythm"},
        "navigation": "Small, predictable navigation that supports the main conversion path.",
        "components": ["hero", "proof block", "feature section", "testimonial", "FAQ", "CTA"],
        "responsive": "Keep the primary message and CTA visible and readable on narrow screens.",
        "motion": "Respectful reveal motion with reduced-motion behavior.",
        "do": ["make the promise specific", "show proof near claims", "keep one primary CTA"],
        "dont": ["use fake urgency", "stack unrelated CTAs", "hide key terms in animation"],
        "assertion_tags": ["message_clarity", "proof", "focused_conversion"],
    },
}

ALIASES = {
    "game": "interactive_narrative_game",
    "narrative_game": "interactive_narrative_game",
    "interactive narrative": "interactive_narrative_game",
    "finance": "finance_admin",
    "admin": "finance_admin",
    "mobile": "mobile_content",
    "content": "mobile_content",
    "shop": "ecommerce",
    "store": "ecommerce",
    "landing": "landing_page",
}

STACK_ADAPTATIONS = {
    "react": "Use component tokens and semantic props; keep interaction state in the component contract.",
    "nextjs": "Keep the Design System stack-neutral; map tokens to the existing app shell and preserve server/client boundaries.",
    "html-tailwind": "Map semantic tokens to CSS custom properties/utilities; do not let utility order become the Design System.",
    "vue": "Map component rules to the existing component library and keep state semantics explicit in templates.",
    "svelte": "Keep tokens in a shared CSS layer and preserve accessible state transitions across components.",
    "react-native": "Map the touch target and navigation rules to native primitives; preserve reading order and platform affordances.",
    "flutter": "Map tokens to ThemeData and platform navigation while keeping the semantic contract independent of widgets.",
    "swiftui": "Map tokens to environment styles and native navigation; preserve Dynamic Type and reduced-motion behavior.",
    "python": "No UI assumptions are applied; keep the request on the backend path unless a visual surface is explicitly added.",
    "unknown": "Unknown stack: preserve the design principle and record the implementation mapping as an owner-reviewed adaptation.",
    "generic": "Generic stack: return principle-level guidance and leave implementation mapping explicit.",
}


def normalize_product_type(value):
    raw = str(value or "saas").strip().lower().replace("-", "_")
    if raw in PRODUCT_PATTERNS:
        return raw
    return ALIASES.get(raw, "saas")


def normalize_stack(value):
    raw = str(value or "unknown").strip().lower().replace(" ", "-")
    return raw if raw in STACK_ADAPTATIONS else "unknown"


def get_pattern(product_type):
    return deepcopy(PRODUCT_PATTERNS[normalize_product_type(product_type)])


def stack_adaptation(stack):
    normalized = normalize_stack(stack)
    return {"stack": normalized, "guidance": STACK_ADAPTATIONS[normalized], "principle_preserved": True}
