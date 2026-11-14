"""#68 My groups canvas source; native compilation and actions remain unproved.

Consumes the deployed repaired1.0.0.2 interfaces recorded in core_batch/
v1.0.0.1/flow-io.json. The parent supplies bindings, navigation and actor guard.
No direct list writes, participant eligibility checks or runtime dependencies.
"""
from scripts.build_discovery_app import control

SCREEN_NAME = 'scrMyGroups'
FLOW_NAMES = ('TandemMyGroups', 'TandemUpdateGroup', 'TandemLeaveGroup')
PENDING = '!IsBlank(varGroupsIntent)'
BUSY = 'varGrpBusy || varGrpSending'
MODAL = '!IsBlank(varGrpDialog)'


def _labels(path):
    return f'Concat(Table({path}) As grpLabel, Text(grpLabel.Value.label), ", ")'


def _profile(path):
    fields = [('Teaches', 'teachLanguages'), ('Learning', 'learnLanguages'),
              ('Cultures to share', 'shareCultures'), ('Cultures of interest', 'learnCultures')]
    parts = [f'"{title}: " & {_labels(path + "." + key)}' for title, key in fields]
    parts += [f'"Time zone: " & Coalesce(Text({path}.timeZone.label), "Not specified")',
              f'"Learning focus: " & Text({path}.learningFocus)',
              f'"Comments: " & Text({path}.comments)']
    return ' & Char(10) & '.join(parts)


_DETAIL = ('Text(grpRow.Value.exchangeType) & " exchange" & Char(10) & '
           f'"Languages: " & {_labels("grpRow.Value.languageFocus")} & Char(10) & '
           f'"Cultures: " & {_labels("grpRow.Value.cultureFocus")} & Char(10) & '
           'Text(grpRow.Value.purpose) & Char(10) & Char(10) & "Current members" & Char(10) & '
           'Concat(Table(grpRow.Value.members) As grpMember, '
           'Text(grpMember.Value.displayName) & Char(10) & '
           + _profile('grpMember.Value') + ', Char(10) & Char(10))')

# Refresh clears stale display data, never the frozen mutation intent/payload.
# groupstatus belongs to #64; a failed read must not imply Waiting.
LOAD = '''Set(varGrpBusy, true);
Set(varGrpLoaded, false);
Set(varGrpError, "");
Set(varGrpStatus, "");
Set(varGrpDiagnostic, "");
Clear(grpRows);
If(IsBlank(varAppActorId) || varAppActorId <= 0,
    Set(varGrpError, "Open your own saved registration, then open My groups."),
    IfError(
    Set(varGrpRead, TandemMyGroups.Run(varAppActorId));
    If(varGrpRead.resultcode = "OK",
        ClearCollect(grpRows,
            ForAll(Table(ParseJSON(varGrpRead.groupsjson)) As grpRow,
                {groupId: Value(grpRow.Value.groupId),
                 membershipId: Value(grpRow.Value.membershipId),
                 name: Text(grpRow.Value.name), purpose: Text(grpRow.Value.purpose),
                 exchangeType: Text(grpRow.Value.exchangeType),
                 capacity: Value(grpRow.Value.capacity), state: Text(grpRow.Value.state),
                 memberCount: Value(grpRow.Value.memberCount), freeSlots: Value(grpRow.Value.freeSlots),
                 expectedETag: Text(grpRow.Value.expectedETag),
                 detail: GROUP_DETAIL}));
        Reset(grpList);
        Set(varGrpStatus, varGrpRead.groupstatus);
        Set(varGrpLoaded, true),
        Set(varGrpError, "Groups could not load (" & varGrpRead.resultcode & "). Reference: " & varGrpRead.runreference)
    ),
    Set(varGrpDiagnostic, FirstError.Message);
    Clear(grpRows); Set(varGrpStatus, "");
    Set(varGrpError, "Groups could not load completely. Select Refresh to try again.")
    )
);
Set(varGrpBusy, false)'''.replace('GROUP_DETAIL', _DETAIL)

