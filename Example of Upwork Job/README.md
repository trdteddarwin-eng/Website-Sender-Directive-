# Example of Upwork Job

This folder contains examples of Upwork jobs the user has approved. Each file represents a job that was reviewed, approved ("yes, let's do this"), and either applied to or identified as a good fit.

## Purpose
- **Reference guide** for the auto-apply pipeline — read these before scoring/classifying new jobs
- **Taste profile** — these examples define what a good job looks like for this user
- **Dedup check** — if a scraped job matches one already here, skip it
- **Training data** — use the patterns (budget ranges, skill requirements, job types, client profiles) to improve AI scoring accuracy

## File Format

Each job file should be named: `YYYY-MM-DD_short-job-title.md`

Example content:
```markdown
# Job Title
- **URL:** https://www.upwork.com/jobs/~01234567890
- **Budget:** $1,500 fixed
- **Type:** website | automation | other
- **Skills:** React, Node.js, etc.
- **Status:** applied | approved | won | lost
- **Date Added:** 2026-02-23

## Description
[Paste or summarize the job description]

## Why This Was a Good Fit
[Brief note on why this job was approved]
```

## How the Pipeline Uses This

1. Before Phase 2 (AI scoring), the classifier reads this folder to calibrate what "relevant" means
2. Before Phase 5 (auto-apply), the pipeline checks if the job URL already exists here
3. After user approves a job ("yes, let's do this"), it gets added here automatically
