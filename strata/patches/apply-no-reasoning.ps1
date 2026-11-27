param([switch]$Revert)
# Apply (or revert) the no-reasoning patch to the installed Strata 0.1.69 server.
# Originals are kept in .\backup\*.orig.  `strata update` replaces serve\ and undoes this.

$ErrorActionPreference = 'Stop'
$serve  = 'C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\serve'
$backup = Join-Path $PSScriptRoot 'backup'
$front  = Join-Path $serve 'frontend.py'
$tpl    = Join-Path $serve 'chat_template.jinja'
$enc    = New-Object System.Text.UTF8Encoding($false)

function Read-Text($path) { [IO.File]::ReadAllText($path) }
function Write-Text($path, $text) { [IO.File]::WriteAllText($path, $text, $enc) }

if ($Revert) {
    Copy-Item (Join-Path $backup 'frontend.py.orig') $front -Force
    Copy-Item (Join-Path $backup 'chat_template.jinja.orig') $tpl -Force
    Write-Output 'reverted serve\frontend.py and serve\chat_template.jinja from .\backup'
    exit 0
}

$frontText = Read-Text $front
$tplText   = Read-Text $tpl
$changed   = @()

# 1) frontend.py: force enable_thinking=False for both request dialects before the template kwargs leave.
$openaiAnchor = @"
            kwargs.update(effort_kwargs(v))
    return _env_to_user(_late_system_to_user(messages)), tools, kwargs
"@
$openaiNew = @"
            kwargs.update(effort_kwargs(v))
    kwargs["enable_thinking"] = False        # no-reasoning patch: every OpenAI request renders without <think>
    return _env_to_user(_late_system_to_user(messages)), tools, kwargs
"@
$anthropicAnchor = @"
        kwargs["enable_thinking"] = False
    return _env_to_user(_late_system_to_user(messages)), tools, kwargs
"@
$anthropicNew = @"
        kwargs["enable_thinking"] = False
    kwargs["enable_thinking"] = False        # no-reasoning patch: every Anthropic request renders without <think>
    return _env_to_user(_late_system_to_user(messages)), tools, kwargs
"@
if ($frontText -notmatch 'no-reasoning patch') {
    if (-not $frontText.Contains($openaiAnchor)) { throw 'frontend.py: OpenAI anchor not found (a different Strata build?)' }
    if (-not $frontText.Contains($anthropicAnchor)) { throw 'frontend.py: Anthropic anchor not found (a different Strata build?)' }
    $frontText = $frontText.Replace($openaiAnchor, $openaiNew).Replace($anthropicAnchor, $anthropicNew)
    Write-Text $front $frontText
    $changed += 'frontend.py'
}

# 2) chat_template.jinja: the template can no longer think even if a caller forgets to pass the flag.
if ($tplText -notmatch 'set enable_thinking = false') {
    $tplAnchor = @"
{%- endif %}
{%- set sysns = namespace(count=0, text='') %}
"@
    $tplNew = @"
{%- endif %}
{%- set enable_thinking = false %}
{%- set sysns = namespace(count=0, text='') %}
"@
    if (-not $tplText.Contains($tplAnchor)) { throw 'chat_template.jinja: anchor not found (a different Strata build?)' }
    $tplText = $tplText.Replace($tplAnchor, $tplNew)
    Write-Text $tpl $tplText
    $changed += 'chat_template.jinja'
}

if ($changed.Count -eq 0) { Write-Output 'already patched; nothing to do' }
else { Write-Output ('patched: ' + ($changed -join ', ')) }