# All retries use this record, including the exact serialized edit JSON. Selection,
# inputs, refreshed ETags and current actor are deliberately absent from SEND.
# Only these bounded pre-domain rejections permit a deliberate replacement.
# Receipt/release failures and unknown writes use other codes and stay frozen.
UPDATE_CAN_REVISE = '''!IsBlank(varGrpUpdateResponse.success) && varGrpUpdateResponse.success = false &&
    !IsBlank(varGrpUpdateResponse.resultcode) &&
    varGrpUpdateResponse.resultcode in ["REVISION_CONFLICT", "GROUP_BUSY", "GROUP_ENDED_FINAL", "CAPACITY_INVALID", "CAPACITY_CHANGED_OR_INVALID"]'''
LEAVE_CAN_REVISE = '''!IsBlank(varGrpLeaveResponse.success) && varGrpLeaveResponse.success = false &&
    !IsBlank(varGrpLeaveResponse.writeattempted) && varGrpLeaveResponse.writeattempted = false &&
    !IsBlank(varGrpLeaveResponse.outcomeunknown) && varGrpLeaveResponse.outcomeunknown = false'''
SEND = '''Set(varGrpSending, true);
Set(varGrpSuccess, false);
Set(varGrpCode, "");
Set(varGrpReference, "");
Set(varGrpCanRevise, false);
Set(varGrpOutcome, "");
Set(varGrpDiagnostic, "");
IfError(
    If(varGrpFrozen.kind = "Edit",
        Set(varGrpUpdateResponse, TandemUpdateGroup.Run(varGrpFrozen.requestJson));
        Set(varGrpSuccess, varGrpUpdateResponse.success);
        Set(varGrpCode, varGrpUpdateResponse.resultcode);
        Set(varGrpReference, varGrpUpdateResponse.runreference);
        Set(varGrpCanRevise, UPDATE_REVISE_GUARD),
        Set(varGrpLeaveResponse, TandemLeaveGroup.Run(varGrpFrozen.actorId, varGrpFrozen.groupId, varGrpFrozen.membershipId, varGroupsIntent));
        Set(varGrpSuccess, varGrpLeaveResponse.success);
        Set(varGrpCode, varGrpLeaveResponse.resultcode);
        Set(varGrpReference, varGrpLeaveResponse.runreference);
        Set(varGrpCanRevise, LEAVE_REVISE_GUARD)
    );
    If(varGrpSuccess = true,
        Set(varGrpOutcome, If(varGrpFrozen.kind = "Edit", "Changes saved for " & varGrpFrozen.name & ".", "Left " & varGrpFrozen.name & "."));
        Set(varGroupsIntent, Blank());
        Set(varGrpDialog, "");
        GROUP_REFRESH,
        Set(varGrpOutcome, "Operation not confirmed (" & varGrpCode & "). Reference: " & varGrpReference & If(varGrpCanRevise, ". No group change was made. Retry the same operation or select Refresh and revise.", ". Retry keeps the same operation. If unresolved, retain this reference for support."))
    ),
    Set(varGrpCanRevise, false);
    Set(varGrpDiagnostic, FirstError.Message);
    Set(varGrpOutcome, "No confirmation received. Retry the same operation; its saved group and inputs are retained. If unresolved, ask for support before starting another operation.")
);
Set(varGrpSending, false)'''.replace('GROUP_REFRESH', LOAD).replace('UPDATE_REVISE_GUARD', UPDATE_CAN_REVISE).replace('LEAVE_REVISE_GUARD', LEAVE_CAN_REVISE)

# Refresh alone does not release an intent. This explicit action may release it
# only after an actual no-domain response; it never reports mutation success.
REVISE = '''If(varGrpCanRevise = true && !IsBlank(varGroupsIntent) && !varGrpBusy && !varGrpSending,
    Set(varGroupsIntent, Blank());
    Set(varGrpCanRevise, false);
    Set(varGrpDialog, "");
    Set(varGrpOutcome, "Earlier operation made no group change. Review the refreshed group before starting a new operation.");
    GROUP_REFRESH
)'''.replace('GROUP_REFRESH', LOAD)

