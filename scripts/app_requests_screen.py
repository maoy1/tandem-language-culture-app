"""#67 Requests canvas source. Native Studio/binding/runtime checks are NOT RUN.

Parent owns navigation, datasource binding and packaging. No backend changes.
Catalogue choices reuse the registration connector; eligibility belongs to flows.
"""
from scripts.build_discovery_app import control

SCREEN_NAME = 'scrRequests'
FLOW_NAMES = ['TandemMyRequests', 'TandemCancelRequest',
              'TandemRespondRequest', 'TandemRespondGroupJoinRequest']
PENDING = '!IsBlank(varRequestsIntent)'
BUSY = 'varReqBusy || varReqSending'
MODAL = '!IsBlank(varReqDialog)'

LOAD = '''Set(varReqBusy, true);
Set(varReqError, "");
Set(varReqDiagnostic, "");
Set(varReqLoaded, false);
Set(varReqInspectRequestId, If(!IsBlank(varRequestsIntent), varReqIntentRequest, varReqSelected.requestId));
Set(varReqSelected, Blank());
Clear(reqRows);
If(IsBlank(varReqTab), Set(varReqTab, "Received"));
If(IsBlank(varAppActorId) || varAppActorId <= 0,
    Set(varReqError, "Open My registration and select your saved profile first"),
    If(!IsBlank(varRequestsIntent) && varReqIntentActor <> varAppActorId,
        Set(varReqError, "Return to the saved profile used for the unresolved action before refreshing."),
        IfError(
            Set(varReqReadResponse, TandemMyRequests.Run(varAppActorId));
            If(varReqReadResponse.resultcode = "OK",
                ClearCollect(reqRows,
                    ForAll(Table(ParseJSON(varReqReadResponse.requestsjson)) As reqRow,
                        {requestId: Value(reqRow.Value.requestId),
                         requestType: Text(reqRow.Value.requestType),
                         direction: Text(reqRow.Value.direction),
                         status: Text(reqRow.Value.status),
                         created: Text(reqRow.Value.created),
                         availability: Text(reqRow.Value.availability),
                         processing: Boolean(reqRow.Value.processing),
                         completed: Boolean(reqRow.Value.completed),
                         introduction: Text(reqRow.Value.introduction),
                         canAccept: Boolean(reqRow.Value.actions.accept),
                         canDecline: Boolean(reqRow.Value.actions.decline),
                         canCancel: Boolean(reqRow.Value.actions.cancel)}));
                Set(varReqSelected, LookUp(reqRows, requestId = varReqInspectRequestId));
                Set(varReqLoaded, true),
                Set(varReqError, "Requests could not load. Code: " & varReqReadResponse.resultcode & ". Reference: " & varReqReadResponse.runreference)
            ),
            Clear(reqRows);
            Set(varReqDiagnostic, FirstError.Message);
            Set(varReqError, "Requests could not load. Check the app connection or try Refresh. No action result is implied.")
        )
    )
);
Set(varReqBusy, false)'''

# These are the exact nine positional arguments in flow-io.json. JSON arrays
# contain bare, invariant numeric IDs, never single-column Value objects.
PERSONAL_CALL = '''TandemRespondRequest.Run(varReqIntentActor, varReqIntentRequest,
    varReqIntentDecision, varReqIntentName, varReqIntentType, varReqIntentCapacity,
    varReqIntentLanguages, varReqIntentCultures, varRequestsIntent)'''

