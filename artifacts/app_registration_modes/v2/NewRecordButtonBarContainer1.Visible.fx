IfError(
    Form1.Mode = FormMode.View &&
    !IsBlank(varRegistrationEmail) &&
    IsBlank(
        LookUp(
            [@Participants],
            'Participant account'.Email = varRegistrationEmail,
            ID
        )
    ),
    false
)
