# AI-assisted development disclosure (starting draft for the prize narrative)

The official rules ([§3.2](https://docs.nlr.gov/docs/fy26osti/96647.pdf)) allow generative AI but require the narrative to state **the extent
to which it was used and how**; the competitor stays responsible for accuracy, authenticity and authorship. This file is a factual draft.

* **Tooling.** Arena.ai Agent Mode (several large language models) in a sandboxed checkout of this repository, with read access to the owner's
  public sibling repositories and to public web pages. It cannot sign in to DrivenData and never uploads a submission; the owner does.
* **What the AI did here.** Wrote and ran essentially all code under `src/`, `scripts/` and `tests/`; designed and executed the pre-registered
  fractional factorial and add-on experiments; built the GitHub Pages site, registries and knowledge documents; verified sources.
* **What humans did.** The owner wrote the brief, supplied the competition files through their own GitHub mirrors, ran the sibling projects whose
  rasters and scores are analysed here, and decides which file (if any) to upload.
* **Where AI judgement is most likely to be wrong.** (1) The hide-and-recover holdout is a catalogue-gap proxy, not new-fault truth; (2) the
  truth-density calibration rests on owner-reported scores that appear only in the task statement; (3) band semantics of the provided raster come
  from an owner mirror whose descriptions are demonstrably wrong for `tc`; (4) family assignments of conductivity/radiometrics are design choices.
  Each is flagged in `registry/irregularities.json`.
* **How claims are checked.** Frozen pre-registrations committed before runs, brute-force parity tests of the metric against the published equations,
  an independent plain-rasterio verifier for every shipped file, SHA-256-pinned inputs, and a rule that unknowns stay unknown.
* **Data.** Only the competition files supplied through the owner's mirrors and the public/official sources listed in `registry/sources.json`
  (USGS GeoDAWN / 3DEP derivatives, DOE GDR 1391 CC BY 4.0). Check each licence and that external data may be shared with the sponsor before the narrative.
