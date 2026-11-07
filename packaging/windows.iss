#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{6E9EE0AA-C970-47CD-9E16-D4CBA61F3144}
AppName=WinLS
AppVersion={#AppVersion}
AppPublisher=WinLS
DefaultDirName={localappdata}\Programs\WinLS
DefaultGroupName=WinLS
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\release
OutputBaseFilename=WinLS-{#AppVersion}-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\WindowsLocationSimulator.exe

[InstallDelete]
Type: files; Name: "{app}\_internal\icuuc.dll"
Type: files; Name: "{app}\_internal\icudt78.dll"

[Files]
Source: "..\dist\WindowsLocationSimulator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\WinLS"; Filename: "{app}\WindowsLocationSimulator.exe"
Name: "{autodesktop}\WinLS"; Filename: "{app}\WindowsLocationSimulator.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\WindowsLocationSimulator.exe"; Description: "Launch WinLS"; Flags: nowait postinstall skipifsilent

