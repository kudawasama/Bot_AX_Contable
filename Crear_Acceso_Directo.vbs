Set oWS = WScript.CreateObject("WScript.Shell")
sDesktop = oWS.SpecialFolders("Desktop")
sScriptDir = oWS.CurrentDirectory

' Nombre del acceso directo
sLinkFile = sDesktop & "\Bot AX Contable {Cotano_}.lnk"

Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = sScriptDir & "\Lanzar_Bot_Universal.bat"
oLink.WorkingDirectory = sScriptDir
oLink.Description = "Sistema Automático de Contabilidad AX"
oLink.Save

WScript.Echo "Acceso directo creado en el Escritorio con exito."
