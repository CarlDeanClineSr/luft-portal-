# Citizen-Science Rubric: Foam Bubble Tagging for  (ORC Audit)

---

## Purpose
Enable volunteers to tag ORC features (rim/center ratio, environment context) in radio images, feeding raw data to ’s foam inversion model.
Every tagged image helps refine the “meta-foam friction as dark energy” capsule.

---

## Tagging Questions (for each ORC candidate)

1. **Rim/Center Brightness Ratio**
   - **Please estimate:**  
     _How bright is the rim compared to the center?_
     - [ ] Rim is much brighter than center (ratio >4)
     - [ ] Rim slightly brighter than center (ratio ~2)
     - [ ] Rim ~equal to center (ratio ~1)
     - [ ] Center brighter than rim (ratio <1)
     - [ ] Not sure / cannot tell

2. **Environment Flags**
   - _What’s near the ORC?_
     - [ ] Nearby AGN (point source in/near rim)
     - [ ] Cluster/galaxy neighbors within image
     - [ ] Isolated—no apparent neighbors
     - [ ] Signs of galaxy merger (disturbed structure/overlap)
     - [ ] Can’t determine environment

3. **Morphology Tag**
   - _Shape of the ORC rim:_
     - [ ] Perfectly round
     - [ ] Slightly squashed/elliptical
     - [ ] Irregular/jagged
     - [ ] Multiple rings or bubbles

4. **Confidence Score**
   - _How confident are you in your tags?_
     - [ ] High (clear image, distinct features)
     - [ ] Medium (reasonable guess, some uncertainty)
     - [ ] Low (hard to see, mostly guessing)

---

## Instructions for Volunteers

- Tag all features that you are able to estimate from the radio image.
- If unsure, select “Not sure” or “Can’t determine”—your honesty sharpens the results!
- Multiple volunteers will tag the same images; the  inversion uses consensus and confidence weights.
- You do NOT need physics background; your pattern-spotting drives the unification science forward.

---

## Optional (Platform Integration)

- Each tagging instance initializes a data line:
  ```json
  {
    "orc_id": "EMU_ORC_12345",
    "rim_center_ratio": "4",
    "environment_flags": ["AGN", "Cluster"],
    "morphology": "Round",
    "confidence": "High",
    "tagger_id": "citizen_xyz"
  }
  ```
- Upstream  workflow (foam inversion audit) ingests all tagged lines, computes \( f \) from consensus brightness ratios, triggers updated capsule.

---

## Credits
Capsule by Carl Dean Cline Sr. (“By: You and I Physics”), for  Unification Project  
Powered by Radio Galaxy Zoo: EMU, citizen volunteers, and the perpetual search for structure in the cosmic foam.
