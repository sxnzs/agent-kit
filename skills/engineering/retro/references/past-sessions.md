# Past-Session Search

Read only when the owner asks to check earlier sessions during Step 2.

## How to search

1. Derive one short query per collected mistake class from Step 1. Use concrete tokens such as the command, error text, file path, or rule name rather than broad words like "mistake".
2. Use the recall skill to search earlier sessions for each query.
3. Filter out passing mentions and keep only sessions where the owner corrected the same class of failure or the agent repeated the same manual step.
4. Append each matching class to the Step 1 list with one line naming the session reference (date or session ID) and a short quote.

## How hits affect routing

When a class appears in both the current session and an earlier session, treat it as a repeated correction. Route it directly to destination 1 (deterministic check) in Step 3 instead of logging a new `.corrections` entry.

Done when every collected class has been queried and all verified matches are in the Step 1 list.
