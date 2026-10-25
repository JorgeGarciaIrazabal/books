## F1-P

Four causal beats, close third past through Neri, ticket room → landing, 17:20–17:40.

**Beat 1 — The ask (17:20–17:23, ticket room).** Neri holds the token; Olin produces the reason "I need to see someone." She wants him to name the want plainly, but asking costs her standing with the brother whose approval she still wants. She touches the token through the pocket — a private check that it's still hers — and does not offer it. Olin's counter: "One trip. One." Setup: the token is transferable; its transfer is the story's only irreversible act.

**Beat 2 — The pressure (17:23–17:28, still the room).** Olin raises the clock: gate at 17:55, ferry at 17:40, walk of eight minutes. Neri does the same arithmetic he does, out loud, and he hears it. Her choice is now legible to both of them: keep the token and walk, or hand it over and watch him cross. For the author, a motive is planned (Olin's real reason is his own and stays hidden); at opening, neither Neri nor the reader possesses it, and the plan must not leak it into her POV. Olin acts with his own agency: he does not seize the token — he can't, she keeps it in her pocket — he argues, and he stops, waiting on her answer.

**Beat 3 — The commitment (17:28, doorway of the ticket room).** Neri makes a costly, concrete commitment: she keeps the token, tells Olin she'll walk with him to the landing but not onto the boat, and offers what she can — her presence, the walk, the eight minutes of company without the crossing. The cost is real and immediate: by refusing, she also refuses the reconciliation-by-errand he is offering. Alternative considered and rejected on-page logic: handing it over, which she cannot do without abandoning the apprenticeship she has earned. Payoff: Olin's "One trip. One." lands as answer to a question she asked without asking.

**Beat 4 — The earned outcome (17:29–17:40, the walk).** Feasibility check: 17:28 + 8 minutes = 17:36 arrival; ferry departs 17:40 and cannot wait; Neri boards, Olin does not. The fixed limit — one token, one person, no exception tonight — is accepted, not defeated: she reaches the gate at 17:55 only if the crossing holds to twelve minutes, and the story ends on that arithmetic completing. The gate/apprenticeship is claimed; the sibling question is left open, which is the honest ending for a story about a token. Reader knowledge at close: the token was consumed, she crossed, he didn't, and why he wanted it remains his.

## F1-D

The ticket room smelled of ink and cold metal. Olin stood by the window, watching the landing as if he could see the ferry from here.

"The gate closes at fifty-five," Neri said.

"Mm."

"And the ferry doesn't wait." She touched the token through her right coat pocket. It was warm there, or she imagined it was. "I could walk with you. To the water."

Olin turned. "That's not—" He stopped. His hand came out, not to take anything, just open, then closed again. "You want me to explain myself."

"I want you to want something I can hear."

"One trip. One." He said it like a man reading a fare table, and she hated that he could make it sound reasonable. "You've had yours. The apprenticeship, the—" He gestured at her, at the room, at everything she had built while he was gone.

She moved the token to her left pocket. Her fingers found it there, and she let them stay a moment, as if warmth could transfer. "Then take the trip," she said. "I'll walk with you to the boat."

"You'd do that?"

"I'd do that." The ferry horn sounded once, far off. Twelve minutes, she thought. Eight to walk. "I'd do that, and you'd still owe me an explanation I can believe."

Olin looked at her for a long time, and she kept her face blank, kept the token where her hand could close around it. When he finally looked away, toward the door, she knew he would not take it — not tonight, not without her giving it — and that this was its own kind of answer.

She walked out first, into the cold, and did not look back to see if he followed.

---

**State delta:** Token remains in Neri's custody (left coat pocket) at scene end, 17:28. Neri has committed to escorting Olin to the landing without surrendering passage. Olin's true motive remains unknown to Neri and reader. No boarding has occurred.

## F1-C

```json
{
  "errors": [
    {
      "line": "L1",
      "conflict": "F1-02 fixes the ticket-room-to-landing walk at eight minutes; departing 17:20 would arrive 17:28, not 17:25.",
      "quote": "reached the landing at 17:25 after the eight-minute walk",
      "repair": "Change arrival to 17:28 (or departure to 17:17), keeping the eight-minute walk per F1-02."
    },
    {
      "line": "L3",
      "conflict": "F1-03: Olin's true reason is unknown to Neri and reader at the start; his speech is not objective truth. Neri cannot know his motive.",
      "quote": "She knew Olin wanted it to visit their mother",
      "repair": "Replace with an inference Neri can actually hold, e.g., she suspected or wondered, without asserting his motive as fact."
    },
    {
      "line": "L4",
      "conflict": "F1-02: the last ferry departs at 17:40 and cannot wait. Olin's claim that it will wait until six contradicts a fixed fact, and Neri's disbelief cannot repair the false statement as objective narration.",
      "quote": "The ferry will wait until six",
      "repair": "Either attribute the claim clearly as Olin's lie with Neri's disbelief carrying the scene, or remove the false schedule; the fixed fact is the 17:40 departure."
    },
    {
      "line": "L6",
      "conflict": "F1-01/F1-04: a token admits exactly one person, is consumed on boarding, and the siblings cannot both cross tonight. One token cannot buy passage for both.",
      "quote": "bought passage for both of them with that one token, and both boarded",
      "repair": "Limit boarding to the single token-holder; the other sibling cannot cross tonight."
    },
    {
      "line": "L8",
      "conflict": "F1-02: the crossing takes twelve minutes; a 17:40 departure reaches the far bank at 17:52, not 17:46.",
      "quote": "at 17:46, it reached the far bank",
      "repair": "Change arrival to 17:52 (17:40 + twelve minutes)."
    },
    {
      "line": "L9",
      "conflict": "Close third through Neri: Olin's private state is not available (F1-03). Neri cannot know whether he looked offended; the sentence asserts access to his inner state and then denies it.",
      "quote": "Olin looked offended; she could not tell whether he was",
      "repair": "Describe only observable behavior, e.g., his face went still, or she watched his expression without being able to read it."
    },
    {
      "line": "L10",
      "conflict": "F1-02: last ferry departs 17:40. At 17:32 there are eight minutes until departure — the arithmetic is right — but the scene contract fixes the ticket room window at 17:20–17:28, so a 17:32 timestamp falls outside the scene; additionally the walk to the landing takes eight minutes, so this count would occur at/after arrival, not in the room.",
      "quote": "At 17:32 she counted eight minutes until departure",
      "repair": "Move the count inside the 17:20–17:28 window (e.g., 17:24, sixteen minutes out) or relocate it to the landing at 17:36 with four minutes remaining."
    }
  ],
  "queries": [
    {
      "line": "L5",
      "reason": "Moving the token to the left pocket then retrieving it is physically possible but seems to contradict F1-01's 'right coat pocket' as its fixed location; unclear whether this is intentional business or a custody-tracking slip. If intentional, state delta should record the pocket change."
    },
    {
      "line": "L2/L5",
      "reason": "L2 establishes the token in the right pocket; L5 moves it to the left. Keeping physical custody unambiguous (scene contract) requires that the transfer be deliberate and trackable. Not an error on its own, but flagged for custody clarity."
    }
  ],
  "preserve": ["L7"]
}
```

## F2-P

Four causal beats, close third past through Rafi, booth doorway, 12:00–12:20.

**Beat 1 — The arrival (12:00–12:02).** Rafi has the booth key on the desk and twenty minutes. Leena arrives with Pia; Leena wants the room, Pia wants her take, and neither says the bargain out loud. Rafi notices the violin case before he notices anything else. Setup: the key is a physical, movable object — he can hand it over or move it on the page, and either motion is a decision.

**Beat 2 — The unnamed bargain (12:02–12:04).** Leena works the practical irritation: "We could have half an hour," as though wanting it might change the booking. Rafi hears the ask underneath and does not answer it directly; he is tired of being useful only when something is needed. Leena's agency: she could ask plainly and doesn't — she wants help without discussing the estrangement, and she wants Pia spared the argument. Pia's agency: she is a person with her own attention and discomfort — she asks about the key, she shifts, she watches her mother — not a prop. For the author, a motive for Leena's leaving the band is planned but unknown; at opening, Rafi does not know why, and narration must not endorse any version, including his own suspicions.

**Beat 3 — The commitment (12:04–12:05).** Rafi's consequential choice: he will surrender the slot if Leena asks for him — not the room, him — and the distinction is the story. The cost is concrete: a choice for Pia costs Rafi the audition recording due at 12:30. Feasibility: a take begun at 12:05 runs fifteen minutes to 12:20, exactly the slot's end; there is time for exactly one complete take, not two. Rafi moves the key on the page rather than handing it over, and that motion commits the remaining time to one recording. Payoff: Leena's "Just the room. Not forgiveness." answers the question neither of them named.

**Beat 4 — The earned outcome (12:05–12:20, booth interior).** The fixed limit is accepted, not solved: the other group's booking at 12:20 is unchangeable, and one uninterrupted fifteen-minute take cannot serve two applications. Rafi records; Pia plays. No healed family relationship is required or shown — the audition is lost, the estrangement is unspoken, and the scene ends on the recording running out at 12:20 with the door release that follows. The comic warmth lives in the timing and the practical negotiation, not in reconciliation.

## F2-D

The key sat on the desk like a small accusation. Rafi picked it up, turned it over in his fingers, and put it in his bag. Leena was already talking.

"We could have half an hour," she said, as though wanting it might change the booking. "Twenty minutes, even. Pia's—" She stopped, glanced at her daughter, and started again. "The audition's at twelve-thirty. Hers too."

Pia had the violin case open on her knees and was tightening a bow with her teeth, watching the door. Rafi watched her watch the door.

"You need the room," Rafi said.

"I need the room." Leena said it flat, no music in it. "You need the room."

"At twelve-twenty the next group—"

"Unchangeable," Leena said. "I know. I know the schedule." She leaned against the doorframe, arms crossed over her chest, the way she used to when they argued about set lists. "Just the room. Not forgiveness."

Rafi took the key out of his bag. He held it out, then set it back on the desk between them, closer to her side. Pia looked up from her bow, frowned, and went back to the rosin.

"Ask me," Rafi said.

Leena's arms stayed crossed. "Ask you what?"

"Ask me. For you." He kept his hand on the key, not pushing it across. "I'll give you the time if you ask for me. Not the booth. Me."

Pia said, "Mama, your shoe's untied," and bent to look at her own feet, then hers, then stopped.

Rafi counted: fifteen minutes, one take, the group at twelve-twenty. He slid the key across the desk. It stopped at the edge of her shadow.

"For Pia," Leena said. "Just the room. Not forgiveness."

Rafi opened the booth door and held it. He did not step aside for her apology. He stepped aside for the violin.

---

**State delta:** Booth key transferred to Leena at ~12:05 via desk slide after conditional offer; Rafi's audition recording forfeited. Leena's reason for leaving the band remains unknown to Rafi and reader. Estrangement undiscussed; no reconciliation depicted. One complete take remains possible before 12:20.

## F2-C

```json
{
  "errors": [
    {
      "line": "L2",
      "conflict": "F2-03: Rafi starts with the key on the desk and 'can hand it over or move it on the page.' Putting it in his bag and then fetching it when Pia asked transfers custody away and back without a decision; also 'when Pia asked' implies Pia receives or handles the key, which the contract does not authorize. Key custody must stay clear.",
      "quote": "put it in his bag, then fetched it from the bag when Pia asked",
      "repair": "Keep the key on the desk or in Rafi's hand until a deliberate handover; do not route custody through Pia."
    },
    {
      "line": "L3",
      "conflict": "F2-01: the booth is booked only until 12:20, and F2-02 requires one uninterrupted fifteen-minute recording due 12:30. There is no half hour to 'have'; the slot is twenty minutes, and a joint take cannot fit.",
      "quote": "We could have half an hour",
      "repair": "Have Leena misstate the schedule in a way the fixed facts correct (e.g., 'We could use twenty minutes'), or give her a line about wanting more time than exists, with Rafi's knowledge correcting it."
    },
    {
      "line": "L4",
      "conflict": "F2-02 fixes the surname as Kapoor; 'Kappor' contradicts the fixed name.",
      "quote": "Leena Kappor stood in the doorway",
      "repair": "Correct the spelling to 'Leena Kapoor.'"
    },
    {
      "line": "L6",
      "conflict": "F2-02: a joint take or edited fragments cannot satisfy either application; the slot cannot produce both complete takes. One fifteen-minute joint take cannot satisfy both.",
      "quote": "one fifteen-minute joint take would satisfy both applications",
      "repair": "Remove the claim; a joint take satisfies neither application under F2-02."
    },
    {
      "line": "L8",
      "conflict": "F2-03: Rafi does not know why Leena left the band and cannot access her thoughts; envy is asserted as his knowledge with no evidence or source.",
      "quote": "Rafi knew she had left the band because she envied him",
      "repair": "Convert to unsupported suspicion clearly marked as his, e.g., he wondered if it was envy, or remove the causal claim entirely."
    },
    {
      "line": "L10",
      "conflict": "F2-01/F2-02: the next group's booking is at 12:20, not 12:05 + fifteen minutes as an independent fact; at 12:05 there are fifteen minutes until the 12:20 booking — the count is correct — but the scene contract fixes the doorway window at 12:00–12:05, so a 12:05 count sits at the window's edge; more importantly, if a take begins at 12:05 it ends exactly at 12:20, meaning the count conflates the slot end with the next booking as if more time remained. The arithmetic itself (fifteen minutes from 12:05 to 12:20) is consistent; flagged as a boundary case rather than a hard error.",
      "quote": "At 12:05 he counted fifteen minutes until the next group's booking",
      "repair": "If treated as an error: anchor the count earlier (12:00–12:05 window) or make clear the fifteen minutes ends exactly at the unchangeable 12:20 booking with no margin."
    }
  ],
  "queries": [
    {
      "line": "L1",
      "reason": "Arithmetically consistent with F2-01/F2-02 (12:05 + 15 = 12:20) and matches the scene contract's implied timeline, but it pre-commits the story's central choice before any negotiation occurs; a structural question, not a factual error."
    },
    {
      "line": "L5",
      "reason": "Rafi's conditional ('he would surrender the slot if Leena asked') is compatible with F2-03/F2-04, but whether this constitutes a resolved choice or an intention is a matter of scene execution, not fixed facts; retained as a valid line pending how the commitment lands."
    },
    {
      "line": "L10",
      "reason": "See error entry; the timestamp sits at the scene window's boundary (12:00–12:05) and the count is correct, so this is a query about placement and emphasis rather than a definite factual contradiction."
    }
  ],
  "preserve": ["L7", "L9"]
}
```
