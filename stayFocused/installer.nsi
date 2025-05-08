!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "StayFocused"
OutFile "StayFocused-Setup.exe"
InstallDir "$PROGRAMFILES\StayFocused"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\StayFocused.exe"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  
  # Add files
  File "dist\StayFocused.exe"
  File "LICENSE.txt"
  
  # Create start menu shortcuts
  CreateDirectory "$SMPROGRAMS\StayFocused"
  CreateShortcut "$SMPROGRAMS\StayFocused\StayFocused.lnk" "$INSTDIR\StayFocused.exe"
  CreateShortcut "$SMPROGRAMS\StayFocused\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  # Create desktop shortcut
  CreateShortcut "$DESKTOP\StayFocused.lnk" "$INSTDIR\StayFocused.exe"
  
  # Write uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  # Add uninstall information to Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "DisplayName" "StayFocused"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "DisplayIcon" "$INSTDIR\StayFocused.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "Publisher" "Govinda Tudu"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "DisplayVersion" "1.0.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "URLInfoAbout" "https://github.com/govinda520"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                   "HelpLink" "https://github.com/govinda520"
  
  # Get size of installed files
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused" \
                     "EstimatedSize" "$0"
SectionEnd

Section "Uninstall"
  # Remove files
  Delete "$INSTDIR\StayFocused.exe"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\uninstall.exe"
  
  # Remove shortcuts
  Delete "$SMPROGRAMS\StayFocused\StayFocused.lnk"
  Delete "$SMPROGRAMS\StayFocused\Uninstall.lnk"
  Delete "$DESKTOP\StayFocused.lnk"
  
  # Remove directories
  RMDir "$SMPROGRAMS\StayFocused"
  RMDir "$INSTDIR"
  
  # Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\StayFocused"
SectionEnd 