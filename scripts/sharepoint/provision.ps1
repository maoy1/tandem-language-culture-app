[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [string]$SiteUrl,

    [string]$SchemaPath = "$PSScriptRoot/../../config/sharepoint_schema.json",

    [switch]$ValidateOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Result {
    param(
        [ValidateSet("OK", "CREATE", "MANUAL", "ERROR")]
        [string]$Level,
        [string]$Message
    )

    Write-Host ("[{0}] {1}" -f $Level, $Message)
}

if (-not (Get-Module -ListAvailable -Name PnP.PowerShell)) {
    throw "PnP.PowerShell is required. Install it once with: Install-Module PnP.PowerShell -Scope CurrentUser"
}

if (-not (Test-Path -LiteralPath $SchemaPath)) {
    throw "Schema file not found: $SchemaPath"
}

$schema = Get-Content -Raw -LiteralPath $SchemaPath | ConvertFrom-Json
$listDefinitions = @($schema.lists)

Connect-PnPOnline -Url $SiteUrl -Interactive

function Get-ConfiguredList {
    param([string]$ListName)
    return Get-PnPList -Identity $ListName -ErrorAction SilentlyContinue
}

function Ensure-List {
    param([object]$Definition)

    $list = Get-ConfiguredList -ListName $Definition.name
    if ($null -eq $list) {
        if ($ValidateOnly) {
            Write-Result -Level "ERROR" -Message "Missing list: $($Definition.name)"
            return $null
        }
        if ($PSCmdlet.ShouldProcess($Definition.name, "Create SharePoint list")) {
            New-PnPList -Title $Definition.name -Template GenericList | Out-Null
            Write-Result -Level "CREATE" -Message "Created list: $($Definition.name)"
            return Get-ConfiguredList -ListName $Definition.name
        }
    }

    Write-Result -Level "OK" -Message "List exists: $($Definition.name)"
    return $list
}

function Add-ConfiguredField {
    param(
        [string]$ListName,
        [object]$Definition
    )

    if ($Definition.provisioning -eq "manual") {
        Write-Result -Level "MANUAL" -Message "$ListName.$($Definition.internalName) must be created or checked in SharePoint as a $($Definition.type) field."
        return
    }

    if ($Definition.type -eq "Lookup") {
        $lookupList = Get-ConfiguredList -ListName $Definition.lookupList
        if ($null -eq $lookupList) {
            throw "Lookup target list is missing: $($Definition.lookupList)"
        }

        $required = if ($Definition.required -eq $true) { "TRUE" } else { "FALSE" }
        $multiple = if ($Definition.allowMultiple -eq $true) { "TRUE" } else { "FALSE" }
        $lookupId = "{$($lookupList.Id)}"
        $fieldXml = "<Field Type='Lookup' Name='$($Definition.internalName)' StaticName='$($Definition.internalName)' DisplayName='$($Definition.displayName)' List='$lookupId' ShowField='$($Definition.lookupField)' Mult='$multiple' Required='$required' />"

        if ($ValidateOnly) {
            Write-Result -Level "ERROR" -Message "Missing lookup field: $ListName.$($Definition.internalName)"
            return
        }

        if ($PSCmdlet.ShouldProcess("$ListName.$($Definition.internalName)", "Create SharePoint lookup field")) {
            Add-PnPFieldFromXml -List $ListName -FieldXml $fieldXml | Out-Null
            Write-Result -Level "CREATE" -Message "Created lookup field: $ListName.$($Definition.internalName)"
        }
        return
    }

    $parameters = @{
        List             = $ListName
        DisplayName      = $Definition.displayName
        InternalName     = $Definition.internalName
        Type             = $Definition.type
        AddToDefaultView = $false
    }

    if ($Definition.required -eq $true) {
        $parameters.Required = $true
    }
    if ($Definition.type -eq "Choice") {
        $parameters.Choices = @($Definition.choices)
    }

    if ($ValidateOnly) {
        Write-Result -Level "ERROR" -Message "Missing field: $ListName.$($Definition.internalName)"
        return
    }

    if ($PSCmdlet.ShouldProcess("$ListName.$($Definition.internalName)", "Create SharePoint field")) {
        $createdField = Add-PnPField @parameters
        if ($null -ne $Definition.defaultValue) {
            Set-PnPField -List $ListName -Identity $Definition.internalName -Values @{ DefaultValue = $Definition.defaultValue } | Out-Null
        }
        Write-Result -Level "CREATE" -Message "Created field: $ListName.$($Definition.internalName)"
    }
}

function Ensure-Index {
    param(
        [string]$ListName,
        [string]$FieldName
    )

    $field = Get-PnPField -List $ListName -Identity $FieldName -ErrorAction SilentlyContinue
    if ($null -eq $field) {
        Write-Result -Level "ERROR" -Message "Cannot index missing field: $ListName.$FieldName"
        return
    }

    if ($field.Indexed -eq $true) {
        Write-Result -Level "OK" -Message "Index exists: $ListName.$FieldName"
        return
    }

    if ($ValidateOnly) {
        Write-Result -Level "ERROR" -Message "Missing index: $ListName.$FieldName"
        return
    }

    if ($PSCmdlet.ShouldProcess("$ListName.$FieldName", "Create SharePoint list index")) {
        Set-PnPField -List $ListName -Identity $FieldName -Values @{ Indexed = $true } | Out-Null
        Write-Result -Level "CREATE" -Message "Created index: $ListName.$FieldName"
    }
}

foreach ($listDefinition in $listDefinitions) {
    $list = Ensure-List -Definition $listDefinition
    if ($null -eq $list) {
        continue
    }

    foreach ($fieldDefinition in @($listDefinition.fields)) {
        $field = Get-PnPField -List $listDefinition.name -Identity $fieldDefinition.internalName -ErrorAction SilentlyContinue
        if ($null -eq $field) {
            Add-ConfiguredField -ListName $listDefinition.name -Definition $fieldDefinition
            continue
        }

        if ($fieldDefinition.required -eq $true -and $field.Required -ne $true) {
            Write-Result -Level "ERROR" -Message "Field is not required: $($listDefinition.name).$($fieldDefinition.internalName)"
        } else {
            Write-Result -Level "OK" -Message "Field exists: $($listDefinition.name).$($fieldDefinition.internalName)"
        }
    }

    foreach ($index in @($listDefinition.indexes)) {
        Ensure-Index -ListName $listDefinition.name -FieldName $index
    }
}

Write-Host ""
if ($ValidateOnly) {
    Write-Host "Validation completed. ERROR entries require attention; MANUAL entries require one-time SharePoint checks."
} else {
    Write-Host "Provisioning completed. Review ERROR and MANUAL entries before using the lists."
}
