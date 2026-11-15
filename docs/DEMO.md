# Fictional demo guide

Everything in the seeded examples is fictional and for software evaluation. No production conclusion or product release is represented.

Run `python3 -m causeledger.server --demo --db data/demo.sqlite3` and open the local URL.

## Washer omission investigation

The fictional record has 60 held training assemblies, 3 missing washers, containment and disposition records, a verified occurrence cause (fixture permits assembly without washer), and a verified escape cause (rotation check passes a missing washer).

The occurrence action is a washer-presence fixture feature, labeled prevention. The escape action is a validated presence check, labeled detection. The former has fictional effectiveness results; the latter deliberately does not.

1. Select the washer case and review its single remaining closure gap.
2. Select **Close case**, enter `Demo evaluator` as recorder and a reason. Save. Expect a closure-blocked error and no new revision.
3. Select **Record evidence**. Enter title `Escape challenge follow-up`, source `Fictional training record E-09`, observation `30/30 missing-washer challenge units rejected; three subsequent training lots of 60 units each met the planned check criteria.` Save.
4. Select **Review evidence**, select that evidence, choose `accepted` and record the rationale `Fictional example; method, sample window and target reviewed for this demo.` Save.
5. Select **Record effectiveness**, select the final-inspection action, and link the accepted record. Use observation dates `2026-10-09` through `2026-10-12`, result `30/30 challenge units rejected and three training lots of 60 completed, matching the planned target and sample window.`, outcome `pass`. Save.
6. Expect no closure gaps. Select **Close case** and record a reason. Expect closed status.
7. Reopen with a reason, then withdraw the follow-up evidence with rationale `Training exercise: source record invalidated`. Expect the effectiveness gap to return.
8. Export and inspect the JSON, then use `python3 -m causeledger.verify EXPORT_PATH` to check consistency.

## Inspection lamp drift

The second case begins at problem definition. It deliberately makes no verified claim about illumination causing a missed defect. Use it to test initial containment, measurements, hypotheses and reviewer decisions.

## Screenshots and visual QA

Actual browser screenshots are pending because the available browser could not connect to the local runtime. The SVG storyboard is labeled illustrative demo material. Do not represent it as a screenshot or a passed UI test.
