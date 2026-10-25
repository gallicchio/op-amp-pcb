# Design reviews

Independent reviews of the board before it is ordered, by other LLMs and by the
author, each in its own dated directory so that several can run at once without
touching each other or the project:

    design_reviews/
      DESIGN_REVIEW_PROMPT.md           the brief to give a reviewer
      <YYYY-MM-DD>_<Model-Version>/     one reviewer's directory: REPORT.md and
                                        everything it made or copied
      <YYYY-MM-DD>_<Model-Version>/project/   a reviewer's working copy of the
                                        project (gitignored; never committed)

A reviewer only ever writes inside its own directory. The brief says what to review,
how to work and what the report must contain. A later round gets a later date, so the
rounds sort themselves.

## Round 1, 2026-10-24: rev A before ordering

| directory | reviewer | verdict |
|---|---|---|
| `2026-10-24_Claude-Fable-5.1/` | the author's own review, written before reading any other | order after named fixes: COMPENSATION 2 alone is open circuit, not the bare 100 pF (rewire pole 2); "a short to a rail is survived" is false for the stocked SOT-23 (words); the 50 mA supply limit as the rule; ON marks on the switches; stale numbers. Patch in its `patch_round1.diff`, built clean in its copy; applied to the project on 2026-10-25 before the round opened, with the input terminals' ground symbols turned down as well |

Reconciliation of the round (what each found, what changed) is written up in
`CLAUDE_CODE_CHAT.md` when the round closes.
