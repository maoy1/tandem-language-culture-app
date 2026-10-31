# Backlog alignment with the current design

This file records the local alignment review of the 31 GitHub tickets. It is
not a replacement for the GitHub issue bodies; it identifies which tickets
must be revised before implementation.

## Overall status

- Issues `#1`–`#3` are closed; POC-03 was merged in PR #34.
- Issue `#18` is open and moves ahead of wider testing and discovery as the access/privacy gate.
- Other ticket status must be checked on GitHub when work starts; this file records design alignment, not a live status mirror.
- Issues `#2`–`#15` form the core vertical slice.
- Issues `#16`–`#31`, except the promoted privacy work in `#18`, are later extensions and should not drive the initial
  SharePoint schema.

## Required revisions before implementation

| Ticket | Alignment action |
|---|---|
| #2 | Define and validate the Language catalogue, Time zone catalogue, and approved participant fields. Remove Culture catalogue, Location catalogue, culture fields, and other removed fields. The repository provides the schema, local validation/tests, Excel import support, and manual setup guidance; list creation and tenant configuration remain manual. |
| #3 | Use Power Apps for self-registration. Keep Participant account required, unique, and locked to the signed-in user; expose the Time zone lookup as a required catalogue dropdown. Location/city is deferred. Share through a Teams tab. Do not claim that the app filter provides SharePoint row security: the unique identity field prevents the built-in item-level permission setting. |
| #4 | Acceptance verified by the owner on 2026-10-31: save/reopen persistence, multiple Teach and Learn values, simultaneous learner/sharer use, and teach-only saving all pass. Both fields are catalogue lookups in the schema, providing identifiers for future discovery. Close on completion PR merge; #18 still gates wider testing and discovery. |
| #5 | Remove “culture interests” from the current participant profile. Keep only approved language/profile context; do not add unapproved fields to the current schema. Location/city may be considered later as an optional enhancement. |
| #6 | The current POC status choices are `Active` and `Needs review`. `Paused`, `Inactive`, and a separate “open to new connections” field require a later design decision before being added. |
| #7 | Do not require an “open to new connections” field in the current POC. Base initial eligibility on approved participant status, languages, and selected time zone. |
| #13 | Define the future Groups and Group Members schema before implementing group lifecycle. Do not add culture themes or participant role fields. |
| #18 | Parent for private self-service registration. Complete #39 (prerequisites), #40 (two-account proof), #41 (registration integration) before closing. Architecture is undecided. #42 (candidate access) is deferred to discovery #7–#9 and does not block registration completion. |
| #39 | Assessment in progress: live inherited Read/Edit list roles and existing instant-flow connection modes observed. Policy scope is hidden for non-owned environments; applicable connector policy, intended-user licensing, caller identity and self-onboarding are unverified. No approach selected; #40 cannot start. Evidence in POC_18_PARTICIPANT_ACCESS.md. |
| #40 | After #39: isolated synthetic-data proof with two normal accounts; own-record access and self-onboarding must work automatically. |
| #41 | After #40: integrate with registration, preserve data and retest; before wider testing. |
| #42 | After #41, with #7–#9: controlled candidate access without general list access or manual per-candidate grants. |
| #25 | Align tests with fields that actually exist. Tests for Paused, Inactive, or two-group behavior belong after their schema decisions are recorded. |
| #29 | Define freshness fields and status behavior in `CURRENT_DESIGN.md` before implementing tracking. In particular, decide whether `LastConfirmedAt` and `Needs confirmation` are required. |

## Compatible tickets

The following tickets do not currently contradict the agreed product boundary,
provided they use the current schema and do not reintroduce removed fields:

- #3–#4: self-registration, controlled language preferences, and the Power Apps registration form
- #8–#12: discovery, requests, acceptance, and 1:1 tandem creation
- #14–#15: leaving a group and the active-group warning
- #16–#17: group discovery and join requests
- #19–#24: group/request permissions and notifications
- #26–#28: synthetic data, scale testing, and reproducibility
- #30–#31: reminders and admin overview after freshness behavior is defined

Tickets #13–#24, except participant-only ticket #18, still require the future group/request lists; they must not
expand the initial Participants schema.

## PR and document gate

PR #32 established the manual SharePoint schema baseline. This POC-03 change
supersedes its original rich Location/derived-time-zone assumption with the
Time zone catalogue and Power Apps design. Every later PR must link to
`CURRENT_DESIGN.md` and state which design sections it implements. A product
change must update `CURRENT_DESIGN.md` in the same PR before the schema or
ticket is changed.
