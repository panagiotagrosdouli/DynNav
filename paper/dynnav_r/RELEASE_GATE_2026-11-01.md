# V3 paper — submission preflight (1 November 2026)

## Publication decision

**Candidate:** *When the Same Place Is Not the Same State: History-Conditioned Safe-Return Planning under Action-Triggered Topology Hazards*.

**State:** manuscript complete as a conference-format **candidate**, **not submitted or accepted**. The highest-confidence publishable contribution is the bounded representation result: an executed action can change later return connectivity, so geometric position alone may be insufficient when active stochastic topology hazards depend on prior traversals. The augmented-state construction itself is standard MDP Markovization; the novelty claim is the particular action-triggered stochastic return-connectivity mechanism and its controlled experimental characterization.

### Confirmed evidence available

- **Primary:** frozen 96-scenario, 250 paired seeds/scenario, same-exact-oracle state-only comparator; 0.74425 vs 0.66604 return-infeasibility; scenario-level difference -0.07821 with 95% bootstrap interval [-0.10900, -0.04983]. It improves 36/96 scenarios and is nonworse in 96/96 under the tested generator (not a universal dominance theorem).
- **Theory/mechanism:** same-endpoint history aliasing and a conditional lower bound; series-critical approximation and known joint-cut counterexample.
- **Supporting evidence:** hand-authored synthetic geometric worlds, held-out probability/horizon tests, hard-versus-soft objective negative result, ROS 2/Nav2 integration and successful protocol-valid Gazebo mechanism probes. Gazebo did not establish a stable comparative efficacy advantage.
- **Manuscript:** 8 pages in an earlier successful [Paper build run 39019793338](https://github.com/panagiotagrosdouli/DynNav/actions/runs/39019793338); 22 cited BibTeX keys matched to 22 bibliography entries on 2026-11-01. A fresh build is required for each release candidate.
- **Source of numbers:** [evidence_manifest.json](evidence_manifest.json) and [CLAIM_EVIDENCE_MATRIX.md](../../CLAIM_EVIDENCE_MATRIX.md).

### New automated gates

The paper build checks:

1. All cited bibliography keys are present, unique and used;
2. Abstract scenario counts, return-risk rates, improved/nonworse scenario counts and bootstrap interval agree with the pinned manifest;
3. No placeholder text; IEEE conference source uses anonymized author block;
4. IEEE LaTeX compilation and no unresolved references;
5. PDF exists and is at most 8 pages **for a provisional IEEE conference manuscript** (the check must be revisited if a different venue imposes different requirements).

Run locally from the repository root:

```bash
python paper/dynnav_r/check_submission.py
cd paper/dynnav_r && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Provisional venue plan (verified 1 November 2026)

- **Primary conference candidate: IROS 2027** (Florence). [IEEE RAS calendar](https://www.ieee-ras.org/event/2027-ieee-rsj-international-conference-on-intelligent-robots-and-systems-iros-70525/) lists the **1 March 2027** paper deadline. The conference's official detailed submission instructions, final page-length and video policies must be checked when released; the current 8-page IEEE draft is *not* automatically venue-compliant.
- **Journal alternative: IEEE Robotics and Automation Letters (RA-L)**, with rolling submission; its current general guidance describes six pages plus up to two paid overlength pages. A stronger reviewer-facing case and journal-specific formatting may be needed. [IEEE RA-L](https://www.ieee-ras.org/publications/ieee-robotics-and-automation-letters/).
- **ICRA 2027 is closed** to new contributed paper submissions as of this review ([official call](https://2027.ieee-icra.org/announcements/call-for-technical-papers/)). Do not imply this manuscript has been submitted there.
- Final target, author list, anonymization and any publication-fee decision require the human authors' explicit approval.

## Remaining tasks before *actual submission*

- [ ] **Human bibliography audit:** open publisher/DOI landing pages for each cited contribution, verify exact titles, author spelling, years, venues, and specific claims of novelty. A correct BibTeX key is *not* a verified scientific citation.
- [ ] **Fresh release build:** full `main` CI (Python versions, ROS, website/research portal), `Paper build`, final figure and PDF visual inspection, manuscript source SHA and artifact digest retention.
- [ ] **Security gate:** resolve production dependency audit issues in the three ancillary Next.js web apps, including current Next.js advisories, through reviewed package+lockfile changes. Never weaken security audit just to obtain green status.
- [ ] **Venue choice and policy check:** select an open conference/journal call; confirm current manuscript page/format limits, anonymization, video/data rules, author responsibilities and AI-assistance disclosure policies. No deadline is assumed in this file.
- [ ] **Human scientific review:** verify no untested generalization, confirm that the same-oracle state-only baseline is described as a restricted representation ablation, and recheck statistical units.
- [ ] **Authorship and permissions:** confirm all contributors, approval to submit, affiliations and acknowledgments; keep review copy anonymized where required.
- [ ] **Immutable release:** tag the tested commit and archive PDF, exact experiment manifests, result artifacts and relevant code/configuration before submission.

### Separate V4 research track

Belief-conditioned V4 remains a **draft follow-up**; its O2 held-out analysis is documented in [PR #205](https://github.com/panagiotagrosdouli/DynNav/pull/205). O2 does not establish operational improvement versus prior-only/detector controls. Neither that partial result nor the incomplete O0/O6/misspecification program should be silently incorporated into the **V3** submission or used to retune the frozen V3 experimental record.

**Recommendation:** prioritize a defensible V3 paper submission; decide on V4 as a separate work after frozen controls and an independent publication go/no-go review. Acceptance is determined by external peer review, not by CI success.
