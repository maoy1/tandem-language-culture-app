If(Form1.Mode <> FormMode.View || IsBlank(RecordsGallery1.Selected.ID),
    Notify("Save or cancel your registration changes first.", NotificationType.Warning),
    If((!IsBlank(varDiscoveryIntent) && varDiscoveryActorId <> RecordsGallery1.Selected.ID) ||
       ((!IsBlank(varRequestsIntent)) || (!IsBlank(varGroupsIntent)) && !IsBlank(varAppActorId) && varAppActorId <> RecordsGallery1.Selected.ID),
        Notify("Finish or clear the earlier request intent before changing profiles.", NotificationType.Warning),
        Set(varAppActorId, RecordsGallery1.Selected.ID);
        Navigate(scrRequests, ScreenTransition.None);
        Set(varReqBusy, true);
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
Set(varReqBusy, false)
    )
)
