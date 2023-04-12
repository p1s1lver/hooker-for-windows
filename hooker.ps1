[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function PrintHookerHelpMsg () {
    $commands = @(
        @{Command="a"; Description="Discovering activities."; Example="a"},
        @{Command="b"; Description="Discovering services."; Example="b"},
        @{Command="c"; Description="Discovering object."; Example="c {objectId}"},
        @{Command="d"; Description="Object2Explain."; Example="d {objectId}"},
        @{Command="v"; Description="Discovering view."; Example="v {viewId}"},
        @{Command="e"; Description="Determines whether a class exists."; Example="e android.app.Application"},
        @{Command="s"; Description="Discovering classes by a class'regex."; Example="s com.tencent.mm.Message.*"},
        @{Command="t"; Description="Discovering offspring classes by a class'name."; Example="t com.tencent.mm.BasicActivity"},
        @{Command="j"; Description="Generating hooked js."; Example='j okhttp3.Request$Builder:build'},
        @{Command="k"; Description="Generating hooked the string generation js with a keyword."; Example="k {YourKeyword}"},
        @{Command="l"; Description="Generating hooked the param generation js with a param keyword."; Example="l {YourKeyword}"},
        @{Command="m"; Description="Discovering so module."; Example="m"},
        @{Command="ex/exit"; Description="Exit to the upper layer."; Example="ex"},
        @{Command="h/help"; Description="Prints this help message."; Example="h"}
    )

    $List = New-Object System.Collections.ArrayList
    $commands | ForEach-Object {
        $List.Add((New-Object PSObject -Property $_)) | Out-Null
    }

    $List | Format-Table -AutoSize -Property Command, Description, Example | Out-String -Width 4096
}

while ($true) {
    frida-ps -H 10.10.3.148:65320 -ai | Select-String -Pattern '@', '    -' -NotMatch
    Write-Host ""
    Write-Host "[👇] Please Choose Package to attach" -ForegroundColor Green
    $package = Read-Host ":"
    if ($package -eq "ex" -or $package -eq "exit" -or $package -eq "quit" -or $package -eq "q") {
        break
    }
    Write-Host "[🥂] Attached $package."
    python hooker.py -p $package -g true
    while ($true) {
        Write-Host ""
        Write-Host "[👇] Please Enter hooker command" -ForegroundColor Green
        $op = Read-Host ":"
        # help message
        if ($op -in "h", "help") { PrintHookerHelpMsg; continue }
        # exit hooker
        if ($op -in "ex", "exit") { Exit }
        # show activities and sevices
        if ($op -match "^[ab]$") { python hooker.py -p $package -$op true; continue }
        # customized actions
        if ($op -match "^v\s" -or $op -match "^l\s" -or $op -match "^c\s" -or $op -match "^d\s" -or $op -match "^s\s" -or $op -match "^t\s" -or $op -match "^e\s" -or $op -match "^j\s" -or $op -match "^k\s" -or $op -match "^m\s") {
            # Split $op into two parts using the first space as the separator
            $opParts = $op.Split(' ', 2)
            # If there are two parts, format the second part as "-c {secondPart}"
            if ($opParts.Length -eq 2) {
                Write-Host "[🚀] Running $op..." -ForegroundColor Green
                python hooker.py -p $package -$($opParts[0]) $($opParts[1])
            } else {
                Write-Host "[❗] Missing argument. Please enter the missing argument." -ForegroundColor Yellow
            }
            continue
        }
        Write-Host "❗Invalid command"
    }
}