EXECUTE = '''Set(varReqSending, true);
Set(varReqOutcome, "");
Set(varReqDiagnostic, "");
Set(varReqActionSuccess, false);
Set(varReqActionCode, "");
Set(varReqActionMessage, "");
Set(varReqActionReference, "");
If(IsBlank(varAppActorId) || varAppActorId <= 0 || varReqIntentActor <> varAppActorId || IsBlank(varRequestsIntent),
    Set(varReqOutcome, "Open My registration and select the saved profile used for this action first."),
IfError(
    If(varReqIntentDecision = "Cancel",
        Set(varReqCancelResponse, TandemCancelRequest.Run(varReqIntentActor, varReqIntentRequest));
        Set(varReqActionSuccess, varReqCancelResponse.success && varReqCancelResponse.operationcomplete && !varReqCancelResponse.outcomeunknown && varReqCancelResponse.currentstatus = "Cancelled");
        Set(varReqActionCode, varReqCancelResponse.resultcode);
        Set(varReqActionMessage, varReqCancelResponse.message);
        Set(varReqActionReference, varReqCancelResponse.runreference),
        If(varReqIntentKind = "Personal",
            Set(varReqPersonalResponse, PERSONAL_CALL);
            Set(varReqActionSuccess, varReqPersonalResponse.success);
            Set(varReqActionCode, varReqPersonalResponse.resultcode);
            Set(varReqActionMessage, varReqPersonalResponse.message),
            Set(varReqGroupResponse, TandemRespondGroupJoinRequest.Run(varReqIntentRequest, varReqIntentDecision, varRequestsIntent));
            Set(varReqActionSuccess, varReqGroupResponse.success);
            Set(varReqActionCode, varReqGroupResponse.resultcode);
            Set(varReqActionMessage, varReqGroupResponse.errormessage);
            Set(varReqActionReference, varReqGroupResponse.runreference)
        )
    );
    If(varReqActionSuccess,
        Set(varReqOutcome, "Your action is confirmed. Refreshing saved requests…");
        Set(varRequestsIntent, Blank());
        Set(varReqDialog, Blank());
        REFRESH_REQUESTS,
        Set(varReqOutcome, "Action not confirmed. Code: " & varReqActionCode & If(IsBlank(varReqActionReference), "", ". Reference: " & varReqActionReference) & ". Refresh to inspect saved status. Retry retains the same action and settings.")
    ),
    Set(varReqDiagnostic, FirstError.Message);
    Set(varReqOutcome, "No confirmation received. Refresh to inspect saved status. Retry retains the same action and settings.")
));
Set(varReqDialog, Blank());
Set(varReqSending, false)'''.replace('PERSONAL_CALL', PERSONAL_CALL).replace('REFRESH_REQUESTS', LOAD)

CAPTURE = '''If(IsBlank(varRequestsIntent),
    Set(varReqIntentActor, varAppActorId);
    Set(varReqIntentRequest, varReqSelected.requestId);
    Set(varReqIntentKind, varReqSelected.requestType);
    Set(varReqIntentDecision, varReqDialog);
    Set(varReqIntentName, If(varReqDialog = "Accept" && varReqSelected.requestType = "Personal", Trim(reqName.Text), ""));
    Set(varReqIntentType, If(varReqDialog = "Accept" && varReqSelected.requestType = "Personal", reqType.Selected.Value, "Language"));
    Set(varReqIntentCapacity, If(varReqDialog = "Accept" && varReqSelected.requestType = "Personal", reqCapacity.Selected.Value, 2));
    Set(varReqIntentLanguages, If(varReqDialog = "Accept" && varReqSelected.requestType = "Personal" && reqType.Selected.Value <> "Culture",
        "[" & Concat(reqLanguages.SelectedItems As reqFocus, Text(Value(reqFocus.Id), "0", "en-US"), ",") & "]", "[]"));
    Set(varReqIntentCultures, If(varReqDialog = "Accept" && varReqSelected.requestType = "Personal" && reqType.Selected.Value <> "Language",
        "[" & Concat(reqCultures.SelectedItems As reqFocus, Text(Value(reqFocus.Id), "0", "en-US"), ",") & "]", "[]"));
    Set(varRequestsIntent, Text(GUID()))
);
''' + EXECUTE

EDITABLE = 'IsBlank(varRequestsIntent) && !varReqBusy && !varReqSending'
PERSONAL_ACCEPT = 'varReqDialog = "Accept" && varReqSelected.requestType = "Personal"'
VALID_CONFIG = '''!IsBlank(Trim(reqName.Text)) && Len(Trim(reqName.Text)) <= 255 &&
    !IsBlank(reqType.Selected.Value) && !IsBlank(reqCapacity.Selected.Value) &&
    reqCapacity.Selected.Value >= 2 && reqCapacity.Selected.Value <= If(reqType.Selected.Value = "Language", 3, 10) &&
    (reqType.Selected.Value = "Culture" || (!IsEmpty(reqLanguages.SelectedItems) && CountRows(reqLanguages.SelectedItems) <= 100)) &&
    (reqType.Selected.Value = "Language" || (!IsEmpty(reqCultures.SelectedItems) && CountRows(reqCultures.SelectedItems) <= 100))'''


