If(Form1.Mode <> FormMode.View || IsBlank(RecordsGallery1.Selected.ID),
    Notify("Save or cancel your registration changes first.", NotificationType.Warning),
    If((!IsBlank(varDiscoveryIntent) && varDiscoveryActorId <> RecordsGallery1.Selected.ID) ||
       ((!IsBlank(varRequestsIntent)) || (!IsBlank(varGroupsIntent)) && !IsBlank(varAppActorId) && varAppActorId <> RecordsGallery1.Selected.ID),
        Notify("Finish or clear the earlier request intent before changing profiles.", NotificationType.Warning),
        Set(varAppActorId, RecordsGallery1.Selected.ID);
        Navigate(scrMyGroups, ScreenTransition.None);
        Set(varGrpBusy, true);
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
                 detail: Text(grpRow.Value.exchangeType) & " exchange" & Char(10) & "Languages: " & Concat(Table(grpRow.Value.languageFocus) As grpLabel, Text(grpLabel.Value.label), ", ") & Char(10) & "Cultures: " & Concat(Table(grpRow.Value.cultureFocus) As grpLabel, Text(grpLabel.Value.label), ", ") & Char(10) & Text(grpRow.Value.purpose) & Char(10) & Char(10) & "Current members" & Char(10) & Concat(Table(grpRow.Value.members) As grpMember, Text(grpMember.Value.displayName) & Char(10) & "Teaches: " & Concat(Table(grpMember.Value.teachLanguages) As grpLabel, Text(grpLabel.Value.label), ", ") & Char(10) & "Learning: " & Concat(Table(grpMember.Value.learnLanguages) As grpLabel, Text(grpLabel.Value.label), ", ") & Char(10) & "Cultures to share: " & Concat(Table(grpMember.Value.shareCultures) As grpLabel, Text(grpLabel.Value.label), ", ") & Char(10) & "Cultures of interest: " & Concat(Table(grpMember.Value.learnCultures) As grpLabel, Text(grpLabel.Value.label), ", ") & Char(10) & "Time zone: " & Coalesce(Text(grpMember.Value.timeZone.label), "Not specified") & Char(10) & "Learning focus: " & Text(grpMember.Value.learningFocus) & Char(10) & "Comments: " & Text(grpMember.Value.comments), Char(10) & Char(10))}));
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
Set(varGrpBusy, false)
    )
)
