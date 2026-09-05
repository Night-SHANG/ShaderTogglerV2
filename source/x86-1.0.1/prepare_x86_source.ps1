$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $root "patched-source"
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
git clone --depth 1 --branch 1.0.1 https://github.com/FransBouma/ShaderToggler.git $out
python (Join-Path $root "apply_x86_1.0.1_cn_repeat.py") $out
Write-Host "x86 1.0.1 modified source is ready at: $out"
