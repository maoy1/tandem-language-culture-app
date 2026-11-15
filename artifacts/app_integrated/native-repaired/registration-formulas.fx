// #101: selected formulas from the owner-tested native export.
// Review reference only: do not repack the native app.
// Source SHA256: 673bff977448c4d31390c806681b96fc3d3bc056094d6e61b0e972868c8466ae

// MainScreen1.OnVisible
Set(varRegistrationEmail, Blank());
Set(varRegistrationEmail, IfError(Office365Users.MyProfileV2({'$select': "mail"}).mail, Blank()));
UpdateContext({ itemSelected: !IsBlank(varRegistrationEmail) && !IsBlank(LookUp([@Participants], 'Participant account'.Email = varRegistrationEmail).ID) });
If(IsBlank(varRegistrationEmail), Notify("Your work email could not be loaded. Reopen My registration to try again.", NotificationType.Error))

// RecordsGallery1.Items
If(IsBlank(varRegistrationEmail), Filter([@Participants], ID = -1), Filter([@Participants], 'Participant account'.Email = varRegistrationEmail))

// RecordsGallery1.Default
If(!IsBlank(varRegistrationEmail), LookUp([@Participants], 'Participant account'.Email = varRegistrationEmail))

// Form1.Item
RecordsGallery1.Selected

// Participant account_DataCard1.Visible
false

// Participant account_DataCard1.Update
If(
    Form1.Mode = FormMode.New,
    {
        '@odata.type': "#Microsoft.Azure.Connectors.SharePoint.SPListExpandedUser",
        Claims: "i:0#.f|membership|" & Lower(User().Email),
        DisplayName: User().FullName,
        Email: varRegistrationEmail,
        Department: "",
        JobTitle: "",
        Picture: ""
    },
    ThisItem.'Participant account'
)

// SubmitFormButton1.OnSelect
If(Form1.Mode = FormMode.New && (IsBlank(varRegistrationEmail) || IsBlank(User().Email)),
    Notify("Your work account could not be loaded. Reopen My registration and try again.", NotificationType.Error),
If(
    IsEmpty(cmbTeachLanguages.SelectedItems) &&
    IsEmpty(cmbLearnLanguages.SelectedItems) &&
    IsEmpty(cmbShareCultures.SelectedItems) &&
    IsEmpty(cmbLearnCultures.SelectedItems),
    Notify(
        "Choose at least one language or culture to share or learn.",
        NotificationType.Error
    ),
    SubmitForm(Form1)
)
)

// DataCardValue1.SearchItems
Choices(Participants.'Time zone',DataCardValue1.SearchText)

// cmbLearnLanguages.SearchItems
Choices(Participants.'Learn languages',cmbLearnLanguages.SearchText)

// cmbTeachLanguages.SearchItems
Choices(Participants.'Teach languages',cmbTeachLanguages.SearchText)

// cmbShareCultures.SearchItems
Choices(Participants.'Cultures I can share',cmbShareCultures.SearchText)

// cmbLearnCultures.SearchItems
Choices(Participants.'Cultures of interest',cmbLearnCultures.SearchText)

// DataCardValue2.SearchItems
Choices(Participants.'Participation status',DataCardValue2.SearchText)
