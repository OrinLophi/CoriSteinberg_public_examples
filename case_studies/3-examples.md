# Case Studies

*Three essays on systems thinking, design, and building what doesn't exist yet.*

---

## The Invisible User

**The best UX problems are the ones nobody named yet.**

When I took over the dynamic testing operation at NowSecure, I noticed something that should have been obvious but wasn't: there was no way to see how your product was performing.

Not at a glance. Not in a dashboard. Not in a report. If you wanted to understand what was happening with a mobile app's security assessments, you had to log into each individual user account and look at the results one by one. For a platform built to give security teams clarity, the experience of using it was the opposite of clear.

So I started asking questions. What data exists? What matters to the people using this? What would actually be useful to surface, and how? I partnered with research and engineering to identify the right data points across the dynamic testing process and route them through the API in a way that made performance visible for the first time.

But pulling on that thread revealed something bigger underneath.

The data was messy because nobody had ever clearly defined who a user was. There were employee accounts, research accounts, test accounts, legacy accounts, and customer accounts — all living together with no distinction. Some former customers who were no longer paying still had active access. Some accounts had lost all their users but were still running dynamic testing in the background, consuming resources for no reason and for no one.

This was not a technical problem. It was a conceptual one. The organization had never asked: who are our users, and what is the nature of each relationship?

I led a cross-functional initiative to answer that question. I met with leaders across the organization to map internal versus external accounts, identified every account type, and cleaned the data. Then, to make sure the problem could not quietly return, I worked with engineering to add three new labels to the API: Customer, Free Trial, Prospect.

Three words. But they changed how the entire company understood its relationship to the people it served.

That is the work I love: finding the question nobody thought to ask, following it to the structure underneath, and building something that makes the invisible visible.

---

## The Common Language

**Before you can fix a system, you have to give it a language.**

One of the first things I noticed when I joined NowSecure was that every automation was written from scratch.

Every time an engineer wrote an automation to dynamically traverse a mobile application's UI, they started from zero. There was no shared baseline. No common starting point. No agreed-upon definition of what normal looked like.

The consequence was invisible but constant: when something broke, no one could tell whether the problem was in the automation itself or in the underlying product. Every escalation looked unique. Every investigation started from scratch. Progress was impossible to measure because there was nothing consistent to measure against.

This was not an engineering problem. It was a language problem. When everything looks different, nothing can be understood.

So I built the language. I developed a set of templates and base cases that every automation could start from — a shared foundation that defined what normal looked like. Once normal existed, the difference between an automation issue and a product bug became clear. Escalations that had seemed unique started revealing patterns. Problems that had been invisible became legible.

But the real measure of a foundation is what gets built on top of it.

Those templates became the starting point for functional advancements, performance improvements, new product features, and self-service capabilities. Eventually, they became the foundation for AI integration. None of it would have been possible without a shared language to build from.

Scale requires a system. A system requires a language. And someone has to build it first.

---

## The Ballet

**My first design system was drawn on paper in a retail stockroom.**

I was a merchandiser at Gap Inc. when I was assigned to a store that was struggling with its rollouts.

Every time a new collection arrived, it would take the team a week or more to get it onto the floor. Merchandise was being backstocked because there was no room, which meant it wasn't selling at its peak. Margins were suffering. The team was stressed. And the harder they worked, the more chaotic it seemed to get.

The root problem was structural: this was a warm-weather store, and the corporate layout guides had been designed without any awareness of that reality. The instructions did not match the space. So the team was improvising every time, under pressure, without a plan.

I have always been able to hold spatial systems in my mind — to visualize where things need to go before they arrive, and to map the sequence of moves required to get there. So before the next shipment came in, I worked out every shift that needed to happen. I drew maps — crude, but readable — specific to that store's actual layout. I created item logs for the people processing the shipment so no one was left waiting or wondering what to do next.

Everyone had a role. Everyone had the tools they needed. No one was left idling while I figured out the answer in real time.

I thought of it then, and I still think of it now, as a ballet. Moving parts working in sync. A choreography designed so that the chaos of an incoming shipment becomes a coordinated, predictable, even elegant execution.

What I did not have language for at the time was that this was design. It was service design, experience architecture, and change management — wrapped in a retail apron and executed in a stockroom.

The instinct has never changed. See the whole system. Map the dependencies before they become problems. Give people the tools and the clarity to succeed without waiting on you. Make the invisible visible.

It started in a stockroom. It has carried me everywhere since.

---

*These essays were written to accompany the code examples in this repository. The technical work and the thinking behind it are the same work — one expressed in Python and Swift, the other in prose.*
