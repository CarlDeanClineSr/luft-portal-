# Imperial Math — Language-Agnostic Grammar

This is the canonical, text-first specification for Carl Dean Cline Sr.'s Imperial Math expression style. No poster or image is required—the engine reads the grammar directly and it works in any language.

## Core grammar
- Use `by` for multiplication and `per` for division.
- Keep physical units explicit (no hidden constants).
- Compute χ (chi) = `abs(delta_force per force_raw)`.
- Apply the χ boundary: if `chi > 0.15`, scale by `0.85`.
- Constants: `CHI_THRESHOLD = 0.15`, `CHI_SCALE_FACTOR = 0.85`.

## Reference pattern (swap nouns into your language)
```
CHI_THRESHOLD = 0.15
CHI_SCALE_FACTOR = 0.85

force = G by mass1 by mass2 per distance^2
force_raw = G by mass1 by mass2 per distance^2
chi = abs(delta_force per force_raw)
if chi > CHI_THRESHOLD:
    force = force_raw by CHI_SCALE_FACTOR
else:
    force = force_raw
```

## Examples in top world languages
- **English:** `force = G by mass1 by mass2 per distance^2`
- **Español:** `fuerza = G by masa1 by masa2 per distancia^2`
- **العربية:** `قوة = G by كتلة1 by كتلة2 per مسافة^2`
- **日本語:** `力 = G by 質量1 by 質量2 per 距離^2`
- **Русский:** `сила = G by масса1 by масса2 per расстояние^2`
- **Português:** `força = G by massa1 by massa2 per distância^2`

Use the same structure for any other language by swapping the nouns while keeping `by` and `per` as the machine-readable operators.
