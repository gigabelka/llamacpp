param([switch]$Revert)
# Apply (or revert) the no-reasoning patch to the installed Strata server.
# `terminal\current` follows a `strata update` to the new version's serve\ folder.
# Before the first patch each file is kept beside itself as <name>.pre-no-reasoning.
# The 0.1.69 originals in .\backup\*.orig are history, not a revert source for a newer build.
#
# Thinking is OFF by default and ON only when the server process sees STRATA_ALLOW_THINKING=1.
# strata\run-iq3_s-coding-reason.bat sets that variable; nothing else does, so the noreason
# preset, install\run-iq3_s.bat and plain `strata launch` keep the behaviour documented in
# strata\README.md section 4. The gate is in both layers: frontend.py (both dialects) and
# chat_template.jinja (which cannot think unless frontend.py passes the flag).

$ErrorActionPreference = 'Stop'
$serve  = 'C:\Users\viktor\AppData\Local\Strata\terminal\current\serve'
$front  = Join-Path $serve 'frontend.py'
$tpl    = Join-Path $serve 'chat_template.jinja'
$enc    = New-Object System.Text.UTF8Encoding($false)

function Read-Text($path) { [IO.File]::ReadAllText($path) }
function Write-Text($path, $text) { [IO.File]::WriteAllText($path, $text, $enc) }
function LF($text) { $text -replace "`r`n", "`n" }

if ($Revert) {
    foreach ($file in @($front, $tpl)) {
        $pre = "$file.pre-no-reasoning"
        if (-not (Test-Path $pre)) {
            throw "$file was not patched by this script (no $pre); restore it with 'strata update' or the component repair instead of copying an older build's file."
        }
        Copy-Item $pre $file -Force
    }
    Write-Output 'reverted serve\frontend.py and serve\chat_template.jinja from their .pre-no-reasoning copies'
    exit 0
}

$frontText = Read-Text $front
$tplText   = Read-Text $tpl
$changed   = @()
$return = '    return _env_to_user(_late_system_to_user(messages)), tools, kwargs'

# The gate inserted into both request dialects of frontend.py. 4 spaces: the body of the
# two to_messages functions. `os` is already imported by frontend.py.
$gate = @"
    if not os.environ.get("STRATA_ALLOW_THINKING"):
        kwargs["enable_thinking"] = False       # no-reasoning patch: this request renders without <think> unless STRATA_ALLOW_THINKING=1
    kwargs["strata_allow_thinking"] = bool(os.environ.get("STRATA_ALLOW_THINKING"))
"@
$gate = LF $gate

$oldOpenai = @"
            kwargs.update(effort_kwargs(v))
    kwargs["enable_thinking"] = False        # no-reasoning patch: every OpenAI request renders without <think>
$return
"@
$oldOpenai = LF $oldOpenai
$newOpenai = @"
            kwargs.update(effort_kwargs(v))
$gate
$return
"@
$newOpenai = LF $newOpenai
$cleanOpenai = @"
            kwargs.update(effort_kwargs(v))
$return
"@
$cleanOpenai = LF $cleanOpenai

$oldAnthropic = @"
        kwargs["enable_thinking"] = False
    kwargs["enable_thinking"] = False        # no-reasoning patch: every Anthropic request renders without <think>
$return
"@
$oldAnthropic = LF $oldAnthropic
$newAnthropic = @"
        kwargs["enable_thinking"] = False
$gate
$return
"@
$newAnthropic = LF $newAnthropic
$cleanAnthropic = @"
        kwargs["enable_thinking"] = False
$return
"@
$cleanAnthropic = LF $cleanAnthropic

$oldTpl = @"
{%- endif %}
{%- set enable_thinking = false %}
{%- set sysns = namespace(count=0, text='') %}
"@
$oldTpl = LF $oldTpl
$cleanTpl = @"
{%- endif %}
{%- set sysns = namespace(count=0, text='') %}
"@
$cleanTpl = LF $cleanTpl
$newTpl = @"
{%- endif %}
{%- set enable_thinking = (enable_thinking | default(true)) and (strata_allow_thinking | default(false)) %}
{%- set sysns = namespace(count=0, text='') %}
"@
$newTpl = LF $newTpl

# --- frontend.py ---------------------------------------------------------------------------
if (-not $frontText.Contains('strata_allow_thinking')) {
    if (-not (Test-Path "$front.pre-no-reasoning")) { Copy-Item $front "$front.pre-no-reasoning" -Force }

    $upgrading = $frontText -match 'no-reasoning patch'
    if ($upgrading) {
        $pairs = @(@($oldOpenai, $newOpenai, 'OpenAI'), @($oldAnthropic, $newAnthropic, 'Anthropic'))
    } else {
        $pairs = @(@($cleanOpenai, $newOpenai, 'OpenAI'), @($cleanAnthropic, $newAnthropic, 'Anthropic'))
    }
    $out = $frontText
    foreach ($pair in $pairs) {
        if (-not $out.Contains($pair[0])) { throw "frontend.py: $($pair[2]) anchor not found (a different Strata build?)" }
        $out = $out.Replace($pair[0], $pair[1])
    }
    if ($out -eq $frontText) { throw 'frontend.py: nothing changed (anchors matched empty text?)' }
    $frontText = $out
    Write-Text $front $frontText
    $changed += $(if ($upgrading) { 'frontend.py (upgraded)' } else { 'frontend.py' })
}

# --- chat_template.jinja -------------------------------------------------------------------
if (-not $tplText.Contains('strata_allow_thinking')) {
    if (-not (Test-Path "$tpl.pre-no-reasoning")) { Copy-Item $tpl "$tpl.pre-no-reasoning" -Force }
    $upgrading = $tplText.Contains('{%- set enable_thinking = false %}')
    $anchor = $(if ($upgrading) { $oldTpl } else { $cleanTpl })
    if (-not $tplText.Contains($anchor)) { throw 'chat_template.jinja: anchor not found (a different Strata build?)' }
    $tplText = $tplText.Replace($anchor, $newTpl)
    Write-Text $tpl $tplText
    $changed += $(if ($upgrading) { 'chat_template.jinja (upgraded)' } else { 'chat_template.jinja' })
}

if ($changed.Count -eq 0) { Write-Output 'already patched; nothing to do' }
else { Write-Output ('patched: ' + ($changed -join ', ')) }
