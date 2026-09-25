# Backlog alignment with the current design

This file records the local alignment review of the 31 GitHub tickets. It is
not a replacement for the GitHub issue bodies; it identifies which tickets
must be revised before implementation.

## Overall status

- Issue `#1` is closed.
- Issues `#2`–`#31` are open.
- Issues `#2`–`#15` form the core vertical slice.
- Issues `#16`–`#31` are later extensions and should not drive the initial
  SharePoint schema.

## Required revisions before implementation

| Ticket | Alignment action |
|---|---|
| #2 | Define and validate the Language catalogue and approved participant fields only. Remove Culture catalogue, Time zone catalogue, Location catalogue, culture fields, and other removed fields from the schema. The repository provides the schema, local validation/tests, Excel import support, and manual setup guidance; list creation and tenant configuration remain manual. |
| #5 | Remove “culture interests” from the current participant profile. Keep language/profile context only when separately approved; do not add unapproved fields to the current schema. |
| #6 | The current POC status choices are `Active` and `Needs review`. `Paused`, `Inactive`, and a separate “open to new connections” field require a later design decision before being added. |
| #7 | Do not require an “open to new connections” field in the current POC. Base initial eligibility on approved participant status and language/location data. |
| #13 | Define the future Groups and Group Members schema before implementing group lifecycle. Do not add culture themes or participant role fields. |
| #25 | Align tests with fields that actually exist. Tests for Paused, Inactive, or two-group behavior belong after their schema decisions are recorded. |
| #29 | Define freshness fields and status behavior in `CURRENT_DESIGN.md` before implementing tracking. In particular, decide whether `LastConfirmedAt` and `Needs confirmation` are required. |

## Compatible tickets

The following tickets do not currently contradict the agreed product boundary,
provided they use the current schema and do not reintroduce removed fields:

- #3–#4: self-registration and controlled language preferences
- #8–#12: discovery, requests, acceptance, and 1:1 tandem creation
- #14–#15: leaving a group and the active-group warning
- #16–#18: group discovery, join requests, and participant edit protection
- #19–#24: group/request permissions and notifications
- #26–#28: synthetic data, scale testing, and reproducibility
- #30–#31: reminders and admin overview after freshness behavior is defined

Tickets #13–#24 still require the future group/request lists; they must not
expand the initial Participants schema.

## PR and document gate

PR #32 must be aligned before merge because its schema currently includes the
removed catalogues and culture fields. Every later PR must link to
`CURRENT_DESIGN.md` and state which design sections it implements. A product
change must update `CURRENT_DESIGN.md` in the same PR before the schema or
ticket is changed.
