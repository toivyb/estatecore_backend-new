# EstateCore Backend Smoke Test Script
# Logs in as super_admin, retrieves token, and calls all major endpoints.

# 1. Login and capture token
$login = Invoke-RestMethod -Method POST `
  -Uri https://estatecore-backend-floral-hill-9253.fly.dev/login `
  -ContentType application/json `
  -Body (@{ email="admin@example.com"; password="admin123" } | ConvertTo-Json)

$token = $login.access_token
Write-Host "Token: $token"

# 2. /me endpoint
Write-Host "`n---- /me ----"
Invoke-RestMethod -Method GET `
  -Uri https://estatecore-backend-floral-hill-9253.fly.dev/me `
  -Headers @{ Authorization = "Bearer $token" }

# 3. /add-user
Write-Host "`n---- /add-user ----"
Invoke-RestMethod -Method POST `
  -Uri https://estatecore-backend-floral-hill-9253.fly.dev/add-user `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType application/json `
  -Body (@{ email="newuser@test.com"; password="test123"; role="tenant" } | ConvertTo-Json)

# 4. /rent/list
Write-Host "`n---- /rent/list ----"
Invoke-RestMethod -Method GET `
  -Uri https://estatecore-backend-floral-hill-9253.fly.dev/rent/list `
  -Headers @{ Authorization = "Bearer $token" }

# 5. /maintenance/list
Write-Host "`n---- /maintenance/list ----"
Invoke-RestMethod -Method GET `
  -Uri https://estatecore-backend-floral-hill-9253.fly.dev/maintenance/list `
  -Headers @{ Authorization = "Bearer $token" }

# 6. /access/logs (super admin only)
Write-Host "`n---- /access/logs ----"
Invoke-RestMethod -Method GET `
  -Uri https://estatecore-backend-floral-hill-9253.fly.dev/access/logs `
  -Headers @{ Authorization = "Bearer $token" }
