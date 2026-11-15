If(
    Form1.Mode <> FormMode.View,
    Notify("Save or cancel your current registration changes first.", NotificationType.Warning),
    IsBlank(varRegistrationEmail),
    Notify("Your work account is still loading. Try again shortly.", NotificationType.Warning),
    IfError(
        With(
            {
                existingProfile: LookUp(
                    [@Participants],
                    'Participant account'.Email = varRegistrationEmail
                )
            },
            If(
                !IsBlank(existingProfile.ID),
                Notify("Your registration already exists. Use the pencil to edit it.", NotificationType.Information),
                NewForm(Form1);
                UpdateContext({ newMode: true, editMode: false, itemSelected: true })
            )
        ),
        Notify("Your registration could not be checked. Please try again.", NotificationType.Error)
    )
)
