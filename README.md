# 📚 Smart Study Planner Agent (no API needed)

You enter subjects, exam dates, difficulty (1-5) and confidence (1-5), plus how many hours
you can study per day. The agent gives every 30-minute block to the subject that needs it most.

**How it decides** (`api/_planner.py`, about 100 lines of plain Python):
- need = difficulty x (6 - confidence)
- urgency grows as the exam gets closer
- the next block goes to the highest need x urgency, shared out fairly over time
- 3 days before the exam: "Revise" mode. 1 day before: "Final revision" mode
- rest days are skipped, and it warns you when your time is too short

No database, no API keys, no packages to install. Uses only the Python standard library.

## Run on your computer
```bash
python local_server.py        # open http://localhost:3000
python tests/test_planner.py  # optional: quick checks (or: pytest)
```

## Deploy to Vercel (free)
**Option A: command line**
```bash
npm i -g vercel
vercel login
vercel --prod
```
**Option B: GitHub**
1. Push this folder to a GitHub repository.
2. Go to vercel.com > Add New > Project > import the repo.
3. Leave all settings as they are and click Deploy.

Vercel serves `public/` as the website and runs `api/plan.py` as a Python function.
Files starting with `_` (like `_planner.py`) are helpers and are not exposed as URLs.

## Run in VS Code
1. Install Python 3.9+ and VS Code, then install the **Python** extension.
2. VS Code > File > Open Folder > choose `study_agent`.
3. Press **F5** (or Run and Debug > "Run Study Planner website").
   The browser opens at http://localhost:3000.
4. To run the checks: Run and Debug > "Run tests", or Terminal > Run Task > "Run tests".
5. Stop the server with the red square in the debug toolbar.
