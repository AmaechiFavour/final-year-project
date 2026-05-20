# setup-email.ps1 - Email Configuration Script for Windows
# Usage: Run this script in PowerShell to configure email for the Flask app

Write-Host "=== E-Learning Portal Email Configuration ===" -ForegroundColor Green
Write-Host ""

# Prompt for email configuration
$email = Read-Host "Enter your Gmail email address"
$appPassword = Read-Host "Enter your Gmail app password (not your regular password)" -AsSecureString

# Convert secure string to plain text for environment variable
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($appPassword)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Set environment variables
[Environment]::SetEnvironmentVariable("MAIL_USERNAME", $email, "User")
[Environment]::SetEnvironmentVariable("MAIL_PASSWORD", $plainPassword, "User")
[Environment]::SetEnvironmentVariable("MAIL_SERVER", "smtp.gmail.com", "User")
[Environment]::SetEnvironmentVariable("MAIL_PORT", "465", "User")

Write-Host ""
Write-Host "✓ Email configuration saved!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: You need to restart your PowerShell/Terminal for changes to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Steps to get your Gmail App Password:" -ForegroundColor Cyan
Write-Host "1. Go to: https://myaccount.google.com/apppasswords" 
Write-Host "2. Select 'Mail' and 'Windows Computer'"
Write-Host "3. Copy the generated 16-character password"
Write-Host "4. Paste it when prompted above"