def screen():
    def label(name, **props):
        return control(name, 'Label@2.5.1', {'Font': "Font.'Segoe UI'", 'Size': '12', **props})

    def button(name, **props):
        return control(name, 'Classic/Button@2.2.0', {'Height': '40', 'Size': '12', **props})

    def text(name, **props):
        return control(name, 'Classic/TextInput@2.3.2', {'Size': '12', **props})

    def combo(name, **props):
        return control(name, 'Classic/ComboBox@2.4.0', {
            'DisplayFields': '["Value"]', 'SearchFields': '["Value"]',
            'Size': '12', 'Height': '40', 'SelectMultiple': 'false',
            'DisplayMode': f'If({EDITABLE}, DisplayMode.Edit, DisplayMode.Disabled)', **props})

    can_browse = f'{EDITABLE} && IsBlank(varReqDialog)'
    rows = '''Filter(reqRows,
        Switch(varReqTab,
            "Sent", direction = "Sent" && status = "Pending",
            "Received", direction = "Received" && requestType = "Personal" && status = "Pending",
            "Group incoming", direction = "Received" && requestType = "Group" && status = "Pending",
            "History", status <> "Pending", false))'''
    c = [
        label('reqTitle', Text='"My requests"', X='24', Y='16', Width='Parent.Width - 640', Height='44', Size='24', FontWeight='FontWeight.Semibold'),
        button('reqBack', Text='"My registration"', X='Parent.Width - 300', Y='20', Width='160', DisplayMode='If(varReqBusy || varReqSending || !IsBlank(varReqDialog), DisplayMode.Disabled, DisplayMode.Edit)', OnSelect='Navigate(MainScreen1, ScreenTransition.None)'),
        button('reqRefresh', Text='"Refresh"', X='Parent.Width - 128', Y='20', Width='104', DisplayMode='If(varReqBusy || varReqSending || (!IsBlank(varReqDialog) && IsBlank(varRequestsIntent)), DisplayMode.Disabled, DisplayMode.Edit)', OnSelect=LOAD),
        label('reqState', Text='If(varReqBusy, "Loading saved requests…", If(!IsBlank(varReqError), varReqError, "Review requests you sent or received. Select a request for details and available actions."))', X='24', Y='84', Width='Parent.Width - 48', Height='52'),
    ]
    for i, tab in enumerate(['Sent', 'Received', 'Group incoming', 'History']):
        c.append(button('reqTab' + str(i), Text='"' + tab + '"', X=str(24 + i * 174), Y='144', Width='162',
                        DisplayMode=f'If({can_browse}, DisplayMode.Edit, DisplayMode.Disabled)',
                        OnSelect=f'Set(varReqTab, "{tab}"); Set(varReqSelected, Blank())'))
    c += [
        control('reqList', 'Gallery@2.15.0', {'Items': rows, 'X': '24', 'Y': '200', 'Width': '392', 'Height': 'Parent.Height - 224', 'TemplateSize': '112',
            'AccessibleLabel': '"Requests in the selected view"', 'DisplayMode': f'If({can_browse}, DisplayMode.Edit, DisplayMode.Disabled)',
            'TemplateFill': 'If(ThisItem.requestId = varReqSelected.requestId, RGBA(225,239,250,1), RGBA(255,255,255,1))',
            'OnSelect': 'Set(varReqSelected, ThisItem); Set(varReqOutcome, "")'}, [
                label('reqRowTitle', Text='"Request #" & Text(ThisItem.requestId) & " · " & ThisItem.requestType', X='12', Y='8', Width='Parent.TemplateWidth - 24', Height='32', FontWeight='FontWeight.Semibold', OnSelect='Select(Parent)'),
                label('reqRowState', Text='ThisItem.direction & " · " & ThisItem.status & If(ThisItem.processing, " · Processing", "") & Char(10) & ThisItem.created', X='12', Y='44', Width='Parent.TemplateWidth - 24', Height='60', OnSelect='Select(Parent)')
            ], 'BrowseLayout_Vertical_TwoTextVariant_ver5.0'),
        label('reqEmpty', Text='"No requests in this view."', X='36', Y='220', Width='360', Height='60', Visible=f'varReqLoaded && IsEmpty({rows})'),
        label('reqSelectedTitle', Text='If(IsBlank(varReqSelected.requestId), "Select a request", "Request #" & Text(varReqSelected.requestId) & " · " & varReqSelected.requestType)', X='440', Y='200', Width='Parent.Width - 464', Height='48', Size='20'),
        text('reqDetails', Default='If(IsBlank(varReqSelected.requestId), "", varReqSelected.direction & " · " & varReqSelected.status & Char(10) & "Created: " & varReqSelected.created & Char(10) & "Availability: " & varReqSelected.availability & Char(10) & "Completion: " & If(varReqSelected.processing, "Processing; membership completion is not confirmed", If(varReqSelected.completed, "Complete", "Not complete")) & Char(10) & Char(10) & "Introduction" & Char(10) & Coalesce(varReqSelected.introduction, ""))', DisplayMode='DisplayMode.View', Mode='TextMode.MultiLine', X='440', Y='256', Width='Parent.Width - 464', Height='Parent.Height - 464', AccessibleLabel='"Saved request details and plain-text introduction"'),
    ]
    for i, action in enumerate(['Accept', 'Decline', 'Cancel']):
        allow = 'varReqSelected.can' + action
        c.append(button('reqAction' + action, Text='"' + action + '"', X=str(440 + i * 150), Y='Parent.Height - 196', Width='138', Visible=f'!IsBlank(varReqSelected.requestId) && {allow}',
            DisplayMode=f'If({can_browse} && varReqLoaded && {allow}, DisplayMode.Edit, DisplayMode.Disabled)',
            OnSelect=f'Set(varReqDialog, "{action}"); Set(varReqOutcome, ""); Reset(reqName); Reset(reqType); Reset(reqCapacity); Reset(reqLanguages); Reset(reqCultures)'))
    c += [
        button('reqRetry', Text='"Retry same action"', X='440', Y='Parent.Height - 144', Width='190', Visible=PENDING, DisplayMode='If(varReqBusy || varReqSending, DisplayMode.Disabled, DisplayMode.Edit)', OnSelect=EXECUTE),
        button('reqNewIntent', Text='"Review new action"', X='644', Y='Parent.Height - 144', Width='190', Visible=PENDING, DisplayMode='If(varReqBusy || varReqSending, DisplayMode.Disabled, DisplayMode.Edit)', OnSelect='Set(varReqDialog, "New intent")'),
        label('reqOutcome', Text='varReqOutcome & If(!IsBlank(varRequestsIntent), Char(10) & "Unresolved: " & varReqIntentDecision & " request #" & Text(varReqIntentRequest) & ". An earlier action may already be saved. Refresh to check its current status before choosing another action.", "")', X='440', Y='Parent.Height - 92', Width='Parent.Width - 464', Height='84'),
    ]
    # Modal children are appended last so the shaded backdrop covers the parent nav.
    visible = '!IsBlank(varReqDialog)'
    c.append(control('reqShade', 'Rectangle@2.3.0', {'X': '0', 'Y': '0', 'Width': 'Parent.Width', 'Height': 'Parent.Height', 'Fill': 'RGBA(0,0,0,0.45)', 'Visible': visible}))
    c.append(control('reqPanel', 'Rectangle@2.3.0', {'X': '(Parent.Width - 860) / 2', 'Y': '84', 'Width': '860', 'Height': 'Parent.Height - 104', 'Fill': 'RGBA(255,255,255,1)', 'Visible': visible}))
    # Absolute screen-relative positions keep 1366x768 baseline legible.
    def modal_label(name, **props):
        props.setdefault('Visible', visible)
        c.append(label(name, X='reqPanel.X + 24', Width='812', **props))
    modal_label('reqDialogTitle', Text='If(varReqDialog = "New intent", "Review before starting a new action", varReqDialog & " request #" & Text(varReqSelected.requestId))', Y='100', Height='40', Size='20', FontWeight='FontWeight.Semibold')
    modal_label('reqDialogHelp', Text='If(varReqDialog = "New intent", "The previous action may already have saved. Refresh and inspect saved status before proceeding. Starting a different action ends this local retry. It does not undo any saved change.", If(' + PERSONAL_ACCEPT + ', "Choose the new group’s name, type, size and focuses. Each focus needs someone who can share and a different person who wants to learn.", "Confirm this action for the selected request."))', Y='144', Height='76')
    form_visible = visible + ' && (' + PERSONAL_ACCEPT + ') && IsBlank(varRequestsIntent)'
    for name, title, y in [('reqNameLabel', 'Group name (required, up to 255 characters)', 228), ('reqTypeLabel', 'Exchange type', 314), ('reqLanguageLabel', 'Language focuses (required for Language / Combined)', 400), ('reqCultureLabel', 'Culture focuses (required for Culture / Combined)', 486)]:
        c.append(label(name, Text='"' + title + '"', X='reqPanel.X + 24', Y=str(y), Width='630', Height='28', Visible=form_visible))
    c.append(text('reqName', Default='""', MaxLength='255', X='reqPanel.X + 24', Y='260', Width='812', Height='40', AccessibleLabel='"Group name"', Visible=form_visible, DisplayMode=f'If({EDITABLE}, DisplayMode.Edit, DisplayMode.Disabled)'))
    c.append(combo('reqType', Items='["Language", "Culture", "Combined"]', DefaultSelectedItems='["Language"]', X='reqPanel.X + 24', Y='346', Width='382', Visible=form_visible, AccessibleLabel='"Exchange type"', OnChange='Reset(reqCapacity); Reset(reqLanguages); Reset(reqCultures)'))
    c.append(label('reqCapacityLabel', Text='"Total capacity, including both participants"', X='reqPanel.X + 430', Y='314', Width='406', Height='28', Visible=form_visible))
    c.append(combo('reqCapacity', Items='Sequence(If(reqType.Selected.Value = "Language", 2, 9), 2)', DisplayFields='["Value"]', SearchFields='["Value"]', IsSearchable='false', DefaultSelectedItems='[2]', X='reqPanel.X + 430', Y='346', Width='406', Visible=form_visible, AccessibleLabel='"Total group capacity"'))
    for name, field, excluded, y in [('reqLanguages', 'Teachlanguages', 'Culture', 432), ('reqCultures', 'ShareCultures', 'Language', 518)]:
        c.append(combo(name, Items=f'Choices([@Participants].{field})', DefaultSelectedItems='[]', SelectMultiple='true', IsSearchable='true',
                       X='reqPanel.X + 24', Y=str(y), Width='812', Visible=form_visible,
                       DisplayMode=f'If({EDITABLE} && reqType.Selected.Value <> "{excluded}", DisplayMode.Edit, DisplayMode.Disabled)', AccessibleLabel='"' + name[3:] + ' focus selections"'))
    modal_label('reqDialogRules', Text='"Language: 2 or 3 people total. Culture / Combined: 2–10. Each focus requires a sharer and a different learner. Choose up to 100 focuses per catalogue. "', Y='568', Height='52', **{'Visible': form_visible})
    c.append(button('reqConfirm', Text='If(varReqSending, "Submitting…", If(varReqDialog = "New intent", "Start a different action", "Confirm " & Lower(varReqDialog)))', X='reqPanel.X + 24', Y='Parent.Height - 92', Width='240', Visible=visible,
        DisplayMode='If(varReqBusy || varReqSending || (!IsBlank(varRequestsIntent) && varReqDialog <> "New intent") || (varReqDialog <> "New intent" && (!varReqLoaded || IsBlank(varAppActorId) || varAppActorId <= 0 || IsBlank(varReqSelected.requestId) || !Switch(varReqDialog, "Accept", varReqSelected.canAccept, "Decline", varReqSelected.canDecline, "Cancel", varReqSelected.canCancel, false))) || ((' + PERSONAL_ACCEPT + ') && !(' + VALID_CONFIG + ')), DisplayMode.Disabled, DisplayMode.Edit)',
        OnSelect='If(varReqDialog = "New intent", Set(varRequestsIntent, Blank()); Set(varReqDialog, Blank()); Set(varReqOutcome, "Select an action after reviewing the saved status."); ' + LOAD + ', ' + CAPTURE + ')'))
    c.append(button('reqDismiss', Text='"Back"', X='reqPanel.X + 280', Y='Parent.Height - 92', Width='140', Visible=visible, DisplayMode='If(varReqSending, DisplayMode.Disabled, DisplayMode.Edit)', OnSelect='Set(varReqDialog, Blank())'))
    return {'Screens': {SCREEN_NAME: {'Properties': {'Fill': '=RGBA(250,250,250,1)'}, 'Children': c}}}
