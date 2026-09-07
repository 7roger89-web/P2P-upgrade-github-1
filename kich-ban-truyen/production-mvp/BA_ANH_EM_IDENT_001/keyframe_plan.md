# BA_ANH_EM_IDENT_001 — Keyframe Plan v1

Source baseline: main @ `82cca93b4883cb1d173ef275a453f88fbc65c115`

Purpose: convert the verified Story Core into the minimum visual evidence needed before any expensive video generation.

## Locked visual/story invariants

- Setting: `shallow_beach_water`.
- Đông Vũ: male, 9, glasses, responsible eldest/leader.
- Bảo Đăng: male, 5, curious explorer.
- Minh Phúc: male, 2, fearless/mischievous toddler.
- Rùa: curious troublemaker.
- Sứa: MALE, energetic/hot-tempered, blue-violet fantasy energy.
- Sam: quiet protector; protection is intentional and voluntary.
- Tone: stylized family comedy; no injury, punishment, hunting, or trophy framing.
- Logo is earned only after emotional/comedic de-escalation.

## Minimum keyframes

| KF | Time | Story beat | Required visual evidence | Primary risk |
|---|---:|---|---|---|
| KF1 | ~1.5s | B1_RUA_BITES | Brothers already visible/nearby; Rùa gives one quick readable comic bite to Sứa in shallow water | bite must not read as injury |
| KF2 | ~3.5s | B2_SUA_CHARGES | Male Sứa: pause → surprise → comic anger; unmistakable blue-violet charge | transparent/glowing subject |
| KF3 | ~5.0s | B3_SUA_RELEASES | Short energy burst aimed toward fleeing Rùa; no contact shown | energy trajectory |
| KF4 | ~6.2s | B4_SAM_BLOCKS | Sam deliberately occupies the space between Sứa and Rùa, shell facing energy, Rùa clearly protected behind Sam | hardest spatial/interaction shot |
| KF5 | ~8.5s | B5_BROTHERS_RESPOND | Đông Vũ leads/protects with glasses readable; Bảo Đăng studies Sứa curiously; Minh Phúc bonds fearlessly with Sam | six-character readability |
| KF6 | ~11.5s | B6_DEESCALATE | Rùa sheepish, Sứa calming, Minh Phúc hugging Sam, group warmth readable without dialogue | ensemble identity/occlusion |
| KF7 | ~13.5s | B7_EARNED_LOGO | Resolved tableau plus small residual blue-violet light positioned to hand off into deterministic logo graphics | logo must follow resolution |

## Generation order

Do **not** render all seven immediately.

1. Create KF4 first at low/medium resolution. It is the hardest causal/spatial frame and will expose whether Sam's intentional protection reads correctly.
2. If KF4 is visually readable, create KF2 to validate male Sứa + transparency + blue-violet energy.
3. Then create KF5 to validate all six locked characters in one composition.
4. Only after those three pass, create the remaining four keyframes.

This is fail-fast: if the three highest-risk frames cannot be locked, generating the easy frames first only wastes effort.

## KF4 acceptance criteria

KF4 PASS requires all of the following:

- Sứa is visibly male-coded according to the locked character design; no redesign.
- Sứa is the clear source of blue-violet fantasy energy.
- Sam is visibly moving/positioned **by choice** between Sứa and Rùa.
- Sam's shell is the shield surface.
- Rùa is clearly behind/under Sam's protection.
- No character appears injured.
- Shallow beach water remains readable.
- Composition is understandable with audio muted.
- No extra character/object is introduced to solve the action.
- No food-theft or chase logic reappears.

If KF4 fails only because of spatial control, escalate in this order:
`AI image/reference composition → controlled layout/depth/pose assist → deterministic blockout/composite`.

Do not default to Blender for all shots.

## Video pilot gate

The first actual video-generation pilot should be **S4 / B4_SAM_BLOCKS**, because it combines:
- three-character interaction,
- deliberate protection timing,
- blue-violet energy,
- shallow water,
- occlusion.

Video generation is intentionally **not authorized by this preproduction plan**. This file only defines the minimum evidence and pilot target.
