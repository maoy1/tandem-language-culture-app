If(varReqSending, "Submitting…", If(varReqDialog = "New intent", "Start a different action", varReqDialog = "Cancel", "Withdraw request", "Confirm " & Lower(varReqDialog)))
