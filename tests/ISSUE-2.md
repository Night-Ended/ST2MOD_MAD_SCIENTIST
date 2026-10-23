# Issue 2 checks on Windows

Use PowerShell 7, an existing .NET 9 SDK, and locally installed game/BaseLib assemblies:

```powershell
./tests/run_issue2.ps1 `
  -DotnetPath 'C:/path/to/dotnet.exe' `
  -GameDirectory 'C:/path/to/Slay the Spire 2' `
  -BaseLibAssembly 'C:/path/to/BaseLib.dll'
python tests/validate_resources.py
```

The offline runner downloads nothing, restores process environment variables on exit, and writes local build outputs/logs under .validation and test bin/obj directories. It does not launch or install a mod. Results: **80 contract assertions**, **534 static resource assertions**, and **0 compiler errors / 18 existing nullable warnings** against installed public-beta v0.111.0 and BaseLib 3.4.7. The original Python validator separately passed **4/4** checks.

Contract tests link actual production implementations against narrow game doubles and real Harmony. tests/InstalledApi compiles all production C# against installed game, Harmony, GodotSharp and BaseLib assemblies. It omits Godot generators, mod analyzers and packing. Its DLL is a compile-check artifact, not an installable release.

The full MadScientist.csproj restore eventually succeeded from official nuget.org. The subsequent full build failed with **17 STS001 errors / 20 warnings**: missing power smart descriptions, Architect dialogue keys and unprefixed FusedXCard localization. These unresolved blockers and evidence are detailed in docs/issue-2-validation.md.

The 63-card matrix explicitly leaves game play, upgrade, copy/fusion, save/reload and multiplayer unverified. Maintainers must resolve the release build and perform those checks. Do not run the existing tools/test_headless.ps1 on official user data; use verified disposable user-data and Steam-cloud isolation. Multiplayer needs a second client. Static key/group/header checks do not demonstrate correct rendered localization or layout.
