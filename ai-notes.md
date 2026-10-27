# AI Notes

## 1. What I used AI for
- Section 1: explained the design questions and drafted the README design, which I then edited.
- Section 2: helped write the models, seed script, availability, booking, cancel, reschedule and patient endpoints, plus the pytest tests. I ran and tested each endpoint in /docs.
- Section 3: guided me through deploying to Render and setting up the GitHub Actions pipeline.
- Setup: helped me get Python, VS Code and the virtual environment working after a year away from coding.
- Understanding: explained how cancel and reschedule work until I could follow them.

## 2. Where AI improved my work
- I answered the design questions in my own words first. The AI pointed out that double booking can't be prevented by the GET alone and needs a re-check at booking time plus a database constraint. Prompt: I sent my answers and asked for them to be corrected and sharpened.

## 3. Where AI was wrong or incomplete, and how I caught it
- The setup commands (`type nul > file`) failed in my PowerShell terminal. I caught it from the red error and the missing files in the sidebar, and used the PowerShell version instead.
- The availability endpoint hides past slots but not slots inside the next hour, while booking rejects them. I noticed the mismatch when reading how the project fits together. (Add whether you fixed it.)
- Add anything else you actually hit, for example the import errors you fixed.

## Mistakes I made and fixed
- Misspelled `appointments` in an import and pasted code over a file. I fixed both by reading the error messages.