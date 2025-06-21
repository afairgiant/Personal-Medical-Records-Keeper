# Medical Records Management System - Test Runner (PowerShell)
# Usage: .\run_tests.ps1 <test_type>

param(
    [Parameter(Mandatory=$false)]
    [string]$TestType = "help",
    
    [Parameter(Mandatory=$false)]
    [string]$TestFile = ""
)

function Write-Banner {
    param([string]$Message)
    Write-Host "=" * 60 -ForegroundColor Yellow
    Write-Host $Message -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Yellow
}

function Run-TestCommand {
    param(
        [string[]]$Command,
        [string]$Description
    )
    
    Write-Banner $Description
    Write-Host "Command: $($Command -join ' ')" -ForegroundColor Cyan
    
    try {
        & $Command[0] $Command[1..($Command.Length-1)]
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Tests completed successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Error running command: $_" -ForegroundColor Red
    }
}

# Ensure we're in the project directory
$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDir

# Base pytest command
$BasePytest = @("python", "-m", "pytest")

switch ($TestType.ToLower()) {
    "all" {
        $cmd = $BasePytest + @("tests/")
        Run-TestCommand $cmd "All Tests"
    }
    
    "unit" {
        $cmd = $BasePytest + @("-m", "unit", "tests/")
        Run-TestCommand $cmd "Unit Tests"
    }
    
    "integration" {
        $cmd = $BasePytest + @("tests/test_integration.py")
        Run-TestCommand $cmd "Integration Tests"
    }
    
    "auth" {
        $cmd = $BasePytest + @("tests/test_auth.py")
        Run-TestCommand $cmd "Authentication Tests"
    }
    
    "api" {
        $cmd = $BasePytest + @("tests/test_api.py")
        Run-TestCommand $cmd "API Tests"
    }
    
    "patients" {
        $cmd = $BasePytest + @("tests/test_patients.py")
        Run-TestCommand $cmd "Patient-related Tests"
    }
    
    "medical" {
        $cmd = $BasePytest + @("tests/test_medical_records.py")
        Run-TestCommand $cmd "Medical Records Tests"
    }
    
    "users" {
        $cmd = $BasePytest + @("tests/test_users.py")
        Run-TestCommand $cmd "User Management Tests"
    }
    
    "security" {
        $cmd = $BasePytest + @("-m", "security", "tests/")
        Run-TestCommand $cmd "Security Tests"
    }
    
    "quick" {
        $cmd = $BasePytest + @("-m", "not slow", "tests/")
        Run-TestCommand $cmd "Quick Tests (excluding slow tests)"
    }
    
    "coverage" {
        try {
            python -c "import pytest_cov" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $cmd = $BasePytest + @("--cov=app", "--cov-report=html", "--cov-report=term-missing", "tests/")
                Run-TestCommand $cmd "Tests with Coverage Report"
                Write-Host "`n📊 Coverage report generated in htmlcov/ directory" -ForegroundColor Cyan
            } else {
                throw "pytest-cov not found"
            }
        }
        catch {
            Write-Host "⚠️  pytest-cov not installed. Install with: pip install pytest-cov" -ForegroundColor Yellow
            $cmd = $BasePytest + @("tests/")
            Run-TestCommand $cmd "All Tests (without coverage)"
        }
    }
    
    "verbose" {
        $cmd = $BasePytest + @("-v", "-s", "tests/")
        Run-TestCommand $cmd "Verbose Tests"
    }
    
    "file" {
        if (-not $TestFile) {
            Write-Host "❌ Please specify a test file name" -ForegroundColor Red
            Write-Host "Usage: .\run_tests.ps1 file -TestFile <test_file_name>" -ForegroundColor Yellow
            exit 1
        }
        
        if (-not $TestFile.StartsWith("test_")) {
            $TestFile = "test_$TestFile"
        }
        if (-not $TestFile.EndsWith(".py")) {
            $TestFile = "$TestFile.py"
        }
        
        $cmd = $BasePytest + @("tests/$TestFile")
        Run-TestCommand $cmd "Specific Test File: $TestFile"
    }
    
    "help" {
        Write-Host "Medical Records Management System - Test Runner (PowerShell)" -ForegroundColor Green
        Write-Host "=" * 60 -ForegroundColor Yellow
        Write-Host "Usage: .\run_tests.ps1 <test_type> [-TestFile <filename>]" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Available test types:" -ForegroundColor White
        Write-Host "  all          - Run all tests" -ForegroundColor Gray
        Write-Host "  unit         - Run unit tests only" -ForegroundColor Gray
        Write-Host "  integration  - Run integration tests only" -ForegroundColor Gray
        Write-Host "  auth         - Run authentication tests only" -ForegroundColor Gray
        Write-Host "  api          - Run API tests only" -ForegroundColor Gray
        Write-Host "  patients     - Run patient-related tests" -ForegroundColor Gray
        Write-Host "  medical      - Run medical records tests" -ForegroundColor Gray
        Write-Host "  users        - Run user management tests" -ForegroundColor Gray
        Write-Host "  security     - Run security tests only" -ForegroundColor Gray
        Write-Host "  quick        - Run quick tests (excludes slow tests)" -ForegroundColor Gray
        Write-Host "  coverage     - Run tests with coverage report" -ForegroundColor Gray
        Write-Host "  verbose      - Run tests with verbose output" -ForegroundColor Gray
        Write-Host "  file         - Run specific test file (use -TestFile parameter)" -ForegroundColor Gray
        Write-Host "  help         - Show this help message" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor White
        Write-Host "  .\run_tests.ps1 all" -ForegroundColor Cyan
        Write-Host "  .\run_tests.ps1 auth" -ForegroundColor Cyan
        Write-Host "  .\run_tests.ps1 file -TestFile auth" -ForegroundColor Cyan
        Write-Host "  .\run_tests.ps1 coverage" -ForegroundColor Cyan
    }
    
    default {
        Write-Host "❌ Unknown test type: $TestType" -ForegroundColor Red
        Write-Host "Run '.\run_tests.ps1 help' for available options" -ForegroundColor Yellow
    }
}
