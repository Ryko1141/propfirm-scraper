@echo off
REM Reorganize files into cleaner structure

echo.
echo ======================================================================
echo REORGANIZING FILES INTO CLEANER STRUCTURE
echo ======================================================================
echo.

REM Create docs folder structure
echo Creating folder structure...
mkdir docs\integration 2>nul
mkdir docs\implementation 2>nul
mkdir docs\features 2>nul
mkdir docs\summaries 2>nul
mkdir docs\guides 2>nul
mkdir docs\references 2>nul
echo Done!

echo.
echo Moving documentation files...
echo ----------------------------------------------------------------------

REM Integration docs
if exist COMPLETE_INTEGRATION.md move COMPLETE_INTEGRATION.md docs\integration\ && echo Moved COMPLETE_INTEGRATION.md
if exist INTEGRATION_SUMMARY.md move INTEGRATION_SUMMARY.md docs\integration\ && echo Moved INTEGRATION_SUMMARY.md
if exist RISK_MONITOR_INTEGRATION.md move RISK_MONITOR_INTEGRATION.md docs\integration\ && echo Moved RISK_MONITOR_INTEGRATION.md

REM Implementation docs
if exist IMPLEMENTATION.md move IMPLEMENTATION.md docs\implementation\ && echo Moved IMPLEMENTATION.md
if exist DATABASE_ARCHITECTURE.md move DATABASE_ARCHITECTURE.md docs\implementation\ && echo Moved DATABASE_ARCHITECTURE.md
if exist DATABASE_COMPLETE.md move DATABASE_COMPLETE.md docs\implementation\ && echo Moved DATABASE_COMPLETE.md
if exist TAXONOMY_INTEGRATION_COMPLETE.md move TAXONOMY_INTEGRATION_COMPLETE.md docs\implementation\ && echo Moved TAXONOMY_INTEGRATION_COMPLETE.md

REM Feature docs
if exist LLM_GUARDRAILS.md move LLM_GUARDRAILS.md docs\features\ && echo Moved LLM_GUARDRAILS.md
if exist MAX_DAILY_DD_RULE.md move MAX_DAILY_DD_RULE.md docs\features\ && echo Moved MAX_DAILY_DD_RULE.md
if exist NOTIFIER_REFACTOR.md move NOTIFIER_REFACTOR.md docs\features\ && echo Moved NOTIFIER_REFACTOR.md
if exist PROP_RULES.md move PROP_RULES.md docs\features\ && echo Moved PROP_RULES.md

REM Summary docs
if exist LLM_GUARDRAILS_SUMMARY.md move LLM_GUARDRAILS_SUMMARY.md docs\summaries\ && echo Moved LLM_GUARDRAILS_SUMMARY.md
if exist PIPELINE_UPDATE_SUMMARY.md move PIPELINE_UPDATE_SUMMARY.md docs\summaries\ && echo Moved PIPELINE_UPDATE_SUMMARY.md
if exist QA_TESTING_SUMMARY.md move QA_TESTING_SUMMARY.md docs\summaries\ && echo Moved QA_TESTING_SUMMARY.md
if exist PROJECT_STATUS.md move PROJECT_STATUS.md docs\summaries\ && echo Moved PROJECT_STATUS.md

REM Guide docs
if exist TESTING_GUIDE.md move TESTING_GUIDE.md docs\guides\ && echo Moved TESTING_GUIDE.md
if exist CONTRIBUTING.md move CONTRIBUTING.md docs\guides\ && echo Moved CONTRIBUTING.md

REM Reference docs
if exist PLATFORM_COMPARISON.md move PLATFORM_COMPARISON.md docs\references\ && echo Moved PLATFORM_COMPARISON.md

echo.
echo Moving script files...
echo ----------------------------------------------------------------------

REM Move scripts
if exist assess_scrape.py move assess_scrape.py scripts\ && echo Moved assess_scrape.py
if exist rescrape_missing.py move rescrape_missing.py scripts\ && echo Moved rescrape_missing.py
if exist validate_coverage.py move validate_coverage.py scripts\ && echo Moved validate_coverage.py
if exist run_all_tests.py move run_all_tests.py scripts\ && echo Moved run_all_tests.py

echo.
echo Moving test files...
echo ----------------------------------------------------------------------

REM Move tests
if exist test_integration.py move test_integration.py tests\ && echo Moved test_integration.py

echo.
echo ======================================================================
echo REORGANIZATION COMPLETE
echo ======================================================================
echo.
echo New structure:
echo   propfirm-scraper/
echo   ├── docs/
echo   │   ├── integration/      (integration guides)
echo   │   ├── implementation/   (technical details)
echo   │   ├── features/         (feature documentation)
echo   │   ├── summaries/        (project summaries)
echo   │   ├── guides/           (user guides)
echo   │   └── references/       (reference docs)
echo   ├── tests/                (all test files)
echo   ├── scripts/              (utility scripts)
echo   └── [config, database, examples, output, src]
echo.
echo Root directory is now much cleaner!
echo.
pause
