param([string]$Email="admin@example.com",[string]$Password="Admin123!")

$J = @{ email=$Email; password=$Password } | ConvertTo-Json
$resp = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5060/api/login -ContentType 'application/json' -Body $J

$env:ESTATECORE_TOKEN = $resp.access_token
$env:ESTATECORE_REFRESH = $resp.refresh_token

Write-Host "OK. Token stored in `$env:ESTATECORE_TOKEN"
