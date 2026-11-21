If(IsBlank(varReqSelected.requestId), "",
    If(varReqSelected.processing,
    "Accepted. Your exchange is being set up. Refresh to check progress.",
    Switch(varReqSelected.status,
        "Pending", If(varReqSelected.direction = "Sent", "Waiting for a reply.", "Waiting for your response."),
        "Accepted", "Accepted.",
        "Declined", "Declined.",
        "Cancelled", If(varReqSelected.direction = "Sent", "You withdrew this request.", "The sender withdrew this request."),
        varReqSelected.status)) & Char(10) &
    "Sent: " & IfError(Text(DateTimeValue(varReqSelected.created), DateTimeFormat.ShortDateTime), "Date unavailable") &
    If(varReqSelected.status = "Pending" && varReqSelected.availability = "UnavailablePending",
        Char(10) & "The person or group is no longer available. You can still withdraw or decline where offered.", "") &
    If(varReqSelected.requestType = "Group" && !IsBlank(Trim(Coalesce(varReqSelected.introduction, ""))),
        Char(10) & Char(10) & "Introduction" & Char(10) & varReqSelected.introduction, ""))
