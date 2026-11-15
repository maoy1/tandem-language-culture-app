If(Form1.Mode <> FormMode.View || IsBlank(RecordsGallery1.Selected.ID),
    Notify("Save or cancel your registration changes before opening Discovery.", NotificationType.Warning),
    If((!IsBlank(varDiscoveryIntent) && varDiscoveryActorId <> RecordsGallery1.Selected.ID) || (((!IsBlank(varRequestsIntent)) || (!IsBlank(varGroupsIntent))) && !IsBlank(varAppActorId) && varAppActorId <> RecordsGallery1.Selected.ID),
        Notify("Finish or clear the earlier request intent before changing profiles.", NotificationType.Warning),
        Set(varDiscoveryActorId, RecordsGallery1.Selected.ID);
        Set(varDiscoveryTab, If(!IsBlank(varDiscoveryIntent) && varDiscoveryIntentKind = "Group", "Groups", "People"));
        Navigate(scrDiscovery, ScreenTransition.None);
        Set(varDiscoveryBusy, true);
Set(varDiscoveryError, "");
Clear(colDiscoveryPeople); Clear(colDiscoveryGroups);
IfError(
    Set(varDiscoveryResponse, TandemDiscovery.Run(varDiscoveryActorId));
    If(varDiscoveryResponse.resultcode = "OK",
        ClearCollect(colDiscoveryPeople,
            ForAll(Table(ParseJSON(varDiscoveryResponse.candidatesjson)) As r,
                {kind: "Person", targetId: Value(r.Value.profileId),
                 title: Text(r.Value.displayName), summary: Text(r.Value.fitType),
                 detail: "Teaches: " & Concat(Table(r.Value.profile.teachLanguages) As x, Text(x.Value.label), ", ") & Char(10) & "Learning: " & Concat(Table(r.Value.profile.learnLanguages) As x, Text(x.Value.label), ", ") & Char(10) & "Cultures to share: " & Concat(Table(r.Value.profile.shareCultures) As x, Text(x.Value.label), ", ") & Char(10) & "Cultures of interest: " & Concat(Table(r.Value.profile.learnCultures) As x, Text(x.Value.label), ", ") & Char(10) & "Time zone: " & Coalesce(Text(r.Value.profile.timeZone.label), "Not specified") & Char(10) & "Learning focus: " & Text(r.Value.profile.learningFocus) & Char(10) & "Comments: " & Text(r.Value.profile.comments) & Char(10) & Char(10) & If(!IsEmpty(Table(r.Value.match.canLearnLanguageIds)), "You can learn: " & Concat(Filter(Table(r.Value.profile.teachLanguages) As x, Value(x.Value.id) in ForAll(Table(r.Value.match.canLearnLanguageIds) As mid, Value(mid.Value))) As matched, Text(matched.Value.label), ", ") & Char(10), "") & If(!IsEmpty(Table(r.Value.match.canShareLanguageIds)), "You can teach: " & Concat(Filter(Table(r.Value.profile.learnLanguages) As x, Value(x.Value.id) in ForAll(Table(r.Value.match.canShareLanguageIds) As mid, Value(mid.Value))) As matched, Text(matched.Value.label), ", ") & Char(10), "") & If(!IsEmpty(Table(r.Value.match.canLearnCultureIds)), "You can learn about: " & Concat(Filter(Table(r.Value.profile.shareCultures) As x, Value(x.Value.id) in ForAll(Table(r.Value.match.canLearnCultureIds) As mid, Value(mid.Value))) As matched, Text(matched.Value.label), ", ") & Char(10), "") & If(!IsEmpty(Table(r.Value.match.canShareCultureIds)), "You can share about: " & Concat(Filter(Table(r.Value.profile.learnCultures) As x, Value(x.Value.id) in ForAll(Table(r.Value.match.canShareCultureIds) As mid, Value(mid.Value))) As matched, Text(matched.Value.label), ", ") & Char(10), "")}));
        ClearCollect(colDiscoveryGroups,
            ForAll(Table(ParseJSON(varDiscoveryResponse.groupsjson)) As r,
                {kind: "Group", targetId: Value(r.Value.groupId),
                 title: Text(r.Value.name),
                 summary: Text(r.Value.memberCount) & "/" & Text(r.Value.capacity) & " members · " & Text(r.Value.freeSlots) & " places available",
                 detail: Text(r.Value.exchangeType) & " exchange · Open" & Char(10) & "Languages: " & Concat(Table(r.Value.languageFocus) As x, Text(x.Value.label), ", ") & Char(10) & "Cultures: " & Concat(Table(r.Value.cultureFocus) As x, Text(x.Value.label), ", ") & Char(10) & Text(r.Value.description) & Char(10) & Char(10) & "Members" & Char(10) & Concat(Table(r.Value.members) As m, Text(m.Value.displayName) & Char(10) & "Teaches: " & Concat(Table(m.Value.teachLanguages) As x, Text(x.Value.label), ", ") & Char(10) & "Learning: " & Concat(Table(m.Value.learnLanguages) As x, Text(x.Value.label), ", ") & Char(10) & "Cultures to share: " & Concat(Table(m.Value.shareCultures) As x, Text(x.Value.label), ", ") & Char(10) & "Cultures of interest: " & Concat(Table(m.Value.learnCultures) As x, Text(x.Value.label), ", ") & Char(10) & "Time zone: " & Coalesce(Text(m.Value.timeZone.label), "Not specified") & Char(10) & "Learning focus: " & Text(m.Value.learningFocus) & Char(10) & "Comments: " & Text(m.Value.comments), Char(10) & Char(10))})),
        Set(varDiscoveryError, Switch(varDiscoveryResponse.resultcode,
            "PROFILE_UNAVAILABLE", "Your saved profile is not currently available for discovery. Review your registration and availability.",
            "Discovery could not load. Reference: " & varDiscoveryResponse.runreference))
    ),
    Clear(colDiscoveryPeople); Clear(colDiscoveryGroups);
    Set(varDiscoveryError, "Discovery could not load. Select Refresh to try again.")
);
Set(varDiscoveryBusy, false)
    )
)
