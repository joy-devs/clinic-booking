# AI Notes

## 1. What I used AI for
- **Section 1 (design):** explained the design questions and drafted the design write-up, which I reviewed and edited.
- **Section 2 (API):** helped write the models, seed script, availability, booking, cancel, reschedule and patient endpoints, plus the pytest tests. I ran and tested each endpoint in /docs.
- **Extra features:** helped write the slot ids and statuses, blocked periods, doctor leave, leave notices, the weekend rota, the patient list, descriptive id names and the fill-in templates for the forms.
- **Section 3 (deployment):** guided me through deploying to Render and setting up the GitHub Actions pipeline, and helped read the deploy logs when the first deploy failed.
- **Setup:** helped me get Python, VS Code, Git and the virtual environment working after a year away from coding.
- **Understanding:** explained how cancel, reschedule, UTC and the date format work until I could follow them.
- **Documents:** helped draft the README and these notes, which I edited.

## 2. Where AI improved my work
- I answered the design questions in my own words first. The AI pointed out that double booking can't be prevented by the GET alone and needs a re-check at booking time plus a database constraint. Prompt: I sent my answers and asked for them to be corrected and sharpened.
- The AI suggested keeping slots calculated from working hours, with a stable slot id, instead of storing slot rows. That matched my own design and avoided rewriting the booking logic.

## 3. Where AI was wrong or incomplete, and how I caught it
- **Setup commands:** the `type nul > file` commands failed in my PowerShell terminal. I caught it from the red error and the missing files in the sidebar, and used the PowerShell version instead.
- **Render deploy:** the first deploy failed with `No module named 'psycopg'`. The AI had told me to use an unpinned `requirements.txt` and a `postgresql://` address, and the newer SQLAlchemy picked a different driver. I caught it by reading the deploy logs, and fixed it by naming the `psycopg2` driver explicitly in `database.py`.
- **Swagger examples:** the first examples were pre-filled with real-looking values, such as a patient name and a booking date. I noticed on the live app that they looked like saved data. I asked for templates instead, and later asked for ids to read as “Enter doctor id” and for start fields to come before end fields.
- **Example clashing with sample data:** a pre-filled booking example landed on the same day as a sample leave day and returned a 409. This was found while testing, and the sample leave was moved two weeks out.
- **Availability gap:** the availability endpoint hid past slots but not slots inside the next hour, while booking rejected them. I noticed the mismatch, and it was fixed when slot statuses were added.
- **Code delivered in pieces:** I pasted snippets into the wrong place and broke things. A missing cancel and reschedule block failed 5 tests, `booking.py` lost earlier functions and raised an ImportError, and I overwrote a test file and got a NameError. I fixed each by reading the error message, and asked for whole files after that.

## 4. Decisions I made without AI
- **Slots from working hours:** I decided to calculate slots from the doctor’s working hours instead of storing them. I gave this answer myself in the design step. I trusted it because it avoids creating and cleaning up slot rows.
- **Features from using the system:** I decided what to add from using the API as a patient and as clinic staff: breaks and leave for doctors, notices when a doctor is away, weekend shifts, a patient list, templates in the forms, clearly named ids and start fields before end fields. I trusted my judgment because I could see where a real user would get stuck.
- **Submitting the live link:** I decided to focus on the live app, since that is what the reviewers will open. I checked it directly after each change.

## What I verified myself
- Every endpoint in /docs on my computer and on the live app: success cases, 400, 404 and 409 errors.
- That a booked slot disappears from availability, and a cancelled or rescheduled slot comes back.
- That booking outside working hours, on a weekend with no hours, on a leave day, or inside a blocked period is rejected.
- The full test suite (56 tests), and that GitHub Actions ran green before each deploy.
- That the live app matched my latest code after each merge.

## Mistakes I made and fixed
- Misspelled `appointments` as `appointements` in an import.
- Pasted code over a file instead of adding to the bottom.
- Typed the example date twice in the leave date box, which sent a garbled date.
- Left the repository private until I checked the submission list.