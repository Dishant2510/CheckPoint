; Inno Setup Script for CheckPoint
; CheckPoint — Universal PC Game Save Backup & Restore Manager

#define MyAppName "CheckPoint"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CheckPoint Team"
#define MyAppURL "https://github.com/yourusername/checkpoint"
#define MyAppExeName "CheckPoint.exe"

[Setup]
; Unique App ID (generated for CheckPoint)
AppId={{C4E3A9D1-BD82-4E2F-A00A-A90F845C334A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Place the generated setup file in a folder named 'installer_dist'
OutputDir=installer_dist
OutputBaseFilename=CheckPointSetup
SetupIconFile=app\assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Requires Windows 7 SP1 or newer
MinVersion=6.1.7601

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all files from the PyInstaller dist/CheckPoint folder
Source: "dist\CheckPoint\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
