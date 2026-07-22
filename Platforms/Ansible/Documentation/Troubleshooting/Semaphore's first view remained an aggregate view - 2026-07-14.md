# Semaphore's first view remained an aggregate view

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Investigated:** 2026-07-14

Renaming the original `All` view to `Onboarding` changed its label but did not make it a filtered view; it still displayed every template. I renamed the view back to `All`, created a separate `Onboarding` view, and reassigned the two onboarding templates to it.

Final UI counts were 18 in `All`, four in each identity view, and two in `Onboarding`. I removed the obsolete `Distribute SSH Keys` template after verifying the replacement set. No template was launched during configuration.
