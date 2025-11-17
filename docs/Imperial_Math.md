# Imperial Math — Quick Reference (v0.2)

Purpose
A human-first, single-line notation to describe physical statements. Use short nouns, simple operators and finish lines with audits.

Operators
- + : add
- - : subtract
- -> : turns into / results in
- = : equals / is
- by : multiply
- per : divide
- after T: … : time step

Audits (examples)
- [count OK]
- [charge OK]
- [energy OK]
- [momentum OK]
- [foam mod active]

Core examples
- energy_of(ph) = planck by light per wavelength [audit: energy OK]
- H = 1p + 1e [count OK, charge OK]
- n -> p + e + v + energy(≈0.782 MeV) [count OK, charge OK]

Vectors
Use vector(x=…, y=…, z=…) for direction attributes.

How to read/write
- One statement per line.
- Use attributes in parentheses: e.g., ph(energy=13.6 eV)
- End with an audit tag if matter, charge or energy changed.
