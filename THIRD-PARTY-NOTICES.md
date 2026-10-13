# Third-party notices

The project software MIT grant does not replace third-party terms. Preserve
upstream notices, including in distributions. This is an orientation inventory,
not a completed rights-clearance certificate for every asset or dependency.

## Bundled software

- Three.js and its bundled addons: MIT, copyright 2010-2025 three.js authors.
  The preserved notice is
  [docs/storyboard/vendor/three/LICENSE](https://github.com/mr-pinpin/mr-pinpin-source/blob/main/docs/storyboard/vendor/three/LICENSE).
- Leaflet: BSD 2-Clause, copyright 2010-2023 Volodymyr Agafonkin and
  2010-2011 CloudMade. Preserve its conditions and disclaimer in
  [docs/storyboard/vendor/leaflet/LICENSE](https://github.com/mr-pinpin/mr-pinpin-source/blob/main/docs/storyboard/vendor/leaflet/LICENSE).
- Lucide icons: ISC, with Feather-derived portions identified as MIT.
  Preserve the Lucide/Feather attribution and terms in
  [docs/storyboard/icons.LICENSE](https://github.com/mr-pinpin/mr-pinpin-source/blob/main/docs/storyboard/icons.LICENSE)
  and any upstream notices accompanying copied portions.

These notices also travel inside site releases alongside the bundled libraries.
The deployment repository need not vendor those libraries again. Node/Python
dependencies and hosted build actions keep their respective upstream licenses;
consult the installed versions and their notices when redistributing them.
A system-font reference does not grant a license to redistribute a font.

## Creative material and provenance

The entire docs/storyboard/gpu/** subtree (storyboard/gpu/** in site archives)
is excluded from this project's MIT grant pending documented clearance.
[Its SOURCE.md](https://github.com/mr-pinpin/mr-pinpin-source/blob/main/docs/storyboard/gpu/SOURCE.md)
records adaptation from GauchoAI/gaucho-atlas commit
d80152ea3b62b94a87d82fa37760133ccd083160 with no established upstream license.
Recorded permission to deploy is not evidence of authority to relicense it.
This uncertainty does not itself establish that the existing deployment is
unauthorized. Preserve the origin record; do not invent an upstream MIT grant.

The complete original book export, including its styling, is excluded from the
project software grant: docs/original.html and docs/images/** (original.html and
images/** in deployed archives). Character-specific procedural artwork and geometry in
scripts/blender-pinpin/** are creative content; a Python extension does not
automatically make them MIT software. That workflow also records an external
implementation reference; any copied expression needs its own permission.

External references, models, textures, images, quotations, fonts, and other
third-party material are not relicensed by this project. Neither are third-party
rights within generated outputs. Prompts, provenance, attribution, or an upload
receipt may help investigation but do not prove permission.

Some source and experimental material has incomplete ownership or licensing
evidence. Do not infer clearance from a missing notice or apply the family-use
grant to rights the project does not control. Review asset-specific records and
obtain any needed authorization before reuse or redistribution. No blanket
claim of ownership or of infringement is made by this inventory.

The source audit at tools/assets/licensing-audit.md records findings when
available; it is evidence for review, not a grant of rights. Applicable upstream
terms, valid prior grants, public-domain status, and legal exceptions prevail.
See [CONTENT-LICENSE.md](CONTENT-LICENSE.md) for the limited family-use grant.

## Fonts in new chapter PDF exports

The Scooby R6 PDF export uses Liberation Serif font subsets under SIL OFL 1.1,
with Google (2010) and Red Hat (2012) notices retained in
[the font notice](https://mr-pinpin.github.io/permissions/LIBERATION-FONTS.txt).
The font software keeps its upstream license and reserved-name conditions;
this project's MIT grant does not relicense it. This addition travels with new
reader releases; previously archived PDFs and notices are not rewritten.