_GUIDANCE = ('!IsBlank(Trim(grpTitle.Text)) && Len(grpTitle.Text) <= 255 && '
             'Len(grpPurpose.Text) <= 2000 && '
             'IfError(Value(grpCapacity.Text) >= 2 && Value(grpCapacity.Text) <= 10 && '
             'Value(grpCapacity.Text) >= varGrpEditing.memberCount && '
             'If(varGrpEditing.exchangeType = "Language", Value(grpCapacity.Text) <= 3, true) && '
             'Mod(Value(grpCapacity.Text), 1) = 0, false)')
SAVE = '''If(IsBlank(varGroupsIntent) && !varGrpSending && (INPUT_OK),
    Set(varGroupsIntent, Text(GUID()));
    Set(varGrpFrozen, {kind: "Edit", actorId: varAppActorId,
        groupId: varGrpEditing.groupId, membershipId: varGrpEditing.membershipId,
        name: varGrpEditing.name,
        requestJson: JSON({actorId: varAppActorId, groupId: varGrpEditing.groupId,
            expectedETag: varGrpEditing.expectedETag, intentId: varGroupsIntent,
            edits: {Title: grpTitle.Text, Purpose: grpPurpose.Text,
                Capacity: Value(grpCapacity.Text), State: grpState.Selected.Value}}, JSONFormat.Compact)});
    Set(varGrpDialog, "");
    SEND_OPERATION
)'''.replace('INPUT_OK', _GUIDANCE).replace('SEND_OPERATION', SEND)
LEAVE = '''If(IsBlank(varGroupsIntent) && !varGrpSending,
    Set(varGroupsIntent, Text(GUID()));
    Set(varGrpFrozen, {kind: "Leave", actorId: varAppActorId,
        groupId: varGrpEditing.groupId, membershipId: varGrpEditing.membershipId,
        name: varGrpEditing.name, requestJson: ""});
    Set(varGrpDialog, "");
    SEND_OPERATION
)'''.replace('SEND_OPERATION', SEND)


