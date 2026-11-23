# Always-on routing eval runner

Decision: no always-on routing eval runner.

Reason: the invocation split removes most routing collisions at the source, and a model-graded score costs money and varies between runs. `mattpocock/skills` has no evals. Poteto's `noodle` ships a trigger eval tool in its `skill-creator`, run by hand and by no CI. Revisit as an on-demand tool after a routing failure is observed.
