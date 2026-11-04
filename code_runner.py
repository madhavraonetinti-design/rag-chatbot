"""Run C# practice submissions with a local .NET SDK in a temporary project."""

import shutil
import subprocess
import tempfile
from pathlib import Path


def run_csharp_solution(solution, harness, timeout_seconds=20):
    """Compile and execute a challenge harness; return real build/test output."""
    dotnet = shutil.which("dotnet")
    if not dotnet:
        return {
            "available": False,
            "passed": False,
            "output": "Install the .NET 8 SDK and reopen your terminal to run C# code locally.",
            "tests_passed": 0,
            "tests_total": 0,
        }

    with tempfile.TemporaryDirectory(prefix="csharp-practice-") as temporary_dir:
        project_dir = Path(temporary_dir)
        project_file = project_dir / "Practice.csproj"
        source_file = project_dir / "Program.cs"
        project_file.write_text(
            """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
""",
            encoding="utf-8",
        )
        source_file.write_text(f"{solution}\n{harness}\n", encoding="utf-8")
        try:
            result = subprocess.run(
                [dotnet, "run", "--project", str(project_file), "--configuration", "Release"],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                cwd=project_dir,
            )
        except subprocess.TimeoutExpired:
            return {
                "available": True,
                "passed": False,
                "output": f"Execution exceeded the {timeout_seconds}-second limit and was stopped.",
                "tests_passed": 0,
                "tests_total": 0,
            }

    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    tests_passed = sum(line.startswith("PASS ") for line in result.stdout.splitlines())
    tests_total = tests_passed + sum(line.startswith("FAIL ") for line in result.stdout.splitlines())
    return {
        "available": True,
        "passed": result.returncode == 0 and tests_total > 0 and tests_passed == tests_total,
        "output": output or "The C# program completed without output.",
        "tests_passed": tests_passed,
        "tests_total": tests_total,
    }