def screen():
    """1366x768 source tree. Text inputs provide plain-text scrolling details."""
    def label(name, **p):
        return control(name, 'Label@2.5.1', {'Font': "Font.'Segoe UI'", 'Size': '12', **p})

    def button(name, **p):
        return control(name, 'Classic/Button@2.2.0', {'Height': '40', 'Size': '12', **p})

    def text(name, **p):
        return control(name, 'Classic/TextInput@2.3.2', {'Size': '12', **p})

    idle = 'varGrpLoaded && IsBlank(varGrpError) && !varGrpBusy && !varGrpSending && IsBlank(varGroupsIntent) && IsBlank(varGrpDialog)'
    selected = f'{idle} && !IsBlank(grpList.Selected.groupId)'
    editable = f'{selected} && grpList.Selected.state <> "Ended"'
    mode = lambda condition: f'If({condition}, DisplayMode.Edit, DisplayMode.Disabled)'
    open_edit = '''Set(varGrpEditing, grpList.Selected); Set(varGrpDialog, "Edit");
Set(varGrpOutcome, ""); Reset(grpTitle); Reset(grpPurpose); Reset(grpCapacity); Reset(grpState)'''
    controls = [
        label('grpHeading', Text='"My groups"', X='24', Y='16', Width='Parent.Width - 640', Height='44', Size='24', FontWeight='FontWeight.Semibold'),
        button('grpBack', Text='"My registration"', X='Parent.Width - 300', Y='20', Width='160', DisplayMode=mode('!varGrpBusy && !varGrpSending && IsBlank(varGrpDialog)'), OnSelect='Navigate(MainScreen1, ScreenTransition.None)'),
        button('grpRefresh', Text='"Refresh"', X='Parent.Width - 128', Y='20', Width='104', DisplayMode=mode('!varGrpBusy && !varGrpSending && IsBlank(varGrpDialog)'), OnSelect=LOAD),
        label('grpStatus', Text='If(varGrpBusy, "Loading groups…", If(!IsBlank(varGrpError), varGrpError, varGrpStatus))', X='24', Y='84', Width='Parent.Width - 48', Height='54'),
        control('grpList', 'Gallery@2.15.0', {'Items': 'grpRows', 'X': '24', 'Y': '144', 'Width': '360', 'Height': 'Parent.Height - 168', 'TemplateSize': '116', 'AccessibleLabel': '"Your current groups"', 'DisplayMode': mode(idle), 'TemplateFill': 'If(ThisItem.IsSelected, RGBA(225,239,250,1), RGBA(255,255,255,1))', 'OnSelect': 'Set(varGrpOutcome, "")'}, [
            label('grpRowName', Text='ThisItem.name', X='12', Y='8', Width='Parent.TemplateWidth - 24', Height='44', FontWeight='FontWeight.Semibold', OnSelect='Select(Parent)'),
            label('grpRowState', Text='ThisItem.state & " · " & ThisItem.memberCount & "/" & ThisItem.capacity & " members" & Char(10) & ThisItem.freeSlots & " free slots"', X='12', Y='54', Width='Parent.TemplateWidth - 24', Height='54', OnSelect='Select(Parent)')
        ], 'BrowseLayout_Vertical_TwoTextVariant_ver5.0'),
        label('grpEmpty', Text='"No current groups."', X='36', Y='156', Width='330', Height='64', Visible='varGrpLoaded && !varGrpBusy && IsBlank(varGrpError) && IsEmpty(grpRows)'),
        label('grpSelectedName', Text='If(varGrpLoaded && IsBlank(varGrpError), grpList.Selected.name, "")', X='408', Y='144', Width='Parent.Width - 432', Height='48', Size='20', FontWeight='FontWeight.Semibold'),
        label('grpSelectedState', Text='If(varGrpLoaded && IsBlank(varGrpError) && !IsBlank(grpList.Selected.groupId), grpList.Selected.state & " · " & grpList.Selected.memberCount & "/" & grpList.Selected.capacity & " members · " & grpList.Selected.freeSlots & " free slots", "Select a group to view its members.")', X='408', Y='196', Width='Parent.Width - 432', Height='40'),
        text('grpDetails', Default='If(varGrpLoaded && IsBlank(varGrpError), grpList.Selected.detail, "")', DisplayMode='DisplayMode.View', Mode='TextMode.MultiLine', X='408', Y='244', Width='Parent.Width - 432', Height='Parent.Height - 448', AccessibleLabel='"Group focus, purpose and current member profiles"'),
        button('grpEdit', Text='"Edit group"', X='408', Y='Parent.Height - 192', Width='160', DisplayMode=mode(editable), OnSelect=open_edit),
        button('grpLeave', Text='"Leave group…"', X='580', Y='Parent.Height - 192', Width='160', DisplayMode=mode(selected), OnSelect='Set(varGrpEditing, grpList.Selected); Set(varGrpDialog, "Leave"); Set(varGrpOutcome, "")'),
        label('grpEnded', Text='"Ended is final. Leaving does not reopen a group or rejoin it later."', X='408', Y='Parent.Height - 146', Width='Parent.Width - 432', Height='36'),
        button('grpRetry', Text='"Retry same operation"', X='408', Y='Parent.Height - 104', Width='210', Visible=PENDING, DisplayMode=mode('!varGrpBusy && !varGrpSending'), OnSelect=SEND),
        button('grpRevise', Text='"Refresh and revise"', X='630', Y='Parent.Height - 104', Width='210', Visible=f'{PENDING} && varGrpCanRevise = true', DisplayMode=mode('varGrpCanRevise = true && !varGrpBusy && !varGrpSending'), OnSelect=REVISE),
        label('grpPending', Text='If(!IsBlank(varGroupsIntent), varGrpFrozen.kind & ": " & varGrpFrozen.name & " — inputs retained", "")', X='852', Y='Parent.Height - 104', Width='Parent.Width - 876', Height='40'),
        label('grpOutcome', Text='If(varGrpSending, "Waiting for confirmation…", varGrpOutcome)', X='408', Y='Parent.Height - 60', Width='Parent.Width - 432', Height='56'),
    ]
    # A full-screen modal layer blocks accidental selection behind either dialog.
    controls.append(control('grpModal', 'GroupContainer@1.3.0', {
        'X': '0', 'Y': '0', 'Width': 'Parent.Width', 'Height': 'Parent.Height',
        'Fill': 'RGBA(0,0,0,0.35)', 'Visible': '!IsBlank(varGrpDialog)'}, [
        control('grpDialogPanel', 'GroupContainer@1.3.0', {
            'X': '(Parent.Width - 720) / 2', 'Y': '92', 'Width': '720', 'Height': '584',
            'Fill': 'RGBA(255,255,255,1)'}, [
            label('grpDialogTitle', Text='If(varGrpDialog = "Edit", "Edit group", "Confirm Leave")', X='24', Y='16', Width='672', Height='40', Size='22'),
            label('grpDialogName', Text='varGrpEditing.name', X='24', Y='60', Width='672', Height='44'),
            label('grpTitleLabel', Text='"Group name (required, up to 255 characters)"', X='24', Y='108', Width='672', Height='28', Visible='varGrpDialog = "Edit"'),
            text('grpTitle', Default='varGrpEditing.name', MaxLength='255', X='24', Y='140', Width='672', Height='40', Visible='varGrpDialog = "Edit"', AccessibleLabel='"Group name"'),
            label('grpPurposeLabel', Text='"Purpose (optional, up to 2,000 plain-text characters)"', X='24', Y='188', Width='672', Height='28', Visible='varGrpDialog = "Edit"'),
            text('grpPurpose', Default='varGrpEditing.purpose', MaxLength='2000', Mode='TextMode.MultiLine', X='24', Y='220', Width='672', Height='100', Visible='varGrpDialog = "Edit"', AccessibleLabel='"Group purpose"'),
            label('grpCapacityLabel', Text='"Total capacity (whole number, 2–10; language groups 2 or 3)"', X='24', Y='332', Width='672', Height='28', Visible='varGrpDialog = "Edit"'),
            text('grpCapacity', Default='Text(varGrpEditing.capacity)', Format='TextFormat.Number', X='24', Y='364', Width='200', Height='40', Visible='varGrpDialog = "Edit"', AccessibleLabel='"Total capacity"'),
            label('grpStateLabel', Text='"State — Ended is final"', X='248', Y='332', Width='448', Height='28', Visible='varGrpDialog = "Edit"'),
            control('grpState', 'Classic/DropDown@2.3.1', {'Items': '["Open", "Closed", "Ended"]', 'Default': 'varGrpEditing.state', 'X': '248', 'Y': '364', 'Width': '448', 'Height': '40', 'Visible': 'varGrpDialog = "Edit"', 'AccessibleLabel': '"Group state; Ended is final"'}),
            label('grpEditGuidance', Text='"Capacity cannot be below current membership. Refresh if someone else changes the group. Ending is final."', X='24', Y='416', Width='672', Height='72', Visible='varGrpDialog = "Edit"'),
            label('grpLeaveWarning', Text='"Leave this group? Your current membership will end. The group state stays as it is. This action does not automatically rejoin you later."', X='24', Y='120', Width='672', Height='180', Visible='varGrpDialog = "Leave"'),
            button('grpCancel', Text='"Cancel"', X='24', Y='516', Width='160', OnSelect='Set(varGrpDialog, "")'),
            button('grpSave', Text='"Save changes"', X='472', Y='516', Width='224', Visible='varGrpDialog = "Edit"', DisplayMode=mode('IsBlank(varGroupsIntent) && !varGrpSending && (' + _GUIDANCE + ')'), OnSelect=SAVE),
            button('grpConfirmLeave', Text='"Confirm Leave"', X='472', Y='516', Width='224', Visible='varGrpDialog = "Leave"', DisplayMode=mode('IsBlank(varGroupsIntent) && !varGrpSending'), OnSelect=LEAVE),
        ], variant='ManualLayout')
    ], variant='ManualLayout'))
    return {'Screens': {SCREEN_NAME: {'Properties': {'Fill': '=RGBA(250,250,250,1)'}, 'Children': controls}}}
