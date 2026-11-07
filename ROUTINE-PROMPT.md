# Monday routine: "Money Tricks Exposed - write next topics"

Created with RemoteTrigger (claude.ai/code/routines) once the GitHub account exists and github.com/apps/claude has access
to this repository: cron `30 8 * * 1` (Monday 08:30 UTC; the other channels run at 07:00, 07:30 and 08:00), model
`claude-sonnet-5-5`, source this repository, tools `Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch`, no MCP
connections, environment of the existing routines. Month 1 (topics 1 to 60) was written by hand on 2 Nov 2026: run the
routine once right after creating it to write the next 60, then spot-check its scripts.

## Prompt

You write the scripts for Money Tricks Exposed, an automated English short-video channel that exposes the tricks
stores, apps, restaurants, banks, casinos and advertisers use on people's money, and shows how to beat them. This
repository (money-tricks-exposed) is used by a daily GitHub Actions job that turns topics.json into videos of a bit over
one minute, posted PUBLICLY on TikTok and Instagram for an American audience. Each video: a warm woman's voice reads the
script line by line over real Pixabay stock footage; every word is captioned; some lines show a big punch card at the
top. The tone is a smart friend letting you in on a secret: curious, clear, never preachy, never fearmongering.
A false fact damages the account: every claim must be true and checked.

STEP 1 - Is work needed?
With python3, compute: written = ids in topics.json; used = state.json["en"] (missing file or key = empty list);
remaining = written ids not in used. If remaining >= 100, reply 'Enough topics: N left, nothing to do' and STOP (no commit).

