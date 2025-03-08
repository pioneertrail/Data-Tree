# Remove all __pycache__ directories
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force

# Remove all .pyc files
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File | Remove-Item -Force

Write-Host "Cleaned up Python cache files" 