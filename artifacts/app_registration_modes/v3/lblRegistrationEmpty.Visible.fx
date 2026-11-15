If(
    Form1.Mode <> FormMode.View ||
    IsBlank(varRegistrationEmail) ||
    !IsBlank(RecordsGallery1.Selected.ID),
    false,
    IfError(
        IsBlank(
            LookUp(
                [@Participants],
                'Participant account'.Email = varRegistrationEmail,
                ID
            )
        ),
        false
    )
)