STEP 2 - Choose topics.
Take the next 60 entries of topic_plan.json, in plan order (field n), whose id does not appear in any content/*.json
file. Fewer if the plan ends. If none are left, say the yearly plan is complete and stop.

STEP 3 - Write content/monthNN.json (NN = next two-digit month number after the existing files).
First read the docstring of src/add_content.py and content/month01.json to copy the exact format and style.
Each file is a JSON list of {"id", "lines": [{"text", "card", "scene", "search", "gap"}], "caption", "hashtags"}.
Rules for the script (one per plan entry, about its title and category):
- 16 to 21 lines, 175 to 215 spoken words in total (the voice speaks about three and a half words a second). Short,
  clear sentences; mix very short lines with longer ones; one idea per line.
- Arc: line 1 is the hook, a true and surprising claim of 10 words or fewer, no question mark, that makes people want
  the reveal (e.g. "The middle size on the menu is often a trap.", "Your phone does not need to listen to you.");
  then a concrete everyday scene; the trick revealed; the proof (a named study, a regulator, a court case, real numbers);
  why it works (the psychology, with its name when there is one); two or three concrete ways to beat it; a payoff line
  people want to screenshot; the LAST line asks to follow and contains the word follow.
- Vary the format across the month: experiment story, myth versus truth, history story, how to beat it, the number
  they hope you never do. The same arc sixty times in a row gets boring.
- Written for a voice reading aloud: no digits (write numbers and money in words: "six dollars and fifty cents",
  "twenty percent", "twenty twenty four"), no symbols, no double quotes, no parentheses, no emojis, no abbreviations
  (write "the Federal Trade Commission", "the United States", "cash machines"). Every line ends with . or ! or ?.
  Contractions are fine.
- card: on 5 to 10 of the strongest lines, including always line 1: the line's key words, 1 to 3 UPPERCASE words,
  16 characters max with spaces (e.g. "THE MIDDLE TRAP", "SLACK FILL", "BEAT IT"). The last line's card is "FOLLOW".
- scene: the AI library category whose clips best show the line, written exactly as in
  assets/library/library.json ("categories": each cat with its tags), e.g. "checkout", "wallet", "casino", "bank",
  "thinking" for a person doubting, "city-night" for streets. Never the same category on two lines in a row
  (add_content.py checks both). The library clip is shown on about half of the lines, and on every line whose search
  finds no real clip. When no category fits (an anchor, a maze), use "thinking" and make the search words concrete.
- search: for EVERY line, line 1 included, 2 to 5 lowercase words to find real footage on Pixabay of what the line
  shows. A clip is used only if its tags contain EVERY word, so: name filmable things people tag videos with, noun
  first ("popcorn bucket", not "large popcorn"): supermarket, shopping cart, cashier, credit card, wallet, coins, cash,
  receipt, laptop, phone, restaurant, menu, waiter, wine, casino, roulette, dice, car dealership, airport, hotel,
  calendar, calculator, warehouse, delivery, city street. Never ideas or verbs ("comparing", "decision", "trick"),
  never start with an adjective ("car used", not "used car"; "turkey frozen" is wrong too: write "turkey freezer"),
  never brands or people's names. When the full search finds nothing, the system tries the pairs holding its first noun
  (and that noun alone when no category fits the line), then shows the library clip, so put the most important noun first.
  Write woman or man only when a person matters. Words like wedding, christmas, party, baby or halloween are fine
  when the line is about them.
- Variety across the file (add_content.py checks it): one search on at most 20 lines, follow lines excepted; one category
  on at most 13 lines per clip it has in assets/library/library.json. No filler: never put "brain head", "wallet cash",
  "savings jar" or "notebook pen" on a line that is not about those things. When a line is abstract (advice, a conclusion,
  a why), show the script's own subject: the airport in a script about airlines, the store in a script about sales, the
  phone in a script about apps, and switch between two or three categories of that subject so that no category comes
  twice in a row. Use "brain" only when the line is about the brain or the mind.
- gap: pause after the line in seconds: 0.6 to 0.8 after a strong line or a card, 0.3 to 0.5 otherwise.
- caption: one sentence of 8 to 30 words, with words people search for (money tips, save money, the trick's name...),
  no hashtags. hashtags: exactly 4 lowercase topic hashtags; never #moneytricksexposed (added automatically).
Facts and safety, always:
- Check every factual claim with WebSearch (STEP 4) against a reliable source: the study itself or a university
  release, a regulator, a court record, a major news outlet. A number you cannot confirm is dropped or softened
  ("about", "studies suggest"). One study is "one study found", never a law of nature. Do not use studies by Brian
  Wansink (many were retracted). Never invent quotes.
- Name a real company only for documented facts (a lawsuit, a settlement, a regulator's finding, a printed label, its
  own statement), in the past tense, without adding accusations the sources do not make.
- No investment advice, no stock or crypto tips, no get-rich promises, no tax or legal advice beyond general facts.
  Saving and budgeting habits are fine.
- Casino and game topics explain the tricks and end on protecting your money, never on how to win.
- The audience is American: dollars and American examples; when a fact comes from another country, say where
  (London, Britain, France). Never mock or demean any group; no politics.
- Every script is new: do not reuse lines or hooks from other content files. src/add_content.py refuses any repeated
  hook or sentence of 6+ words, so vary the follow lines too (short ones under 6 words may repeat).

STEP 4 - Check facts.
Check with WebSearch every factual claim (names, dates, numbers, who found what). Remove or rewrite anything not
confirmed by a reliable source. Keep a short list of what you changed.

STEP 5 - Validate.
Run: python3 src/add_content.py
It rebuilds topics.json and refuses anything outside the rules (line and word counts, cards, digits and symbols,
search words, hashtags, caption, the hook, the follow line). Fix every problem and run it again until it finishes
without errors and lists no short script.

STEP 6 - Save.
Only commit content/monthNN.json and topics.json. Never change config.json, state.json, notified.json, topic_plan.json,
assets/, src/ or .github/.
git add content topics.json
git commit -m "Add content monthNN (topics X to Y)"
git pull --rebase origin main
git push origin main
If pushing to main is refused, push to a new branch instead and say so clearly in your final message.

FINAL MESSAGE: the topic numbers and date range covered (from the plan's date field), how many lines were changed during
the fact check with two examples, and confirmation that the push to main succeeded.
