# Character workflow observations — 2026-10-03

The Studio agent delivered PomPom's separate interaction page and complete Mama/Papa packages in the existing conversation. Mama and Papa each produced a solo reference sheet and a separate cast-interaction page from terse requests using Studio-supplied references. Both did so without a follow-up prompt asking for the interaction page.

These are measured task observations, **not a controlled before/after speed benchmark**. The [portable JSON record](character-latency-20261003.json) includes exact user prompts, UTC timestamps, observed image spans, final asset identities, full generation/edit prompts, input-reference hashes and Mama's correction lineage. Native binaries remain in external Studio data. The [PomPom manifest](mr-pompom-assets.json) contains its earlier package and interaction extension.

## Observed timings

All durations below are seconds from server acceptance, except image-tool active time. Final API delivery means the completed final-message event; turn completion is the subsequent completed-status event. First text is the first assistant text event, not a spinner. These are server/API observations, not browser-paint timing.

| Character | Requested scope | Image calls / repairs | First text | Image-tool active | Final API delivery | Turn complete |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Pompom | 1 interaction page | 1 / 0 | 5.694 | 85.575 | 182.677 | 182.745 |
| Mama | Solo + interaction pages | 4 / 2 | 3.909 | 172.025 | 342.477 | 342.554 |
| Papa | Solo + interaction pages | 2 / 0 | 3.736 | 82.786 | 233.202 | 233.316 |

Image-tool active time is the observed union of balanced running/completed **API event windows**. The API exposed non-overlapping intervals for these runs, but those intervals are not per-sheet call durations and do not prove sequential generation. Papa's native record starts both generation calls at approximately 09:41:14; results returned at approximately 09:41:52 and 09:42:36 while the API reported adjacent 38.751-second and 44.035-second windows. Preserve that distinction: the table reports the API active window, not the sum of concurrent native call durations or GPU-only compute time. The remaining elapsed time includes reasoning, reference inspection, shell/tools, registration and delivery; calling all of it overhead would be misleading.

Mama's initial solo sheet duplicated a three-quarter direction. The first repair fixed face/body directions but altered one expression's direction; a second repair corrected expression presentation and removed the misleading directional heading. Both intermediate images are retained in the JSON lineage. Papa used explicit screen-left/screen-right wording, had correct first-pass direction coverage, and used the prepared registration helper. The prepared helper's combined measured registration duration was 0.165059 seconds. Papa's remaining 150.529597 seconds includes reasoning, other tools, inspection and delivery, not just registration or orchestration. This is useful workflow evidence, but it does not isolate the causal effect of either change.

## Scope and clock limits

PomPom's one-page request is smaller than either two-page package. Mama and Papa have the same page count but different characters and reference packs; Mama needed two repair calls while Papa needed none. They ran sequentially in one existing thread with changing instructions/helper availability, not independent cold trials. There is no valid same-scope before/after baseline, no distribution of repeated trials, and no supported universal promise such as a thirty-minute turnaround.

The recorded engineering window began at **2026-10-03T09:28:04Z**. Through Papa's completed turn at **2026-10-03T09:43:55.599377+00:00**, it spanned **951.599 seconds**. That includes preparation and inter-run gaps, and is not any one user turn. The JSON separately records report capture and the elapsed engineering/QA window through that point; later commit/deployment work is outside that observation. The table isolates each accepted request instead of using the whole engineering session as its turnaround.

## Visual and delivery verification

PomPom: six relational scenes preserve infant/adult/older-child scale, secure holds, sibling interaction and parental handoff. Mama: final 24-study solo sheet and six-scene interaction page preserve adult identity, family scale and supported contact, including the established large Scooby. Papa: first-pass solo directions, adult identity, natural expressions and six-scene interaction page are coherent; Rabbit remains the established child peer. No material additional image correction was recommended after final visual QA.

Registered/native byte identity and full-size browser delivery are independently checked in the evidence directory `pinpin-studio-latency-20261003/`: `pompom-interactions-proof.json`, `mama-solo-proof.json`, `mama-interactions-proof.json`, `papa-solo-proof.json`, and `papa-interactions-proof.json`. Exact proof checks/timestamps are in those files. Screenshots show the existing conversation cards and original-size/Fit viewers. Registry candidate statuses remain unchanged; independent QA is not a personal review by Miguel or publication approval.

## Reuse requirements

The [canonical workflow](../character-creation.md) now requires the separate interaction page by default, compact role-bound visual references, brief natural feedback followed by actual execution, explicit screen-facing direction labels and neutral expression headings. Reuse the established character's identity rather than adding a redundant new-design approval loop. The live generic guide is synchronized to this source with its source hash recorded; character dossiers retain each run's actual provenance and decisions.

## Later toolchain improvements are not benchmarked here

After these trials, the context/helper contract gained `characterContext.registrationToolchain`, with a validated `argvPrefix` array and required `--native-path`, `--prompt-file`, `--output-name`, repeatable `--reference`, and paired `--entity`/`--stage` options. The paired options automatically retain package receipts/provenance and return `dossierPath`, removing the need for an ad hoc dossier writer; use the supplied argv rather than rediscovering paths. These hydrated-toolchain, automatic-receipt and wait-policy changes postdate Papa's run, so the timings above do not establish their latency effect; their contract tests are separate from a new measured creative run.

A subsequent live registration-only check reused Papa’s existing two images with their exact prompts and reference IDs: `--entity papa --stage solo` and `--stage interactions` produced the package JSON automatically in 0.043359 and 0.041178 seconds. Project revision, asset registry and asset bytes were unchanged (`prepared-toolchain-live-proof.json`). This validates registration/receipt behavior; it is not a new image-generation benchmark.
