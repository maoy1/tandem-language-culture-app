# Mandatory project constraints

- Production runs only in SharePoint and the associated Power Apps / Power Automate services covered by existing organisational entitlements.
- No additional budget: do not introduce paid hosting, Azure Functions, external APIs/services, premium/custom connectors, new paid licences or trials as an implementation dependency.
- No Python server, local computer, scheduled local script or separately hosted runtime may be required by the deployed participant workflow. Python is permitted for optional local repository validation/tests only.
- Participant registration, updates, discovery, connection and group actions must be self-service. No routine admin approvals, individual permission grants, manual matching or manual user/group maintenance.
- Before relying on any permission, setting, connection, connector, licence or configuration, flag it to the owner and verify availability in the actual tenant. Stop the dependent change if it is unverified; do not silently propose a paid workaround.
- Distinguish one-time setup and exceptional maintenance from routine participant actions. Flag necessary admin work upfront; do not promise zero operational maintenance.
- Work one ticket per branch/PR. Update current design, implementation plan and issue evidence together. Keep issues open until their acceptance criteria and relevant tenant tests pass.
- Ordinary-participant access testing is deferred by the owner; use owner/synthetic data meanwhile. Do not infer ordinary-user exposure from admin group permissions, or declare privacy verified without the test.
- The current implementation authority is docs/CURRENT_DESIGN.md; tandem_app and reference DOCX files are historical sources, not approval to change the design.
